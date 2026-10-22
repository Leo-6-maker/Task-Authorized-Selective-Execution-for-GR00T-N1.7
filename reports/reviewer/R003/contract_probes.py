"""R003 reviewer SYNTHETIC CPU probes, not robot/model/private-original evidence.

Run with the reviewed PR #5 checkout as --source-root. Only stdlib and NumPy
are required. No GPU, simulation, pickle or network access is performed.
"""
import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np

EXPECTED = {
    'tase/task_spec.py': '5b034c4ce2319cf4b0a0fa632f7bba42d8efdf00',
    'tase/event_oracle.py': '0c429689a71cbd0ecc3404a774eb4a6bd362b03e',
    'tase/snapshot.py': 'fd85e3e9ee11dc6d193ded5f88b9743e9a878268',
    'tase/evidence.py': '8cbe5f3c6dceda0216542cf22ecdd29805dffe74',
    'tase/audit_contract.py': '5a1fa83cc77d59b0d5a13957e5d1f417a8086971',
    'tase/retention.py': '9a031f63bae9e62ffe2f5c76d2197e9ac9d3de49',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve(strict=True)
    for name, expected in EXPECTED.items():
        data = (root / name).read_bytes()
        actual = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        if actual != expected:
            raise ValueError('Not the reviewed source bytes: ' + name)
    sys.path.insert(0, str(root))
    from tase.task_spec import TaskSpec
    from tase.event_oracle import EventOracle
    from tase.snapshot import fields, restore_fields, digest
    from tase.audit_contract import check_observation, OBS_KEYS
    from tase.evidence import manifest, verify_manifest
    from tase.retention import traced_control_step, cleanup_resources

    spec = TaskSpec('target', 'basket', {
        n: {'body_id': i+1, 'body_name': n+'_body', 'geoms': [i+1],
            'geom_names': [n+'_geom']}
        for i, n in enumerate(['target', 'other', 'basket'])
    }, [20], [21]).validate()

    def frame(step, obj='other', height=0.03):
        return {
            'step': step, 'eef_pos': np.array([0., 0., height]),
            'eef_quat': np.array([1., 0., 0., 0.]), 'gripper': np.zeros(2),
            'objects': {n: {'pos': np.array([0., 0., height if n == obj else 0.]),
                            'quat': np.array([1., 0., 0., 0.])} for n in spec.objects},
            'left_contacts': {n: n == obj for n in spec.objects},
            'right_contacts': {n: n == obj for n in spec.objects},
            'official_success': False,
        }

    def run_case(name, mutate, obj='other'):
        oracle = EventOracle(spec, {n: [0, 0, 0] for n in spec.objects})
        labels = []
        try:
            for step in range(1, 4):
                value = frame(step, obj=obj)
                mutate(value)
                result = oracle.consume(value)
                labels.append(next(e['label'] for e in result['events'] if e['object'] == obj))
            return {'case': name, 'raises': False, 'labels': labels,
                    'first_violation_step': oracle.first_violation_step}
        except Exception as exc:
            return {'case': name, 'raises': True, 'error_type': type(exc).__name__, 'labels': labels}

    oracle_cases = [
        run_case('valid_wrong_lift_control', lambda f: None),
        run_case('valid_authorized_lift_control', lambda f: None, obj='target'),
        run_case('nonfinite_object_position_control', lambda f: f['objects']['other']['pos'].__setitem__(0, np.nan)),
        run_case('nonfinite_eef_position', lambda f: f['eef_pos'].__setitem__(0, np.nan)),
        run_case('nonfinite_eef_quaternion', lambda f: f['eef_quat'].__setitem__(0, np.nan)),
        run_case('nonfinite_finger_position', lambda f: f['gripper'].__setitem__(0, np.nan)),
        run_case('nonfinite_object_quaternion', lambda f: f['objects']['other']['quat'].__setitem__(0, np.nan)),
        run_case('string_contacts_not_boolean', lambda f: (
            f['left_contacts'].__setitem__('other', 'False'),
            f['right_contacts'].__setitem__('other', 'False'))),
        run_case('prohibited_gate_field', lambda f: f.__setitem__('gate_score', 0.5)),
        run_case('missing_object', lambda f: f['objects'].pop('other')),
    ]
    oracle = EventOracle(spec, {n: [0, 0, 0] for n in spec.objects})
    for step in range(1, 8):
        value = frame(step, height=0)
        value['right_contacts']['other'] = False
        oracle.consume(value)
    oracle.consume(frame(8))
    result = oracle.consume(frame(9))
    oracle_cases.append({'case': 'cross_chunk_sustain',
                         'first_violation_step': result['first_violation_step']})
    source = SimpleNamespace(goal=np.ones(3), history=[np.arange(2)], flag=True)
    saved, _ = fields(source)
    target = SimpleNamespace(goal=np.zeros(3), history=[], flag=False)
    restore_fields(target, saved)
    equal = digest(fields(target)[0]) == digest(saved)
    target.goal[0] = 5
    target.history[0][0] = 5
    oracle_cases.append({'case': 'snapshot_tree_copy', 'roundtrip_digest': equal,
                         'independent_arrays': bool(source.goal[0] == 1 and saved['goal'][0] == 1
                                                    and source.history[0][0] == 0)})

    repairs = []
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        arrays = {k: (np.zeros((1, 1, 256, 256, 3), dtype=np.uint8) if k.startswith('video')
                      else np.zeros((1, 1, 2 if k == 'state.gripper' else 1), dtype=np.float32))
                  for k in OBS_KEYS}
        variants = {
            'valid_observation': arrays,
            'missing_wrist': {k: v for k, v in arrays.items() if k != 'video.wrist_image'},
            'empty_observation': {},
            'wrong_dtype': {**arrays, 'state.x': np.zeros((1, 1, 1), dtype=np.float64)},
        }
        for name, values in variants.items():
            path = folder / (name + '.npz')
            np.savez(path, **values)
            try:
                with np.load(path, allow_pickle=False) as obs:
                    check_observation(obs)
                repairs.append({'case': name, 'accepted': True})
            except ValueError as exc:
                repairs.append({'case': name, 'accepted': False, 'error': str(exc)})
        path = folder / 'file'
        path.write_bytes(b'payload')
        records = manifest(folder, [path], 'synth')
        for name, rows, required in [
            ('valid_manifest', records, {'file'}),
            ('empty_manifest', [], {'file'}),
            ('duplicate_manifest', records*2, {'file'}),
            ('missing_coverage', records, {'file', 'other'}),
        ]:
            try:
                verify_manifest(folder, rows, required=required, source_run='synth')
                repairs.append({'case': name, 'accepted': True})
            except ValueError as exc:
                repairs.append({'case': name, 'accepted': False, 'error': str(exc)})
        states, actions = [], []
        result = {'inner_steps': 0, 'exit_code': 0, 'status': 'SUCCESS'}
        traced_control_step(lambda a: None, np.zeros(7), lambda: np.ones(4),
                            folder, states, actions, result)
        def fail_step(action):
            raise RuntimeError('synthetic physics exception')
        try:
            traced_control_step(fail_step, np.ones(7), lambda: np.ones(4),
                                folder, states, actions, result)
        except RuntimeError:
            pass
        with np.load(folder / 'control_trace.npz', allow_pickle=False) as trace:
            repairs.append({'case': 'partial_step_retention',
                            'retained_successful_steps': len(trace['states']),
                            'completed_step_count': result['inner_steps'],
                            'failure_record_present': (folder/'control_step_errors.jsonl').exists()})
        called = []
        def fail_close():
            raise RuntimeError('synthetic cleanup exception')
        cleanup_resources(folder, result, [('bad', fail_close), ('good', lambda: called.append(True))])
        repairs.append({'case': 'cleanup_failure_retention', 'status': result['status'],
                        'exit_code': result['exit_code'], 'other_cleanup_executed': bool(called),
                        'error_record_present': (folder/'cleanup_errors.json').exists()})
    print(json.dumps({'review_head': 'd64cb1002980738f170e3206d004b4a882166543',
                      'scope': '22 focused synthetic cases; not the full existing unittest suite',
                      'source_blobs': EXPECTED, 'oracle_cases': oracle_cases,
                      'repair_cases': repairs}, indent=2))


if __name__ == '__main__':
    main()
