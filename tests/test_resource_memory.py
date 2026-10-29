"""CPU resource boundaries and genuine CPU subprocesses with explicit stubs.

The native-main proxy replaces torch and GR00T before importing them. Reaching
the model constructor terminates with23, never a MODEL_LOADED receipt. Rejection
terminates with17. Neither case uses a GPU, model, simulator or TEST identity.
"""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tase.resource_memory import (GIB, MINIMUM_FREE_BYTES, RESERVED_FREE_BYTES,
                                 require_free_memory, allocator_fraction)

REPO = Path(__file__).resolve().parents[1]
PROXY = '''import json,sys,types
from pathlib import Path
r=Path(sys.argv[1]);free,total=map(int,sys.argv[2:4])
torch=types.ModuleType('torch');torch.manual_seed=lambda n:None
def cap(value):(r/'allocator.json').write_text(json.dumps(dict(fraction=value)))
torch.cuda=types.SimpleNamespace(manual_seed_all=lambda n:None,
    mem_get_info=lambda:(free,total),set_per_process_memory_fraction=cap,
    reset_peak_memory_stats=lambda:None)
sys.modules['torch']=torch
for name in ['gr00t','gr00t.policy','gr00t.policy.gr00t_policy','gr00t.policy.server_client']:
 sys.modules[name]=types.ModuleType(name)
class ModelBoundary(Exception):pass
def model(**kw):
 (r/'model-boundary.json').write_text(json.dumps(dict(scope='CPU_STUB_NO_MODEL_CREATED',kwargs=kw)))
 raise ModelBoundary()
sys.modules['gr00t.policy.gr00t_policy'].Gr00tPolicy=model
sys.modules['gr00t.policy.gr00t_policy'].Gr00tSimPolicyWrapper=lambda x:x
sys.modules['gr00t.policy.server_client'].PolicyServer=object
from tase.server import main
sys.argv=['tase.server','--model',str(r/'not-a-model'),'--output',str(r/'native-output'),
          '--allocation-record',str(r/'allocation.json'),'--epoch','E2']
try:main()
except ModelBoundary:raise SystemExit(23)
except ValueError as exc:
 (r/'rejection.json').write_text(json.dumps(dict(error=str(exc))))
 raise SystemExit(17)
raise RuntimeError('CPU fixture must never finish real model readiness')
'''


class ResourceMemoryTests(unittest.TestCase):
    def test_floor_boundary_bytes(self):
        with self.assertRaises(ValueError):
            require_free_memory(9*GIB-1)
        require_free_memory(9*GIB)
        self.assertEqual(MINIMUM_FREE_BYTES-RESERVED_FREE_BYTES, 7*GIB)

    def test_invalid_free_inventory_fails_closed(self):
        for value in [True, False, None, '10121', float(10*GIB), -1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_free_memory(value)

    def test_invalid_total_inventory_fails_closed(self):
        for value in [True, None, '16376', float(16*GIB), 0, 9*GIB-1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                allocator_fraction(9*GIB, value)

    def test_actual_gpu1_inventory_retains_two_gib_and_fraction_cap(self):
        free, total = 10121*1024**2, 16376*1024**2
        fraction = allocator_fraction(free, total)
        self.assertEqual(fraction, (free-2*GIB)/total)
        self.assertLessEqual(fraction, .55)
        self.assertGreater((free-2*GIB)-6482296832, 0)

    def test_legacy_admissible_allocator_calculation_is_identical(self):
        for total_gib in [20, 32, 48, 80]:
            for free_gib in range(16, total_gib+1):
                free, total = free_gib*GIB, total_gib*GIB
                self.assertEqual(allocator_fraction(free,total),
                                 min(.55, (free-2*1024**3)/total))

    def test_allocator_budget_preserves_cap_and_headroom(self):
        for total_gib in [12, 16, 24, 32]:
            for free_gib in range(9, total_gib+1):
                fraction = allocator_fraction(free_gib*GIB,total_gib*GIB)
                self.assertLessEqual(fraction, .55)
                self.assertLessEqual(fraction*total_gib*GIB,
                                     (free_gib-2)*GIB+1e-4)

    def launcher(self, root, memory_mib):
        from scripts import e2_test_server as server
        allocation=root/'allocation.json'
        allocation.write_text(json.dumps(dict(shared_gpu_inference_authorized=True,
            gpu_index=1,gpu_uuid='GPU_CPU_SYNTHETIC')))
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(server,'authorize',return_value=({},[],{})))
        stack.enter_context(patch.object(server,'verify',return_value={} ))
        stack.enter_context(patch.object(server.subprocess,'check_output',
            return_value=f'1, GPU_CPU_SYNTHETIC, {memory_mib}\n'))
        launch=stack.enter_context(patch.object(server,'_run_owned_server',return_value=0))
        return stack, launch, lambda: server.serve(root,REPO,'CPU_ONLY','CPU_ONLY',
            allocation,Path(sys.executable),Path(sys.executable),'test-server-cpu-memory',1,0)

    def test_launcher_low_memory_never_spawns_or_creates_native_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stack,launch,run=self.launcher(root,9*1024-1)
            with stack, self.assertRaises(ValueError):run()
            launch.assert_not_called()
            self.assertFalse((root/'runs').exists())

    def test_launcher_gpu1_routes_same_authorized_uuid_without_real_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stack,launch,run=self.launcher(root,10121)
            with stack:self.assertEqual(run(),0)
            env=launch.call_args.args[-1]
            self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'GPU_CPU_SYNTHETIC')
            self.assertEqual(env['MUJOCO_EGL_DEVICE_ID'],'1')
            self.assertFalse((root/'runs/TEST').exists())

    def native_proxy(self, label, free, total, expected):
        evidence=os.environ.get('TASE_CPU_MEMORY_EVIDENCE')
        cm=contextlib.nullcontext(None) if evidence else tempfile.TemporaryDirectory()
        with cm as tmp:
            root=Path(evidence)/label if evidence else Path(tmp)
            root.mkdir(parents=True,exist_ok=True)
            (root/'allocation.json').write_text(json.dumps(dict(shared_gpu_inference_authorized=True)))
            proxy=root/'cpu_native_proxy.py';proxy.write_text(PROXY)
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',PYTHONNOUSERSITE='1',PYTHONPATH=str(REPO),PYTHONOPTIMIZE=str(sys.flags.optimize))
            command=[sys.executable,str(REPO/'scripts/record_process.py'),
                '--receipt',str(root/'proxy.exit.json'),'--',sys.executable,str(proxy),
                str(root),str(free),str(total)]
            with (root/'stdout.private.txt').open('w') as out,(root/'stderr.private.txt').open('w') as err:
                result=subprocess.run(command,cwd=REPO,env=env,stdout=out,stderr=err)
            self.assertEqual(result.returncode,expected)
            self.assertEqual(json.loads((root/'proxy.exit.json').read_text())['exit_code'],expected)
            self.assertEqual((root/'model-boundary.json').exists(),expected==23)
            self.assertFalse((root/'native-output/loaded.json').exists())
            self.assertFalse((root/'runs/TEST').exists())
            if expected==23:
                cap=json.loads((root/'allocator.json').read_text())['fraction']
                self.assertEqual(cap,allocator_fraction(free,total))
            else:self.assertFalse((root/'allocator.json').exists())

    def test_native_rechecks_decreased_memory_before_model_constructor(self):
        self.native_proxy('memory-decreased',9*GIB-1,16376*1024**2,17)

    def test_native_gpu1_memory_fraction_before_stubbed_model_boundary(self):
        self.native_proxy('gpu1-shared',10121*1024**2,16376*1024**2,23)

    def test_native_entire_16376mib_device_can_pass_cpu_resource_check(self):
        self.native_proxy('gpu1-idle',16376*1024**2,16376*1024**2,23)
