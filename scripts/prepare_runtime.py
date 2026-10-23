"""Install pinned native environments under an isolated workspace; never use a GPU.

This installer does not run the upstream EGL smoke or load the model. The caller
must create a fresh task-owned root and put HOME/cache paths beneath it.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

UPSTREAM_SHA = 'dac54b313160c201c450f97df0fd74ebd379c892'
SETUP_SHA256 = '11fabf6b1f14d72c53beefbced70c03d7a331068415d8f2b04fc70ec5156b7ea'


def contained(root, path):
    path = Path(path).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError('path must be strictly inside task root')
    return path


def cpu_setup(source):
    """Keep upstream dependency commands; replace deletion and omit GPU smoke."""
    if hashlib.sha256(source.encode()).hexdigest() != SETUP_SHA256:
        raise ValueError('upstream setup identity mismatch')
    marker = 'rm -rf $HOME/.libero\n'
    if source.count(marker) != 1:
        raise ValueError('setup boundary changed')
    result = source.split(marker)[0]
    result = result.replace('rm -rf $LIBERO_UV_ENV\n',
                            'test ! -e "$LIBERO_UV_ENV"\n')
    if 'rm -rf' in result:
        raise ValueError('unexpected deletion remains')
    return result + '\n# EGL/configuration smoke deferred until GPU allocation.\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--uv', type=Path, required=True)
    parser.add_argument('--stage', choices=['server', 'sim'], required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    upstream = contained(root, root / 'upstream/Isaac-GR00T')
    for key in ['HOME', 'XDG_CACHE_HOME', 'HF_HOME', 'UV_CACHE_DIR']:
        contained(root, os.environ[key])
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream,
                               text=True).strip() != UPSTREAM_SHA:
        raise ValueError('wrong upstream commit')
    receipt_dir = root / 'runs' / ('install-' + args.stage)
    receipt_dir.mkdir()  # no overwrite or automatic repeated installation
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES='-1', WANDB_MODE='disabled',
               HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1',
               UV_CONCURRENT_DOWNLOADS='2', UV_CONCURRENT_BUILDS='1',
               MAX_JOBS='2', OMP_NUM_THREADS='2',
               PATH=str(args.uv.resolve().parent) + os.pathsep + env['PATH'])
    if args.stage == 'server':
        command = [str(args.uv.resolve()), 'sync', '--frozen', '--no-dev']
    else:
        original = upstream / 'gr00t/eval/sim/LIBERO/setup_libero.sh'
        source = original.read_text()
        patched = cpu_setup(source)
        destination = original.with_name('setup_libero_cpu.sh')
        with destination.open('x') as f:
            f.write(patched)
        (receipt_dir / 'setup.diff').write_text(''.join(difflib.unified_diff(
            source.splitlines(True), patched.splitlines(True),
            fromfile='upstream/setup_libero.sh', tofile='setup_libero_cpu.sh')))
        command = ['bash', str(destination)]
    receipt = {'stage': args.stage, 'upstream_sha': UPSTREAM_SHA,
               'status': 'STARTED', 'command': command, 'gpu_allowed': False}
    start = time.monotonic()
    code = 1
    try:
        with (receipt_dir / 'stdout.txt').open('xb') as out, \
             (receipt_dir / 'stderr.txt').open('xb') as err:
            run = subprocess.run(command, cwd=upstream, env=env, stdout=out,
                                 stderr=err, timeout=1200)
        code = run.returncode
        receipt['status'] = 'PASS' if code == 0 else 'FAIL'
    except subprocess.TimeoutExpired:
        code = 124
        receipt['status'] = 'TIMEOUT'
    finally:
        receipt.update(exit_code=code, wall_seconds=time.monotonic()-start)
        (receipt_dir / 'receipt.json').write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt))
    return code


if __name__ == '__main__':
    sys.exit(main())
