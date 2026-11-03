"""Synthetic E2 path/byte boundaries; no model or physics."""
import json
import tempfile
from pathlib import Path
import unittest
from tase.evidence import sha256
from tase.e2_evidence import manifest,verify_manifest


class E2StorageTests(unittest.TestCase):
    def fixture(self,base):
        root=base/'workspace';cache=base/'task-cache';root.mkdir();cache.mkdir()
        target=cache/'runs-local';target.mkdir();(target/'DEV').mkdir()
        path=target/'DEV/sample.bin';path.write_bytes(b'original E2 bytes')
        (root/'runs').symlink_to(target,target_is_directory=True)
        owner=cache/'e2-cache-ownership.json';owner.write_text(json.dumps({'epoch':'E2','workspace':str(root)}))
        (root/'operator').mkdir()
        (root/'operator/e2-storage-alias.json').write_text(json.dumps({'epoch':'E2','workspace':str(root),
            'cache_root':str(cache),'target':str(target),'ownership_marker_sha256':sha256(owner)}))
        return root,cache,path

    def test_owned_alias_preserves_ids_and_byte_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root,cache,path=self.fixture(Path(temp));logical=root/'runs/DEV/sample.bin'
            rows=manifest(root,[logical],'sample')
            self.assertEqual(rows[0]['artifact_id'],'runs/DEV/sample.bin')
            verify_manifest(root,rows,required={'runs/DEV/sample.bin'},source_run='sample')
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):verify_manifest(root,rows)

    def test_unregistered_or_different_workspace_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root,cache,path=self.fixture(Path(temp));marker=root/'operator/e2-storage-alias.json'
            marker.unlink()
            with self.assertRaises(FileNotFoundError):manifest(root,[root/'runs/DEV/sample.bin'],'sample')
            marker.write_text(json.dumps({'epoch':'E2','workspace':'/unrelated','cache_root':str(cache),
                'target':str(path.parent.parent),'ownership_marker_sha256':sha256(cache/'e2-cache-ownership.json')}))
            with self.assertRaises(ValueError):manifest(root,[root/'runs/DEV/sample.bin'],'sample')

    def test_nested_symlink_cannot_escape_owned_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root,cache,path=self.fixture(base);outside=base/'unrelated';outside.write_bytes(b'private')
            (path.parent/'escape.bin').symlink_to(outside)
            with self.assertRaises(ValueError):manifest(root,[root/'runs/DEV/escape.bin'],'sample')
