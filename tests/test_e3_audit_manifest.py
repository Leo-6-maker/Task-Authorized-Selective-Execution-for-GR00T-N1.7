"""CPU native-manifest integration and mutation negatives; no simulator/model."""
import json
from pathlib import Path
import tempfile
import unittest
from e3.audit_manifest import verify_complete_manifest
from tase.e2_evidence import manifest


class CompleteNativeManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace=Path(self.temp.name)
        self.folder=self.workspace/'runs/E3A_TEST/e3a-test-0001'
        self.folder.mkdir(parents=True)
        self.required=['reservation.json','runner_claim.json','result.json','task_spec.json']
        for name in self.required+['physical_frames.jsonl','action-000.npz','observation-000.npz',
                                  'snapshot-000.pkl','controller.json']:
            (self.folder/name).write_bytes(('SYNTHETIC_CPU_PLACEHOLDER '+name).encode())
        self.seal()
        (self.folder/'supervisor_exit.json').write_text(json.dumps(dict(
            complete_child_receipt=True,wrapper_returncode=0)))

    def seal(self):
        records=manifest(self.workspace,[f for f in self.folder.iterdir()
                         if f.name not in ['artifact_manifest.json','supervisor_exit.json']],self.folder.name)
        (self.folder/'artifact_manifest.json').write_text(json.dumps(records))

    def verify(self):verify_complete_manifest(self.workspace,self.folder,self.required)

    def records(self):return json.loads((self.folder/'artifact_manifest.json').read_text())
    def write_records(self,v):(self.folder/'artifact_manifest.json').write_text(json.dumps(v))

    def test_complete_superset_and_late_supervisor_receipt_pass(self):
        self.assertGreater(len(self.records()),len(self.required))
        self.verify()

    def test_no_late_supervisor_yet_does_not_change_runner_manifest(self):
        # This helper verifies runner coverage only. Eligibility still needs the
        # independent ledger's completed supervisor/child exit0 checks.
        (self.folder/'supervisor_exit.json').unlink()
        self.verify()

    def test_mandatory_file_missing_even_if_manifest_resealed_denied(self):
        (self.folder/'task_spec.json').unlink();self.seal()
        with self.assertRaisesRegex(ValueError,'missing native originals'):self.verify()

    def test_extra_native_file_omitted_from_manifest_denied(self):
        rows=[x for x in self.records() if not x['artifact_id'].endswith('/action-000.npz')]
        self.write_records(rows)
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):self.verify()

    def test_native_file_added_after_sealing_denied(self):
        (self.folder/'unrecorded.txt').write_text('new original')
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):self.verify()

    def test_manifest_file_absent_from_directory_denied(self):
        (self.folder/'controller.json').unlink()
        with self.assertRaises(FileNotFoundError):self.verify()

    def test_changed_original_bytes_denied(self):
        (self.folder/'physical_frames.jsonl').write_text('changed original')
        with self.assertRaisesRegex(ValueError,'content mismatch'):self.verify()

    def test_duplicate_manifest_identity_denied(self):
        rows=self.records();rows.append(rows[0]);self.write_records(rows)
        with self.assertRaisesRegex(ValueError,'duplicate artifact ID'):self.verify()

    def test_cross_episode_source_run_denied(self):
        rows=self.records();rows[0]['source_run']='e3a-test-0002';self.write_records(rows)
        with self.assertRaisesRegex(ValueError,'cross-run'):self.verify()

    def test_external_file_cannot_expand_expected_coverage(self):
        external=self.workspace/'runs/external.txt';external.write_text('outside episode')
        self.write_records(self.records()+manifest(self.workspace,[external],self.folder.name))
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):self.verify()

    def test_symlink_original_and_unexpected_subdirectory_denied(self):
        for kind in ['symlink','directory']:
            p=self.folder/'untrusted'
            if kind=='symlink':p.symlink_to(self.folder/'result.json')
            else:p.mkdir()
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError,'non-file/symlink'):self.verify()
            if kind=='symlink':p.unlink()
            else:p.rmdir()

    def test_manifest_may_not_cover_its_own_or_late_receipt_bytes(self):
        for name in ['artifact_manifest.json','supervisor_exit.json']:
            rows=self.records()
            rows+=manifest(self.workspace,[self.folder/name],self.folder.name)
            self.write_records(rows)
            with self.subTest(name=name):
                with self.assertRaises(ValueError):self.verify()
            self.seal()


if __name__=='__main__':unittest.main()
