"""CPU audit of retained native M1 evidence; never runs a model or simulator.

Requires the simulator environment's numpy. Writes sanitized, derived facts;
raw observations/actions/videos remain private. Explicit validation errors stop delivery.
"""
import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tase.evidence import verify_manifest, write_json, sha256
from tase.audit_contract import require, validate_run, check_observation, OBS_KEYS, LANGUAGE

def audit(root, delivery_manifest=None):
    import numpy as np
    root = Path(root).resolve(strict=True)
    config_path = Path(__file__).resolve().parents[1]/'configs/dev_baseline.json'
    config = json.loads(config_path.read_text())
    config_hash = sha256(config_path)
    require(config['split'] == 'DEV' and config['condition'] == 'C0', 'unauthorized audit configuration')
    require(not (root/'runs/episodes/.reservation-lock').exists(), 'active or interrupted reservation')
    if delivery_manifest is not None:
        delivery = json.loads(Path(delivery_manifest).read_text())
        raw = [e for e in delivery['artifacts'] if e['visibility'] == 'private' and e['storage'] == 'runtime']
        verify_manifest(root, raw, required={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()})
    rows, checks = ([], [])
    ordinals = []
    keys = ['action.' + s for s in ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']]
    fields = ['run_id', 'task', 'init_index', 'status', 'official_success', 'exit_code', 'policy_calls', 'policy_requests_attempted', 'inner_steps', 'settling_steps', 'wall_seconds', 'repo_sha', 'config_hash', 'init_hash', 'settled_state_hash', 'scene_xml_hash', 'egl_binding_check']
    for folder in sorted((root / 'runs/episodes').iterdir()):
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        result = json.loads((folder / 'result.json').read_text())
        reservation = json.loads((folder / 'reservation.json').read_text())
        require(result['split'] == reservation['split'] == 'DEV', 'audit contract failed at legacy check 30')
        require(result['repo_sha'] == reservation['repo_sha'], 'audit contract failed at legacy check 31')
        full = validate_run(root, folder, result, reservation, config, config_hash)
        ordinals.append(reservation['budget_ordinal'])
        row = {k: result.get(k) for k in fields}
        row['full_policy_episode'] = full
        row['error_type'] = result.get('error_type')
        rows.append(row)
        if not reservation['probe_only']:
            receipt = json.loads((root / 'runs' / f'{folder.name}.exit.json').read_text())
            require(receipt['exit_code'] == result['exit_code'], 'audit contract failed at legacy check 40')
        if not full:
            if result.get('policy_requests_attempted', 0):
                require(result['policy_calls'] == 0 and result['inner_steps'] == 0 and
                        result['status'] == 'RUNTIME_ERROR', 'unsupported partial legacy run requires explicit investigation')
                with np.load(folder/'observation-000.npz', allow_pickle=False) as obs:
                    rejected = check_observation(obs, allow_dtype_rejection=True)
                    require(bool(rejected), 'recorded dtype rejection has no dtype defect')
            continue
        contract = json.loads((folder / 'horizon.json').read_text())
        require(contract == dict(n_action_steps=8, action_horizon=16, video_delta_indices=[0], state_delta_indices=[0]), 'audit contract failed at legacy check 44')
        parity = json.loads((folder / 'reset_parity.json').read_text())
        require(parity['state_unchanged'] is True, 'reset state parity must be explicit true')
        mapping = parity['latest_native_observation_equal']
        require(set(mapping) == OBS_KEYS | {LANGUAGE} and all(v is True for v in mapping.values()),
                'reset parity key set or boolean values incomplete')
        require(parity['history'] == contract, 'reset history/horizon mismatch')
        decisions = [json.loads(s) for s in (folder / 'decisions.jsonl').read_text().splitlines()]
        require(len(decisions) == result['policy_calls'], 'audit contract failed at legacy check 50')
        require(sum((d['inner_steps'] for d in decisions)) == result['inner_steps'], 'audit contract failed at legacy check 51')
        require(any((d['official_success'] for d in decisions)) == result['official_success'], 'audit contract failed at legacy check 52')
        require(decisions[-1]['terminated'], 'audit contract failed at legacy check 53')
        if result['status'] == 'TIME_LIMIT':
            require(result['inner_steps'] == 720 and (not result['official_success']), 'audit contract failed at legacy check 55')
        expected = []
        for i, decision in enumerate(decisions):
            require(decision['index'] == i, 'audit contract failed at legacy check 58')
            require(type(decision['index']) is int and type(decision['inner_steps']) is int,
                    'decision indices/counts must be integers')
            require(all(type(decision[k]) is bool for k in ['official_success', 'terminated', 'truncated']),
                    'decision outcomes must be boolean')
            require(not (decision['terminated'] or decision['truncated']) or i == len(decisions)-1,
                    'extra decisions after terminal outcome')
            require(1 <= decision['inner_steps'] <= 8, 'audit contract failed at legacy check 59')
            with np.load(folder / f'action-{i:03d}.npz', allow_pickle=False) as actions:
                require(len(actions.files) == len(keys) and set(actions.files) == set(keys), 'action key set incomplete or duplicated')
                for key in keys:
                    require(actions[key].shape == (1, 16, 1), 'audit contract failed at legacy check 63')
                    require(actions[key].dtype == np.float32, 'audit contract failed at legacy check 64')
                    require(np.isfinite(actions[key]).all(), 'audit contract failed at legacy check 65')
                values = np.stack([actions[k][0, :decision['inner_steps'], 0] for k in keys], axis=1)
                values[:, -1] = -np.sign(2 * values[:, -1] - 1)
                expected.append(values)
            with np.load(folder / f'observation-{i:03d}.npz', allow_pickle=False) as obs:
                check_observation(obs)
                for key in obs.files:
                    arr = obs[key]
                    if key.startswith('video'):
                        require(arr.shape == (1, 1, 256, 256, 3) and arr.dtype == np.uint8, 'audit contract failed at legacy check 73')
                    else:
                        require(arr.shape == (1, 1, 2 if key == 'state.gripper' else 1), 'audit contract failed at legacy check 75')
                        require(arr.dtype == np.float32 and np.isfinite(arr).all(), 'audit contract failed at legacy check 76')
        with np.load(folder / 'control_trace.npz', allow_pickle=False) as trace:
            require(set(trace.files) == {'states', 'converted_actions'}, 'trace schema mismatch')
            require(np.isfinite(trace['states']).all() and np.isfinite(trace['converted_actions']).all(),
                    'nonfinite trace')
            require(len(trace['states']) == result['inner_steps'], 'audit contract failed at legacy check 78')
            require(np.array_equal(np.concatenate(expected), trace['converted_actions']), 'audit contract failed at legacy check 79')
        checks.append({'run_id': folder.name, 'artifact_hashes': 'PASS', 'native_reset_history_parity': 'PASS', 'request_dtypes_shapes': 'PASS', 'native_action_prefix_and_one_gripper_conversion': 'PASS', 'audited_control_steps': result['inner_steps']})
    require(sorted(ordinals) == list(range(1, len(rows)+1)), 'duplicate/missing reservation ordinal')
    complete = [r for r in rows if r['full_policy_episode']]
    logs = [json.loads(s) for s in (root / 'runs/server-03/inference.jsonl').read_text().splitlines()]
    passes = [r for r in logs if r['status'] == 'PASS']
    require(all(r['status'] in ['PASS', 'ERROR'] for r in logs), 'unknown request status')
    cursor = 0
    for row in rows:
        requests = logs[cursor:cursor+(row['policy_requests_attempted'] or 0)]
        require(sum(r['status'] == 'PASS' for r in requests) == row['policy_calls'],
                'request-to-run call count mismatch')
        cursor += len(requests)
    for record in passes:
        require(set(record['output_shapes']) == set(keys) and
                all(v == [1, 16, 1] for v in record['output_shapes'].values()), 'server output contract mismatch')
        expected_shapes = {k: ([1,1,256,256,3] if k.startswith('video') else
                              [1,1,2 if k == 'state.gripper' else 1]) for k in OBS_KEYS}
        require(record['input_shapes'] == expected_shapes, 'server input contract mismatch')
        require(np.isfinite(record['inference_ms']) and record['inference_ms'] > 0, 'invalid inference duration')
    require(len(passes) == sum((r['policy_calls'] for r in complete)), 'audit contract failed at legacy check 87')
    require(len(logs) == sum((r['policy_requests_attempted'] or 0 for r in rows)), 'audit contract failed at legacy check 88')
    require([r['request'] for r in logs] == list(range(1, len(logs) + 1)), 'audit contract failed at legacy check 89')
    require(json.loads((root / 'runs/server-03.exit.json').read_text())['exit_code'] == 0, 'audit contract failed at legacy check 90')
    require(len(rows) <= 24, 'audit contract failed at legacy check 91')
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    latency = [r['inference_ms'] for r in passes]
    times = [r['wall_seconds'] for r in complete]
    return {'protocol_id': 'TASE-001-v1.0', 'scope': 'M0-M1 / DEV / native C0', 'budget': {'limit': 24, 'used': len(rows), 'remaining': 24 - len(rows)}, 'outcomes_all_attempts': counts, 'complete_policy_episodes': len(complete), 'successes': sum((r['official_success'] for r in complete)), 'policy_server_requests': len(logs), 'model_forwards': len(passes), 'validation_rejected_requests': len(logs) - len(passes), 'inner_steps': sum((r['inner_steps'] for r in rows)), 'inference_ms': {'min': min(latency), 'median': statistics.median(latency), 'mean': statistics.mean(latency), 'max': max(latency), 'first': latency[0]}, 'episode_wall_seconds': {'min': min(times), 'median': statistics.median(times), 'mean': statistics.mean(times), 'max': max(times)}, 'peak_allocated_bytes': max((r['peak_allocated_bytes'] for r in logs)), 'peak_reserved_bytes': max((r['peak_reserved_bytes'] for r in logs)), 'server_exit_code': 0, 'runs': rows, 'audit': checks, 'review_limitation': 'Executor CPU recomputation of private raw evidence; independent reviewer access still required'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--csv', type=Path)
    p.add_argument('--delivery-manifest',type=Path)
    a = p.parse_args()
    data = audit(a.private_runtime, a.delivery_manifest)
    write_json(a.output, data)
    if a.csv:
        with a.csv.open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(data['runs'][0]))
            writer.writeheader()
            writer.writerows(data['runs'])
    print(json.dumps({k: v for k, v in data.items() if k not in ['runs', 'audit']}, indent=2))
if __name__ == '__main__':
    main()
