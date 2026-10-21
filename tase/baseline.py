"""Single-environment DEV runner using the official native policy/wrappers.

No gate, shadow, training, recovery, perturbation, or TEST access is implemented.
Fixed initialization is an explicit reset adapter; native observation/action
conversion, MultiStepWrapper history and control remain upstream code.
"""
import argparse
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path
from .evidence import append_json, manifest, now_sgt, reserve_episode, sha256, write_json

TASKS = {name: f'pick_up_the_{name}_and_place_it_in_the_basket'
         for name in ['alphabet_soup', 'cream_cheese', 'ketchup']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--task', choices=TASKS, required=True)
    p.add_argument('--init-index', type=int, choices=[0, 1], required=True)
    p.add_argument('--config', type=Path, default=Path('configs/dev_baseline.json'))
    p.add_argument('--allocation-record', type=Path, required=True)
    p.add_argument('--probe-only', action='store_true')
    p.add_argument('--port', type=int, default=5558)
    a = p.parse_args()
    config = json.loads(a.config.read_text())
    if config['split'] != 'DEV' or config['condition'] != 'C0':
        raise ValueError('M1 permits only native C0 DEV in this runner')
    if not json.loads(a.allocation_record.read_text()).get('shared_gpu_inference_authorized'):
        raise ValueError('GPU usage not authorized')
    repo_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
    if dirty:
        raise ValueError('commit implementation before runtime; dirty worktree refused')
    folder = reserve_episode(a.workspace / 'runs/episodes', a.run_id, {
        'split': 'DEV', 'task': a.task, 'init_index': a.init_index,
        'repo_sha': repo_sha, 'config_hash': sha256(a.config),
        'probe_only': a.probe_only, 'started_at_sgt': now_sgt()})
    start = time.perf_counter()
    result = dict(run_id=a.run_id, task=a.task, init_index=a.init_index, split='DEV',
                  repo_sha=repo_sha, config_hash=sha256(a.config),
                  status='STARTED', official_success=None, policy_calls=0,
                  inner_steps=0, settling_steps=0, exit_code=1,
                  started_at_sgt=now_sgt())
    native = wrapped = client = video = None
    try:
        import numpy as np
        import cv2
        import gymnasium as gym
        import torch
        from PIL import Image
        from libero.libero import benchmark, get_libero_path
        from gr00t.eval.sim.LIBERO.libero_env import LiberoEnv
        from gr00t.eval._horizon_contract import PolicyHorizonSpec
        from gr00t.eval.sim.wrapper.multistep_wrapper import MultiStepWrapper
        from gr00t.policy.server_client import PolicyClient
        np.random.seed(config['environment_seed'])
        suite = benchmark.get_benchmark_dict()['libero_object']()
        task_index = suite.get_task_names().index(TASKS[a.task])
        task = suite.get_task(task_index)
        bddl = Path(get_libero_path('bddl_files')) / task.problem_folder / task.bddl_file
        init_file = Path(get_libero_path('init_states')) / task.problem_folder / task.init_states_file
        # Only the two declared DEV indices are executed. No model selection by seed.
        initial_states = suite.get_task_init_states(task_index)
        selected_init = np.asarray(initial_states[a.init_index], dtype=np.float64)
        np.save(folder / 'benchmark_init.npy', selected_init, allow_pickle=False)
        result.update(init_hash=sha256(folder / 'benchmark_init.npy'),
                      init_file_sha256=sha256(init_file), bddl_sha256=sha256(bddl),
                      full_task_name=task.name, native_language=task.language)
        native = LiberoEnv(task_bddl_file=str(bddl), task_description=task.language)
        raw = native._env
        native.reset(seed=config['environment_seed'])
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
        client.reset()
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
        video = cv2.VideoWriter(str(folder / 'rollout.mp4'), cv2.VideoWriter_fourcc(*'mp4v'),
                                20.0, (512, 256))
        if not video.isOpened():
            raise RuntimeError('video writer unavailable')
        state_rows, converted_rows = [], []
        original_step = raw.step

        def traced_step(action):
            converted = np.array(action, copy=True)
            value = original_step(action)
            state_rows.append(np.array(raw.get_sim_state(), copy=True))
            converted_rows.append(converted)
            frame = np.concatenate([value[0]['agentview_image'][::-1, ::-1],
                                    value[0]['robot0_eye_in_hand_image'][::-1, ::-1]], axis=1)
            video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            return value

        raw.step = traced_step
        done = False
        while not done:
            request = {k: (np.asarray(v)[None] if not k.startswith('annotation') else [v])
                       for k, v in observation.items()}
            n = result['policy_calls']
            np.savez_compressed(folder / f'observation-{n:03d}.npz', **{
                k: v for k, v in request.items() if not k.startswith('annotation')})
            tick = time.perf_counter()
            actions, _ = client.get_action(request)
            latency_ms = (time.perf_counter()-tick)*1000
            result['policy_calls'] += 1
            keys = ['action.'+x for x in ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']]
            if set(actions) != set(keys):
                raise ValueError('unexpected action streams')
            for key in keys:
                arr = np.asarray(actions[key])
                if arr.shape != (1, contract.action_horizon, 1) or not np.isfinite(arr).all():
                    raise ValueError('action shape/horizon/finite contract mismatch')
            np.savez_compressed(folder / f'action-{n:03d}.npz', **actions)
            # Copies protect raw policy chunks from upstream in-place gripper helpers.
            prefix = {key: np.array(actions[key][0], copy=True) for key in keys}
            before = len(converted_rows)
            observation, _, done, truncated, info = wrapped.step(prefix)
            count = len(converted_rows)-before
            success = bool(np.any(info['success']))
            result['inner_steps'] += count
            result['official_success'] = bool(result['official_success'] or success)
            append_json(folder / 'decisions.jsonl', dict(index=n, native_baseline=True,
                        inference_roundtrip_ms=latency_ms, inner_steps=count,
                        official_success=success, terminated=bool(done), truncated=bool(truncated)))
            # Audit the actual bottom-level controller input against one conversion.
            for i, actual in enumerate(converted_rows[before:]):
                expected = np.array([actions[key][0, i, 0] for key in keys])
                expected[-1] = -np.sign(2*expected[-1]-1)
                if not np.array_equal(actual, expected):
                    raise ValueError('native action/gripper transformation mismatch')
            np.savez_compressed(folder / 'control_trace.npz',
                                states=np.asarray(state_rows), converted_actions=np.asarray(converted_rows))
            if truncated:
                done = True
        result.update(status='SUCCESS' if result['official_success'] else 'TIME_LIMIT', exit_code=0)
        return 0
    except Exception as exc:
        result.update(status='RUNTIME_ERROR', error_type=type(exc).__name__,
                      error_message=str(exc), exit_code=1)
        (folder / 'traceback.txt').write_text(traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        if video is not None:
            video.release()
        if client is not None:
            client.close()
        if native is not None:
            try:
                native.close()
            except Exception:
                (folder / 'close_error.txt').write_text(traceback.format_exc())
        result.update(wall_seconds=time.perf_counter()-start, completed_at_sgt=now_sgt())
        write_json(folder / 'result.json', result)
        records = manifest(a.workspace, sorted(folder.glob('*')), a.run_id)
        write_json(folder / 'artifact_manifest.json', records)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    sys.exit(main())
