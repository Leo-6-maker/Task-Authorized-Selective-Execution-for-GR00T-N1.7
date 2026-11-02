"""CPU export integrity tests; production originals are never modified."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from review_tools.recheck_e3_final import PACKAGE, analyze, recheck


class FinalExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        p = cls.repo/PACKAGE
        load = lambda name: json.loads((p/name).read_text())
        cls.base = [load('AUDIT_FINAL_ORIGINAL.json'), load('LEDGER.json'),
                    json.loads((cls.repo/'configs/e3_cells.proposed.json').read_text())['cells'],
                    load('CHECKPOINTS.json'), load('ORIGINAL_INVENTORY.json')]

    def setUp(self):
        self.args = copy.deepcopy(self.base)

    def rejected(self):
        with self.assertRaises(ValueError):
            analyze(*self.args)

    def test_actual_complete_export(self):
        result = analyze(*self.args)
        self.assertEqual((result['eligible'], result['unknown'], result['clean_G_workers']), (160, 0, 72))

    def test_missing_planned_unit(self):
        self.args[1].pop()
        self.rejected()

    def test_duplicate_id(self):
        self.args[1][1]['run_id'] = self.args[1][0]['run_id']
        self.rejected()

    def test_unknown_must_not_be_safe(self):
        self.args[0]['epochs'][0]['rows'][0]['outcome_known'] = False
        self.rejected()

    def test_native_failure_cannot_be_success(self):
        self.args[1][0]['native_exit'] = 1
        self.rejected()

    def test_original_0001_cannot_acquire_new_identity(self):
        self.args[1][0]['authorization']['authorized_head'] = self.args[1][1]['authorization']['authorized_head']
        self.rejected()

    def test_original_0001_cannot_replace_historical_grant(self):
        self.args[1][0]['authorization']['review_commit'] = '0'*40
        self.rejected()

    def test_wrong_source_hash(self):
        self.args[1][0]['result_sha256'] = '0'*64
        self.rejected()

    def test_reject_cannot_execute(self):
        decision = self.args[1][1]['decisions'][0]
        decision['decision'] = 'REJECT'
        self.rejected()

    def test_wrong_arm_seed(self):
        self.args[1][1]['cell']['policy_seed'] += 1
        self.rejected()

    def test_worker_forced_termination_not_clean(self):
        self.args[1][1]['shadow_lifecycle']['forced'] = True
        self.rejected()

    def test_rng_guard_failure(self):
        self.args[1][1]['noninterference_all_state_rng_unchanged'] = False
        self.rejected()

    def test_missing_checkpoint(self):
        self.args[3].pop()
        self.rejected()

    def test_counterfeit_statistics(self):
        self.args[0]['statistics']['groups'][0]['metrics']['wrong_lift']['bounds'] = [1, 1]
        self.rejected()

    def test_export_tamper_rejected_before_other_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'LEDGER.json').write_text('tampered')
            (p/'SOURCE_BINDING.json').write_text(json.dumps({
                'public_data_sha256': {'LEDGER.json': '0'*64}}))
            with self.assertRaisesRegex(ValueError, 'public data hash differs'):
                recheck(self.repo, p)


if __name__ == '__main__':
    unittest.main()
