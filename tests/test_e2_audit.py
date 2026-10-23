"""SYNTHETIC E2 safe-artifact audit; no simulation, pickle load or policy."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import asdict
import numpy as np
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.evidence import manifest,sha256
from tase.audit_contract import OBS_KEYS

REPO=Path(__file__).resolve().parents[1]
loader=importlib.util.spec_from_file_location('audit_epoch',REPO/'scripts/audit_epoch.py')
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)


def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value)+'\n')


def build(root):
    config=REPO/'configs/e2_dev.json';run='e2-dev-0001';folder=root/'runs/DEV'/run;folder.mkdir(parents=True)
    identity=dict(run_id=run,repo_sha='1'*40,config_hash=sha256(config),epoch='E2',protocol_id='TASE-002-v1.0',
        runtime_lock_hash=sha256(config.parent/'runtime_lock_E2.json'),task='alphabet_soup',init_index=0,condition='C0',system='B0',scenario_id='synthetic',policy_seed=1,environment_seed=2)
    write(folder/'reservation.json',dict(identity,budget_ordinal=1))
    write(folder/'result.json',dict(identity,status='SUCCESS',exit_code=0,inner_steps=1,settling_steps=10,
        official_success=True,policy_calls=1,policy_requests_attempted=1,first_wrong_lift_step=None))
    spec=TaskSpec('alphabet_soup_1','basket',{n:{'geoms':[i+1],'geom_names':[n+'_geom'],'body_id':i+1,'body_name':n+'_body'}
        for i,n in enumerate(['alphabet_soup_1','other','basket'])},[20],[21]).validate()
    write(folder/'task_spec.json',asdict(spec));base={n:[0.,0.,0.] for n in spec.objects}
    language='pick up the alphabet soup and place it in the basket'
    write(folder/'e2_identity.json',{'true_task_target':spec.target,'baseline_positions':base,'actual_policy_language':language})
    write(folder/'policy_reset.json',{'scenario_id':'synthetic','seed':1})
    for name in ['horizon.json','reset_parity.json']:write(folder/name,{'fixture':'SYNTHETIC'})
    write(folder/'actual_requests.jsonl',{'index':0,'actual_policy_language':language,'trusted_task_spec_sha256':sha256(folder/'task_spec.json')})
    controls=[0.,0.,0.,0.,0.,0.,1.]
    frame={'step':1,'eef_pos':[0.,0.,0.],'eef_quat':[1.,0.,0.,0.],'gripper':[0.,0.],
        'objects':{n:{'pos':[0.,0.,0.],'quat':[1.,0.,0.,0.]} for n in spec.objects},
        'left_contacts':{n:False for n in spec.objects},'right_contacts':{n:False for n in spec.objects},'official_success':True}
    frame['oracle']=EventOracle(spec,base).consume(copy.deepcopy(frame));frame['control_input']=controls
    write(folder/'physical_frames.jsonl',frame)
    np.savez(folder/'control_trace.npz',states=np.zeros((1,2)),converted_actions=np.array([controls]))
    write(folder/'gate_decisions.jsonl',{'index':0,'decision':'ACCEPT','completed_controls_before':0,'completed_controls_after':1})
    np.savez(folder/'action-000.npz',**{'action.'+k:np.zeros((1,16,1),np.float32) for k in ['x','y','z','roll','pitch','yaw','gripper']})
    observation={k:np.zeros((1,1,256,256,3),np.uint8) if k.startswith('video') else np.zeros((1,1,2 if k=='state.gripper' else 1),np.float32) for k in OBS_KEYS}
    np.savez(folder/'observation-000.npz',**observation)
    (folder/'snapshot-000.pkl').write_bytes(b'SYNTHETIC_NOT_A_PICKLE_MUST_NOT_DESERIALIZE')
    write(folder/'snapshots.jsonl',{'decision':0,'completed_controls':0,'file_sha256':sha256(folder/'snapshot-000.pkl')})
    (folder/'rollout.mp4').write_bytes(b'SYNTHETIC_NO_VIDEO_VALIDATION_CLAIM')
    write(root/'runs'/f'{run}.exit.json',{'child_pid':123,'child_returncode':0,'exit_code':0})
    write(root/'runs'/f'{run}.exit.started.json',{'child_pid':123})
    return folder


def seal(root,folder):
    write(folder/'artifact_manifest.json',manifest(root,[p for p in folder.iterdir() if p.name!='artifact_manifest.json'],folder.name))


class E2AuditTests(unittest.TestCase):
    def test_valid_safe_control_does_not_deserialize_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=build(root);seal(root,folder)
            result=module.audit(root,REPO/'configs/e2_dev.json')
            self.assertEqual(result['dev_used'],1)
            self.assertTrue(result['all_process_receipts_complete'])
    def test_rehashed_corruptions_are_rejected(self):
        for mutation in ['empty_gate','changed_action','changed_language','missing_snapshot','wrong_child','runtime_identity']:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);folder=build(root)
                if mutation=='empty_gate':(folder/'gate_decisions.jsonl').write_text('')
                if mutation=='changed_action':
                    with np.load(folder/'action-000.npz') as f:actions=dict(f)
                    actions['action.x'][0,0,0]=1;np.savez(folder/'action-000.npz',**actions)
                if mutation=='changed_language':
                    p=folder/'actual_requests.jsonl';row=json.loads(p.read_text());row['actual_policy_language']='wrong';write(p,row)
                if mutation=='missing_snapshot':(folder/'snapshot-000.pkl').unlink()
                if mutation=='wrong_child':write(root/'runs/e2-dev-0001.exit.json',{'child_pid':999,'exit_code':0})
                if mutation=='runtime_identity':
                    for name in ['reservation.json','result.json']:
                        p=folder/name;row=json.loads(p.read_text());row['runtime_lock_hash']='0'*64;write(p,row)
                seal(root,folder)
                with self.assertRaises((ValueError,KeyError,FileNotFoundError)):module.audit(root,REPO/'configs/e2_dev.json')
