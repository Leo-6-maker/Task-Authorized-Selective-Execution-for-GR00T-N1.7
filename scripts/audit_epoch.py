"""CPU audit of E2 JSON/NPZ/byte manifests; never loads pickle, policy or sim."""
import argparse
import copy
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require,check_observation,OBS_KEYS
from tase.evidence import sha256,write_json
from tase.e2_evidence import verify_manifest
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.m2_context import jsonable,compare_frames
from tase.gate_features import score_contacts,contact_view
from tase.execution_gate import KEYS


def read(path):return json.loads(path.read_text())
def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def audit(workspace,config, *, test_audit=False):
    cfg=read(config);require(cfg['run_epoch']=='E2' and cfg['protocol_id']=='TASE-002-v1.0','wrong epoch')
    split=cfg['split'];require(split in ['DEV','CALIB'] or (split=='TEST' and test_audit),'TEST audit requires independent TEST auditor')
    root=workspace/'runs'/split;folders=sorted(p for p in root.iterdir() if p.is_dir() and p.name!='.reservation-lock')
    require(len(folders)<=cfg['maximum_episode_attempts'],'budget exceeded')
    rows=[];ordinals=[]
    for folder in folders:
        reservation=read(folder/'reservation.json');ordinals.append(reservation['budget_ordinal'])
        result_file=folder/'result.json'
        if not result_file.exists():
            start_file=workspace/'runs'/f'{folder.name}.exit.started.json'
            exit_file=workspace/'runs'/f'{folder.name}.exit.json'
            process_complete=start_file.exists() and exit_file.exists()
            exit_receipt=read(exit_file) if exit_file.exists() else {}
            if process_complete:require(read(start_file)['child_pid']==exit_receipt['child_pid'],'partial process ID mismatch')
            rows.append({k:reservation.get(k) for k in ['run_id','task','init_index','condition','system','repo_sha','config_hash','runtime_lock_hash']}|
                {'status':'STARTED_OR_INTERRUPTED','slot_consumed':True,'complete':False,'result_present':False,
                 'process_receipts_complete':process_complete,'exit_code':exit_receipt.get('exit_code'),
                 'child_returncode':exit_receipt.get('child_returncode'),'official_success':None})
            continue
        result=read(result_file)
        for key in ['run_id','repo_sha','config_hash','runtime_lock_hash','epoch','protocol_id','task','init_index','condition','system','scenario_id','policy_seed','environment_seed']:
            require(result[key]==reservation[key],'reservation/result mismatch: '+key)
        require(result['config_hash']==sha256(config),'config changed')
        require(result['runtime_lock_hash']==sha256(config.parent/'runtime_lock_E2.json'),'runtime identity changed')
        gate_k=cfg['gate_k']
        if split=='CALIB':
            for key in ['splits_hash','calibration_plan_hash','planned_init_hash']:
                require(result[key]==reservation[key],'CALIB reservation mismatch: '+key)
            require(result['splits_hash']==sha256(config.parent/'e2_splits.json') and
                    result['calibration_plan_hash']==sha256(config.parent/'e2_calibration_plan.json'),'CALIB frozen identity differs')
            declared=read(config.parent/'e2_calib_cells.json')['planned_cells']
            bound=next(c for c in declared if c['run_id']==folder.name)
            require(all(result[key]==value for key,value in bound.items()),'CALIB cell differs')
            if result['system']=='G':
                selection=read(config.parent/'e2_calib_selection.json')
                require(result['calibration_selection_hash']==reservation['calibration_selection_hash']==sha256(config.parent/'e2_calib_selection.json'),'CALIB selected operating point differs')
                require(selection['status']=='SELECTED_WITHIN_PREDECLARED_RULE','invalid selection');gate_k=selection['selected_k']
                if result['status'] in ['SUCCESS','TIME_LIMIT','SEMANTIC_ABORT']:
                    worker=read(folder/'shadow_worker_exit.json')
                    require(type(worker['worker_pid']) is int and worker['worker_returncode']==0,'CALIB Gate worker failed exit')
        excluded={'artifact_manifest.json'}|({'supervisor_exit.json','reconciliation.json'} if split=='TEST' else set())
        names={p.relative_to(workspace).as_posix() for p in folder.iterdir() if p.is_file() and p.name not in excluded}
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
        snapshots=lines(folder/'snapshots.jsonl');guards=lines(folder/'noninterference.jsonl')
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
            horizon=read(folder/'horizon.json');parity=read(folder/'reset_parity.json')
            require(horizon=={'n_action_steps':cfg['execution_horizon_candidate'],'action_horizon':16,
                             'video_delta_indices':[0],'state_delta_indices':[0]},'native horizon changed')
            equality=parity['latest_native_observation_equal']
            require(parity['state_unchanged'] is True and parity['history']==horizon and
                    set(equality)==set(OBS_KEYS)|{'annotation.human.action.task_description'} and
                    all(value is True for value in equality.values()),'native reset parity failed')
            accepted=[g for g in gates if g['decision']=='ACCEPT'];decisions=lines(folder/'decisions.jsonl')
            require([d['index'] for d in decisions]==[g['index'] for g in accepted],'native decision coverage')
            for decision,gate in zip(decisions,accepted):
                require(decision['inner_steps']==gate['completed_controls_after']-gate['completed_controls_before'] and
                        decision['native_baseline']==(result['system']=='B0'),'native decision/control binding')
            if result['status']=='TIME_LIMIT':
                # Pinned MultiStepWrapper sets done=True at its own control cap;
                # it leaves the inner LIBERO truncated flag unchanged (False).
                require(result['inner_steps']==cfg['max_inner_steps'] and decisions[-1]['terminated'] is True,'time limit stopped early')
            if result['status']=='SUCCESS':
                require(decisions[-1]['terminated'] is True and decisions[-1]['official_success'] is True,'success not terminal')
            if result['status']=='SEMANTIC_ABORT':require(gates[-1]['decision']=='REJECT','semantic abort is not a reject')
            require([s['decision'] for s in snapshots]==list(range(result['policy_calls'])),'snapshot record coverage')
            if result['system']=='G':
                require([g['index'] for g in guards]==list(range(result['policy_calls'])),'missing Gate noninterference receipt')
                require({p.name for p in folder.glob('prediction-*.json')}=={f'prediction-{i:03d}.json' for i in range(result['policy_calls'])},'missing Gate prediction')
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
                prediction=read(prediction_file);snapshot=next(s for s in snapshots if s['decision']==index)
                if split=='TEST':
                    from tase.test_context import validate_prediction_envelope
                    validate_prediction_envelope(prediction,snapshot['snapshot_hash'],before)
                require(prediction['status']=='PASS' and 1<=prediction['steps']==len(prediction['frames'])<=8,'invalid prediction length/status')
                require(prediction['source_snapshot_hash']==prediction['restored_snapshot_hash']==snapshot['snapshot_hash'],'prediction snapshot binding')
                require(views['views']==[contact_view(frame,spec.objects) for frame in prediction['frames']],'Gate view differs from actual prediction')
                history={name:0 for name in spec.objects}
                for frame in frames[:before]:
                    for name in history:history[name]=history[name]+1 if frame['left_contacts'][name] and frame['right_contacts'][name] else 0
                require(views['actual_contact_history']==history and views['trusted_target']==spec.target,'Gate historical contacts/target changed')
                computed=score_contacts(views['views'],list(spec.objects),spec.target,views['actual_contact_history'],before,gate_k)
                require(all(gate[k]==v for k,v in computed.items()),'contact Gate decision differs')
                if gate['decision']=='ACCEPT':
                    numeric=lambda frame:{**frame,'gripper':np.asarray(frame['gripper'])}
                    comparison=compare_frames([numeric(f) for f in prediction['frames']],
                                              [numeric(f) for f in frames[before:after]],cfg)
                    require(comparison['status']=='PASS','accepted predicted/actual prefix differs')
        for path in folder.glob('observation-*.npz'):
            with np.load(path,allow_pickle=False) as observation:check_observation(observation)
        for snapshot in snapshots:
            require(sha256(folder/f"snapshot-{snapshot['decision']:03d}.pkl")==snapshot['file_sha256'],'snapshot byte identity mismatch')
        for guard in guards:
            require(guard['main_state_unchanged'] is True and guard['policy_rng_unchanged'] is True and guard['before_hash']==guard['after_hash'],'noninterference failure')
            require(guard['policy_rng_before']==guard['policy_rng_after'] and guard['model_calls_from_shadow']==0,'policy state/calls changed')
            require(guard['before_hash']==next(s for s in snapshots if s['decision']==guard['index'])['snapshot_hash'],'guard snapshot binding')
        if full:
            require(sum(g['completed_controls_after']-g['completed_controls_before'] for g in gates)==len(frames),'Gate/control coverage mismatch')
        rows.append({k:result.get(k) for k in ['run_id','task','init_index','condition','system','status','official_success','inner_steps','policy_calls','policy_requests_attempted','first_wrong_lift_step','exit_code','repo_sha','config_hash','runtime_lock_hash']}|{'slot_consumed':True,'complete':complete,'result_present':True,'process_receipts_complete':complete})
    require(sorted(ordinals)==list(range(1,len(folders)+1)),'reservation ordinals missing/duplicated')
    return {'epoch':'E2','protocol_id':'TASE-002-v1.0','scope':'JSON_NPZ_BYTE_AUDIT_NO_PICKLE_OR_SIM',
            split.lower()+'_used':len(folders),split.lower()+'_cap':cfg['maximum_episode_attempts'],'rows':rows,
            'all_process_receipts_complete':all(r['process_receipts_complete'] for r in rows),
            'all_attempt_results_present':all(r['result_present'] for r in rows),
            'independent_review':'NOT_PERFORMED_BY_THIS_EXECUTOR'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path('configs/e2_dev.json'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=audit(a.workspace,a.config);write_json(a.output,data);print(json.dumps(data,indent=2))
