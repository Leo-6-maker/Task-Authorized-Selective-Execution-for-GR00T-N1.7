"""CPU negatives for the owner-selected resource route; no model or CUDA use."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from e3 import resource as route
from e3.freeze import verify_freeze,historical
from tests.test_e3_r016_freeze import copy_freeze_fixture

REPO=Path(__file__).resolve().parents[1]


class ResourceRouteTests(unittest.TestCase):
    def test_gpu0_config_has_no_fallback_or_reduced_memory_limits(self):
        self.assertEqual(route.configured_index(),0)
        record=dict(gpu_index=0,gpu_uuid='GPU-CPU-SYNTHETIC')
        with patch('e3.resource.subprocess.check_output',return_value=
                   '1, GPU-OTHER, 32000\n0, GPU-CPU-SYNTHETIC, 9216\n'):
            self.assertEqual(route.live_gpu(record)['egl_device_id'],'0')
        with patch('e3.resource.subprocess.check_output',return_value='1, GPU-OTHER, 32000\n'):
            with self.assertRaises(ValueError):route.live_gpu(record)

    def test_config_cannot_disable_limits_or_implicitly_select_a_device(self):
        baseline=json.loads((REPO/'configs/e3_gpu_resource.json').read_text())
        changes=[dict(physical_gpu_index=True),dict(physical_gpu_index='0'),
                 dict(physical_gpu_index=2),dict(automatic_fallback=True),
                 dict(minimum_free_bytes=0),dict(maximum_process_fraction=1.),
                 dict(reserved_free_bytes=0)]
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'configs').mkdir()
            for change in changes:
                (root/'configs/e3_gpu_resource.json').write_text(json.dumps(dict(baseline,**change)))
                with self.subTest(change=change),patch.object(route,'__file__',str(root/'e3/resource.py')):
                    with self.assertRaises(ValueError):route.configured_index()

    def test_refrozen_route_is_required_hash_bound_and_cannot_be_omitted(self):
        self.enterContext(patch('e3.freeze.historical',
            side_effect=lambda _,revision,path:historical(REPO,revision,path)))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);lock=copy_freeze_fixture(root)
            target=root/'configs/e3_gpu_resource.json';raw=target.read_bytes()
            verify_freeze(root)
            target.unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):verify_freeze(root)
            target.write_bytes(raw+b'\n')
            with self.assertRaises(ValueError):verify_freeze(root)
            target.write_bytes(raw)
            lock=copy.deepcopy(lock);del lock['source_sha256']['configs/e3_gpu_resource.json']
            (root/'configs/e3_protocol_lock.proposed.json').write_text(json.dumps(lock))
            with self.assertRaisesRegex(ValueError,'missing active'):verify_freeze(root)


if __name__=='__main__':unittest.main()
