"""Run a child and persist its real exit code, including startup failures.

Use only non-secret arguments. This receipt is private operator evidence.
"""
import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from tase.evidence import now_sgt, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        parser.error('child command required')
    receipt = args.receipt
    started = receipt.with_suffix('.started.json')
    if receipt.exists() or started.exists():
        raise FileExistsError('process receipt must be new')
    child = subprocess.Popen(command)
    write_json(started, {'started_at_sgt': now_sgt(), 'wrapper_pid': os.getpid(),
                         'child_pid': child.pid, 'command': command})

    def forward(signum, frame):
        if child.poll() is None:
            child.send_signal(signum)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)
    code = child.wait()
    write_json(receipt, {'completed_at_sgt': now_sgt(), 'child_pid': child.pid,
                         'child_returncode': code, 'exit_code': code if code >= 0 else 128-code,
                         'signal': -code if code < 0 else None})
    return code if code >= 0 else 128-code


if __name__ == '__main__':
    sys.exit(main())
