"""CPU-only ledger, actual server request and video-coverage reconciliation."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.audit_contract import require
from tase.evidence import write_json,sha256


def read(path):return json.loads(path.read_text())
def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def reconcile(workspace,output):
    import cv2
    import numpy as np
    cv2.setNumThreads(1);cv2.ocl.setUseOpenCL(False);output.mkdir()
    rows=[];media=[];lookup={};figures=[];event_windows=[]
    for split,cap in [('DEV',24),('CALIB',48)]:
        folders=sorted(p for p in (workspace/'runs'/split).iterdir() if p.is_dir() and p.name!='.reservation-lock')
        require(len(folders)<=cap,'budget exceeded')
        for folder in folders:
            reserved=read(folder/'reservation.json');result=read(folder/'result.json') if (folder/'result.json').is_file() else None
            start=read(workspace/'runs'/f'{folder.name}.exit.started.json');end=read(workspace/'runs'/f'{folder.name}.exit.json')
            require(start['child_pid']==end['child_pid'],'actual attempt PID differs')
            physical=lines(folder/'physical_frames.jsonl');identity=read(folder/'e2_identity.json')
            keys=['run_id','task','init_index','condition','system','scenario_id','policy_seed','environment_seed','repo_sha','config_hash','runtime_lock_hash','budget_ordinal']
            row={k:reserved[k] for k in keys};row.update(split=split,result_present=result is not None,
                status=result['status'] if result else 'STARTED_OR_INTERRUPTED',exit_code=end['exit_code'],
                child_returncode=end['child_returncode'],physical_controls_observed=len(physical),
                model_requests=result['policy_requests_attempted'] if result else len(list(folder.glob('observation-*.npz'))),
                first_wrong_lift_step=result.get('first_wrong_lift_step') if result else None,
                official_success=result['official_success'] if result else None)
            if result:require(result['exit_code']==end['exit_code'] and result['inner_steps']==len(physical),'result/actual exit/control differs')
            rows.append(row);lookup[folder.name]=(row,identity)
            onset=row['first_wrong_lift_step'];selected=[onset-8,onset-1,onset,onset+1,onset+8] if split=='CALIB' and onset else []
            cap_video=cv2.VideoCapture(str(folder/'rollout.mp4'));decoded=0;kept={};opened=cap_video.isOpened()
            while True:
                ok,image=cap_video.read()
                if not ok:break
                decoded+=1
                if decoded in selected:kept[decoded]=image
            cap_video.release()
            if result:require(opened and decoded==len(physical),'complete video coverage differs')
            media.append({'run_id':folder.name,'complete_result':result is not None,'decoded_frames':decoded,
                'physical_controls':len(physical),'coverage_complete':decoded==len(physical),
                'event_label_frame_object_counts':dict(Counter(e['label'] for f in physical for e in f['oracle']['events']))})
            if selected:
                tiles=[];window=[]
                for step in selected:
                    require(step in kept,'missing first-event media control')
                    canvas=np.zeros((288,512,3),np.uint8);canvas[32:]=kept[step]
                    cv2.putText(canvas,folder.name+' ctrl='+str(step),(6,22),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1)
                    tiles.append(canvas);window.append(physical[step-1])
                figures.append(np.concatenate(tiles,axis=1));event_windows.append({'run_id':folder.name,
                    'baseline_positions':identity['baseline_positions'],'true_target':identity['true_task_target'],'first_wrong_lift_step':onset,'physical_frames':window})
    mapping=[('server-e2-01',[f'e2-dev-{i:04d}' for i in range(1,7)]),('server-e2-02',['e2-dev-0019']),
        ('server-e2-03',[f'e2-dev-{i:04d}' for i in range(7,13)]),('server-e2-04',[f'e2-dev-{i:04d}' for i in range(13,19)]),
        ('server-e2-05',[f'e2-calib-{i:04d}' for i in range(1,25)]),('server-e2-06',[f'e2-calib-{i:04d}' for i in range(25,49)])]
    servers=[]
    state={f'state.{k}':[1,1,2 if k=='gripper' else 1] for k in ['x','y','z','roll','pitch','yaw','gripper']}
    inputs={**state,'video.image':[1,1,256,256,3],'video.wrist_image':[1,1,256,256,3]}
    outputs={f'action.{k}':[1,16,1] for k in ['x','y','z','roll','pitch','yaw','gripper']}
    for server,ids in mapping:
        requests=lines(workspace/'runs'/server/'actual_requests.jsonl');inference=lines(workspace/'runs'/server/'inference.jsonl');offset=0
        for run_id in ids:
            row,identity=lookup[run_id];count=row['model_requests']
            for actual in requests[offset:offset+count]:
                require(actual['scenario']['scenario_id']==row['scenario_id'] and actual['scenario']['seed']==row['policy_seed'] and
                        actual['actual_policy_language']==[identity['actual_policy_language']],'actual language/seed/scenario differs')
            offset+=count
        require(offset==len(requests)==len(inference),'all model requests including partial attempts must reconcile')
        require([x['request'] for x in requests]==[x['request'] for x in inference]==list(range(1,len(requests)+1)),'actual request sequence differs')
        require(all(x['status']=='PASS' and x['input_shapes']==inputs and x['output_shapes']==outputs for x in inference),'native observed input/output contract differs')
        end=read(workspace/'runs'/f'{server}.exit.json');start=read(workspace/'runs'/f'{server}.exit.started.json')
        require(start['child_pid']==end['child_pid'],'actual server PID differs')
        servers.append({'server':server,'actual_requests':len(requests),'actual_exit_code':end['exit_code'],
            'child_returncode':end['child_returncode'],'all_native_contracts_and_language_seed_verified':True})
    require(sum(r['model_requests'] for r in rows)==sum(s['actual_requests'] for s in servers),'episode/server total differs')
    with (output/'attempt_ledger.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    write_json(output/'media_check.json',{'scope':'EXECUTOR_DECODE_NOT_INDEPENDENT_MEDIA_LABELING','rows':media,
        'complete_result_videos':sum(m['complete_result'] for m in media),'all_complete_result_videos_match_controls':True,
        'known_original_interruption_retained':'e2-dev-0006: undecodable MP4,537 saved main controls,actual exit143,missing result retained'})
    if figures:require(cv2.imwrite(str(output/'calibration-first-event-contact-sheet.png'),np.concatenate(figures,axis=0)),'frame export failed')
    write_json(output/'calibration_first_event_windows.json',{'scope':'ACTUAL_CALIB_DEVELOPMENT_EVENT_WINDOWS_NOT_TEST_OR_REVIEW_APPROVAL','rows':event_windows})
    summary={'epoch':'E2','protocol_id':'TASE-002-v1.0','attempts_including_failures':len(rows),
        'DEV_used':sum(r['split']=='DEV' for r in rows),'CALIB_used':sum(r['split']=='CALIB' for r in rows),
        'TEST_used':0,'TEST_authorized':False,'statuses':dict(Counter(r['status'] for r in rows)),
        'physical_controls_observed':sum(r['physical_controls_observed'] for r in rows),'actual_model_requests':sum(s['actual_requests'] for s in servers),
        'all_attempt_start_exit_pairs_present':True,'all_result_files_present':all(r['result_present'] for r in rows),
        'servers':servers,'ledger_sha256':sha256(output/'attempt_ledger.csv'),'independent_review':'NOT_PERFORMED'}
    write_json(output/'ledger_reconciliation.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(reconcile(a.workspace,a.output),indent=2))
