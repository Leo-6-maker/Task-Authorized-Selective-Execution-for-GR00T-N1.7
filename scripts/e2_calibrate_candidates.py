"""One functional shadow prediction per fixed CALIB B0 candidate, never policy.

P4 candidate evaluation is separate from independent consistency repetitions.
Only first-major-event-or-earlier prefixes; stop at the first error, retain IDs.
"""
import argparse
import json
import os
import pickle
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scripts.audit_epoch import audit,read,lines
from tase.evidence import sha256,write_json,now_sgt
from tase.e2_ledger import reserve_candidate
from tase.e2_evidence import manifest,verify_manifest
from tase.audit_contract import require
from tase.shadow import Shadow
from tase.snapshot import digest
from tase.task_spec import TaskSpec
from tase.gate_features import contact_view,score_contacts
from tase.m2_context import compare_frames,jsonable
from scripts.audit_m2 import frame_arrays,KEYS
from tase.calibration import select


def run(workspace,repo,output):
    import subprocess
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip(),'commit code before functional predictions')
    repo_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    require(read(workspace/'runs/gpu-authorization.json')['shared_gpu_inference_authorized'] is True,'resource permission missing')
    cfg=read(repo/'configs/e2_calib.json');plan=read(repo/'configs/e2_calibration_plan.json')
    checked=audit(workspace,repo/'configs/e2_calib.json')
    cells=[c for c in read(repo/'configs/e2_calib_cells.json')['planned_cells'] if c['system']=='B0']
    require(len(cells)==24 and {r['run_id'] for r in checked['rows']}=={c['run_id'] for c in cells},'CALIB B0 ledger must close all24, including failures')
    require(all(r['complete'] and r['status'] in ['SUCCESS','TIME_LIMIT'] and r['exit_code']==0 for r in checked['rows']),'close/repair failed B0 acquisition before candidate selection')
    root=workspace/'runs/CALIB_candidates';root.mkdir(exist_ok=True)
    require(not list(root.iterdir()),'candidate work already started; audit existing IDs before recovery')
    library=[];records=[]
    for cell in cells:
        source=workspace/'runs/CALIB'/cell['run_id'];result=read(source/'result.json')
        spec=TaskSpec(**read(source/'task_spec.json')).validate();frames=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
        snaps={r['decision']:r for r in lines(source/'snapshots.jsonl')};onset=result['first_wrong_lift_step'];worker=None;ids=[]
        try:
            for decision in lines(source/'decisions.jsonl'):
                index=decision['index'];anchor=snaps[index];before=anchor['completed_controls']
                if onset is not None and before>=onset:break
                name=cell['run_id']+f'-d{index:03d}';ids.append(name)
                case=reserve_candidate(root,name,{'split':'CALIB','epoch':'E2','protocol_id':'TASE-002-v1.0',
                    'repo_sha':repo_sha,'runtime_lock_hash':sha256(repo/'configs/runtime_lock_E2.json'),
                    'classification':'P4_FUNCTIONAL_FIXED_CANDIDATE_NOT_INDEPENDENT_CONSISTENCY','source_run':cell['run_id'],
                    'decision':index,'new_model_requests_permitted':False,'controller_pid':os.getpid(),
                    'source_manifest_sha256':sha256(source/'artifact_manifest.json'),'source_snapshot_sha256':anchor['file_sha256'],
                    'calibration_plan_hash':sha256(repo/'configs/e2_calibration_plan.json')})
                write_json(case/'started.json',{'controller_pid':os.getpid(),'started_at_sgt':now_sgt()})
                row={'candidate_id':name,'source_run':cell['run_id'],'decision':index,'status':'STARTED'}
                try:
                    path=source/f'snapshot-{index:03d}.pkl';require(sha256(path)==anchor['file_sha256'],'snapshot bytes differ')
                    with path.open('rb') as stream:snapshot=pickle.load(stream)
                    require(digest(snapshot)==anchor['snapshot_hash'],'complete source snapshot differs')
                    with np.load(source/f'action-{index:03d}.npz',allow_pickle=False) as data:prefix={k:np.array(data[k][0],copy=True) for k in KEYS}
                    if worker is None:
                        worker=Shadow(cell['task'],cell['init_index'],read(source/'horizon.json'),result['environment_seed'])
                        write_json(case/'worker_setup.json',worker.setup)
                    tick=time.perf_counter();prediction=worker.predict(snapshot,prefix);seconds=time.perf_counter()-tick
                    write_json(case/'prediction.json',jsonable(prediction))
                    require(prediction['status']=='PASS' and prediction['source_snapshot_hash']==prediction['restored_snapshot_hash']==anchor['snapshot_hash'],'prediction/restore differs')
                    count=prediction['steps'];require(type(count) is int and 1<=count<=8,'invalid prefix length')
                    comparison=compare_frames(prediction['frames'],frames[before:before+count],cfg)
                    require(comparison['status']=='PASS' and count==decision['inner_steps'] and prediction['terminated']==decision['terminated'] and prediction['truncated']==decision['truncated'],'saved-source comparison differs')
                    views=[contact_view(f,spec.objects) for f in prediction['frames']]
                    scored={str(k):score_contacts(views,list(spec.objects),spec.target,anchor['contact_history'],before,k) for k in plan['candidates']}
                    major=onset is not None and before<onset<=before+count
                    row.update(condition=cell['condition'],first_major_window=major,
                        completed_controls_before=before,prediction_controls=count,new_model_requests=0,
                        worker_pid=worker.process.pid,controller_pid=os.getpid(),prediction_seconds=seconds,
                        decisions={k:v['decision'] for k,v in scored.items()},scores=scored,**comparison)
                    write_json(case/'contact_views.json',{'views':views,'trusted_target':spec.target,'actual_contact_history':anchor['contact_history']})
                except BaseException as exc:
                    row.update(status='ERROR',error_type=type(exc).__name__);raise
                finally:
                    write_json(case/'result.json',row)
                    write_json(case/'artifact_manifest.json',manifest(workspace,sorted(case.iterdir()),name))
                library.append(row);records.append({'candidate_id':name,'manifest_sha256':sha256(case/'artifact_manifest.json')})
        finally:
            try:
                if worker is not None:worker.close()
            finally:
                write_json(workspace/'runs/CALIB_candidate_processes'/f"{cell['run_id']}.worker_exit.json",{
                    'controller_pid':os.getpid(),'source_run':cell['run_id'],'case_ids':ids,
                    'worker_pid':worker.process.pid if worker is not None else None,
                    'worker_returncode':worker.process.exitcode if worker is not None else None})
        print(json.dumps({'source_run':cell['run_id'],'functional_candidates':len(ids),'new_model_requests':0}),flush=True)
    index=workspace/'runs/CALIB_candidates/library_manifest.json';write_json(index,records)
    chosen=select(library,sha256(repo/'configs/e2_calibration_plan.json'))
    chosen.update(candidate_count=len(library),library_manifest_sha256=sha256(index),new_model_requests=0,
                  repo_sha=repo_sha,runtime_lock_hash=sha256(repo/'configs/runtime_lock_E2.json'))
    write_json(output,chosen);print(json.dumps(chosen,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.workspace,a.repo,a.output)
