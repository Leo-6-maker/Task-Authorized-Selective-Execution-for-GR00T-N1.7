"""CPU audit of E2 JSON/NPZ/byte manifests; never loads pickle, policy or sim."""
import argparse
import copy
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require,check_observation
from tase.evidence import verify_manifest,sha256,write_json
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.m2_context import jsonable
from tase.gate_features import score_contacts
from tase.execution_gate import KEYS


def read(path):return json.loads(path.read_text())
def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def audit(workspace,config):
    cfg=read(config);require(cfg['run_epoch']=='E2' and cfg['protocol_id']=='TASE-002-v1.0','wrong epoch')
    root=workspace/'runs/DEV';folders=sorted(p for p in root.iterdir() if p.is_dir() and p.name!='.reservation-lock')
    require(len(folders)<=cfg['maximum_episode_attempts'],'budget exceeded')
    rows=[];ordinals=[]
    for folder in folders:
        reservation=read(folder/'reservation.json');ordinals.append(reservation['budget_ordinal'])
        result_file=folder/'result.json'
        if not result_file.exists():
            rows.append({'run_id':folder.name,'status':'STARTED_OR_INTERRUPTED','slot_consumed':True,'complete':False});continue
        result=read(result_file)
        for key in ['run_id','repo_sha','config_hash','runtime_lock_hash','epoch','protocol_id','task','init_index','condition','system','scenario_id','policy_seed','environment_seed']:
            require(result[key]==reservation[key],'reservation/result mismatch: '+key)
        require(result['config_hash']==sha256(config),'config changed')
        require(result['runtime_lock_hash']==sha256(config.parent/'runtime_lock_E2.json'),'runtime identity changed')
        names={p.relative_to(workspace).as_posix() for p in folder.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
        verify_manifest(workspace,read(folder/'artifact_manifest.json'),required=names,source_run=folder.name)
        exit_file=workspace/'runs'/f'{folder.name}.exit.json'
        start_file=workspace/'runs'/f'{folder.name}.exit.started.json'
        complete=exit_file.exists() and start_file.exists()
        if complete:
            exit_receipt=read(exit_file);start_receipt=read(start_file)
            require(exit_receipt['child_pid']==start_receipt['child_pid'],'process ID mismatch')
            require(exit_receipt['exit_code']==result['exit_code'],'child exit mismatch')
        frames=lines(folder/'physical_frames.jsonl');gates=lines(folder/'gate_decisions.jsonl')
        require(len(frames)==result['inner_steps'],'physical frame count mismatch')
        require([f['step'] for f in frames]==list(range(1,len(frames)+1)),'physical frame sequence')
        full=result['status'] in ['SUCCESS','TIME_LIMIT','SEMANTIC_ABORT']
        if full:
            require(complete and result['exit_code']==0,'full outcome missing normal child exit')
            require(result['settling_steps']==cfg['settling_steps'],'full outcome incomplete settling')
            require([g['index'] for g in gates]==list(range(result['policy_calls'])),'missing or duplicate gate decisions')
            require(set(p.name for p in folder.glob('action-*.npz'))=={f'action-{i:03d}.npz' for i in range(result['policy_calls'])},'action coverage incomplete')
            require(set(p.name for p in folder.glob('observation-*.npz'))=={f'observation-{i:03d}.npz' for i in range(result['policy_calls'])},'observation coverage incomplete')
            require(set(p.name for p in folder.glob('snapshot-*.pkl'))=={f'snapshot-{i:03d}.pkl' for i in range(result['policy_calls'])},'snapshot coverage incomplete')
            require(type(result['official_success']) is bool and result['official_success']==(result['status']=='SUCCESS'),'success/status mismatch')
            require(result['inner_steps']<=cfg['max_inner_steps'],'policy control cap exceeded')
            for name in ['e2_identity.json','task_spec.json','policy_reset.json','horizon.json','reset_parity.json','actual_requests.jsonl','snapshots.jsonl','rollout.mp4']:
                require((folder/name).is_file(),'full outcome required evidence missing: '+name)
        if (folder/'task_spec.json').exists():
            spec=TaskSpec(**read(folder/'task_spec.json')).validate();identity=read(folder/'e2_identity.json')
            require(spec.target==result['task']+'_1'==identity['true_task_target'],'trusted target changed')
            policy_target=cfg['c2_policy_targets'][result['task']] if result['condition']=='C2' else result['task']
            require(identity['actual_policy_language']=='pick up the '+policy_target.replace('_',' ')+' and place it in the basket','condition/instruction binding mismatch')
            oracle=EventOracle(spec,identity['baseline_positions'],cfg['oracle_lift_m'],cfg['oracle_sustain_control_steps'],cfg['oracle_relative_motion_tolerance_m'])
            for frame in frames:
                computed=oracle.consume({k:v for k,v in frame.items() if k not in ['oracle','control_input']})
                require(jsonable(computed)==frame['oracle'],'oracle valid-frame labels changed')
            require(oracle.first_violation_step==result.get('first_wrong_lift_step'),'first violation mismatch')
            requests=lines(folder/'actual_requests.jsonl')
            require(len(requests)>=result['policy_calls'],'request coverage missing')
            require(all(r['actual_policy_language']==identity['actual_policy_language'] and r['trusted_task_spec_sha256']==sha256(folder/'task_spec.json') for r in requests),'actual request binding differs')
            require([r['index'] for r in requests]==list(range(len(requests))),'request sequence')
            reset=read(folder/'policy_reset.json')
            require(reset['scenario_id']==result['scenario_id'] and reset['seed']==result['policy_seed'],'reset binding mismatch')
        if result['inner_steps']:
            with np.load(folder/'control_trace.npz',allow_pickle=False) as trace:
                require(set(trace.files)=={'states','converted_actions'},'trace schema mismatch')
                controls=trace['converted_actions']
                require(len(trace['states'])==len(controls)==len(frames),'trace length mismatch')
                require(np.isfinite(trace['states']).all() and np.isfinite(controls).all(),'nonfinite trace')
                require(np.array_equal(controls,np.asarray([f['control_input'] for f in frames])),'frame/control trace differs')
        for gate in gates:
            index=gate['index'];before=gate['completed_controls_before'];after=gate['completed_controls_after']
            require(after>=before and after-before<=8,'gate prefix step count')
            if gate['decision'] in ['REJECT','ERROR']:
                require(before==after==result['inner_steps'],'reject/error main execution not zero')
            if gate['decision']=='ACCEPT':
                with np.load(folder/f'action-{index:03d}.npz',allow_pickle=False) as chunk:
                    require(set(chunk.files)==set(KEYS),'action coverage')
                    for offset,frame in enumerate(frames[before:after]):
                        expected=np.array([chunk[k][0,offset,0] for k in KEYS]);expected[-1]=-np.sign(2*expected[-1]-1)
                        require(np.array_equal(expected,frame['control_input']),'accepted candidate/controller mismatch')
            prediction_file=folder/f'prediction-{index:03d}.json'
            if result['system']=='G' and prediction_file.exists() and gate['decision']!='ERROR':
                views=next(r for r in lines(folder/'gate_contact_views.jsonl') if r['index']==index)
                computed=score_contacts(views['views'],list(spec.objects),spec.target,views['actual_contact_history'],before,cfg['gate_k'])
                require(all(gate[k]==v for k,v in computed.items()),'contact Gate decision differs')
        for path in folder.glob('observation-*.npz'):
            with np.load(path,allow_pickle=False) as observation:check_observation(observation)
        for snapshot in lines(folder/'snapshots.jsonl'):
            require(sha256(folder/f"snapshot-{snapshot['decision']:03d}.pkl")==snapshot['file_sha256'],'snapshot byte identity mismatch')
        for guard in lines(folder/'noninterference.jsonl'):
            require(guard['main_state_unchanged'] is True and guard['policy_rng_unchanged'] is True and guard['before_hash']==guard['after_hash'],'noninterference failure')
        if full:
            require(sum(g['completed_controls_after']-g['completed_controls_before'] for g in gates)==len(frames),'Gate/control coverage mismatch')
        rows.append({k:result.get(k) for k in ['run_id','task','init_index','condition','system','status','official_success','inner_steps','policy_calls','policy_requests_attempted','first_wrong_lift_step','exit_code']}|{'slot_consumed':True,'complete':complete})
    require(sorted(ordinals)==list(range(1,len(folders)+1)),'reservation ordinals missing/duplicated')
    return {'epoch':'E2','protocol_id':'TASE-002-v1.0','scope':'JSON_NPZ_BYTE_AUDIT_NO_PICKLE_OR_SIM',
            'dev_used':len(folders),'dev_cap':cfg['maximum_episode_attempts'],'rows':rows,
            'all_process_receipts_complete':all(r['complete'] for r in rows),
            'independent_review':'NOT_PERFORMED_BY_THIS_EXECUTOR'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path('configs/e2_dev.json'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=audit(a.workspace,a.config);write_json(a.output,data);print(json.dumps(data,indent=2))
