"""CPU re-audit of executor-created, hash-verified R003 DEV originals only.

This reads trusted local pickles; never use on an untrusted attachment.
No MuJoCo, GPU or policy invocation. Original M2 and supplement remain separate.
"""
import argparse
import json
import pickle
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_m2 import read,lines,frame_arrays,KEYS
from tase.audit_contract import require
from tase.evidence import write_json,verify_manifest,sha256
from tase.snapshot import digest
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.m2_context import compare_frames,jsonable


def load(path):
    with path.open('rb') as f:return pickle.load(f)


def audit(original,supplement):
    cfg=read(Path('configs/m2_supplement_r003.json'));validation=read(Path('configs/m2_validation.json'))
    source=original/'runs/episodes/dev-m2-017';folder=supplement/'runs/m2-r003-01'
    required={p.relative_to(supplement).as_posix() for p in folder.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
    verify_manifest(supplement,read(folder/'artifact_manifest.json'),required=required,source_run='m2-r003-01')
    identity=read(folder/'identity.json');result=read(folder/'result.json')
    require(identity['config']==cfg and identity['config_sha256']==sha256('configs/m2_supplement_r003.json'),'supplement config differs')
    require(result['status']=='PASS' and result['shadow_attempts']==6 and result['total_shadow_attempts']==80,'failed/incomplete diagnostic')
    require(result['new_model_calls']==result['new_autonomous_episodes']==0 and result['old_model_artifacts_unchanged'] is True,'model scope differs')
    require(read(supplement/'runs/m2-r003-01.exit.json')['child_returncode']==0,'diagnostic did not exit normally')
    cleanup=lines(folder/'cleanup.jsonl')
    require({r['resource'] for r in cleanup}=={'shadow','reference'} and all(r['status']=='CLOSED' for r in cleanup),'cleanup incomplete')
    require(next(r for r in cleanup if r['resource']=='shadow')['exit_code']==0,'worker did not exit normally')
    original_frames=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
    replay=[frame_arrays(f) for f in lines(folder/'replay_frames.jsonl')]
    require(len(replay)==result['history_replay_control_steps']==32,'history count')
    require(compare_frames(replay,original_frames[72:104],validation)['status']=='PASS','history physical/event mismatch')
    states=lines(folder/'replay_states.jsonl')
    with np.load(source/'control_trace.npz',allow_pickle=False) as trace:
        require([r['step'] for r in states]==list(range(73,105)),'state sequence missing')
        require(all(np.array_equal(r['native_state'],trace['states'][r['step']-1]) and r['exact_original_state'] is True for r in states),'native replay differs')
    anchor=load(source/'snapshot-009.pkl')
    require(sha256(source/'snapshot-009.pkl')==result['source_anchor_sha256'] and digest(anchor)==result['source_anchor_digest'],'source anchor differs')
    spec=TaskSpec(**read(source/'task_spec.json'))
    cases=[];ordinals=[];all_frames=0
    for index in cfg['boundary_decisions']:
        snapshot=load(folder/f'reconstructed-d{index:03d}.pkl');meta=read(folder/f'reconstructed-d{index:03d}.json')
        require(meta['scope']==cfg['scope'] and meta['snapshot_digest']==digest(snapshot),'reconstructed identity')
        require(snapshot['progress']['policy_control_steps']==index*8 and len(snapshot['history']['reward'])==index*8,'reconstructed progress')
        oracle=EventOracle(spec,{n:[0,0,z] for n,z in anchor['oracle']['baseline_z'].items()});oracle.restore(anchor['oracle'])
        for f in original_frames[72:index*8]:oracle.consume({k:v for k,v in f.items() if k not in ['oracle','control_input']})
        require(digest(oracle.state())==digest(snapshot['oracle']),'reconstructed historical oracle differs')
        for repeat in range(3):
            case_id=f'r003-dev-m2-017-d{index:03d}-r{repeat}';case=supplement/'runs/m2_shadow'/case_id
            reservation=read(case/'reservation.json');ordinals.append(reservation['budget_ordinal'])
            require(reservation['boundary_decision']==index and reservation['repeat']==repeat and reservation['run_id']==case_id and reservation['model_calls_permitted'] is False,'case identity')
            prediction=load(case/'prediction.pkl');recorded=read(case/'result.json');guard=read(case/'noninterference.json')
            require(prediction['status']=='PASS' and prediction['steps']==8,'prediction incomplete')
            frames=[frame_arrays(f) for f in prediction['frames']]
            require(prediction['restored_snapshot_hash']==prediction['source_snapshot_hash']==digest(snapshot),'roundtrip differs')
            computed=compare_frames(frames,original_frames[index*8:index*8+8],validation)
            require(computed['status']=='PASS' and all(recorded[k]==v for k,v in computed.items()),'prediction comparison differs')
            require(prediction['terminated'] is False and prediction['truncated'] is False,'termination differs')
            require(guard['reference_state_unchanged'] is True and guard['before_hash']==guard['after_hash']==digest(snapshot),'reference changed')
            require(guard['model_server_running'] is False and guard['model_calls_from_shadow']==0,'model scope changed')
            oracle.restore(snapshot['oracle'])
            for f in frames:
                output=oracle.consume({k:v for k,v in f.items() if k not in ['oracle','control_input']})
                require(jsonable(output)==f['oracle'],'predicted oracle output differs')
            onset=[f['step'] for f in frames if any(e['label']=='WRONG_OBJECT_LIFT' and e['new_lift'] for e in f['oracle']['events'])]
            require(onset==([94] if index==11 else []),'new lift onset differs')
            require(frames[-1]['oracle']['first_violation_step']==94,'sticky onset differs')
            all_frames+=len(frames)
            cases.append({'case_id':case_id,'boundary_decision':index,'repeat':repeat,'first_step':index*8+1,'last_step':index*8+8,
                'first_violation_step':94,'new_lift_onset_steps':onset,'status':computed['status'],
                **{k:computed[k] for k in ['position_m','orientation_rad','gripper_m']},'roundtrip_exact':True,'reference_unchanged':True})
    require(ordinals==list(range(75,81)) and all_frames==result['prediction_control_steps']==48,'budget/prediction mismatch')
    require({p.name for p in (supplement/'runs/m2_shadow').iterdir()}=={r['case_id'] for r in cases},'unaccounted supplemental cases')
    for name in ['reference_setup.json','shadow_setup.json']:
        setup=read(folder/name);require(setup['environment_instances']==1 and setup['explicit_native_resets']==1 and setup['settling_steps']==10,'setup count')
    return {'status':'PASS','runtime_sha':identity['repo_sha'],'config_sha256':identity['config_sha256'],'scope':cfg['scope'],
        'original_distinct_snapshots':24,'original_comparisons':74,'original_predicted_controls':589,
        'reconstructed_boundaries':2,'supplemental_comparisons':6,'supplemental_predicted_controls':48,
        'historical_replay_controls':32,'new_model_calls':0,'new_autonomous_episodes':0,'dev_used':18,'shadow_used':80,
        'setup_environment_instances':2,'setup_settling_controls':20,'first_violation_step':94,
        'independent_raw_review':'NOT_VERIFIED_BY_REVIEWER','cases':cases}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--supplement',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=audit(a.original,a.supplement);write_json(a.output,data)
    print(json.dumps({k:v for k,v in data.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
