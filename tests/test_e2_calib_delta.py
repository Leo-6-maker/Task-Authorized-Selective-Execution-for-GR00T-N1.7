"""Synthetic derivative integrity failures; no CALIB or TEST execution."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tase.evidence import sha256
from scripts.e2_audit_calib_delta import validate_package


class CalibDeltaTests(unittest.TestCase):
    def test_valid_safe_manifest_and_tampered_source_or_bytes_fail(self):
        for mutation in [None,'bytes','source','extra','traversal']:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/'numeric.npz';np.savez(path,state=np.zeros((3,7)))
                origin=dict(source_path='runs/CALIB/e2-calib-0001/control_trace.npz',source_sha256='1'*64)
                record=dict(export_path='numeric.npz',bytes=path.stat().st_size,sha256=sha256(path),origins=[origin])
                data=dict(artifacts=[record],source_files=[dict(origin)])
                if mutation=='bytes':path.write_bytes(b'corrupt')
                if mutation=='source':data['source_files'][0]['source_sha256']='2'*64
                if mutation=='extra':(root/'extra.json').write_text('{}')
                if mutation=='traversal':record['export_path']='../numeric.npz'
                (root/'manifest.json').write_text(json.dumps(data))
                if mutation is None:self.assertEqual(len(validate_package(root)[0]['artifacts']),1)
                else:
                    with self.assertRaises(ValueError):validate_package(root)

    def test_rehashed_object_or_nonfinite_numeric_export_is_still_rejected(self):
        for arr in [np.array([{'unsafe':1}],dtype=object),np.array([np.nan])]:
            with self.subTest(dtype=str(arr.dtype)),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/'numeric.npz';np.savez(path,state=arr)
                (root/'manifest.json').write_text(json.dumps(dict(source_files=[],artifacts=[dict(
                    export_path='numeric.npz',bytes=path.stat().st_size,sha256=sha256(path),origins=[])])))
                with self.assertRaises(ValueError):validate_package(root)


if __name__=='__main__':unittest.main()
