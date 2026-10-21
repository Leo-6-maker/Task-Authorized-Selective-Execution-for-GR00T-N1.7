"""Collect public-safe source/model/dependency identities from the isolated runtime."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tase.evidence import now_sgt, sha256, write_json


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.workspace.resolve()
    upstream = root / 'upstream/Isaac-GR00T'
    repo = root / 'course-repo'
    packages = {}
    for name, python in {
        'server': upstream / '.venv/bin/python',
        'sim': upstream / 'gr00t/eval/sim/LIBERO/libero_uv/.venv/bin/python'
    }.items():
        command = [str(python), '-c',
            'import json,sys,importlib.metadata as m; '
            'print(json.dumps(dict(python=sys.version.split()[0],packages='
            '{d.metadata["Name"]:d.version for d in m.distributions()})))']
        packages[name] = json.loads(subprocess.check_output(command, text=True))
    source_paths = ['pyproject.toml', 'uv.lock', 'gr00t/policy/gr00t_policy.py',
                    'gr00t/policy/server_client.py', 'gr00t/eval/_horizon_contract.py',
                    'gr00t/eval/sim/LIBERO/libero_env.py',
                    'gr00t/eval/sim/LIBERO/setup_libero.sh',
                    'gr00t/eval/sim/LIBERO/setup_libero_cpu.sh',
                    'gr00t/eval/sim/wrapper/multistep_wrapper.py']
    hf_cache = root / 'cache/huggingface/hub'
    cached = {model.name: sorted(p.name for p in (model / 'snapshots').glob('*'))
              for model in hf_cache.glob('models--*')}
    result = {
        'protocol_id': 'TASE-001-v1.0', 'captured_at_sgt': now_sgt(),
        'status': 'IDENTITY_CAPTURE_ONLY_SEE_STAGE_REPORT_FOR_VALIDATION',
        'repo_sha': git(repo, 'rev-parse', 'HEAD'),
        'upstream_repo': 'NVIDIA/Isaac-GR00T',
        'upstream_sha': git(upstream, 'rev-parse', 'HEAD'),
        'libero_sha': git(upstream / 'external_dependencies/LIBERO', 'rev-parse', 'HEAD'),
        'upstream_tracked_diff': git(upstream, 'diff', '--stat'),
        'source_sha256': {path: sha256(upstream / path) for path in source_paths},
        'model': json.loads((root / 'checkpoints/download_manifest.json').read_text()),
        'packages': packages, 'cached_auxiliary_model_snapshots': cached,
        'config': {'path': 'configs/dev_baseline.json',
                   'sha256': sha256(repo / 'configs/dev_baseline.json')},
        'patches': [{'path': 'scripts/prepare_runtime.py',
                     'sha256': sha256(repo / 'scripts/prepare_runtime.py'),
                     'purpose': 'CPU-only isolated upstream dependency setup; no deletion or EGL smoke'}],
        'gpu_authorization': 'Project owner explicitly permits shared inference if VRAM is sufficient',
        'formal_test_authorized': False, 'training_authorized': False,
        'raw_storage_location': 'Task-owned private workspace; relative artifact IDs in manifest'}
    write_json(a.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
