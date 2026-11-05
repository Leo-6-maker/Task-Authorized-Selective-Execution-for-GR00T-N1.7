"""CPU-only audit of the exact upstream gripper helpers, not a simulator test."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    path = a.upstream / 'gr00t/eval/sim/LIBERO/libero_env.py'
    source = path.read_text()
    tree = ast.parse(source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name in ['normalize_gripper_action', 'invert_gripper_action']]
    if len(selected) != 2:
        raise ValueError('native gripper helpers not found')
    namespace = {'np': np}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    mapping = []
    for value in [0.0, 0.5, 1.0]:
        original = np.array([0., 0., 0., 0., 0., 0., value])
        actual = namespace['invert_gripper_action'](
            namespace['normalize_gripper_action'](original.copy()))
        expected = -np.sign(2*value-1)
        if actual[-1] != expected or original[-1] != value:
            raise ValueError('gripper mapping/copy protection mismatch')
        mapping.append({'policy_gripper': value, 'raw_controller_gripper': float(actual[-1])})
    report = {'status': 'SOURCE_HELPERS_EXECUTED_CPU_ONLY',
              'native_wrapper_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'mapping': mapping, 'environment_created': False,
              'model_forward': False, 'runtime_contract_validated': False}
    with a.output.open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
