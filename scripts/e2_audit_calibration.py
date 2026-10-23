"""Recompute fixed CALIB candidate library and selection; JSON/NPZ only."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import audit,read,lines
from scripts.audit_m2 import frame_arrays
from tase.audit_contract import require
from tase.evidence import sha256,write_json
from tase.e2_evidence import verify_manifest
from tase.m2_context import compare_frames
from tase.gate_features import contact_view,score_contacts
from tase.task_spec import TaskSpec
from tase.calibration import select


def candidates(workspace,repo,selection_path):
    checked=audit(workspace,repo/'configs/e2_calib.json');cfg=read(repo/'configs/e2_calib.json')
    plan_hash=sha256(repo/'configs/e2_calibration_plan.json');selection=read(selection_path)
    root=workspace/'runs/CALIB_candidates';index=read(root/'library_manifest.json')
    require(sha256(root/'library_manifest.json')==selection['library_manifest_sha256'],'library index differs')
    expected={};sources={};library=[]
    for row in checked['rows']:
        if row['system']!='B0':continue
        require(row['status'] in ['SUCCESS','TIME_LIMIT'] and row['complete'],'CALIB B0 source incomplete')
        source=workspace/'runs/CALIB'/row['run_id'];result=read(source/'result.json')
        frames=[frame_arrays(f) for f in lines(source/'physical_frames.jsonl')]
        snaps={s['decision']:s for s in lines(source/'snapshots.jsonl')};decisions=lines(source/'decisions.jsonl')
        spec=TaskSpec(**read(source/'task_spec.json')).validate();onset=result['first_wrong_lift_step']
        source_ids=[]
        for decision in decisions:
            anchor=snaps[decision['index']];before=anchor['completed_controls']
            if onset is not None and before>=onset:break
            name=row['run_id']+f"-d{decision['index']:03d}";source_ids.append(name)
            expected[name]=(row,source,result,frames,anchor,decision,spec)
        sources[row['run_id']]=source_ids
    require(len(sources)==24,'CALIB B0 sources missing')
    actual={p.parent.name for p in root.glob('*/reservation.json')}
    require(actual==set(expected)=={r['candidate_id'] for r in index} and len(index)==len(expected)<=2160,'candidate attempts, including failures/partials, differ')
    start=read(workspace/'runs/calibration-candidates-v1.exit.started.json')
    end=read(workspace/'runs/calibration-candidates-v1.exit.json')
    require(start['child_pid']==end['child_pid'] and end['child_returncode']==end['exit_code']==0,'candidate controller actual exit differs')
    processes={}
    for source,ids in sources.items():
        worker=read(workspace/'runs/CALIB_candidate_processes'/f'{source}.worker_exit.json')
        require(worker['controller_pid']==start['child_pid'] and worker['worker_returncode']==0 and
                type(worker['worker_pid']) is int and worker['case_ids']==ids,'candidate worker exit/accounting differs')
        processes[source]=worker
    for entry in index:
        name=entry['candidate_id'];case=root/name
        require(sha256(case/'artifact_manifest.json')==entry['manifest_sha256'],'candidate manifest differs')
        required={p.relative_to(workspace).as_posix() for p in case.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
        verify_manifest(workspace,read(case/'artifact_manifest.json'),required=required,source_run=name)
        row,source,result,frames,anchor,decision,spec=expected[name]
        reservation=read(case/'reservation.json');began=read(case/'started.json');saved=read(case/'result.json')
        prediction=read(case/'prediction.json');views=read(case/'contact_views.json')
        require(reservation['split']=='CALIB' and reservation['source_run']==row['run_id'] and
                reservation['decision']==decision['index'] and reservation['calibration_plan_hash']==plan_hash,'candidate reservation differs')
        require(reservation['repo_sha']==selection['repo_sha'] and reservation['runtime_lock_hash']==selection['runtime_lock_hash']==sha256(repo/'configs/runtime_lock_E2.json'),'candidate code/runtime differs')
        require(reservation['source_manifest_sha256']==sha256(source/'artifact_manifest.json') and
                reservation['source_snapshot_sha256']==anchor['file_sha256'],'source identity differs')
        require(prediction['status']=='PASS' and prediction['source_snapshot_hash']==prediction['restored_snapshot_hash']==anchor['snapshot_hash'],'snapshot restoration differs')
        before=anchor['completed_controls'];count=prediction['steps']
        require(type(count) is int and 1<=count<=8 and count==decision['inner_steps'] and
                prediction['terminated']==decision['terminated'] and prediction['truncated']==decision['truncated'],'native prefix/termination differs')
        comparison=compare_frames([frame_arrays(f) for f in prediction['frames']],frames[before:before+count],cfg)
        require(comparison['status']=='PASS' and all(saved[k]==v for k,v in comparison.items()),'candidate numeric comparison differs')
        contact=[contact_view(f,spec.objects) for f in prediction['frames']]
        history={n:0 for n in spec.objects}
        for frame in frames[:before]:
            for n in history:history[n]=history[n]+1 if frame['left_contacts'][n] and frame['right_contacts'][n] else 0
        require(views['views']==contact and views['trusted_target']==spec.target and views['actual_contact_history']==anchor['contact_history']==history,'contact-only view/history differs')
        scores={str(k):score_contacts(contact,list(spec.objects),spec.target,history,before,k) for k in [1,2,3]}
        major=result['first_wrong_lift_step'] is not None and before<result['first_wrong_lift_step']<=before+count
        require(saved['scores']==scores and saved['decisions']=={k:v['decision'] for k,v in scores.items()} and
                saved['condition']==row['condition'] and saved['first_major_window']==major,'candidate labels/scoring differs')
        require(reservation['new_model_requests_permitted'] is False and saved['new_model_requests']==0,'unexpected model permission/calls')
        require(saved['controller_pid']==began['controller_pid']==reservation['controller_pid']==start['child_pid'] and
                saved['worker_pid']==processes[row['run_id']]['worker_pid'],'case/process PID differs')
        library.append(saved)
    recomputed=select(library,plan_hash)
    require(all(selection[k]==v for k,v in recomputed.items()),'frozen selection does not recompute')
    require(selection['candidate_count']==len(library),'candidate denominator differs')
    return {'status':'CANDIDATES_AND_SELECTION_RECOMPUTE_NOT_GPT_APPROVAL','candidate_count':len(library),
        'prediction_controls':sum(r['prediction_controls'] for r in library),'source_B0_count':len(sources),
        'worker_exits_verified':len(processes),'controller_exit':end['exit_code'],'selection':selection,
        'all_calib_attempts_including_failures':checked['calib_used'],'new_model_requests':0,'independent_review':'NOT_PERFORMED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=candidates(a.workspace,a.repo,a.selection);write_json(a.output,report);print(json.dumps(report,indent=2))
