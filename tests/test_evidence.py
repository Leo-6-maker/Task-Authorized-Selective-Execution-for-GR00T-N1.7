"""CPU evidence-integrity tests; no model or simulation is mocked as real."""
import tempfile
import unittest
from pathlib import Path
from tase.evidence import manifest, reserve_episode, verify_manifest, write_json


class EvidenceTests(unittest.TestCase):
    def test_failed_and_incomplete_reservations_consume_full_budget(self):
        with tempfile.TemporaryDirectory() as d:
            for i in range(24):
                reserve_episode(d, f'run-{i}', {'split': 'DEV'})
            with self.assertRaises(RuntimeError):
                reserve_episode(d, 'run-25', {'split': 'DEV'})

    def test_reuse_cannot_overwrite_failure(self):
        with tempfile.TemporaryDirectory() as d:
            folder = reserve_episode(d, 'failed', {'split': 'DEV'})
            write_json(folder / 'result.json', {'status': 'ENV_ERROR'})
            with self.assertRaises(FileExistsError):
                reserve_episode(d, 'failed', {'split': 'DEV'})
            self.assertIn('ENV_ERROR', (folder / 'result.json').read_text())

    def test_non_dev_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for split in ['TEST', 'CALIB', None]:
                with self.assertRaises(ValueError):
                    reserve_episode(d, 'x', {'split': split})
            with self.assertRaises(ValueError):
                reserve_episode(d, '../escape', {'split': 'DEV'})

    def test_tampered_artifact_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'action.bin'
            p.write_bytes(b'original')
            records = manifest(d, [p], 'dev-1')
            verify_manifest(d, records)
            p.write_bytes(b'modified')
            with self.assertRaises(ValueError):
                verify_manifest(d, records)

    def test_external_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e:
            p = Path(e) / 'private'
            p.write_text('outside')
            with self.assertRaises(ValueError):
                manifest(d, [p], 'dev-1')

    def test_busy_reservation_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / '.reservation-lock').mkdir()
            with self.assertRaises(FileExistsError):
                reserve_episode(d, 'x', {'split': 'DEV'})


if __name__ == '__main__':
    unittest.main()
