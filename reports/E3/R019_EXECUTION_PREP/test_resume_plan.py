"""CPU-only planning negative/integration tests using real reviewed fixtures.

These tests never issue grants, import native packages or reserve a real ID.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('E3_APPROVED_CPU_REPO',
                           '/nonexistent-use-E3_APPROVED_CPU_REPO'))
module = importlib.util.spec_from_file_location('readonly_resume_plan', HERE/'resume_plan.py')
plan = importlib.util.module_from_spec(module)
module.loader.exec_module(plan)


class ResumePlanTests(unittest.TestCase):
    def setUp(self):
        self.cells = json.loads((REPO/'configs/e3_cells.proposed.json').read_text())['cells']
        self.audit = json.loads((REPO/'reports/E3/R018/RECONCILED_ANALYSIS_v1.json').read_text())['audit']
        self.review = json.loads((HERE/'R019_REVIEW.original.json').read_text())
        self.rec = json.loads((REPO/'reports/E3/R018/RECONCILIATION_0001_v1.json').read_text())

    def build(self):
        return plan.build(self.cells, self.audit, self.review, self.rec)

    def test_exact159_and_first_checkpoint_reuses_only_original0001(self):
        before = copy.deepcopy([self.cells, self.audit, self.review, self.rec])
        value = self.build()
        self.assertEqual(len(value['remaining_once_only_ids']), 159)
        self.assertNotIn('e3a-test-0001', value['remaining_once_only_ids'])
        self.assertEqual(value['remaining_once_only_ids'][0], 'e3a-test-0002')
        self.assertEqual(value['checkpoints'][0]['all_original_ids'],
                         [f'e3a-test-{i:04d}' for i in range(1, 5)])
        self.assertEqual(value['checkpoints'][0]['historical_reuse_only'], ['e3a-test-0001'])
        self.assertEqual([self.cells, self.audit, self.review, self.rec], before)
        self.assertFalse(value['native_execution_authorized'])

    def test_all28_A4_and8_B6_checkpoints_keep_original_order(self):
        value = self.build()
        blocks = value['checkpoints']
        self.assertEqual([len([b for b in blocks if b['epoch'] == e])
                          for e in ['E3A', 'E3B']], [28, 8])
        self.assertEqual([i for b in blocks for i in b['all_original_ids']],
                         [c['run_id'] for c in self.cells])
        self.assertEqual(blocks[28]['through'], 6)
        self.assertTrue(all(b['actual_checkpoint_status'] == 'NOT_EXECUTED' for b in blocks))

    def test_zero_consumption_must_not_restart0001(self):
        first = self.audit['epochs'][0]['rows'][0]
        first.update(reserved=False, outcome_known=False, status='NOT_STARTED', actual_exit=None)
        with self.assertRaisesRegex(ValueError, 'no replay'):
            self.build()

    def test_unexpected_consumed0002_stops_instead_of_skipping(self):
        self.audit['epochs'][0]['rows'][1].update(
            reserved=True, outcome_known=True, status='SUCCESS', actual_exit=0)
        with self.assertRaisesRegex(ValueError, 'unexpected reservation'):
            self.build()

    def test_partial_or_failed_unknown_record_never_replaced(self):
        for status in ['INTERRUPTED_OR_PARTIAL', 'CLEANUP_ERROR', 'ERROR']:
            with self.subTest(status=status):
                first = self.audit['epochs'][0]['rows'][0]
                first.update(status=status, outcome_known=False, actual_exit=1)
                with self.assertRaises(ValueError):
                    self.build()

    def test_false_aggregate_cannot_hide_full_rows(self):
        self.audit['epochs'][0]['consumed'] = 0
        with self.assertRaisesRegex(ValueError, 'aggregate'):
            self.build()

    def test_missing_or_duplicate_original_ID_denied(self):
        original = copy.deepcopy(self.cells)
        for kind in ['missing', 'duplicate']:
            with self.subTest(kind=kind):
                self.cells = copy.deepcopy(original)
                if kind == 'missing':
                    self.cells.pop()
                else:
                    self.cells[-1] = self.cells[-2]
                with self.assertRaises(ValueError):
                    self.build()

    def test_seed_or_arm_drift_denied(self):
        for field, value in [('policy_seed', -1), ('system', 'A0')]:
            with self.subTest(field=field):
                original = self.cells[1][field]
                self.cells[1][field] = value
                with self.assertRaisesRegex(ValueError, 'identity drift'):
                    self.build()
                self.cells[1][field] = original

    def test_old_acquisition_and_grant_cannot_be_rewritten(self):
        for field in ['execution_head', 'review_commit']:
            with self.subTest(field=field):
                before = self.rec['acquisition'][field]
                self.rec['acquisition'][field] = plan.APPROVED_HEAD
                with self.assertRaisesRegex(ValueError, 'acquisition rewritten'):
                    self.build()
                self.rec['acquisition'][field] = before

    def test_result_or_manifest_hash_conflict_denied(self):
        for field in ['original_result', 'original_manifest']:
            with self.subTest(field=field):
                before = self.rec[field]['sha256']
                self.rec[field]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    self.build()
                self.rec[field]['sha256'] = before

    def test_missing_or_duplicate_custody_file_denied(self):
        before = copy.deepcopy(self.rec['original_files'])
        for kind in ['missing', 'duplicate']:
            with self.subTest(kind=kind):
                self.rec['original_files'] = copy.deepcopy(before)
                if kind == 'missing':
                    self.rec['original_files'].pop()
                else:
                    self.rec['original_files'][-1] = self.rec['original_files'][0]
                with self.assertRaisesRegex(ValueError, 'unique78'):
                    self.build()

    def test_old_frozen_failure_must_remain_failed(self):
        self.rec['old_frozen_audit_failures'][0]['actual_exit'] = 0
        with self.assertRaisesRegex(ValueError, 'old frozen failure'):
            self.build()

    def test_incomplete_physics_audit_cannot_promote_eligibility(self):
        self.rec['checks']['actual_physics_oracle_action_checks'] = False
        with self.assertRaisesRegex(ValueError, 'incomplete reconciliation'):
            self.build()

    def test_R019_cannot_be_upgraded_to_execution_permission(self):
        self.review['authorization_boundary']['new_TEST_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'cannot become an execution grant'):
            self.build()

    def cli(self, root, review=None, output=None):
        audit = root/'audit.json'
        audit.write_text(json.dumps(self.audit))
        review_path = root/'review.json'
        review_path.write_bytes((HERE/'R019_REVIEW.original.json').read_bytes()
                                if review is None else json.dumps(review).encode())
        command = [sys.executable, *(['-O'] if sys.flags.optimize else []),
                   str(HERE/'resume_plan.py'), '--repo', str(REPO),
                   '--workspace', str(root/'workspace'), '--audit', str(audit),
                   '--review', str(review_path), '--reconciliation',
                   str(REPO/'reports/E3/R018/RECONCILIATION_0001_v1.json'),
                   '--output', str(output or root/'plan.json')]
        return subprocess.run(command, capture_output=True, text=True)

    def test_actual_CLI_writes_new_plan_then_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            result = self.cli(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            raw = (root/'plan.json').read_bytes()
            self.assertFalse(json.loads(raw)['native_execution_authorized'])
            second = self.cli(root)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(raw, (root/'plan.json').read_bytes())

    def test_actual_CLI_rejects_forged_review_without_output(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self.review['disposition'] = 'E3_TEST_AUTHORIZED'
            result = self.cli(root, review=self.review)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root/'plan.json').exists())

    def test_actual_CLI_refuses_write_inside_original_runs(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            output = root/'workspace/runs/new-plan.json'
            output.parent.mkdir(parents=True)
            result = self.cli(root, output=output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
