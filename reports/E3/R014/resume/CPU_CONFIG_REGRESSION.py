"""CPU-only deployment regression for the observed LIBERO bootstrap EOF.

Execute only pinned LIBERO's small os/yaml configuration __init__.py via runpy,
never import LIBERO benchmark, GR00T, MuJoCo or a scene. Real child subprocesses
use closed stdin and CUDA disabled. This is not another scene diagnostic.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BOOTSTRAP = r'''
import builtins,hashlib,json,os,runpy,sys
from pathlib import Path
config=Path(sys.argv[2]);mode=sys.argv[3]
if mode=='guarded':
    if not config.is_file():raise ValueError('explicit existing LIBERO config required before imports')
    data=json.loads(config.read_text());root=Path(sys.argv[4]).resolve(strict=True)
    for key,relative in [('benchmark_root','.'),('bddl_files','bddl_files'),('init_states','init_files'),('assets','assets')]:
        if Path(data[key]).resolve(strict=True)!=(root/relative).resolve(strict=True):raise ValueError('configuration source binding differs')
    os.environ['LIBERO_CONFIG_PATH']=str(config.parent)
    builtins.input=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('interactive input forbidden'))
before=hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None
status=runpy.run_path(sys.argv[1],run_name='CPU_ONLY_LIBERO_CONFIG_BOOTSTRAP')
if any(n.startswith(('mujoco','robosuite','gr00t','libero.libero.benchmark')) for n in sys.modules):raise RuntimeError('forbidden native import in CPU regression')
if before is not None and hashlib.sha256(config.read_bytes()).hexdigest()!=before:raise RuntimeError('existing configuration changed')
print(json.dumps(dict(status='CONFIG_BOOTSTRAP_CPU_ONLY',config_preserved=True,native_imports=False)))
'''


class ConfigurationSubprocessTests(unittest.TestCase):
    def child(self, home, config, mode):
        env = dict(os.environ, HOME=str(home), CUDA_VISIBLE_DEVICES='',
                   HF_HUB_OFFLINE='1', PYTHONNOUSERSITE='1')
        env.pop('LIBERO_CONFIG_PATH', None)
        return subprocess.run([sys.executable, *(['-O'] if sys.flags.optimize else []),
                               '-c', BOOTSTRAP, str(ARGS.upstream_init), str(config),
                               mode, str(ARGS.upstream_init.parent)],
                              stdin=subprocess.DEVNULL, capture_output=True,
                              env=env, text=True, timeout=15)

    def test_original_missing_binding_reproduces_real_EOF_without_native_import(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.child(home, Path(home)/'.libero/config.yaml', 'original')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('EOFError', result.stderr)
            self.assertIn('Do you want to specify', result.stdout)
            self.assertFalse((Path(home)/'.libero/config.yaml').exists())

    def test_explicit_existing_project_config_loads_without_prompt_or_write(self):
        before = ARGS.config.read_bytes()
        with tempfile.TemporaryDirectory() as home:
            result = self.child(home, ARGS.config, 'guarded')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['native_imports'], False)
            self.assertFalse((Path(home)/'.libero').exists())
        self.assertEqual(ARGS.config.read_bytes(), before)

    def test_missing_explicit_config_fails_before_interactive_side_effect(self):
        with tempfile.TemporaryDirectory() as home:
            config = Path(home)/'uncreated/config.yaml'
            result = self.child(home, config, 'guarded')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('explicit existing LIBERO config required', result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertFalse(config.parent.exists())
            self.assertFalse((Path(home)/'.libero').exists())

    def test_config_pointing_to_another_source_fails_before_bootstrap(self):
        with tempfile.TemporaryDirectory() as home:
            config = Path(home)/'config.yaml'
            value = json.loads(ARGS.config.read_text())
            value['assets'] = home
            config.write_text(json.dumps(value))
            before = config.read_bytes()
            result = self.child(home, config, 'guarded')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('configuration source binding differs', result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(config.read_bytes(), before)
            self.assertFalse((Path(home)/'.libero').exists())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-init', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    ARGS, extra = parser.parse_known_args()
    unittest.main(argv=[sys.argv[0], *extra])
