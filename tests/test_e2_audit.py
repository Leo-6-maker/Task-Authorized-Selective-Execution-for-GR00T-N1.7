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
from tase.gate_features import score_contacts,contact_view

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
    horizon={'n_action_steps':8,'action_horizon':16,'video_delta_indices':[0],'state_delta_indices':[0]}
    write(folder/'horizon.json',horizon)
    write(folder/'reset_parity.json',{'state_unchanged':True,'history':horizon,
        'latest_native_observation_equal':{key:True for key in list(OBS_KEYS)+['annotation.human.action.task_description']}})
    write(folder/'actual_requests.jsonl',{'index':0,'actual_policy_language':language,'trusted_task_spec_sha256':sha256(folder/'task_spec.json')})
    controls=[0.,0.,0.,0.,0.,0.,1.]
    frame={'step':1,'eef_pos':[0.,0.,0.],'eef_quat':[1.,0.,0.,0.],'gripper':[0.,0.],
        'objects':{n:{'pos':[0.,0.,0.],'quat':[1.,0.,0.,0.]} for n in spec.objects},
        'left_contacts':{n:False for n in spec.objects},'right_contacts':{n:False for n in spec.objects},'official_success':True}
    frame['oracle']=EventOracle(spec,base).consume(copy.deepcopy(frame));frame['control_input']=controls
    write(folder/'physical_frames.jsonl',frame)
    np.savez(folder/'control_trace.npz',states=np.zeros((1,2)),converted_actions=np.array([controls]))
    write(folder/'gate_decisions.jsonl',{'index':0,'decision':'ACCEPT','completed_controls_before':0,'completed_controls_after':1})
    write(folder/'decisions.jsonl',{'index':0,'inner_steps':1,'official_success':True,'terminated':True,'truncated':False,'native_baseline':True})
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


def gate_fixture(root,folder):
    for name in ['reservation.json','result.json']:
        path=folder/name;row=json.loads(path.read_text());row['system']='G';write(path,row)
    path=folder/'decisions.jsonl';row=json.loads(path.read_text());row['native_baseline']=False;write(path,row)
    spec=TaskSpec(**json.loads((folder/'task_spec.json').read_text()))
    frame=json.loads((folder/'physical_frames.jsonl').read_text());view=contact_view(frame,spec.objects)
    history={name:0 for name in spec.objects};snapshot_hash='2'*64
    path=folder/'snapshots.jsonl';row=json.loads(path.read_text());row['snapshot_hash']=snapshot_hash;write(path,row)
    write(folder/'prediction-000.json',{'status':'PASS','steps':1,'frames':[frame],
        'source_snapshot_hash':snapshot_hash,'restored_snapshot_hash':snapshot_hash,'terminated':True,'truncated':False})
    write(folder/'gate_contact_views.jsonl',{'index':0,'views':[view],'actual_contact_history':history,'trusted_target':spec.target})
    write(folder/'gate_decisions.jsonl',dict(score_contacts([view],list(spec.objects),spec.target,history,0,2),
        index=0,completed_controls_before=0,completed_controls_after=1))
    write(folder/'noninterference.jsonl',{'index':0,'before_hash':snapshot_hash,'after_hash':snapshot_hash,
        'main_state_unchanged':True,'policy_rng_unchanged':True,'policy_rng_before':{'policy_calls':1},
        'policy_rng_after':{'policy_calls':1},'model_calls_from_shadow':0})


class E2AuditTests(unittest.TestCase):
    def test_pinned_native_720_step_timeout_uses_done_not_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=build(root);result=json.loads((folder/'result.json').read_text())
            result.update(status='TIME_LIMIT',official_success=False,inner_steps=720,policy_calls=90,policy_requests_attempted=90);write(folder/'result.json',result)
            first=json.loads((folder/'physical_frames.jsonl').read_text());base={k:v for k,v in first.items() if k not in ['oracle','control_input']};base['official_success']=False
            spec=TaskSpec(**json.loads((folder/'task_spec.json').read_text()));oracle=EventOracle(spec,{name:[0.,0.,0.] for name in spec.objects})
            frames=[];gates=[];decisions=[];snapshots=[];requests=[]
            initial_request=json.loads((folder/'actual_requests.jsonl').read_text())
            with np.load(folder/'observation-000.npz',allow_pickle=False) as data:observation={k:np.array(data[k]) for k in data.files}
            for step in range(1,721):
                frame=copy.deepcopy(base);frame['step']=step;frame['oracle']=oracle.consume(copy.deepcopy(frame));frame['control_input']=first['control_input'];frames.append(frame)
            for index in range(90):
                np.savez(folder/f'action-{index:03d}.npz',**{'action.'+key:np.zeros((1,16,1),np.float32) for key in ['x','y','z','roll','pitch','yaw','gripper']})
                np.savez_compressed(folder/f'observation-{index:03d}.npz',**observation)
                path=folder/f'snapshot-{index:03d}.pkl';path.write_bytes(b'SYNTHETIC_NOT_PICKLE')
                snapshots.append({'decision':index,'completed_controls':index*8,'file_sha256':sha256(path)})
                gates.append({'index':index,'decision':'ACCEPT','completed_controls_before':index*8,'completed_controls_after':(index+1)*8})
                decisions.append({'index':index,'inner_steps':8,'native_baseline':True,'official_success':False,'terminated':index==89,'truncated':False})
                requests.append({**initial_request,'index':index})
            for name,rows in [('physical_frames.jsonl',frames),('gate_decisions.jsonl',gates),('decisions.jsonl',decisions),('snapshots.jsonl',snapshots),('actual_requests.jsonl',requests)]:
                (folder/name).write_text(''.join(json.dumps(row)+'\n' for row in rows))
            np.savez(folder/'control_trace.npz',states=np.zeros((720,2)),converted_actions=np.array([first['control_input']]*720))
            seal(root,folder);self.assertEqual(module.audit(root,REPO/'configs/e2_dev.json')['rows'][0]['status'],'TIME_LIMIT')
            decisions[-1]['terminated']=False;(folder/'decisions.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in decisions));seal(root,folder)
            with self.assertRaises(ValueError):module.audit(root,REPO/'configs/e2_dev.json')
    def test_missing_result_keeps_actual_process_exit_and_budget_slot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=build(root);(folder/'result.json').unlink();seal(root,folder)
            write(root/'runs/e2-dev-0001.exit.json',{'child_pid':123,'child_returncode':-15,'exit_code':143})
            report=module.audit(root,REPO/'configs/e2_dev.json');row=report['rows'][0]
            self.assertEqual(report['dev_used'],1);self.assertFalse(row['complete']);self.assertFalse(row['result_present'])
            self.assertEqual(row['exit_code'],143);self.assertEqual(row['child_returncode'],-15)
            self.assertTrue(report['all_process_receipts_complete']);self.assertFalse(report['all_attempt_results_present'])
    def test_gate_predictions_and_guards_bind_to_the_scored_evidence(self):
        for mutation in [None,'missing_guards','dishonest_guard','missing_prediction','forged_view','bad_accepted_rollout']:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);folder=build(root);gate_fixture(root,folder)
                if mutation=='missing_guards':(folder/'noninterference.jsonl').write_text('')
                if mutation=='dishonest_guard':
                    path=folder/'noninterference.jsonl';row=json.loads(path.read_text());row['policy_rng_after']['policy_calls']=2;write(path,row)
                if mutation=='missing_prediction':(folder/'prediction-000.json').unlink()
                if mutation=='forged_view':
                    path=folder/'gate_contact_views.jsonl';row=json.loads(path.read_text())
                    for side in ['left_contacts','right_contacts']:row['views'][0][side]['other']=True
                    write(path,row);path=folder/'gate_decisions.jsonl';row=json.loads(path.read_text());row['risk']=1;write(path,row)
                if mutation=='bad_accepted_rollout':
                    path=folder/'prediction-000.json';row=json.loads(path.read_text());row['frames'][0]['eef_pos'][0]=1;write(path,row)
                seal(root,folder)
                if mutation is None:module.audit(root,REPO/'configs/e2_dev.json')
                else:
                    with self.assertRaises((ValueError,KeyError,FileNotFoundError)):module.audit(root,REPO/'configs/e2_dev.json')
    def test_valid_safe_control_does_not_deserialize_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=build(root);seal(root,folder)
            result=module.audit(root,REPO/'configs/e2_dev.json')
            self.assertEqual(result['dev_used'],1)
            self.assertTrue(result['all_process_receipts_complete'])
    def test_rehashed_corruptions_are_rejected(self):
        for mutation in ['empty_gate','changed_action','changed_language','missing_snapshot','wrong_child','runtime_identity','reset_parity','horizon','native_decisions','early_timeout']:
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
                if mutation=='reset_parity':
                    p=folder/'reset_parity.json';row=json.loads(p.read_text());row['state_unchanged']=False;write(p,row)
                if mutation=='horizon':
                    p=folder/'horizon.json';row=json.loads(p.read_text());row['n_action_steps']=4;write(p,row)
                if mutation=='native_decisions':(folder/'decisions.jsonl').write_text('')
                if mutation=='early_timeout':
                    p=folder/'result.json';row=json.loads(p.read_text());row.update(status='TIME_LIMIT',official_success=False);write(p,row)
                seal(root,folder)
                with self.assertRaises((ValueError,KeyError,FileNotFoundError)):module.audit(root,REPO/'configs/e2_dev.json')
