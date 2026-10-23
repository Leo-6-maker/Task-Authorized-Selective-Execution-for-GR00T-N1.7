"""Bounded E2 DEV saved-snapshot comparisons. Runs real sim, never policy.

Only use trusted task-owned originals after source manifest validation.
Two repeats per requested decision; any failure stops without retry/ID change.
"""
import argparse
import json
import pickle
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from tase.audit_contract import require
from tase.evidence import reserve_episode,sha256,write_json
from tase.e2_evidence import verify_manifest,manifest
from tase.shadow import Shadow
from tase.snapshot import digest
from tase.m2_context import compare_frames,jsonable
from audit_m2 import frame_arrays,read,lines,KEYS


def run(workspace,source_id,decisions):
    cfg=read(Path('configs/e2_dev.json'));source=workspace/'runs/DEV'/source_id
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'commit code before sim')
    require(read(workspace/'runs/gpu-authorization.json')['shared_gpu_inference_authorized'] is True,'resource permission missing')
    required={p.relative_to(workspace).as_posix() for p in source.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
    verify_manifest(workspace,read(source/'artifact_manifest.json'),required=required,source_run=source_id)
    result=read(source/'result.json');require(result['epoch']=='E2','wrong source epoch')
    require(result['status'] in ['SUCCESS','TIME_LIMIT'],'incomplete source episode')
    frames=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
    records={r['decision']:r for r in lines(source/'snapshots.jsonl')}
    require(len(decisions)==len(set(decisions)) and set(decisions)<=set(records),'invalid or duplicate decisions')
    worker=None;out=[]
    try:
        for index in decisions:
            record=records[index];path=source/f'snapshot-{index:03d}.pkl'
            require(sha256(path)==record['file_sha256'],'untrusted snapshot bytes')
            with path.open('rb') as f:snapshot=pickle.load(f)
            require(digest(snapshot)==record['snapshot_hash'],'snapshot identity mismatch')
            with np.load(source/f'action-{index:03d}.npz',allow_pickle=False) as action:
                prefix={k:np.array(action[k][0],copy=True) for k in KEYS}
            for repeat in range(2):
                case_id=f'{source_id}-d{index:03d}-r{repeat}'
                case=reserve_episode(workspace/'runs/consistency',case_id,{'split':'DEV','epoch':'E2',
                    'protocol_id':'TASE-002-v1.0','repo_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                    'source_run':source_id,'decision':index,'repeat':repeat,'source_snapshot_sha256':sha256(path),
                    'classification':'DEV_DIAGNOSTIC_NOT_INDEPENDENT_TEST','policy_requests_permitted':False},limit=96)
                row={'status':'STARTED','case_id':case_id,'source_run':source_id,'decision':index,'repeat':repeat}
                try:
                    if worker is None:
                        worker=Shadow(result['task'],result['init_index'],read(source/'horizon.json'),result['environment_seed'])
                        write_json(case/'worker_setup.json',worker.setup)
                    predicted=worker.predict(snapshot,prefix)
                    write_json(case/'prediction.json',jsonable(predicted))
                    require(predicted['status']=='PASS','worker error')
                    before=record['completed_controls'];actual=frames[before:before+predicted['steps']]
                    row.update(compare_frames(predicted['frames'],actual,cfg))
                    row['roundtrip_exact']=predicted['source_snapshot_hash']==predicted['restored_snapshot_hash']==digest(snapshot)
                    expected=next(r for r in lines(source/'decisions.jsonl') if r['index']==index)
                    row['termination_exact']=predicted['terminated']==expected['terminated'] and predicted['truncated']==expected['truncated']
                    row.update(prediction_controls=predicted['steps'],new_model_calls=0,policy_rng='N/A_NO_POLICY_PROCESS')
                    require(row['status']=='PASS' and row['roundtrip_exact'] and row['termination_exact'],'comparison differs')
                except Exception as exc:
                    row.update(status='ERROR',error_type=type(exc).__name__)
                    raise
                finally:
                    write_json(case/'result.json',row)
                    write_json(case/'artifact_manifest.json',manifest(workspace,sorted(case.iterdir()),case_id))
                    out.append(row)
    finally:
        if worker is not None:worker.close()
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--source-run',required=True);p.add_argument('--decisions',type=int,nargs='+',required=True)
    a=p.parse_args();print(json.dumps(run(a.workspace,a.source_run,a.decisions),indent=2))
