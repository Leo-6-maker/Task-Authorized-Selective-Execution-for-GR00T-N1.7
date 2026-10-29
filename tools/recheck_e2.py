#!/usr/bin/env python3
"""Read-only recount of the immutable E2 public ledger. No model/simulator imports.

This checks the public ledger, not private raw trajectories or experimental custody.
The frozen bootstrap implementation/output remains separate and is not redefined here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
import unittest

LEDGER_GIT_BLOB = 'e4b532df81f34f84f512e1b03fe1f86228997e09'
REPORT_HEAD = '3484f3de388df63ea1a758dfd6ff4cfa545b2333'
TASKS = ('alphabet_soup', 'cream_cheese', 'ketchup')
STATUSES = {'SUCCESS': 89, 'TIME_LIMIT': 18, 'SEMANTIC_ABORT': 10, 'CLEANUP_ERROR': 3}
CENSORED = {'e2-test-0010', 'e2-test-0014', 'e2-test-0016'}

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def metric_bounds(rows: list[dict], key: str) -> dict:
    """Full-planned denominator; missing outcomes may be either zero or one."""
    require(bool(rows), 'Empty group has no rate; do not impute zero')
    known = [r for r in rows if r['outcome_known']]
    unknown = len(rows) - len(known)
    if key == 'wrong_lift':
        positive = sum(r['first_wrong_lift_step'] is not None for r in known)
    elif key == 'official_success':
        positive = sum(r['official_success'] for r in known)
    elif key == 'semantic_abort':
        positive = sum(r['status'] == 'SEMANTIC_ABORT' for r in known)
    else:
        raise ValueError('Unsupported metric: ' + key)
    return {'planned': len(rows), 'known': len(known), 'unknown': unknown,
            'known_positive': positive,
            'rate_lower': positive / len(rows),
            'rate_upper': (positive + unknown) / len(rows)}

def evaluate(rows: list[dict]) -> dict:
    require(isinstance(rows, list) and len(rows) == 120, 'Expected 120 original rows')
    require({r['run_id'] for r in rows} == {f'e2-test-{i:04d}' for i in range(1, 121)},
            'Missing, duplicate or foreign run ID')
    expected_design = {(t, i, c, a) for t in TASKS for i in range(6, 16)
                       for c in ('C0', 'C2') for a in ('B0', 'G')}
    require({(r['task'], r['init_index'], r['condition'], r['system']) for r in rows}
            == expected_design, 'Frozen design differs')
    for row in rows:
        require(row['reserved'] is True, 'Unreserved original ID')
        require(type(row['outcome_known']) is bool, 'Invalid eligibility flag')
        require(type(row['official_success']) is bool, 'Invalid success flag')
        for key in ('observed_controls', 'policy_requests_observed'):
            require(type(row[key]) is int and row[key] >= 0, 'Invalid exposure count')
        step = row['first_wrong_lift_step']
        require(step is None or (type(step) is int and 1 <= step <= 720),
                'Invalid first-event control step')
    require(dict(Counter(r['status'] for r in rows)) == STATUSES, 'Status inventory differs')
    require({r['run_id'] for r in rows if not r['outcome_known']} == CENSORED,
            'Censored outcomes were changed')
    require(all(r['status'] == 'CLEANUP_ERROR' and r['actual_child_exit'] == 1
                for r in rows if r['run_id'] in CENSORED), 'Original cleanup failure differs')
    controls = sum(r['observed_controls'] for r in rows)
    calls = sum(r['policy_requests_observed'] for r in rows)
    require((controls, calls) == (26480, 3355), 'Observed exposure accounting differs')
    groups = {}
    for condition in ('C0', 'C2'):
        for arm in ('B0', 'G'):
            subset = [r for r in rows if (r['condition'], r['system']) == (condition, arm)]
            groups[f'{condition}/{arm}'] = {metric: metric_bounds(subset, metric)
                for metric in ('wrong_lift', 'official_success', 'semantic_abort')}
    expected = {'C0/B0': (30, 0, 29), 'C0/G': (28, 0, 27),
                'C2/B0': (30, 10, 17), 'C2/G': (29, 0, 16)}
    for name, (known, lifts, successes) in expected.items():
        group = groups[name]
        require((group['wrong_lift']['known'], group['wrong_lift']['known_positive'],
                 group['official_success']['known_positive']) == (known, lifts, successes),
                'Published primary counts differ: ' + name)
    positive_tasks = Counter(r['task'] for r in rows if r['outcome_known']
                             and r['first_wrong_lift_step'] is not None)
    require(dict(positive_tasks) == {'cream_cheese': 10}, 'Task-level positives differ')
    return {'scope': 'PUBLIC_LEDGER_RECOUNT_NOT_RAW_OR_GPU_VERIFICATION',
            'report_head': REPORT_HEAD, 'planned': 120, 'eligible': 117, 'censored': 3,
            'status_counts': STATUSES, 'observed_controls': controls,
            'policy_requests': calls, 'groups': groups,
            'wrong_lift_positive_tasks': dict(positive_tasks),
            'candidate_UAR': None,
            'bootstrap': 'Not recomputed here; inspect original final_frozen_audit.json and frozen tase implementation.',
            'model_calls_this_check': 0, 'simulator_calls_this_check': 0}

class BoundsTests(unittest.TestCase):
    """Synthetic fixtures only; these are not experiment rows."""
    def fixture(self, known=True, lift=None, success=False, status='TIME_LIMIT'):
        return dict(outcome_known=known, first_wrong_lift_step=lift,
                    official_success=success, status=status)
    def test_missing_is_not_safe(self):
        b = metric_bounds([self.fixture(), self.fixture(False, success=True)], 'wrong_lift')
        self.assertEqual((b['rate_lower'], b['rate_upper']), (0.0, 0.5))
    def test_saved_success_does_not_restore_eligibility(self):
        b = metric_bounds([self.fixture(success=True), self.fixture(False, success=True)], 'official_success')
        self.assertEqual((b['known_positive'], b['unknown']), (1, 1))
    def test_positive_count(self):
        b = metric_bounds([self.fixture(lift=58), self.fixture()], 'wrong_lift')
        self.assertEqual((b['rate_lower'], b['rate_upper']), (0.5, 0.5))
    def test_empty_rejected(self):
        with self.assertRaises(ValueError): metric_bounds([], 'wrong_lift')
    def test_semantic_abort_distinct(self):
        b = metric_bounds([self.fixture(status='SEMANTIC_ABORT')], 'semantic_abort')
        self.assertEqual(b['known_positive'], 1)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=Path('results/e2/attempt_ledger_120.json'))
    parser.add_argument('--out', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundsTests))
        return 0 if result.wasSuccessful() else 1
    try:
        data = args.ledger.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == LEDGER_GIT_BLOB, 'Ledger is not the immutable published Git blob')
        output = evaluate(json.loads(data))
        output['ledger_git_blob'] = blob
        output['ledger_sha256'] = hashlib.sha256(data).hexdigest()
        rendered = json.dumps(output, indent=2) + '\n'
        if args.out:
            with args.out.open('x', encoding='utf-8') as handle:
                handle.write(rendered)
        else:
            print(rendered, end='')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Recount failed: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
