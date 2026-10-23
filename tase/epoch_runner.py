"""E2 epoch runner reusing the native M1 execution path. No TEST entry."""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from .evidence import append_json, now_sgt, reserve_episode, sha256, write_json
from .e2_evidence import manifest
from .retention import cleanup_resources, traced_control_step

TASKS = {name: f'pick_up_the_{name}_and_place_it_in_the_basket'
         for name in ['alphabet_soup', 'cream_cheese', 'ketchup']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--task', choices=TASKS, required=True)
    p.add_argument('--init-index', type=int, required=True)
    p.add_argument('--config', type=Path, default=Path('configs/e2_dev.json'))
    p.add_argument('--condition', choices=['C0','C2'], default='C0')
    p.add_argument('--system', choices=['B0','G'], default='B0')
    p.add_argument('--verify-reset', action='store_true')
    p.add_argument('--allocation-record', type=Path, required=True)
    p.add_argument('--probe-only', action='store_true')
    p.add_argument('--port', type=int, default=5558)
    p.add_argument('--m2', action='store_true', help='R002 bounded DEV capture; no Gate intervention')
    a = p.parse_args()
    config = json.loads(a.config.read_text())
    split=config['split']
    if config['protocol_id'] != 'TASE-002-v1.0' or config['run_epoch'] != 'E2' or split not in ['DEV','CALIB']:
        raise ValueError('only E2 DEV and conditional CALIB; TEST requires R2')
    if split=='DEV' and a.init_index not in [0,1]:raise ValueError('DEV initializations remain fixed')
    if a.m2 or a.probe_only:
        raise ValueError('E2 does not reuse legacy M2 IDs or unplanned probes')
    scenario_number=list(TASKS).index(a.task)*10+a.init_index*2+(a.condition=='C2')
    cell={'run_id':a.run_id,'epoch':'E2','protocol_id':'TASE-002-v1.0','split':split,
          'task':a.task,'init_index':a.init_index,'condition':a.condition,'system':a.system,
          'scenario_id':f'E2-{split}-{a.task}-i{a.init_index}-{a.condition}',
          'policy_seed':config['policy_seed_base']+scenario_number,
          'environment_seed':config['environment_seed_base']+scenario_number,
          'policy_target':config['c2_policy_targets'][a.task] if a.condition=='C2' else a.task}
    declared=json.loads(Path('configs/e2_dev_cells.json' if split=='DEV' else 'configs/e2_calib_cells.json').read_text())
    planned=declared['planned_cells']+declared.get('diagnostic_cells',[])
    bound=next((row for row in planned if row['run_id']==a.run_id),None)
    if bound is None or any(cell[key]!=value for key,value in bound.items()):
        raise ValueError('attempt must match a committed E2 cell, including diagnostic attempts')
    if not json.loads(a.allocation_record.read_text()).get('shared_gpu_inference_authorized'):
        raise ValueError('GPU usage not authorized')
    repo_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
    if dirty:
        raise ValueError('commit implementation before runtime; dirty worktree refused')
    runtime_lock_hash = sha256(a.config.parent/'runtime_lock_E2.json')
    extra={}
    if split=='CALIB':
        from scripts.e2_audit_pairs import summarize
        summarize(a.workspace,Path.cwd())
        splits=json.loads(Path('configs/e2_splits.json').read_text())
        selected_init=next((r for r in splits['rows'] if r['task']==a.task and r['init_index']==a.init_index and r['split']=='CALIB'),None)
        if selected_init is None:raise ValueError('CALIB cell is outside frozen holdout')
        extra={'splits_hash':sha256('configs/e2_splits.json'),'calibration_plan_hash':sha256('configs/e2_calibration_plan.json'),
               'planned_init_hash':selected_init['init_hash']}
        plan=json.loads(Path('configs/e2_calibration_plan.json').read_text())
        if plan['splits_hash']!=extra['splits_hash'] or plan['cells_hash']!=sha256('configs/e2_calib_cells.json') or plan['TEST_authorized'] is not False:
            raise ValueError('CALIB plan/split/cell binding differs')
        if a.system=='G':
            selection=json.loads(Path('configs/e2_calib_selection.json').read_text())
            if selection['status']!='SELECTED_WITHIN_PREDECLARED_RULE' or selection['calibration_plan_hash']!=extra['calibration_plan_hash']:
                raise ValueError('CALIB G requires valid frozen selection')
            extra['calibration_selection_hash']=sha256('configs/e2_calib_selection.json');config=dict(config,gate_k=selection['selected_k'])
    if a.system=='G':
        # Recompute all committed short-check receipts before any DEV Gate
        # reservation/model call. This is a machine gate under R004, not review.
        from scripts.e2_audit_validation import audit as audit_validation
        audit_validation(a.workspace,Path('configs/e2_shadow_plan.json'))
    metadata={
        'split': split, 'task': a.task, 'init_index': a.init_index,
        'repo_sha': repo_sha, 'config_hash': sha256(a.config), 'runtime_lock_hash': runtime_lock_hash,
        'probe_only': a.probe_only, 'started_at_sgt': now_sgt(),
        **cell,**extra}
    if split=='DEV':folder=reserve_episode(a.workspace/'runs/DEV',a.run_id,metadata,limit=config['maximum_episode_attempts'])
    else:
        from .e2_ledger import reserve_calibration
        folder=reserve_calibration(a.workspace/'runs/CALIB',a.run_id,metadata)
    start = time.perf_counter()
    result = dict(run_id=a.run_id, task=a.task, init_index=a.init_index, split=split,
                  repo_sha=repo_sha, config_hash=sha256(a.config), runtime_lock_hash=runtime_lock_hash,
                  status='STARTED', official_success=False, policy_calls=0,
                  policy_requests_attempted=0,
                  inner_steps=0, settling_steps=0, exit_code=1,
                  started_at_sgt=now_sgt())
    result.update(**cell,**extra)
    native = wrapped = client = video = m2 = None
    try:
        import numpy as np
        import cv2
        import gymnasium as gym
        from gymnasium.vector.utils import concatenate, create_empty_array
        import torch
        from PIL import Image
        from libero.libero import benchmark, get_libero_path
        from gr00t.eval.sim.LIBERO.libero_env import LiberoEnv
        from gr00t.eval._horizon_contract import PolicyHorizonSpec
        from gr00t.eval.sim.wrapper.multistep_wrapper import MultiStepWrapper
        from gr00t.policy.server_client import PolicyClient
        import random
        random.seed(cell['environment_seed']); np.random.seed(cell['environment_seed']); torch.manual_seed(cell['environment_seed'])
        suite = benchmark.get_benchmark_dict()['libero_object']()
        task_index = suite.get_task_names().index(TASKS[a.task])
        task = suite.get_task(task_index)
        bddl = Path(get_libero_path('bddl_files')) / task.problem_folder / task.bddl_file
        init_file = Path(get_libero_path('init_states')) / task.problem_folder / task.init_states_file
        # Only the two declared DEV indices are executed. No model selection by seed.
        # LIBERO's torch.load predates PyTorch 2.6's weights_only default. Keep
        # restricted loading and allow only the numpy types used by these pinned
        # initialization arrays, rather than enabling arbitrary pickle loading.
        safe_numpy = [np.core.multiarray._reconstruct, np.ndarray, np.dtype,
                      type(np.dtype('float64')), type(np.dtype('float32'))]
        with torch.serialization.safe_globals(safe_numpy):
            initial_states = torch.load(init_file, map_location='cpu', weights_only=True)
        selected_init = np.asarray(initial_states[a.init_index], dtype=np.float64)
        np.save(folder / 'benchmark_init.npy', selected_init, allow_pickle=False)
        if split=='CALIB' and sha256(folder/'benchmark_init.npy')!=extra['planned_init_hash']:
            raise ValueError('official initialization differs from committed split content')
        result.update(init_hash=sha256(folder / 'benchmark_init.npy'),
                      init_file_sha256=sha256(init_file), bddl_sha256=sha256(bddl),
                      full_task_name=task.name, native_language=task.language)
        native = LiberoEnv(task_bddl_file=str(bddl), task_description=task.language)
        raw = native._env
        native.reset(seed=cell['environment_seed'])
        obs = raw.set_init_state(selected_init)
        # Raw LIBERO uses -1=open. This is initialization, never a reject/hold action.
        for _ in range(config['settling_steps']):
            obs, _, _, _ = raw.step(np.array([0, 0, 0, 0, 0, 0, -1.0]))
            result['settling_steps'] += 1
        processed = native._process_observation(obs)
        settled = np.asarray(raw.get_sim_state())
        np.save(folder / 'settled_state.npy', settled, allow_pickle=False)
        xml = raw.sim.model.get_xml()
        (folder / 'scene.xml').write_text(xml)
        result.update(settled_state_hash=sha256(folder / 'settled_state.npy'),
                      scene_xml_hash=sha256(folder / 'scene.xml'),
                      control_hz=raw.env.control_freq,
                      task_objects=list(raw.obj_of_interest))
        objects = getattr(raw.env, 'objects', [])
        names = list(objects) if isinstance(objects, dict) else [o.name for o in objects]
        write_json(folder / 'object_catalog.json', {
            'objects': names, 'objects_of_interest': list(raw.obj_of_interest),
            'body_names': list(raw.sim.model.body_names),
            'meaning': 'Native scene inventory only; not a Gate or event oracle'})
        write_json(folder / 'observation_schema.json', {
            k: {'shape': list(np.asarray(v).shape), 'dtype': str(np.asarray(v).dtype)}
            for k, v in processed.items()})
        for key in ['video.image', 'video.wrist_image']:
            frame = np.asarray(processed[key])
            if frame.shape != (256, 256, 3) or frame.dtype != np.uint8:
                raise ValueError('native camera contract mismatch')
            Image.fromarray(frame).save(folder / (key + '.png'))
        from OpenGL import GL
        result['gl_renderer'] = GL.glGetString(GL.GL_RENDERER).decode()
        result['gl_vendor'] = GL.glGetString(GL.GL_VENDOR).decode()
        xml_query = subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True)
        own_gpus = [index for index, gpu in enumerate(ET.fromstring(xml_query).findall('gpu'))
                    if any(process.findtext('pid') == str(os.getpid())
                           for process in gpu.findall('./processes/process_info'))]
        result['egl_process_gpu_indices'] = own_gpus
        result['egl_binding_check'] = ('MATCH' if own_gpus ==
            [int(os.environ['MUJOCO_EGL_DEVICE_ID'])] else 'NOT_VERIFIED')
        controllers = raw.robots[0].controller
        write_json(folder / 'controller.json', {
            key: np.asarray(getattr(controllers, key)).tolist()
            for key in ['input_min', 'input_max', 'output_min', 'output_max',
                        'kp', 'kd', 'use_delta', 'control_dim']
            if hasattr(controllers, key)})
        if a.probe_only:
            result.update(status='ENVIRONMENT_PROBE_PASS', exit_code=0)
            return 0

        client = PolicyClient(host='127.0.0.1', port=a.port, timeout_ms=120000)
        reset_ack=client.call_endpoint('reset_and_seed', {'scenario_id':cell['scenario_id'],'seed':cell['policy_seed']})
        if reset_ack['seed']!=cell['policy_seed'] or reset_ack['scenario_id']!=cell['scenario_id']:
            raise ValueError('scenario reset acknowledgement mismatch')
        write_json(folder/'policy_reset.json', reset_ack)
        contract = PolicyHorizonSpec.from_policy(
            client, n_action_steps=config['execution_horizon_candidate'])
        write_json(folder / 'horizon.json', {
            key: value for key, value in vars(contract).items()})

        # Preserve native wrapper.reset history without resetting the settled simulator.
        class FixedReset(gym.Wrapper):
            def reset(self, *, seed=None, options=None):
                return processed, {'success': raw.check_success()}

        wrapped = MultiStepWrapper(FixedReset(native), contract=contract,
                                  max_episode_steps=config['max_inner_steps'],
                                  terminate_on_success=True)
        observation, _ = wrapped.reset()
        # This M1 adapter only substitutes the declared benchmark reset. Verify
        # it neither steps physics nor alters native observation/history values.
        state_unchanged = np.array_equal(np.asarray(raw.get_sim_state()), settled)
        equal_streams = {
            key: (observation[key] == value if key.startswith('annotation') else
                  np.array_equal(np.asarray(observation[key])[-1], np.asarray(value)))
            for key, value in processed.items()}
        write_json(folder / 'reset_parity.json', {
            'state_unchanged': bool(state_unchanged),
            'latest_native_observation_equal': {k: bool(v) for k, v in equal_streams.items()},
            'history': vars(contract),
            'scope': 'native settled reset and official wrapper history; no shadow'})
        if not state_unchanged or not all(equal_streams.values()):
            raise ValueError('fixed-reset native observation/state parity mismatch')
        from .e2_context import E2Context
        m2 = E2Context(raw, wrapped, client, folder, cell, config)
        video = cv2.VideoWriter(str(folder / 'rollout.mp4'), cv2.VideoWriter_fourcc(*'mp4v'),
                                20.0, (512, 256))
        if not video.isOpened():
            raise RuntimeError('video writer unavailable')
        state_rows, converted_rows = [], []
        original_step = raw.step

        def traced_step(action):
            value = traced_control_step(original_step, action, raw.get_sim_state,
                                       folder, state_rows, converted_rows, result)
            if m2 is not None:
                m2.frame(action)
            frame = np.concatenate([value[0]['agentview_image'][::-1, ::-1],
                                    value[0]['robot0_eye_in_hand_image'][::-1, ::-1]], axis=1)
            video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            return value

        raw.step = traced_step
        done = False
        while not done:
            # Use the same declared-space batching as native SyncVectorEnv.
            # Raw MuJoCo state is float64; its native Box contract is float32.
            request = concatenate(wrapped.observation_space, [observation],
                                  create_empty_array(wrapped.observation_space, n=1))
            if m2 is not None:
                request['annotation.human.action.task_description'] = [m2.policy_language]
            append_json(folder/'actual_requests.jsonl', {'index':result['policy_calls'],
                'scenario_id':cell['scenario_id'],'actual_policy_language':m2.policy_language,
                'trusted_task_spec_sha256':sha256(folder/'task_spec.json')})
            n = result['policy_calls']
            np.savez_compressed(folder / f'observation-{n:03d}.npz', **{
                k: v for k, v in request.items() if not k.startswith('annotation')})
            tick = time.perf_counter()
            result['policy_requests_attempted'] += 1
            actions, _ = client.get_action(request)
            latency_ms = (time.perf_counter()-tick)*1000
            result['policy_calls'] += 1
            if a.verify_reset and n == 0:
                first={k:np.array(v,copy=True) for k,v in actions.items()}
                second_ack=client.call_endpoint('reset_and_seed', {'scenario_id':cell['scenario_id'],'seed':cell['policy_seed']})
                result['policy_requests_attempted'] += 1
                actions,_=client.get_action(request)
                exact=set(first)==set(actions) and all(np.array_equal(first[k],actions[k]) for k in first)
                write_json(folder/'scenario_repeatability.json',{'same_observation_same_reset_seed_output_exact':exact,
                    'second_reset_ack':second_ack,'additional_model_calls':1,'scope':'E2_MODEL_CONTRACT_NOT_PHYSICAL_PAIRING'})
                if not exact:raise ValueError('same-reset same-observation action mismatch')
            keys = ['action.'+x for x in ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']]
            if set(actions) != set(keys):
                raise ValueError('unexpected action streams')
            for key in keys:
                arr = np.asarray(actions[key])
                if arr.shape != (1, contract.action_horizon, 1) or arr.dtype != np.float32 or not np.isfinite(arr).all():
                    raise ValueError('action shape/horizon/finite contract mismatch')
            np.savez_compressed(folder / f'action-{n:03d}.npz', **actions)
            # Copies protect raw policy chunks from upstream in-place gripper helpers.
            prefix = {key: np.array(actions[key][0], copy=True) for key in keys}
            before = len(converted_rows)
            from .execution_gate import execute_checked
            decision, execution = execute_checked(prefix, lambda checked:m2.check(n,checked), wrapped.step)
            append_json(folder/'gate_decisions.jsonl',{'index':n,'completed_controls_before':before,**decision,
                'completed_controls_after':len(converted_rows)})
            if decision['decision']!='ACCEPT':
                if len(converted_rows)!=before:raise RuntimeError('reject/error executed main controls')
                result.update(status='SEMANTIC_ABORT' if decision['decision']=='REJECT' else 'MONITOR_ERROR',
                              exit_code=0 if decision['decision']=='REJECT' else 1)
                return result['exit_code']
            observation, _, done, truncated, info = execution
            count = len(converted_rows)-before
            success = bool(np.any(info['success']))
            result['official_success'] = bool(result['official_success'] or success)
            append_json(folder / 'decisions.jsonl', dict(index=n, native_baseline=a.system=='B0',
                        inference_roundtrip_ms=latency_ms, inner_steps=count,
                        official_success=success, terminated=bool(done), truncated=bool(truncated)))
            # Audit the actual bottom-level controller input against one conversion.
            for i, actual in enumerate(converted_rows[before:]):
                expected = np.array([actions[key][0, i, 0] for key in keys])
                expected[-1] = -np.sign(2*expected[-1]-1)
                if not np.array_equal(actual, expected):
                    raise ValueError('native action/gripper transformation mismatch')
            if truncated:
                done = True
        result.update(status='SUCCESS' if result['official_success'] else 'TIME_LIMIT', exit_code=0)
        return 0
    except BaseException as exc:
        result.update(status='RUNTIME_ERROR', error_type=type(exc).__name__,
                      error_message=str(exc), exit_code=1)
        (folder / 'traceback.txt').write_text(traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        cleanup_resources(folder, result, [
            ('m2_shadow', m2.close if m2 is not None else None),
            ('video', video.release if video is not None else None),
            ('client', client.close if client is not None else None),
            ('native', native.close if native is not None else None)])
        if m2 is not None:
            result['first_wrong_lift_step']=m2.oracle.first_violation_step
        result.update(wall_seconds=time.perf_counter()-start, completed_at_sgt=now_sgt())
        write_json(folder / 'result.json', result)
        records = manifest(a.workspace, sorted(folder.glob('*')), a.run_id)
        write_json(folder / 'artifact_manifest.json', records)
        print(json.dumps(result, indent=2))
        return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
