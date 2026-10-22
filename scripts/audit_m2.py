"""Strict CPU re-audit of trusted, executor-created private M2 artifacts.

Pickles are only read from this task's own hash-verified evidence archive. Never
use this entry point on an untrusted attachment. No model or simulator is run.
"""
import argparse
from collections import Counter
import csv
from dataclasses import asdict
import json
from pathlib import Path
import pickle
import re
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require,check_observation,OBS_KEYS
from tase.evidence import verify_manifest,sha256,write_json
from tase.snapshot import digest
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.m2_context import compare_frames,jsonable

REPO=Path(__file__).resolve().parents[1]
KEYS=['action.'+s for s in ['x','y','z','roll','pitch','yaw','gripper']]


def read(path):return json.loads(path.read_text())
def lines(path):return [json.loads(s) for s in path.read_text().splitlines()]


def frame_arrays(frame):
    required={'step','eef_pos','eef_quat','gripper','objects','left_contacts','right_contacts',
              'official_success','oracle','control_input'}
    require(set(frame)==required,'incomplete physical frame')
    shapes={'eef_pos':(3,),'eef_quat':(4,),'gripper':(2,),'control_input':(7,)}
    for key,shape in shapes.items():
        frame[key]=np.asarray(frame[key])
        require(frame[key].shape==shape and np.isfinite(frame[key]).all(),'invalid physical stream '+key)
    for obj in frame['objects'].values():
        require(set(obj)=={'pos','quat'},'object pose schema mismatch')
        for key,shape in [('pos',(3,)),('quat',(4,))]:
            obj[key]=np.asarray(obj[key]);require(obj[key].shape==shape and np.isfinite(obj[key]).all(),'invalid object pose')
    require(all(type(v) is bool for k in ['left_contacts','right_contacts'] for v in frame[k].values()),'contact flags must be boolean')
    require(type(frame['official_success']) is bool,'success must be boolean')
    return frame


def audit(root,m1_root=None):
    cfg=read(REPO/'configs/m2_validation.json');cells=read(REPO/'configs/m2_dev_cells.json')['cells']
    validation_hash=sha256(REPO/'configs/m2_validation.json')
    folders={p.name:p for p in (root/'runs/episodes').iterdir() if p.is_dir()}
    require(set(folders)=={c['run_id'] for c in cells},'M2 acquisition set missing/duplicated/unplanned')
    sources={};snapshots={};events=[];source_rows=[];coverage=Counter()
    requests=lines(root/'runs/server-m2-01/inference.jsonl')
    require(bool(requests),'empty inference log')
    require([r['request'] for r in requests]==list(range(1,len(requests)+1)),'request sequence mismatch')
    request_offset=0
    for cell in cells:
        folder=folders[cell['run_id']];result=read(folder/'result.json');reservation=read(folder/'reservation.json')
        identity=read(folder/'m2_identity.json')
        require(identity['cell']==cell and identity['validation_sha256']==validation_hash,'cell/config identity mismatch')
        require(result['run_id']==reservation['run_id']==folder.name,'run ID mismatch')
        for key in ['task','init_index']:
            require(result[key]==reservation[key]==cell[key],'task/init mismatch')
        for key in ['repo_sha','config_hash','condition','m2_validation_hash']:
            require(result[key]==reservation[key],'reservation identity mismatch: '+key)
        require(result['m2_validation_hash']==validation_hash and result['condition']==cell['condition'],'changed runtime configuration')
        require(result['config_hash']==sha256(REPO/'configs/dev_baseline.json'),'baseline config changed')
        required={p.relative_to(root).as_posix() for p in folder.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
        verify_manifest(root,read(folder/'artifact_manifest.json'),required=required,source_run=folder.name)
        for name in ['physical_frames.jsonl','task_spec.json','horizon.json','reset_parity.json','m2_identity.json','control_trace.npz','decisions.jsonl','rollout.mp4']:
            require((folder/name).is_file(),'missing source artifact '+name)
        receipt=read(root/'runs'/f'{folder.name}.exit.json');started=read(root/'runs'/f'{folder.name}.exit.started.json')
        require(receipt['child_pid']==started['child_pid'] and receipt['child_returncode']==result['exit_code']==0,'source process exit mismatch')
        require(result['status'] in ['SUCCESS','TIME_LIMIT'] and type(result['official_success']) is bool,'incomplete source acquisition')
        require(result['official_success']==(result['status']=='SUCCESS'),'source outcome mismatch')
        require(result['settling_steps']==10 and 0<result['inner_steps']<=cfg['max_policy_steps'],'source control bounds')
        decisions=lines(folder/'decisions.jsonl');n=result['policy_calls']
        require(len(decisions)==n==result['policy_requests_attempted']>0,'source request count mismatch')
        require([d['index'] for d in decisions]==list(range(n)),'decision sequence missing or duplicated')
        require({p.name for p in folder.glob('action-*.npz')}=={f'action-{i:03d}.npz' for i in range(n)},'action file coverage')
        require({p.name for p in folder.glob('observation-*.npz')}=={f'observation-{i:03d}.npz' for i in range(n)},'observation file coverage')
        frames=[frame_arrays(f) for f in lines(folder/'physical_frames.jsonl')]
        require(len(frames)==result['inner_steps']==sum(d['inner_steps'] for d in decisions),'physical frame count mismatch')
        require([f['step'] for f in frames]==list(range(1,len(frames)+1)),'physical control sequence mismatch')
        spec=TaskSpec(**read(folder/'task_spec.json')).validate()
        require(spec.target==cell['task']+'_1' and identity['true_task_spec_target']==spec.target,'authorization target changed')
        require(identity['policy_language']=='pick up the '+cell['policy_target'].replace('_',' ')+' and place it in the basket','instruction binding mismatch')
        snap_records=lines(folder/'snapshots.jsonl')
        require(bool(snap_records),'no saved full-state anchor for oracle re-audit')
        for record in snap_records:
            snap_id=record['id'];index=record['decision']
            require(snap_id==folder.name+f'-d{index:03d}' and snap_id not in snapshots,'duplicate/invalid snapshot ID')
            with (folder/f'snapshot-{index:03d}.pkl').open('rb') as f:snapshot=pickle.load(f)
            require(sha256(folder/f'snapshot-{index:03d}.pkl')==record['file_sha256'],'snapshot bytes mismatch')
            require(digest(snapshot)==record['snapshot_hash'],'complete snapshot digest mismatch')
            require(snapshot['model_xml_sha256']==result['scene_xml_hash'],'snapshot model mismatch')
            require(snapshot['physics_spec']=='mjSTATE_INTEGRATION' and snapshot['physics'].ndim==1 and np.isfinite(snapshot['physics']).all(),'incomplete integration vector')
            require(snapshot['history']['prefix_progress']==0 and len(snapshot['history']['reward'])==record['source_steps'],'snapshot wrapper progress mismatch')
            require(snapshot['progress']['policy_control_steps']==record['source_steps']==sum(d['inner_steps'] for d in decisions[:index]),'snapshot boundary mismatch')
            require(set(snapshot['rng'])=={'numpy','python','torch_cpu'} and len(snapshot['rng']['torch_cpu'])>0,'missing snapshot RNG')
            for name in ['goal_pos','goal_ori','new_update','mass_matrix','J_full']:
                require(snapshot['field_inventory']['controller'][name]=='COPIED','controller cache omitted')
            snapshots[snap_id]=(record,snapshot,folder,index)
            coverage[record['phase']]+=1
        baseline=snapshots[snap_records[0]['id']][1]['oracle']['baseline_z']
        oracle=EventOracle(spec,{k:[0,0,z] for k,z in baseline.items()},cfg['oracle_lift_m'],cfg['oracle_sustain_control_steps'],cfg['oracle_relative_motion_tolerance_m'])
        by_step={s['source_steps']:snapshots[s['id']][1] for s in snap_records}
        for i,frame in enumerate(frames):
            require(set(frame['objects'])==set(spec.objects),'physical object set incomplete')
            require(set(frame['left_contacts'])==set(frame['right_contacts'])==set(spec.objects),'contact set incomplete')
            if i in by_step:require(digest(oracle.state())==digest(by_step[i]['oracle']),'oracle snapshot state mismatch')
            base={k:v for k,v in frame.items() if k not in ['oracle','control_input']}
            computed=oracle.consume(base)
            require(jsonable(computed)==frame['oracle'],'oracle output does not recompute')
        action_rows=[];offset=0
        for i,decision in enumerate(decisions):
            count=decision['inner_steps'];require(type(count) is int and 1<=count<=8,'invalid native prefix length')
            require(not decision['terminated'] or i==n-1,'source continued after termination')
            with np.load(folder/f'observation-{i:03d}.npz',allow_pickle=False) as obs:check_observation(obs)
            with np.load(folder/f'action-{i:03d}.npz',allow_pickle=False) as actions:
                require(len(actions.files)==len(KEYS) and set(actions.files)==set(KEYS),'action key mismatch')
                for key in KEYS:require(actions[key].shape==(1,16,1) and actions[key].dtype==np.float32 and np.isfinite(actions[key]).all(),'invalid native action chunk')
                values=np.stack([actions[k][0,:count,0] for k in KEYS],axis=1);values[:,-1]=-np.sign(2*values[:,-1]-1)
                require(np.array_equal(values,np.asarray([f['control_input'] for f in frames[offset:offset+count]])),'actual native/gripper action mismatch')
                action_rows.append(values)
            offset+=count
        with np.load(folder/'control_trace.npz',allow_pickle=False) as trace:
            require(set(trace.files)=={'states','converted_actions'} and len(trace['states'])==len(frames),'trace completeness')
            require(np.array_equal(trace['converted_actions'],np.concatenate(action_rows)),'control trace mismatch')
        require(decisions[-1]['terminated'] and bool(any(d['official_success'] for d in decisions))==result['official_success'],'official terminal mismatch')
        if result['status']=='TIME_LIMIT':require(len(frames)==cfg['max_policy_steps'],'time limit not reached')
        for name in spec.objects:
            start=0
            while start<len(frames):
                label=next(e['label'] for e in frames[start]['oracle']['events'] if e['object']==name)
                end=start+1
                while end<len(frames) and next(e['label'] for e in frames[end]['oracle']['events'] if e['object']==name)==label:end+=1
                if label!='NO_EVENT':events.append({'run_id':folder.name,'condition':cell['condition'],'object':name,'authorized_target':spec.target,
                    'label':label,'first_step':start+1,'last_step':end,'samples':end-start,'method':'STATE_CONTACT_RECOMPUTATION','independent_review':'NOT_VERIFIED_BY_REVIEWER'})
                start=end
        row={k:result[k] for k in ['run_id','task','condition','status','official_success','policy_calls','inner_steps','wall_seconds','repo_sha']}
        row['first_wrong_lift_step']=oracle.first_violation_step
        source_rows.append(row)
        sources[folder.name]={'frames':frames,'decisions':decisions,'spec':spec,'offset':request_offset,'folder':folder}
        request_offset+=n
    require(request_offset==len(requests),'extra/missing policy requests')
    expected_shapes={k:([1,1,256,256,3] if k.startswith('video') else [1,1,2 if k=='state.gripper' else 1]) for k in OBS_KEYS}
    for r in requests:
        require(r['status']=='PASS' and r['input_shapes']==expected_shapes,'invalid server request')
        require(r['output_shapes']=={k:[1,16,1] for k in KEYS},'server action contract')
    cases=[];repeat_counts=Counter();case_ordinals=[]
    rng_records=lines(root/'runs/server-m2-01/rng_checks.jsonl')
    case_folders=list((root/'runs/m2_shadow').iterdir())
    case_folders.sort(key=lambda p:read(p/'reservation.json')['budget_ordinal'])
    require(bool(case_folders) and len(case_folders)<=cfg['max_shadow_cases'],'shadow budget empty/exhausted')
    require(len(rng_records)==2*len(case_folders),'RNG endpoint receipt coverage')
    for case_index,folder in enumerate(case_folders):
        for name in ['reservation.json','prediction.pkl','noninterference.json','result.json']:require((folder/name).is_file(),'missing shadow evidence '+name)
        reservation=read(folder/'reservation.json');case_ordinals.append(reservation['budget_ordinal'])
        require(reservation['run_id']==folder.name and reservation['model_calls_permitted'] is False,'shadow identity/authority')
        snap_id=reservation['snapshot_id'];require(snap_id in snapshots,'missing source snapshot')
        record,snapshot,source_folder,index=snapshots[snap_id]
        source=sources[reservation['source_episode']]
        require(source_folder==source['folder'] and folder.name==snap_id+f"-r{reservation['repeat']}",'cross-episode shadow binding')
        with (folder/'prediction.pkl').open('rb') as f:prediction=pickle.load(f)
        require(prediction['status']=='PASS','failed prediction must be investigated/reported')
        start=record['source_steps'];actual=source['frames'][start:start+source['decisions'][index]['inner_steps']]
        predicted=[frame_arrays(f) for f in prediction['frames']]
        computed=compare_frames(predicted,actual,cfg)
        require(0<len(predicted)<=cfg['max_prefix_steps'],'shadow exceeded prefix budget')
        require(prediction['restored_snapshot_hash']==prediction['source_snapshot_hash']==record['snapshot_hash'],'roundtrip identity mismatch')
        require(prediction['terminated']==source['decisions'][index]['terminated'] and prediction['truncated']==source['decisions'][index]['truncated'],'termination mismatch')
        guard=read(folder/'noninterference.json')
        require(guard['main_complete_state_unchanged'] is True and guard['before_hash']==guard['after_hash']==record['snapshot_hash'],'main state changed')
        before=guard['policy_rng_before'];after=guard['policy_rng_after']
        for value in [before,after]:
            require(set(value)=={'policy_calls','cpu_rng_sha256','cuda_rng_sha256'},'incomplete RNG fingerprint')
            require(re.fullmatch('[0-9a-f]{64}',value['cpu_rng_sha256']) and len(value['cuda_rng_sha256'])==1 and all(re.fullmatch('[0-9a-f]{64}',s) for s in value['cuda_rng_sha256']),'invalid RNG digest')
        require(before==after==rng_records[2*case_index]==rng_records[2*case_index+1],'policy RNG changed or missing receipt')
        require(before['policy_calls']==source['offset']+index+1,'unexplained policy call during shadow')
        result=read(folder/'result.json')
        require(result['status']==computed['status'] and result['roundtrip_exact'] is True and result['termination_exact'] is True,'recorded comparison mismatch')
        for key in ['position_m','orientation_rad','gripper_m']:require(result[key]==computed[key],'numeric comparison mismatch')
        with np.load(source_folder/f'prefix-{index:03d}.npz',allow_pickle=False) as prefix, np.load(source_folder/f'action-{index:03d}.npz',allow_pickle=False) as actions:
            require(len(prefix.files)==len(KEYS) and set(prefix.files)==set(KEYS) and all(np.array_equal(prefix[k],actions[k][0]) for k in KEYS),'snapshot prefix changed')
        repeat_counts[snap_id]+=1
        cases.append({'case_id':folder.name,'snapshot_id':snap_id,'source_episode':source_folder.name,
            'phase':record['phase'],'repeat':reservation['repeat'],'status':computed['status'],
            **{k:computed[k] for k in ['position_m','orientation_rad','gripper_m']},
            'control_steps':len(actual),'early_success_boundary':len(actual)<8,
            'main_state_and_policy_rng_unchanged':True,'history_replay_steps':prediction['history_replay_steps'],
            'always_accept_category':reservation.get('always_accept_category')})
    require(case_ordinals==list(range(1,len(cases)+1)),'duplicate/missing shadow ordinal')
    require(set(repeat_counts)==set(snapshots) and all(v>=cfg['shadow_repeats'] for v in repeat_counts.values()),'snapshot repeat coverage')
    require(len(snapshots)>=20 and {r['task'] for r in source_rows}=={'alphabet_soup','cream_cheese','ketchup'},'snapshot/task coverage')
    require(set(coverage)>={'APPROACH_NO_CONTACT','CONTACT','LIFT_OR_TRANSPORT','BOUNDARY'},'missing phase stratum')
    budget=read(root/'runs/m2-runtime-budget.json')
    require(budget['new_dev']==len(cells)<=cfg['max_new_dev_episodes'] and budget['shadow_attempts']==len(cases) and budget['snapshots']==len(snapshots),'budget ledger mismatch')
    require(budget['total_dev']==budget['previous_dev']+len(cells)==cfg['max_total_dev_this_package'],'DEV budget mismatch')
    require(read(root/'runs/server-m2-01.exit.json')['child_returncode']==0,'model process did not exit normally')
    parity={'status':'NOT_CHECKED'}
    if m1_root is not None:
        old=m1_root/'runs/episodes/dev-policy-007';new=folders['dev-m2-013']
        with np.load(old/'control_trace.npz') as a,np.load(new/'control_trace.npz') as b:
            parity={'status':'CHECKED','steps_old':len(a['states']),'steps_new':len(b['states']),
                'raw_control_inputs_exact':np.array_equal(a['converted_actions'],b['converted_actions']),
                'full_native_states_exact':np.array_equal(a['states'],b['states'])}
    counts=Counter(e['label'] for e in events)
    return {'scope':'M2_DEV_ONLY; executor CPU re-audit of actual private raw',
        'runtime_sha':source_rows[0]['repo_sha'],'validation_sha256':validation_hash,
        'parent_sha':cfg['parent_sha'],'budget':budget,'remaining_reserved_dev':24-budget['total_dev'],
        'snapshots':len(snapshots),'snapshot_phase_counts':dict(coverage),'shadow_cases':len(cases),
        'shadow_control_steps':sum(c['control_steps'] for c in cases),'source_control_steps':sum(r['inner_steps'] for r in source_rows),
        'model_requests':len(requests),'policy_rng_checks':len(rng_records),'model_calls_from_shadow':0,
        'all_shadow_comparisons_pass':all(c['status']=='PASS' for c in cases),
        'max_position_error_m':max(c['position_m'] for c in cases),
        'max_orientation_error_rad':max(c['orientation_rad'] for c in cases),
        'max_finger_error_m':max(c['gripper_m'] for c in cases),
        'early_success_boundary_cases':sum(c['early_success_boundary'] for c in cases),
        'event_segment_counts':dict(counts),'sources':source_rows,'cases':cases,'event_segments':events,
        'm1_first_episode_vs_m2_always_accept':parity,
        'independent_private_review':'NOT_VERIFIED_BY_REVIEWER'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-runtime',type=Path,required=True);p.add_argument('--m1-runtime',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--csv-dir',type=Path,required=True)
    a=p.parse_args();data=audit(a.private_runtime,a.m1_runtime)
    write_json(a.output,data);a.csv_dir.mkdir(parents=True,exist_ok=True)
    for filename,key in [('snapshot_validation.csv','cases'),('event_cases.csv','event_segments'),('dev_runs.csv','sources')]:
        rows=data[key];require(bool(rows),'empty report table '+key)
        with (a.csv_dir/filename).open('x',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in data.items() if k not in ['sources','cases','event_segments']},indent=2))


if __name__=='__main__':main()
