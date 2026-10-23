"""SYNTHETIC validator evidence only: no model, renderer or physics."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from tase.evidence import manifest, sha256
from tase.audit_contract import OBS_KEYS, LANGUAGE

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('auditor', REPO/'scripts/summarize_baseline.py')
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value)+'\n', encoding='utf-8')


def seal(root, folder):
    files = [p for p in folder.iterdir() if p.name != 'artifact_manifest.json']
    write(folder/'artifact_manifest.json', manifest(root, files, folder.name))


def build(root):
    folder = root/'runs/episodes/synthetic-dev'
    folder.mkdir(parents=True)
    config = sha256(REPO/'configs/dev_baseline.json')
    record = dict(run_id=folder.name, task='alphabet_soup', init_index=0,
        status='SUCCESS', official_success=True, exit_code=0, policy_calls=1,
        policy_requests_attempted=1, inner_steps=1, settling_steps=10,
        wall_seconds=1.0, repo_sha='a'*40, config_hash=config, split='DEV',
        full_task_name='pick_up_the_alphabet_soup_and_place_it_in_the_basket',
        native_language='pick up the alphabet soup and place it in the basket')
    for name, key in [('benchmark_init.npy','init_hash'),('settled_state.npy','settled_state_hash'),('scene.xml','scene_xml_hash')]:
        if name.endswith('.npy'):np.save(folder/name,np.zeros(2),allow_pickle=False)
        else:(folder/name).write_text('SYNTHETIC_SCENE_NO_PHYSICS')
        record[key] = sha256(folder/name)
    for name in ['controller.json','observation_schema.json','object_catalog.json']:
        write(folder/name,{'fixture':'SYNTHETIC'})
    for name in ['rollout.mp4','video.image.png','video.wrist_image.png']:
        (folder/name).write_bytes(b'SYNTHETIC_PLACEHOLDER_NOT_MEDIA_EVIDENCE')
    write(folder/'result.json',record)
    write(folder/'reservation.json',dict(run_id=folder.name,repo_sha=record['repo_sha'],
        config_hash=config,task='alphabet_soup',init_index=0,split='DEV',probe_only=False,budget_ordinal=1))
    for name in ['synthetic-dev','server-03']:
        write(root/'runs'/f'{name}.exit.json',dict(exit_code=0,child_returncode=0,child_pid=1))
        write(root/'runs'/f'{name}.exit.started.json',dict(child_pid=1))
    horizon=dict(n_action_steps=8,action_horizon=16,video_delta_indices=[0],state_delta_indices=[0])
    write(folder/'horizon.json',horizon)
    write(folder/'reset_parity.json',dict(state_unchanged=True,history=horizon,
        latest_native_observation_equal={k:True for k in OBS_KEYS|{LANGUAGE}}))
    keys=['action.'+x for x in ['x','y','z','roll','pitch','yaw','gripper']]
    np.savez(folder/'action-000.npz',**{k:np.zeros((1,16,1),dtype=np.float32) for k in keys})
    obs={k:np.zeros((1,1,256,256,3),dtype=np.uint8) if k.startswith('video') else
         np.zeros((1,1,2 if k=='state.gripper' else 1),dtype=np.float32) for k in OBS_KEYS}
    np.savez(folder/'observation-000.npz',**obs)
    action=np.zeros((1,7),dtype=np.float32);action[0,-1]=1
    np.savez(folder/'control_trace.npz',states=np.zeros((1,2)),converted_actions=action)
    write(folder/'decisions.jsonl',dict(index=0,inner_steps=1,official_success=True,terminated=True,truncated=False))
    write(root/'runs/server-03/inference.jsonl',dict(request=1,status='PASS',inference_ms=1.0,
        peak_allocated_bytes=1,peak_reserved_bytes=2,
        input_shapes={k:list(v.shape) for k,v in obs.items()},output_shapes={k:[1,16,1] for k in keys}))
    seal(root,folder)
    return folder
