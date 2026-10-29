"""Synthetic incremental backups retain prior data, failure bytes and hashes."""
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from scripts.e2_backup import backup


class BackupTests(unittest.TestCase):
    def test_delta_requires_verified_base_and_retains_changes(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'runs').mkdir();(root/'runs/failed.txt').write_text('failure')
            (root/'runs/unchanged.txt').write_text('keep')
            base=backup(root,'first')
            with self.assertRaises(FileNotFoundError):backup(root,'blocked','first')
            (root/'evidence_exports/first/second-copy-verification.json').write_text(json.dumps({**base,'status':'TWO_LOCATIONS_ARCHIVE_AND_EVERY_MEMBER_SHA256_VERIFIED'}))
            (root/'runs/failed.txt').write_text('failure plus retained diagnostic')
            delta=backup(root,'delta','first')
            self.assertEqual(delta['artifacts'],1);self.assertEqual(delta['unchanged_in_verified_base'],1)
            with tarfile.open(root/'evidence_exports/delta/evidence.tar.gz','r:gz') as archive:
                self.assertEqual(archive.extractfile('runs/failed.txt').read(),b'failure plus retained diagnostic')
                manifest=json.load(archive.extractfile('backup-manifest.json'))
                self.assertEqual(len(manifest['source_index']),2);self.assertEqual(manifest['base_archive']['sha256'],base['sha256'])
            self.assertEqual((root/'runs/unchanged.txt').read_text(),'keep')


if __name__=='__main__':unittest.main()
