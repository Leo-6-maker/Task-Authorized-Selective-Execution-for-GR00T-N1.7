"""CPU integration/negative tests. GPU output mocked, no native imports/context.

Freeze fixtures use genuine committed R016/R015 bytes. Synthetic permissions
below are unittest-only and are never emitted as operational review grants.
"""
import builtins
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from e3.authorization import resource, validate_grant
from e3.freeze import verify_freeze, historical
from e3.resource import binding, live_gpu1
from tests.test_e3_cpu import ReactiveGate, frame, spec

REPO = Path(__file__).resolve().parents[1]
HISTORICAL_HEAD = '859e40b5f460365a8853bf3486969e9f8e28951c'
LOCK_PATH = 'configs/e3_protocol_lock.proposed.json'


def copy_freeze_fixture(destination, revision=None):
    """Names and bytes must come from the same tree, including its lock.

    A current fixture also copies any unlocked executable/test/config files so
    coverage-negative tests cannot hide an omission by constructing a subset.
    """
    read = ((lambda name: historical(REPO, revision, name)) if revision else
            (lambda name: (REPO/name).read_bytes()))
    lock = json.loads(read(LOCK_PATH))
    names = set(lock['source_sha256']) | {
        LOCK_PATH, 'configs/e3_scene_identity.frozen.json',
        'docs/reviews/R016-E3-GATE-P-APPROVED.json',
        'docs/protocols/E3-001-v1.0-PROPOSED.md',
        'reports/E3/R015/SCENE_RESULT.json',
        'reports/E3/R015/COMPILED_SCENE_BINDINGS_36.csv'}
    if revision is None:
        from e3.freeze import source_inventory
        names.update(source_inventory(REPO))
    for name in names:
        (destination/name).parent.mkdir(parents=True, exist_ok=True)
        (destination/name).write_bytes(read(name))
    return lock


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        copy_freeze_fixture(self.repo, HISTORICAL_HEAD)
        self.enterContext(patch('e3.freeze.historical',
                                side_effect=lambda _, rev, path: historical(REPO, rev, path)))

    def mutate(self, name, change):
        p = self.repo/name
        v = json.loads(p.read_text())
        change(v)
        p.write_text(json.dumps(v))

    def test_genuine_full160_scientific_freeze_is_not_TEST_grant(self):
        result = verify_freeze(self.repo)
        self.assertEqual(result['clusters'], 36)
        self.assertEqual(result['budgets'], {'E3A':112, 'E3B':48})
        self.assertFalse(result['authorized_real_TEST'])

    def test_gate_P_cannot_be_used_as_gate_C_grant(self):
        p = json.loads((self.repo/'docs/reviews/R016-E3-GATE-P-APPROVED.json').read_text())
        with self.assertRaisesRegex(ValueError, 'new independent E3 grant'):
            validate_grant(p, {}, [], {})

    def test_tampered_approval_denied(self):
        self.mutate('docs/reviews/R016-E3-GATE-P-APPROVED.json',
                    lambda x: x.update(runtime_execution_authorized=True))
        with self.assertRaises(ValueError): verify_freeze(self.repo)

    def test_self_authorized_lock_denied(self):
        self.mutate('configs/e3_protocol_lock.proposed.json',
                    lambda x: x.update(authorized_real_TEST=True))
        with self.assertRaises(ValueError): verify_freeze(self.repo)

    def test_wrong_scene_binding_and_rewritten_public_original_denied(self):
        for name in ['configs/e3_scene_identity.frozen.json', 'reports/E3/R015/SCENE_RESULT.json']:
            with self.subTest(name=name):
                original = (self.repo/name).read_bytes()
                self.mutate(name, lambda x: x.update(constructors=8))
                with self.assertRaises(ValueError): verify_freeze(self.repo)
                (self.repo/name).write_bytes(original)

    def test_cell_or_runtime_lock_drift_denied(self):
        for name in ['configs/e3_cells.proposed.json', 'configs/runtime_lock_E2.json']:
            with self.subTest(name=name):
                original = (self.repo/name).read_bytes()
                (self.repo/name).write_bytes(original+b'\n')
                with self.assertRaises(ValueError): verify_freeze(self.repo)
                (self.repo/name).write_bytes(original)

    def test_code_drift_even_if_lock_rewritten_denied(self):
        p = self.repo/'e3/reactive_gate.py'
        p.write_bytes(p.read_bytes()+b'\n# synthetic drift\n')
        import hashlib
        self.mutate('configs/e3_protocol_lock.proposed.json',
                    lambda x: x['source_sha256'].update({'e3/reactive_gate.py':hashlib.sha256(p.read_bytes()).hexdigest()}))
        with self.assertRaisesRegex(ValueError, 'reviewed E2/scientific/A0 source'):
            verify_freeze(self.repo)

    def test_ordinary_executable_source_drift_denied(self):
        p = self.repo/'e3/server.py'
        p.write_bytes(p.read_bytes()+b'\n# synthetic drift\n')
        with self.assertRaisesRegex(ValueError, 'source lock differs'):
            verify_freeze(self.repo)

    def test_historical_names_come_from_historical_lock_not_new_worktree(self):
        original = json.loads(historical(REPO, HISTORICAL_HEAD, LOCK_PATH))
        self.assertEqual(json.loads((self.repo/LOCK_PATH).read_text()), original)
        self.assertNotIn('e3/audit_manifest.py', original['source_sha256'])
        self.assertFalse((self.repo/'e3/audit_manifest.py').exists())
        self.assertEqual(verify_freeze(self.repo)['clusters'], 36)


class ActualRefrozenWorktreeTests(unittest.TestCase):
    def test_actual_new_worktree_and_lock_pass_without_historical_fixture_patch(self):
        # Real current files + current lock, genuine Git history, no test double.
        result = verify_freeze(REPO)
        self.assertEqual(result['clusters'], 36)
        self.assertFalse(result['authorized_real_TEST'])


class CurrentRefrozenTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.lock = copy_freeze_fixture(self.repo)
        self.enterContext(patch('e3.freeze.historical',
                                side_effect=lambda _, rev, path: historical(REPO, rev, path)))

    def test_current_fixture_includes_both_new_files_and_their_new_hashes(self):
        from e3.discovery import sha
        for name in ['e3/audit_manifest.py', 'tests/test_e3_audit_manifest.py']:
            self.assertIn(name, self.lock['source_sha256'])
            self.assertEqual(sha(self.repo/name), self.lock['source_sha256'][name])
        self.assertEqual(verify_freeze(self.repo)['budgets'], {'E3A':112, 'E3B':48})

    def test_either_new_locked_file_missing_is_rejected(self):
        for name in ['e3/audit_manifest.py', 'tests/test_e3_audit_manifest.py']:
            with self.subTest(name=name):
                p = self.repo/name; before = p.read_bytes(); p.unlink()
                try:
                    with self.assertRaises((FileNotFoundError, ValueError)):verify_freeze(self.repo)
                finally:p.write_bytes(before)

    def test_either_new_locked_file_mutation_is_rejected(self):
        for name in ['e3/audit_manifest.py', 'tests/test_e3_audit_manifest.py']:
            with self.subTest(name=name):
                p = self.repo/name; before = p.read_bytes(); p.write_bytes(before+b'\n# CPU synthetic mutation\n')
                try:
                    with self.assertRaisesRegex(ValueError, 'source lock differs'):verify_freeze(self.repo)
                finally:p.write_bytes(before)

    def test_omitting_new_module_or_test_from_lock_is_rejected(self):
        for name in ['e3/audit_manifest.py', 'tests/test_e3_audit_manifest.py']:
            with self.subTest(name=name):
                lock = copy.deepcopy(self.lock); del lock['source_sha256'][name]
                (self.repo/LOCK_PATH).write_text(json.dumps(lock))
                with self.assertRaisesRegex(ValueError, 'source lock missing active files'):verify_freeze(self.repo)

    def test_unlocked_added_python_file_is_rejected(self):
        (self.repo/'e3/unlocked_CPU_test_only.py').write_text('# not executable permission\n')
        with self.assertRaisesRegex(ValueError, 'source lock missing active files'):verify_freeze(self.repo)

    def test_current_runtime_or_scientific_config_drift_is_rejected(self):
        for name in ['configs/e3_run_config.proposed.json', 'e3/server.py']:
            with self.subTest(name=name):
                p = self.repo/name; before = p.read_bytes(); p.write_bytes(before+b'\n')
                try:
                    with self.assertRaises(ValueError):verify_freeze(self.repo)
                finally:p.write_bytes(before)


class R016BoundaryTests(unittest.TestCase):
    def test_three_contact_streak_lost_just_before_boundary_does_not_latch(self):
        gate = ReactiveGate(spec())
        for step in range(1,9):
            gate.observe(frame(step, 'wrong_1' if 5 <= step <= 7 else None))
        result = gate.decide(8)
        self.assertEqual(result['decision'], 'ACCEPT')
        self.assertEqual(result['triggers'], [])
        self.assertEqual(result['future_shadow_calls'], 0)

    def test_same_contact_streak_persisting_at_boundary_rejects(self):
        gate = ReactiveGate(spec())
        for step in range(1,9):
            gate.observe(frame(step, 'wrong_1' if step >= 6 else None))
        self.assertEqual(gate.decide(8)['decision'], 'REJECT')


class GPU1RoutingTests(unittest.TestCase):
    def setUp(self):
        self.identity = dict(authorized_head='a'*40, review_commit='b'*40)
        self.record = dict(protocol_id='E3-001-v1.0', **self.identity,
                           shared_gpu_inference_authorized=True, gpu_index=1,
                           gpu_uuid='GPU-SYNTHETIC-TEST-ONLY',
                           owner_approval_evidence='SYNTHETIC_UNIT_TEST_NOT_PERMISSION')
        self.env = dict(CUDA_VISIBLE_DEVICES=self.record['gpu_uuid'],
                        MUJOCO_EGL_DEVICE_ID='1', MUJOCO_GL='egl', PYOPENGL_PLATFORM='egl')

    def test_resource_and_binding_allow_only_physical_GPU1(self):
        resource(self.record, self.identity)
        binding(self.record, self.env)
        for bad in [0, True, '1', 2, None]:
            changed = dict(self.record, gpu_index=bad)
            with self.subTest(index=bad):
                with self.assertRaises(ValueError): resource(changed, self.identity)
                with self.assertRaises(ValueError): binding(changed, self.env)

    def test_wrong_environment_uuid_or_EGL_denied(self):
        for key, bad in [('CUDA_VISIBLE_DEVICES','0'), ('CUDA_VISIBLE_DEVICES','1'),
                         ('CUDA_VISIBLE_DEVICES','GPU-OTHER'), ('MUJOCO_EGL_DEVICE_ID','0'),
                         ('MUJOCO_GL','osmesa'), ('PYOPENGL_PLATFORM','glx')]:
            with self.subTest(key=key, value=bad):
                with self.assertRaises(ValueError): binding(self.record, dict(self.env, **{key:bad}))

    def test_live_inventory_no_GPU0_fallback_and_exact_9GiB_floor(self):
        with patch('e3.resource.subprocess.check_output') as query:
            query.return_value = '0, GPU-OTHER, 99999\n1, GPU-SYNTHETIC-TEST-ONLY, 9216\n'
            self.assertEqual(live_gpu1(self.record)['gpu_index'], 1)
            for value in ['0, GPU-OTHER, 99999\n',
                          '1, GPU-SYNTHETIC-TEST-ONLY, 9215\n',
                          '1, GPU-OTHER, 12000\n',
                          '1, GPU-SYNTHETIC-TEST-ONLY, 12000\n'*2]:
                query.return_value = value
                with self.subTest(inventory=value):
                    with self.assertRaises(ValueError): live_gpu1(self.record)

    def test_direct_native_server_denial_before_output_or_torch_import(self):
        from e3.server import main
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); allocation = root/'allocation.json'
            allocation.write_text(json.dumps(self.record))
            argv = ['e3.server', '--model', str(root/'model'), '--output', str(root/'output'),
                    '--allocation-record', str(allocation), '--epoch', 'E3', '--repo', str(REPO),
                    '--review-commit', 'b'*40, '--review-path', 'docs/reviews/SYNTHETIC.json']
            with patch('e3.authorization.authorize', return_value=({}, [], self.identity)), \
                 patch.object(sys, 'argv', argv), patch.dict(os.environ, self.env, clear=True), \
                 patch('e3.server.live_gpu1', side_effect=ValueError('synthetic live memory denial')):
                with self.assertRaisesRegex(ValueError, 'live memory denial'): main()
            self.assertFalse((root/'output').exists())
            with patch('e3.authorization.authorize', return_value=({}, [], self.identity)), \
                 patch.object(sys, 'argv', argv), patch.dict(os.environ, dict(self.env, MUJOCO_EGL_DEVICE_ID='0'), clear=True), \
                 patch('e3.server.live_gpu1') as live:
                with self.assertRaisesRegex(ValueError, 'binding differs'): main()
                live.assert_not_called()
            self.assertFalse((root/'output').exists())

    def test_supervisor_and_direct_runner_reject_GPU0_before_reservation(self):
        from e3.supervisor import run
        from e3.native_runner import main
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); allocation = root/'allocation.json'
            allocation.write_text(json.dumps(dict(self.record, gpu_index=0)))
            with patch('e3.supervisor.authorize', return_value=({}, [], self.identity)):
                with self.assertRaisesRegex(ValueError, 'GPU1-only'):
                    run(root, REPO, 'e3a-test-0001', 'b'*40, 'docs/reviews/SYNTHETIC.json',
                        allocation, root/'python', 'test-server-e3-synthetic')
            with patch('e3.native_runner.authorize', return_value=({}, [], self.identity)):
                with self.assertRaisesRegex(ValueError, 'GPU1-only'):
                    main(['--workspace', str(root), '--allocation-record', str(allocation),
                          '--run-id', 'e3a-test-0001', '--review-commit', 'b'*40,
                          '--review-path', 'docs/reviews/SYNTHETIC.json'])
            self.assertEqual(list(root.iterdir()), [allocation])


if __name__ == '__main__':
    unittest.main()
