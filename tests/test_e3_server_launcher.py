"""CPU-only E3 server admission integration; no real grant/model/CUDA/sim.

Authorized-source and runtime dependencies are synthetic/mocked. Real temporary
allocation bytes flow into the staged native admission receipt. The exclusive
native-output helper is exercised by its existing R007 integration suite.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from e3 import server_launcher as launcher


class ServerLauncherAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.repo = Path(__file__).resolve().parents[1]
        self.identity = dict(authorized_head='a'*40, review_commit='b'*40,
                             grant_protocol='E3-001-v1.0')
        self.allocation = self.workspace/'allocation.json'
        self.record = dict(protocol_id='E3-001-v1.0', **self.identity,
                           shared_gpu_inference_authorized=True, gpu_index=1,
                           gpu_uuid='GPU-SYNTHETIC-TEST-ONLY',
                           owner_approval_evidence='SYNTHETIC_UNIT_TEST_NOT_PERMISSION')
        self.allocation.write_text(json.dumps(self.record))
        self.preflight = dict(status='SYNTHETIC_FIXED_RUNTIME_VERIFIED')
        self.authorize = self.enter('authorize', return_value=({}, [], self.identity))
        self.inventory = self.enter('verify_inventory')
        self.runtime = self.enter('verify', return_value=self.preflight)
        self.gpu = self.enter('subprocess.check_output',
                              return_value='1, GPU-SYNTHETIC-TEST-ONLY, 12000\n')
        self.socket = self.enter('socket.socket')
        self.handoff = self.enter('_run_owned_server', return_value=0)

    def enter(self, name, **kwargs):
        target = 'e3.scene.verify_inventory' if name == 'verify_inventory' else 'e3.server_launcher.'+name
        return self.enterContext(patch(target, **kwargs))

    def run_server(self):
        return launcher.serve(self.workspace, self.repo, 'b'*40,
                              'docs/reviews/SYNTHETIC-E3-GRANT.json',
                              self.allocation, self.workspace/'server/bin/python',
                              self.workspace/'sim/bin/python', 'test-server-e3-cpu', 1, 5561)

    def test_admitted_entry_binds_exact_allocation_bytes_and_preserves_native_creation(self):
        before = self.allocation.read_bytes()
        self.assertEqual(self.run_server(), 0)
        args = self.handoff.call_args.args
        workspace, repo, python, session, admission, command, env = args
        self.assertEqual(admission['allocation_sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(admission['authorization'], self.identity)
        self.assertEqual(admission['preflight'], self.preflight)
        self.assertEqual(admission['gpu_uuid'], self.record['gpu_uuid'])
        self.assertEqual(admission['egl_device_id'], '1')
        self.assertEqual(env['HOME'], str(workspace/'runtime/home'))
        self.assertEqual(env['LIBERO_CONFIG_PATH'], str(workspace/'runtime/libero-config'))
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'], self.record['gpu_uuid'])
        self.assertEqual(env['MUJOCO_EGL_DEVICE_ID'], '1')
        self.assertEqual(env['HF_HUB_OFFLINE'], '1')
        self.assertIn('e3.server', command)
        self.assertEqual(command[command.index('--output')+1], str(workspace/'runs'/session))
        self.assertEqual(self.allocation.read_bytes(), before)
        self.assertFalse((workspace/'runs').exists())  # native still creates output exclusively
        # A real helper's nonzero return is forwarded, not reported as success.
        self.handoff.return_value = 7
        self.assertEqual(self.run_server(), 7)

    def test_authorization_denial_has_no_resource_or_directory_side_effect(self):
        self.authorize.side_effect = ValueError('synthetic missing/current grant denied')
        with self.assertRaises(ValueError):
            self.run_server()
        self.inventory.assert_not_called()
        self.runtime.assert_not_called()
        self.gpu.assert_not_called()
        self.handoff.assert_not_called()
        self.assertEqual(list(self.workspace.iterdir()), [self.allocation])

    def test_stale_resource_grant_stops_before_inventory_or_native(self):
        self.record['review_commit'] = 'c'*40
        self.allocation.write_text(json.dumps(self.record))
        with self.assertRaisesRegex(ValueError, 'stale resource'):
            self.run_server()
        self.inventory.assert_not_called()
        self.gpu.assert_not_called()
        self.handoff.assert_not_called()

    def test_inventory_corruption_stops_before_runtime_and_GPU(self):
        self.inventory.side_effect = ValueError('synthetic asset XML mismatch')
        with self.assertRaisesRegex(ValueError, 'XML mismatch'):
            self.run_server()
        self.runtime.assert_not_called()
        self.gpu.assert_not_called()
        self.handoff.assert_not_called()

    def test_insufficient_memory_stops_before_socket_and_handoff(self):
        self.gpu.return_value = '1, GPU-SYNTHETIC-TEST-ONLY, 9215\n'
        with self.assertRaises(ValueError):
            self.run_server()
        self.socket.assert_not_called()
        self.handoff.assert_not_called()

    def test_wrong_physical_UUID_stops_before_socket_and_handoff(self):
        self.gpu.return_value = '1, GPU-DIFFERENT-SYNTHETIC-DEVICE, 12000\n'
        with self.assertRaisesRegex(ValueError, 'UUID differs'):
            self.run_server()
        self.socket.assert_not_called()
        self.handoff.assert_not_called()

    def test_occupied_port_has_no_native_output_creation(self):
        self.socket.return_value.__enter__.return_value.bind.side_effect = OSError('synthetic port in use')
        with self.assertRaises(OSError):
            self.run_server()
        self.handoff.assert_not_called()
        self.assertFalse((self.workspace/'runs').exists())


if __name__ == '__main__':
    unittest.main()
