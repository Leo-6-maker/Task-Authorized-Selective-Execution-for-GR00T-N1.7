"""R003 bounded saved-action DEV diagnostic. No policy imports or requests.

Only use the task's trusted hash-bound original snapshot, never attachments.
Every shadow attempt is reserved in the original shared 80-case ledger.
An error stops the diagnostic; outputs and reservations remain append-only.
"""
import argparse
import copy
import json
import pickle
import subprocess
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require
from tase.evidence import sha256,write_json,append_json,reserve_episode,manifest,verify_manifest
from tase.snapshot import capture,restore,digest
from tase.m2_context import compare_frames,jsonable
from tase.m2_native import make_clone,sample
from tase.shadow import Shadow
from audit_m2 import frame_arrays,KEYS,read,lines


def prefix(source,index):
    with np.load(source/f'action-{index:03d}.npz',allow_pickle=False) as data:
        require(set(data.files)==set(KEYS),'saved action keys')
        require(all(data[k].shape==(1,16,1) and data[k].dtype==np.float32 and np.isfinite(data[k]).all() for k in KEYS),'saved action contract')
        return {k:np.array(data[k][0],copy=True) for k in KEYS}


def run(workspace,folder,cfg):
    source=workspace/'runs/episodes'/cfg['source_episode']
    required={p.relative_to(workspace).as_posix() for p in source.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
    verify_manifest(workspace,read(source/'artifact_manifest.json'),required=required,source_run=source.name)
    oldcases=list((workspace/'runs/m2_shadow').iterdir())
    require(len(oldcases)==cfg['prior_shadow_attempts'],'unexpected ledger; no retry or budget reset')
    require(len(list((workspace/'runs/episodes').iterdir()))==cfg['dev_used'],'DEV ledger changed')
    require(read(workspace/'runs/server-m2-01.exit.json')['child_returncode']==0,'prior model not closed')
    server_files={str(p.relative_to(workspace)):sha256(p) for p in (workspace/'runs/server-m2-01').iterdir() if p.is_file()}
    anchor=next(x for x in lines(source/'snapshots.jsonl') if x['decision']==cfg['anchor_decision'])
    path=source/f"snapshot-{cfg['anchor_decision']:03d}.pkl"
    require(sha256(path)==anchor['file_sha256'],'anchor hash mismatch')
    with path.open('rb') as f:snapshot=pickle.load(f)
    require(digest(snapshot)==anchor['snapshot_hash'] and snapshot['progress']['policy_control_steps']==cfg['anchor_control_steps'],'anchor content mismatch')
    original=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
    decisions=lines(source/'decisions.jsonl');validation=read(Path('configs/m2_validation.json'))
    trace=np.load(source/'control_trace.npz',allow_pickle=False)
    native=shadow=None;progress={};frames=[];reconstructed={};case_rows=[];replay_rows=[]
    result={'status':'STARTED','scope':cfg['scope'],'new_model_calls':0,'new_autonomous_episodes':0,
        'history_replay_control_steps':0,'prediction_control_steps':0,'shadow_attempts':0,
        'source_anchor_sha256':sha256(path),'source_anchor_digest':digest(snapshot),
        'first_wrong_lift_step':None,'independent_raw_review':'NOT_VERIFIED_BY_REVIEWER'}
    try:
        native,raw,wrapped,spec,oracle=make_clone('cream_cheese',0,read(source/'horizon.json'))
        require(asdict(spec)==read(source/'task_spec.json'),'TaskSpec binding mismatch')
        import os,xml.etree.ElementTree as ET
        from OpenGL import GL
        query=ET.fromstring(subprocess.check_output(['nvidia-smi','-q','-x'],text=True))
        binding=[i for i,g in enumerate(query.findall('gpu')) if any(p.findtext('pid')==str(os.getpid()) for p in g.findall('./processes/process_info'))]
        require(binding==[int(os.environ['MUJOCO_EGL_DEVICE_ID'])],'reference EGL GPU binding')
        write_json(folder/'reference_setup.json',{'environment_instances':1,'explicit_native_resets':1,'settling_steps':10,
            'constructor_internal_initialization':True,'egl_gpu_indices':binding,'gl_renderer':GL.glGetString(GL.GL_RENDERER).decode()})
        progress=restore(raw,wrapped,oracle,snapshot)
        require(digest(capture(raw,wrapped,oracle,progress))==digest(snapshot),'anchor full roundtrip mismatch')
        require(np.array_equal(raw.get_sim_state(),trace['states'][71]),'anchor native state differs')
        native_step=raw.step
        def traced(action):
            value=native_step(action)
            progress['policy_control_steps']+=1
            frame=sample(raw,spec,progress['policy_control_steps'])
            frame['oracle']=oracle.consume(frame);frame['control_input']=np.array(action,copy=True)
            frames.append(frame)
            append_json(folder/'replay_frames.jsonl',jsonable(frame))
            state=np.asarray(raw.get_sim_state())
            append_json(folder/'replay_states.jsonl',{'step':frame['step'],'native_state':state.tolist(),
                'exact_original_state':bool(np.array_equal(state,trace['states'][frame['step']-1]))})
            result['history_replay_control_steps']+=1
            require(np.array_equal(state,trace['states'][frame['step']-1]),'history native state differs')
            return value
        raw.step=traced
        for index in range(9,13):
            boundary=index*8
            require(progress['policy_control_steps']==boundary,'reconstructed decision boundary')
            if index in cfg['boundary_decisions']:
                reconstructed[index]=capture(raw,wrapped,oracle,progress)
                with (folder/f'reconstructed-d{index:03d}.pkl').open('xb') as f:pickle.dump(reconstructed[index],f,protocol=5)
                write_json(folder/f'reconstructed-d{index:03d}.json',{'scope':cfg['scope'],'source_anchor':'d009',
                    'completed_controls':boundary,'snapshot_digest':digest(reconstructed[index]),
                    'historical_replay_steps_from_anchor':boundary-72})
                for repeat in range(cfg['repeats_per_boundary']):
                    case_id=f'r003-dev-m2-017-d{index:03d}-r{repeat}'
                    case=reserve_episode(workspace/'runs/m2_shadow',case_id,{'split':'DEV','scope':cfg['scope'],
                        'source_episode':source.name,'source_anchor':'d009','boundary_decision':index,'repeat':repeat,
                        'model_calls_permitted':False,'supplement_config_sha256':sha256('configs/m2_supplement_r003.json')},limit=cfg['max_total_shadow_attempts'])
                    result['shadow_attempts']+=1
                    before=digest(capture(raw,wrapped,oracle,progress))
                    prediction=None;case_result={'status':'STARTED','completed_prediction_steps':0}
                    try:
                        if shadow is None:
                            shadow=Shadow('cream_cheese',0,read(source/'horizon.json'))
                            write_json(folder/'shadow_setup.json',shadow.setup)
                        prediction=shadow.predict(reconstructed[index],prefix(source,index))
                        with (case/'prediction.pkl').open('xb') as f:pickle.dump(prediction,f,protocol=5)
                        result['prediction_control_steps']+=prediction.get('steps',prediction.get('completed_prediction_steps',0))
                        case_result['completed_prediction_steps']=prediction.get('steps',prediction.get('completed_prediction_steps',0))
                        require(prediction['status']=='PASS','worker error')
                        expected=original[boundary:boundary+8]
                        computed=compare_frames(prediction['frames'],expected,validation)
                        case_result.update(computed)
                        case_result.update(roundtrip_exact=prediction['restored_snapshot_hash']==prediction['source_snapshot_hash']==before,
                            terminated=prediction['terminated'],truncated=prediction['truncated'])
                        require(case_result['status']=='PASS' and case_result['roundtrip_exact'],'prediction alignment failed')
                        require(prediction['terminated']==decisions[index]['terminated'] and prediction['truncated']==decisions[index]['truncated'],'prediction termination differs')
                        require(all(f['oracle']['first_violation_step']==94 for f in prediction['frames'] if f['step']>=94),'wrong lift onset differs')
                    except BaseException as exc:
                        case_result.update(status='ERROR',error_type=type(exc).__name__,traceback=traceback.format_exc());raise
                    finally:
                        after=digest(capture(raw,wrapped,oracle,progress))
                        write_json(case/'noninterference.json',{'before_hash':before,'after_hash':after,'reference_state_unchanged':before==after,
                            'model_server_running':False,'model_calls_from_shadow':0,'policy_rng':'NOT_APPLICABLE_NO_POLICY_PROCESS'})
                        case_result.update(case_id=case_id,boundary_decision=index,repeat=repeat,first_step=boundary+1,last_step=boundary+8,
                            history_replay_steps_from_anchor=boundary-72,reference_unchanged=before==after)
                        if before!=after:case_result['status']='ERROR'
                        write_json(case/'result.json',case_result);case_rows.append(case_result)
                        require(before==after,'reference state changed during shadow')
            start=len(frames)
            observation,_,done,truncated,info=wrapped.step(prefix(source,index))
            replay=compare_frames(frames[start:],original[boundary:boundary+8],validation)
            with np.load(source/f'observation-{index+1:03d}.npz',allow_pickle=False) as saved:
                # Original request batching cast native float64 state to Box float32.
                obs_equal=all(np.array_equal(np.asarray(observation[k]).astype(saved[k].dtype),saved[k][0]) for k in saved.files)
            replay.update(decision=index,first_step=boundary+1,last_step=boundary+8,observation_exact_after_native_batch_cast=obs_equal)
            append_json(folder/'replay_alignment.jsonl',replay);replay_rows.append(replay)
            require(replay['status']=='PASS' and obs_equal,'history physical/oracle/observation mismatch')
            require(bool(done)==decisions[index]['terminated'] and bool(truncated)==decisions[index]['truncated'],'history termination mismatch')
        result.update(status='PASS',first_wrong_lift_step=oracle.first_violation_step,
            reconstructed_boundaries=len(reconstructed),case_results=case_rows,replay_results=replay_rows)
    except BaseException as exc:
        result.update(status='ERROR',error_type=type(exc).__name__,traceback=traceback.format_exc())
    finally:
        for name,obj in [('shadow',shadow),('reference',native)]:
            if obj is None:continue
            try:obj.close();append_json(folder/'cleanup.jsonl',{'resource':name,'status':'CLOSED','exit_code':getattr(getattr(obj,'process',None),'exitcode',None)})
            except BaseException as exc:
                result.update(status='CLEANUP_ERROR');append_json(folder/'cleanup.jsonl',{'resource':name,'status':'ERROR','error_type':type(exc).__name__,'traceback':traceback.format_exc()})
        unchanged=all(sha256(workspace/p)==s for p,s in server_files.items())
        result['old_model_artifacts_unchanged']=unchanged
        result['total_shadow_attempts']=len(list((workspace/'runs/m2_shadow').iterdir()))
        if not unchanged:result['status']='ERROR'
        write_json(folder/'result.json',result)
        write_json(folder/'artifact_manifest.json',manifest(workspace,[p for p in folder.rglob('*') if p.is_file()],'m2-r003-01'))
        trace.close()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--run-id',default='m2-r003-01')
    args=p.parse_args();folder=args.workspace/'runs'/args.run_id;folder.mkdir()
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'dirty code; no physics')
    cfg=read(Path('configs/m2_supplement_r003.json'))
    write_json(folder/'identity.json',{'repo_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'config_sha256':sha256('configs/m2_supplement_r003.json'),'config':cfg})
    try:result=run(args.workspace,folder,cfg)
    except BaseException:
        write_json(folder/'preflight_error.json',{'status':'ERROR','traceback':traceback.format_exc()});raise
    print(json.dumps({k:v for k,v in result.items() if k not in ['case_results','replay_results','traceback']},indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
