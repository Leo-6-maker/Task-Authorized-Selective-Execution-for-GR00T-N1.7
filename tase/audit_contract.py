"""Explicit, optimization-safe contracts for private M1 evidence."""
import json
import re
from pathlib import Path
from .evidence import sha256, verify_manifest

POSE = ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']
OBS_KEYS = {'video.image', 'video.wrist_image'} | {'state.'+k for k in POSE}
LANGUAGE = 'annotation.human.action.task_description'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_observation(obs, allow_dtype_rejection=False):
    import numpy as np
    require(len(obs.files) == len(OBS_KEYS) and set(obs.files) == OBS_KEYS,
            'observation key set incomplete or duplicated')
    dtype_errors = []
    for key in OBS_KEYS:
        arr = obs[key]
        shape = (1, 1, 256, 256, 3) if key.startswith('video') else (1, 1, 2 if key == 'state.gripper' else 1)
        require(arr.shape == shape, 'observation shape mismatch: '+key)
        expected = np.uint8 if key.startswith('video') else np.float32
        if arr.dtype != expected:
            dtype_errors.append(key)
        require(np.isfinite(arr).all(), 'nonfinite observation')
    require(not dtype_errors or allow_dtype_rejection, 'observation dtype mismatch')
    return dtype_errors


def validate_run(root, folder, result, reservation, config, config_hash):
    import numpy as np
    require(result['run_id'] == reservation['run_id'] == folder.name, 'run ID mismatch')
    require(result['status'] in ['SUCCESS', 'TIME_LIMIT', 'RUNTIME_ERROR',
                                 'ENVIRONMENT_PROBE_PASS', 'CLEANUP_ERROR'], 'unknown outcome')
    for key in ['repo_sha', 'task', 'init_index', 'config_hash', 'split']:
        require(result[key] == reservation[key], 'reservation/result identity mismatch: '+key)
    require(re.fullmatch('[0-9a-f]{40}', result['repo_sha']), 'invalid source SHA')
    require(result['config_hash'] == config_hash, 'configuration identity mismatch')
    require(result['task'] in config['tasks'] and result['init_index'] in config['development_init_indices'],
            'undeclared development cell')
    require(type(reservation['probe_only']) is bool, 'probe flag must be boolean')
    for key in ['policy_calls', 'inner_steps', 'settling_steps', 'exit_code']:
        require(type(result[key]) is int and result[key] >= 0, 'invalid count: '+key)
    attempted = result.get('policy_requests_attempted', 0)
    require(type(attempted) is int and attempted >= result['policy_calls'], 'invalid attempted requests')
    require(result['inner_steps'] <= config['max_inner_steps'], 'control step limit exceeded')
    require(result['settling_steps'] <= config['settling_steps'], 'settling limit exceeded')
    require(np.isfinite(result['wall_seconds']) and result['wall_seconds'] >= 0, 'invalid wall time')
    names = {p.name for p in folder.iterdir() if p.is_file() and p.name != 'artifact_manifest.json'}
    require({'result.json', 'reservation.json'} <= names, 'missing core record')
    paths = {str((folder/n).relative_to(root).as_posix()) for n in names}
    verify_manifest(root, json.loads((folder/'artifact_manifest.json').read_text()),
                    required=paths, source_run=folder.name)
    require({p.name for p in folder.glob('observation-*.npz')} ==
            {f'observation-{i:03d}.npz' for i in range(attempted)}, 'observation coverage mismatch')
    require({p.name for p in folder.glob('action-*.npz')} ==
            {f'action-{i:03d}.npz' for i in range(result['policy_calls'])}, 'action coverage mismatch')
    if result['settling_steps']:
        required = {'benchmark_init.npy', 'settled_state.npy', 'scene.xml', 'controller.json',
                    'observation_schema.json', 'video.image.png', 'video.wrist_image.png'}
        if not reservation['probe_only']:
            required.add('object_catalog.json')
        require(required <= names, 'missing native initialization evidence')
        for file, key in [('benchmark_init.npy', 'init_hash'), ('settled_state.npy', 'settled_state_hash'),
                          ('scene.xml', 'scene_xml_hash')]:
            require(sha256(folder/file) == result[key], 'initialization identity mismatch')
        expected_task = 'pick_up_the_'+result['task']+'_and_place_it_in_the_basket'
        require(result['full_task_name'] == expected_task and
                result['native_language'] == expected_task.replace('_', ' '), 'task/language identity mismatch')
    if not reservation['probe_only']:
        receipt = json.loads((root/'runs'/f'{folder.name}.exit.json').read_text())
        started = json.loads((root/'runs'/f'{folder.name}.exit.started.json').read_text())
        require(receipt['exit_code'] == result['exit_code'] and receipt['child_pid'] == started['child_pid'],
                'child process identity/exit mismatch')
        code = receipt['child_returncode']
        require(receipt['exit_code'] == (code if code >= 0 else 128-code), 'invalid process returncode mapping')
    else:
        require(attempted == result['policy_calls'] == result['inner_steps'] == 0, 'probe performed policy work')
    full = result['status'] in ['SUCCESS', 'TIME_LIMIT']
    if full:
        require(not reservation['probe_only'] and result['exit_code'] == 0, 'invalid full episode status')
        require(result['settling_steps'] == config['settling_steps'], 'incomplete initialization')
        require(type(result['official_success']) is bool and
                result['official_success'] == (result['status'] == 'SUCCESS'), 'success/outcome mismatch')
        require({'horizon.json', 'reset_parity.json', 'decisions.jsonl', 'control_trace.npz', 'rollout.mp4'} <= names,
                'missing full episode evidence')
        require(attempted == result['policy_calls'] > 0, 'full episode has missing requests')
    return full
