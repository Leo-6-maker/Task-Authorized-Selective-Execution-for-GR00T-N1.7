"""Synthetic review-boundary tests, no policy or simulation."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from scripts.e2_export_review import redact,validate_numpy


class E2ExportTests(unittest.TestCase):
    def test_numeric_files_accept_object_and_nonfinite_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'array.npz'
            np.savez(path,state=np.zeros((3,7)));validate_numpy(path)
            np.savez(path,state=np.asarray([{'untrusted':'object'}],dtype=object))
            with self.assertRaises(ValueError):validate_numpy(path)
            np.savez(path,state=np.asarray([float('nan')]))
            with self.assertRaises(ValueError):validate_numpy(path)

    def test_json_redaction_preserves_scientific_values(self):
        row={'target':'alphabet_soup_1','step':94,'event':None,
             'error':'file /home/example/private/result.json on private-node',
             'nested':['/var/cache/users/example/cache/file',2]}
        clean=redact(row,['private-node'])
        self.assertNotIn('/home/',str(clean));self.assertNotIn('/var/cache/',str(clean))
        self.assertNotIn('private-node',str(clean));self.assertEqual(clean['step'],94)
        self.assertEqual(clean['target'],row['target']);self.assertEqual(clean['event'],None)
