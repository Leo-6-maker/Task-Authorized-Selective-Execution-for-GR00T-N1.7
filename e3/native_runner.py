"""Future grant-only E3 native runner. No native import before E3 admission."""
import argparse,json,os,subprocess,sys,time,traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from tase.evidence import append_json,now_sgt,sha256,write_json
from tase.e2_evidence import manifest
from tase.retention import cleanup_resources,traced_control_step
from e3.authorization import authorize,resource
from e3.ledger import claim,ROOTS
from e3.discovery import require

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['workspace','allocation-record']:p.add_argument('--'+n,type=Path,required=True)
    for n in ['run-id','review-commit','review-path']:p.add_argument('--'+n,required=True)
    p.add_argument('--port',type=int,default=5561)
    a=p.parse_args(argv);repo=Path.cwd();lock,cells,identity=authorize(repo,a.review_commit,a.review_path)
    resource(json.loads(a.allocation_record.read_text()),identity)
    cell=next((c for c in cells if c['run_id']==a.run_id),None);require(cell is not None,'unplanned E3 ID')
    a.task=cell['task'];a.init_index=cell['init_index'];a.system=cell['system'];a.condition=cell['condition'];a.verify_reset=False;a.probe_only=False
    a.config=repo/'configs/e3_run_config.proposed.json';config=json.loads(a.config.read_text());config['source_tasks']=json.loads((repo/'configs/e3_sources.proposed.json').read_text())['tasks'];split='TEST'
    folder=a.workspace/'runs'/ROOTS[cell['epoch']]/a.run_id;metadata=json.loads((folder/'reservation.json').read_text());require(metadata['cell']==cell and metadata['authorization']==identity,'E3 original reservation/code/grant changed')
    start_receipt=json.loads((folder/'supervisor_start.json').read_text());server=a.workspace/'runs'/start_receipt['server_session'];admission=json.loads((server/'test_admission.json').read_text());require(admission['authorization']==identity and admission['port']==a.port and admission['allocation_sha256']==sha256(a.allocation_record),'E3 child/server authorization differs')
    claim(folder,metadata);repo_sha=identity['authorized_head'];runtime_lock_hash=identity['runtime_lock_sha256'];extra={'authorization':identity,'planned_init_hash':cell['init_hash']}
    start = time.perf_counter()
    result = dict(run_id=a.run_id, task=a.task, init_index=a.init_index, split=split,
                  repo_sha=repo_sha, config_hash=sha256(a.config), runtime_lock_hash=runtime_lock_hash,
                  status='STARTED', official_success=False, policy_calls=0,
                  policy_requests_attempted=0,
                  inner_steps=0, settling_steps=0, exit_code=1,
                  started_at_sgt=now_sgt())
    result.update(**cell,**extra)
    if split=='TEST':result.update(epoch=cell['epoch'],protocol_id='E3-001-v1.0')
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
        task_index = suite.get_task_names().index('pick_up_the_'+a.task+'_and_place_it_in_the_basket')
        task = suite.get_task(task_index)
        bddl = Path(get_libero_path('bddl_files')) / task.problem_folder / task.bddl_file
        init_file = Path(get_libero_path('init_states')) / task.problem_folder / task.init_states_file
        from e3.scene import verify_files
        source=next(t for t in config['source_tasks'] if t['task']==cell['task'])
        verify_files(a.workspace/'upstream/Isaac-GR00T/external_dependencies/LIBERO',cell,source)
        # LIBERO's torch.load predates PyTorch 2.6's weights_only default. Keep
        # restricted loading and allow only the numpy types used by these pinned
        # initialization arrays, rather than enabling arbitrary pickle loading.
        safe_numpy = [np.core.multiarray._reconstruct, np.ndarray, np.dtype,
                      type(np.dtype('float64')), type(np.dtype('float32'))]
        with torch.serialization.safe_globals(safe_numpy):
            initial_states = torch.load(init_file, map_location='cpu', weights_only=True)
        selected_init = np.asarray(initial_states[a.init_index], dtype=np.float64)
        np.save(folder / 'benchmark_init.npy', selected_init, allow_pickle=False)
        if split in ['CALIB','TEST'] and sha256(folder/'benchmark_init.npy')!=extra['planned_init_hash']:
            raise ValueError('official initialization differs from committed split content')
        result.update(init_hash=sha256(folder / 'benchmark_init.npy'),
                      init_file_sha256=sha256(init_file), bddl_sha256=sha256(bddl),
                      full_task_name=task.name, native_language=task.language)
        if sha256(folder/'benchmark_init.npy')!=cell['init_hash']:raise ValueError('E3 actual heldout init bytes differ')
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
        if split=='TEST' and (contract.action_horizon!=16 or contract.n_action_steps!=8):
            raise ValueError('TEST native16/8 horizon changed')
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
        from e3.context import E3Context
        m2=E3Context(raw,wrapped,client,folder,cell,config)
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
        np.savez_compressed(folder/'control_trace.npz',states=np.empty((0,len(settled))),converted_actions=np.empty((0,7)))
        test_boundary = None
        if split=='TEST':
            from e3.boundary import Boundary as TestBoundary
            test_boundary=TestBoundary(a.system)
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
            returned=False
            try:
                actions, _ = client.get_action(request)
                returned=True
            finally:
                if split=='TEST':
                    append_json(folder/'inference_timing.jsonl',dict(index=n,
                        inference_roundtrip_ms=(time.perf_counter()-tick)*1000,
                        status='MODEL_RETURNED' if returned else 'REQUEST_ERROR',
                        scope='ALL_TEST_REQUESTS_INCLUDING_REJECTED_AND_FAILED_CANDIDATES'))
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
            from tase.execution_gate import execute_checked
            execute_candidate = test_boundary.execute if test_boundary is not None else execute_checked
            decision, execution = execute_candidate(prefix, lambda checked:m2.check(n,checked), wrapped.step)
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


if __name__=='__main__':sys.exit(main())
