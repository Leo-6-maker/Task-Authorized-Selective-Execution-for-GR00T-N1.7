"""Persistent E3 operator. No native call without independent exact authorization.

Use a task-owned persistent remote session and an independent backup agent.
Importing this module never imports CUDA, MuJoCo, policy or native libraries.
"""
import argparse
import sys

from .contract import drive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['runtime-map', 'operator-directory', 'review-commit', 'review-path', 'session']:
        p.add_argument('--'+name, required=True)
    a = p.parse_args()
    from .native import NativeBackend
    backend = NativeBackend(a.runtime_map, a.operator_directory,
                            a.review_commit, a.review_path, a.session)
    try:
        drive(backend)
        return 0
    except BaseException:
        return 1  # Original traceback, cell and actual exits already retained privately.


if __name__ == '__main__':
    sys.exit(main())
