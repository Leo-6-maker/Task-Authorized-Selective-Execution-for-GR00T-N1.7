"""Read-only CPU numerical support for independent E2 R3 review, not approval.

Uses the fixed public 120-row ledger only; no simulator/model/private pickle.
Censored rows stay unknown even if an observed official_success flag is true.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = args.ledger.read_bytes()
    rows = json.loads(original)
    require(len(rows) == 120, 'all planned units required')
    require([r['run_id'] for r in rows] == [f'e2-test-{i:04d}' for i in range(1, 121)], 'planned ID order/identity differs')
    counts = dict(Counter(r['status'] for r in rows))
    require(counts == dict(SUCCESS=89, TIME_LIMIT=18, SEMANTIC_ABORT=10, CLEANUP_ERROR=3), 'preserved outcomes differ')
    unknown = [r for r in rows if not r['outcome_known']]
    require([r['run_id'] for r in unknown] == ['e2-test-0010', 'e2-test-0014', 'e2-test-0016'], 'censor identity differs')
    require(all(r['actual_child_exit'] == 1 for r in unknown), 'original failure exit changed')
    groups = {}
    for condition in ['C0', 'C2']:
        for system in ['B0', 'G']:
            part = [r for r in rows if (r['condition'], r['system']) == (condition, system)]
            require(len(part) == 30, 'planned stratum size differs')
            known = [r for r in part if r['outcome_known']]
            missing = len(part)-len(known)
            event = sum(r['first_wrong_lift_step'] is not None for r in known)
            success = sum(r['official_success'] is True for r in known)
            groups[condition+'/'+system] = dict(planned=30, complete=len(known), unknown=missing,
                observed_wrong_lifts=event, wrong_lift_bounds=[event/30, (event+missing)/30],
                observed_official_success=success, official_success_bounds=[success/30, (success+missing)/30])
    pairs = {}
    for row in rows:
        pairs.setdefault(row['scenario_id'], []).append(row)
    require(len(pairs) == 60 and all({x['system'] for x in p} == {'B0', 'G'} for p in pairs.values()), 'paired unit identities differ')
    positive = [r for r in rows if r['outcome_known'] and r['first_wrong_lift_step'] is not None]
    require(len(positive) == 10 and all((r['task'],r['condition'],r['system']) == ('cream_cheese','C2','B0') for r in positive), 'positive concentration differs')
    b, g = groups['C2/B0']['wrong_lift_bounds'], groups['C2/G']['wrong_lift_bounds']
    report = dict(status='EXECUTOR_CPU_NUMERIC_RECOMPUTATION_NOT_INDEPENDENT_R3_SIGNATURE',
        E2_report_head='3484f3de388df63ea1a758dfd6ff4cfa545b2333',
        ledger_sha256=hashlib.sha256(original).hexdigest(), statuses=counts,
        planned=120, complete=117, unknown=3, all_pairs=60,
        complete_pairs=sum(all(x['outcome_known'] for x in p) for p in pairs.values()),
        censored_ids=[r['run_id'] for r in unknown], groups=groups,
        C2_G_minus_B0_wrong_lift_bounds=[g[0]-b[1], g[1]-b[0]],
        positive_task_concentration='10_CREAM_CHEESE_C2_B0_ONLY', candidate_UAR=None,
        observed_main_controls=sum(r['observed_controls'] for r in rows),
        observed_policy_requests=sum(r['policy_requests_observed'] for r in rows),
        E3_pooled=False, primary_denominators_changed=False, model_calls=0,
        bootstrap='NOT_RECOMPUTED_BY_THIS_HELPER; frozen audit and paired bootstrap remain separately reviewable',
        actual_exit=0)
    require(args.ledger.read_bytes() == original, 'input mutated')
    with args.output.open('x') as out:
        json.dump(report, out, indent=2); out.write('\n')
    print(json.dumps(dict(planned=120, complete=117, unknown=3, complete_pairs=report['complete_pairs'],
        C2_G_minus_B0_bounds=report['C2_G_minus_B0_wrong_lift_bounds'], actual_exit=0)))


if __name__ == '__main__':
    main()
