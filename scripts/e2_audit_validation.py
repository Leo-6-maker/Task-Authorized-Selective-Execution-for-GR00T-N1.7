"""Recompute fresh E2 short-check results using JSON/byte originals, no pickle.

This is a machine precondition for DEV Gate, never a GPT approval.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require
from tase.evidence import sha256,write_json
from tase.e2_evidence import verify_manifest
from tase.m2_context import compare_frames
from scripts.audit_m2 import frame_arrays,read,lines


def audit(workspace,plan_path):
    plan=read(plan_path);repo=plan_path.parent.parent;cfg=read(repo/'configs/e2_dev.json')
    require(plan['epoch']=='E2' and plan['new_model_requests_permitted'] is False,'invalid validation authority')
    require(plan['config_sha256']==sha256(repo/'configs/e2_dev.json') and
            plan['runtime_lock_sha256']==sha256(repo/'configs/runtime_lock_E2.json'),'plan identity changed')
    expected=set();rows=[];normal=set();phases={};processes={};sources={}
    for c in plan['cases']:
        source=workspace/'runs/DEV'/c['source_run'];invocation='e2v1-'+c['source_run']
        require(c['repeats']==2,'repetition count changed')
        if c['source_run'] not in sources:
            require(sha256(source/'artifact_manifest.json')==c['source_manifest_sha256'],'source manifest changed')
            required={p.relative_to(workspace).as_posix() for p in source.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
            verify_manifest(workspace,read(source/'artifact_manifest.json'),required=required,source_run=c['source_run'])
            frames=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
            sources[c['source_run']]=(frames,{x['index']:x for x in lines(source/'decisions.jsonl')})
        require(sha256(source/f"snapshot-{c['decision']:03d}.pkl")==c['snapshot_sha256'],'planned snapshot bytes changed')
        if invocation not in processes:
            root=workspace/'runs/consistency_processes'
            start=read(root/f'{invocation}.exit.started.json');end=read(root/f'{invocation}.exit.json')
            worker=read(root/f'{invocation}.worker_exit.json')
            require(start['child_pid']==end['child_pid']==worker['controller_pid'],'controller process identity differs')
            require(end['child_returncode']==end['exit_code']==0 and end['signal'] is None,'controller did not exit cleanly')
            require(worker['worker_returncode']==0 and type(worker['worker_pid']) is int,'worker did not exit cleanly')
            processes[invocation]=(start,end,worker)
        start,end,worker=processes[invocation];source_frames,decisions=sources[c['source_run']]
        for repeat in range(2):
            case_id=f"{c['source_run']}-d{c['decision']:03d}-r{repeat}"
            require(case_id not in expected,'duplicate planned check');expected.add(case_id)
            case=workspace/'runs/consistency'/case_id
            required={p.relative_to(workspace).as_posix() for p in case.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
            verify_manifest(workspace,read(case/'artifact_manifest.json'),required=required,source_run=case_id)
            reservation=read(case/'reservation.json');started=read(case/'started.json');result=read(case/'result.json')
            predicted=read(case/'prediction.json')
            require(reservation['source_run']==c['source_run'] and reservation['decision']==c['decision'] and
                    reservation['repeat']==repeat and reservation['source_snapshot_sha256']==c['snapshot_sha256'],'reservation differs')
            require(reservation['policy_requests_permitted'] is False and result['new_model_calls']==0,'unexpected policy permission/calls')
            require(reservation['invocation_id']==started['invocation_id']==result['invocation_id']==invocation,'invocation differs')
            require(started['controller_pid']==result['controller_pid']==start['child_pid'] and
                    result['worker_pid']==worker['worker_pid'] and case_id in worker['case_ids'],'case/process binding differs')
            require(predicted['status']=='PASS' and predicted['source_snapshot_hash']==predicted['restored_snapshot_hash']==c['snapshot_digest'],'snapshot roundtrip differs')
            count=predicted['steps'];require(type(count) is int and 1<=count<=8,'invalid short horizon')
            before=c['completed_controls'];comparison=compare_frames([frame_arrays(f) for f in predicted['frames']],source_frames[before:before+count],cfg)
            decision=decisions[c['decision']]
            require(count==decision['inner_steps'] and predicted['terminated']==decision['terminated'] and predicted['truncated']==decision['truncated'],'native termination differs')
            require(comparison['status']=='PASS' and result['status']=='PASS' and result['roundtrip_exact'] is True and result['termination_exact'] is True,'comparison failed')
            require(all(result[k]==v for k,v in comparison.items()),'saved comparison does not recompute')
            rows.append({'case_id':case_id,'source_run':c['source_run'],'decision':c['decision'],'repeat':repeat,
                         'prediction_controls':count,'phases':c['phases'],**comparison})
        if c['condition']=='C0':
            normal.add((c['source_run'],c['decision']));phases.setdefault(c['task'],set()).update(c['phases'])
    actual={p.parent.name for p in (workspace/'runs/consistency').glob('*/reservation.json')}
    require(actual==expected and len(expected)==plan['planned_checks']<=96,'all attempts, including failed/partial, must reconcile')
    required_phases={'APPROACH_NO_CONTACT','CONTACT_OR_CLOSURE','AUTHORIZED_TRANSPORT','TERMINATION_BOUNDARY'}
    require(len(normal)>=12 and len(phases)==3 and all(required_phases<=v for v in phases.values()),'normal phase coverage insufficient')
    for invocation,(_,_,worker) in processes.items():
        require(set(worker['case_ids'])=={r['case_id'] for r in rows if 'e2v1-'+r['source_run']==invocation},'worker case accounting differs')
    return {'status':'P2_MACHINE_PRECONDITIONS_PASS_NOT_GPT_APPROVAL','epoch':'E2','protocol_id':'TASE-002-v1.0',
        'plan_sha256':sha256(plan_path),'config_sha256':plan['config_sha256'],'runtime_lock_sha256':plan['runtime_lock_sha256'],
        'checks_including_failures':len(actual),'distinct_snapshots':len(plan['cases']),'normal_distinct_snapshots':len(normal),
        'prediction_controls':sum(r['prediction_controls'] for r in rows),'new_model_calls':0,'rows':rows,
        'independent_review':'NOT_PERFORMED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--plan',type=Path,default=Path('configs/e2_shadow_plan.json'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.workspace,a.plan);write_json(a.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
