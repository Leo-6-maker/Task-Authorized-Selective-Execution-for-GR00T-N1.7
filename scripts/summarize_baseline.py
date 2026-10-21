"""CPU audit of retained native M1 evidence; never runs a model or simulator.

Requires the simulator environment's numpy. Writes sanitized, derived facts;
raw observations/actions/videos remain private. Assertion failures stop delivery.
"""
import argparse
import csv
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tase.evidence import verify_manifest, write_json


def audit(root):
    import numpy as np
    rows, checks = [], []
    keys = ['action.'+s for s in ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']]
    fields = ['run_id', 'task', 'init_index', 'status', 'official_success',
              'exit_code', 'policy_calls', 'policy_requests_attempted', 'inner_steps',
              'settling_steps', 'wall_seconds', 'repo_sha', 'config_hash', 'init_hash',
              'settled_state_hash', 'scene_xml_hash', 'egl_binding_check']
    for folder in sorted((root/'runs/episodes').iterdir()):
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        result = json.loads((folder/'result.json').read_text())
        reservation = json.loads((folder/'reservation.json').read_text())
        assert result['split'] == reservation['split'] == 'DEV'
        assert result['repo_sha'] == reservation['repo_sha']
        verify_manifest(root, json.loads((folder/'artifact_manifest.json').read_text()))
        full = result['status'] in ['SUCCESS', 'TIME_LIMIT']
        row = {k: result.get(k) for k in fields}
        row['full_policy_episode'] = full
        row['error_type'] = result.get('error_type')
        rows.append(row)
        if not reservation['probe_only']:
            receipt = json.loads((root/'runs'/f'{folder.name}.exit.json').read_text())
            assert receipt['exit_code'] == result['exit_code']
        if not full:
            continue
        contract = json.loads((folder/'horizon.json').read_text())
        assert contract == dict(n_action_steps=8, action_horizon=16,
                               video_delta_indices=[0], state_delta_indices=[0])
        parity = json.loads((folder/'reset_parity.json').read_text())
        assert parity['state_unchanged']
        assert all(parity['latest_native_observation_equal'].values())
        decisions = [json.loads(s) for s in (folder/'decisions.jsonl').read_text().splitlines()]
        assert len(decisions) == result['policy_calls']
        assert sum(d['inner_steps'] for d in decisions) == result['inner_steps']
        assert any(d['official_success'] for d in decisions) == result['official_success']
        assert decisions[-1]['terminated']
        if result['status'] == 'TIME_LIMIT':
            assert result['inner_steps'] == 720 and not result['official_success']
        expected = []
        for i, decision in enumerate(decisions):
            assert decision['index'] == i
            assert 1 <= decision['inner_steps'] <= 8
            with np.load(folder/f'action-{i:03d}.npz', allow_pickle=False) as actions:
                assert set(actions.files) == set(keys)
                for key in keys:
                    assert actions[key].shape == (1, 16, 1)
                    assert actions[key].dtype == np.float32
                    assert np.isfinite(actions[key]).all()
                values = np.stack([actions[k][0, :decision['inner_steps'], 0] for k in keys], axis=1)
                values[:, -1] = -np.sign(2*values[:, -1]-1)
                expected.append(values)
            with np.load(folder/f'observation-{i:03d}.npz', allow_pickle=False) as obs:
                for key in obs.files:
                    arr = obs[key]
                    if key.startswith('video'):
                        assert arr.shape == (1, 1, 256, 256, 3) and arr.dtype == np.uint8
                    else:
                        assert arr.shape == (1, 1, 2 if key == 'state.gripper' else 1)
                        assert arr.dtype == np.float32 and np.isfinite(arr).all()
        with np.load(folder/'control_trace.npz', allow_pickle=False) as trace:
            assert len(trace['states']) == result['inner_steps']
            assert np.array_equal(np.concatenate(expected), trace['converted_actions'])
        checks.append({'run_id': folder.name, 'artifact_hashes': 'PASS',
                       'native_reset_history_parity': 'PASS', 'request_dtypes_shapes': 'PASS',
                       'native_action_prefix_and_one_gripper_conversion': 'PASS',
                       'audited_control_steps': result['inner_steps']})
    complete = [r for r in rows if r['full_policy_episode']]
    logs = [json.loads(s) for s in (root/'runs/server-03/inference.jsonl').read_text().splitlines()]
    passes = [r for r in logs if r['status'] == 'PASS']
    assert len(passes) == sum(r['policy_calls'] for r in complete)
    assert len(logs) == sum(r['policy_requests_attempted'] or 0 for r in rows)
    assert [r['request'] for r in logs] == list(range(1, len(logs)+1))
    assert json.loads((root/'runs/server-03.exit.json').read_text())['exit_code'] == 0
    assert len(rows) <= 24
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0)+1
    latency = [r['inference_ms'] for r in passes]
    times = [r['wall_seconds'] for r in complete]
    return {'protocol_id': 'TASE-001-v1.0', 'scope': 'M0-M1 / DEV / native C0',
            'budget': {'limit': 24, 'used': len(rows), 'remaining': 24-len(rows)},
            'outcomes_all_attempts': counts, 'complete_policy_episodes': len(complete),
            'successes': sum(r['official_success'] for r in complete),
            'policy_server_requests': len(logs), 'model_forwards': len(passes),
            'validation_rejected_requests': len(logs)-len(passes),
            'inner_steps': sum(r['inner_steps'] for r in rows),
            'inference_ms': {'min': min(latency), 'median': statistics.median(latency),
                             'mean': statistics.mean(latency), 'max': max(latency),
                             'first': latency[0]},
            'episode_wall_seconds': {'min': min(times), 'median': statistics.median(times),
                                     'mean': statistics.mean(times), 'max': max(times)},
            'peak_allocated_bytes': max(r['peak_allocated_bytes'] for r in logs),
            'peak_reserved_bytes': max(r['peak_reserved_bytes'] for r in logs),
            'server_exit_code': 0, 'runs': rows, 'audit': checks,
            'review_limitation': 'Executor CPU recomputation of private raw evidence; independent reviewer access still required'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--csv', type=Path)
    a = p.parse_args()
    data = audit(a.private_runtime)
    write_json(a.output, data)
    if a.csv:
        with a.csv.open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(data['runs'][0]))
            writer.writeheader()
            writer.writerows(data['runs'])
    print(json.dumps({k: v for k, v in data.items() if k not in ['runs', 'audit']}, indent=2))


if __name__ == '__main__':
    main()
