"""CPU-only CALIB derivative; fixed plan, all488 decisions and selected full pairs.

Recomputes existing JSON/NPZ evidence, never loads pickle or creates a simulator.
Original SHA256 and code identities are retained separately from derivative SHA.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import read,lines
from scripts.e2_audit_calibration import candidates,pairs
from scripts.e2_export_review import redact,validate_numpy
from tase.evidence import sha256,write_json
from tase.test_authorization import require
from tase.execution_gate import KEYS
from tase.calibration import select


def export(workspace,repo,out):
    plan=read(repo/'configs/e2_calib_export_plan.json')
    checked=candidates(workspace,repo,repo/'configs/e2_calib_selection.json')
    pair_audit=pairs(workspace,repo)
    require(checked['candidate_count']==488,'fixed488 existing candidates required')
    out.mkdir();records=[];origins={}
    markers=[str(workspace),str(Path.home())]
    code=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    def origin(source):
        key=source.relative_to(workspace).as_posix()
        if key not in origins:
            origins[key]=dict(source_path=key,source_sha256=sha256(source),bytes=source.stat().st_size)
        return origins[key]
    def save(name,data,sources,selection):
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(data)
        records.append(dict(export_path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                            origins=[origin(s) for s in sources],selection=selection))
    def js(name,value,sources,selection):
        save(name,(json.dumps(redact(value,markers),indent=2,allow_nan=False)+'\n').encode(),sources,selection)
    def jl(name,rows,source,selection):
        save(name,(''.join(json.dumps(redact(v,markers),allow_nan=False)+'\n' for v in rows)).encode(),[source],selection)
    source_data={};flat=[]
    library=read(workspace/'runs/CALIB_candidates/library_manifest.json')
    for entry in sorted(library,key=lambda r:r['candidate_id']):
        case=workspace/'runs/CALIB_candidates'/entry['candidate_id']
        r=read(case/'result.json');res=read(case/'reservation.json')
        source=workspace/'runs/CALIB'/r['source_run']
        if r['source_run'] not in source_data:
            source_data[r['source_run']]=read(source/'result.json')
        sr=source_data[r['source_run']]
        row={k:r[k] for k in ['candidate_id','source_run','decision','condition','first_major_window',
                              'completed_controls_before','prediction_controls','new_model_requests']}
        row.update(task=sr['task'],init_index=sr['init_index'],init_hash=sr['init_hash'],system='B0_SOURCE',
            source_status=sr['status'],first_actual_major_step=sr['first_wrong_lift_step'],
            candidate_code_sha=res['repo_sha'],source_code_sha=sr['repo_sha'],runtime_lock_hash=res['runtime_lock_hash'],
            source_manifest_sha256=res['source_manifest_sha256'],source_snapshot_file_sha256=res['source_snapshot_sha256'],
            source_snapshot_state_sha256=read(case/'prediction.json')['source_snapshot_hash'],
            candidate_manifest_sha256=entry['manifest_sha256'],
            source_result_sha256=sha256(source/'result.json'),source_frames_sha256=sha256(source/'physical_frames.jsonl'),
            raw_action_sha256=sha256(source/f"action-{r['decision']:03d}.npz"),
            candidate_result_sha256=sha256(case/'result.json'),prediction_sha256=sha256(case/'prediction.json'),
            contact_views_sha256=sha256(case/'contact_views.json'),
            **{f'k{k}_decision':r['decisions'][str(k)] for k in [1,2,3]})
        flat.append(row)
        for name in ['reservation.json','started.json','result.json','prediction.json','contact_views.json','artifact_manifest.json']:
            origin(case/name)
        for name in ['result.json','physical_frames.jsonl','artifact_manifest.json','snapshots.jsonl',
                     f"action-{r['decision']:03d}.npz",f"snapshot-{r['decision']:03d}.pkl"]:
            origin(source/name)
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    save('candidate_decisions.csv',stream.getvalue().encode(),[workspace/'runs/CALIB_candidates/library_manifest.json'],
         'ALL488_ORIGINAL_FIXED_CANDIDATES_NO_NEW_PREDICTION')
    js('candidate_decisions.json',flat,[workspace/'runs/CALIB_candidates/library_manifest.json'],'ALL488_TYPED_ROWS')
    selection=select([dict(condition=r['condition'],first_major_window=r['first_major_window'],
        decisions={str(k):r[f'k{k}_decision'] for k in [1,2,3]}) for r in flat],sha256(repo/'configs/e2_calibration_plan.json'))
    require(selection['selected_k']==3 and all(m['primary_first_event_candidates']==4 and
            m['C0_local_negative_candidates']==286 for m in selection['metrics']), 'flat rows must independently recover4/286/k3')
    js('selection_recomputed.json',selection,[workspace/'runs/CALIB_candidates/library_manifest.json'],'RECOMPUTED_FROM_PUBLIC488_ROWS')
    # Rule was committed before this original export. No post-export selection changes.
    chosen=plan['positive_B0_ids']+plan['negative_control_B0_ids']
    require([r['b0_run'] for r in pair_audit['pairs'] if r['b0_first_wrong_lift'] is not None]==plan['positive_B0_ids'],
            'existing four positive identities differ from predeclared plan')
    selected_pairs=[]
    for b0 in chosen:
        pair=next(p for p in pair_audit['pairs'] if p['b0_run']==b0);selected_pairs.append(pair)
        for run_id in [pair['b0_run'],pair['g_run']]:
            folder=workspace/'runs/CALIB'/run_id
            for name in ['reservation.json','result.json','task_spec.json','e2_identity.json','horizon.json',
                         'policy_reset.json','reset_parity.json','artifact_manifest.json']:
                js(f'pairs/{run_id}/{name}',read(folder/name),[folder/name],'COMPLETE_SAFE_JSON')
            for name in ['physical_frames.jsonl','gate_decisions.jsonl','decisions.jsonl','snapshots.jsonl',
                         'gate_contact_views.jsonl','noninterference.jsonl','monitor_timing.jsonl','actual_requests.jsonl']:
                path=folder/name
                if path.is_file():jl(f'pairs/{run_id}/{name}',lines(path),path,'COMPLETE_SAFE_SEQUENCE_NOT_EVENT_ONLY')
            paths=sorted(folder.glob('action-*.npz'));actions=[]
            for path in paths:
                validate_numpy(path)
                with np.load(path,allow_pickle=False) as arr:
                    require(set(arr.files)==set(KEYS),'raw16 stream set')
                    actions.append(np.stack([arr[k] for k in KEYS]))
            buf=io.BytesIO();np.savez_compressed(buf,actions=np.stack(actions),
                decision_indices=np.arange(len(actions),dtype=np.int64))
            save(f'pairs/{run_id}/raw_actions.npz',buf.getvalue(),paths,'ALL_RAW_CHUNKS_AXES_DECISION_STREAM_BATCH16CHANNEL')
            for name in ['benchmark_init.npy','control_trace.npz']:
                validate_numpy(folder/name)
                save(f'pairs/{run_id}/{name}',(folder/name).read_bytes(),[folder/name],'UNCHANGED_COMPLETE_SAFE_NUMERIC_FILE')
            for path in sorted(folder.glob('prediction-*.json')):
                js(f'pairs/{run_id}/{path.name}',read(path),[path],'ALL_EXISTING_GATE_PREDICTIONS_NO_NEW_SIM')
            if (folder/'shadow_worker_exit.json').exists():
                js(f'pairs/{run_id}/shadow_worker_exit.json',read(folder/'shadow_worker_exit.json'),
                   [folder/'shadow_worker_exit.json'],'ACTUAL_WORKER_EXIT')
            for suffix in ['exit.started.json','exit.json']:
                path=workspace/'runs'/f'{run_id}.{suffix}'
                js(f'pairs/{run_id}/{suffix}',read(path),[path],'ACTUAL_CHILD_RECEIPT_COMMAND_PATHS_REDACTED')
        for entry in library:
            if entry['candidate_id'].rsplit('-d',1)[0]!=b0:continue
            case=workspace/'runs/CALIB_candidates'/entry['candidate_id']
            for name in ['result.json','contact_views.json','prediction.json','reservation.json','artifact_manifest.json']:
                js(f'candidates/{case.name}/{name}',read(case/name),[case/name],'ALL_FIXED_CANDIDATES_FROM_SELECTED_B0_SOURCES')
    # Exact first-onset crosscheck to the already public sparse event windows.
    old=read(repo/'reports/E2/calibration_first_event_windows.json')
    for prior in old['rows']:
        source=workspace/'runs/CALIB'/prior['run_id']
        require(read(source/'result.json')['first_wrong_lift_step']==prior['first_wrong_lift_step'],
                'previous published onset differs from original')
    js('raw_action_schema.json',dict(keys=KEYS,axes=['decision','stream','batch','horizon16','channel']),[],
       'RAW_ACTION_ARRAY_SCHEMA_NO_NATIVE_CONVERSION')
    js('previous_first_event_windows.json',old,[], 'UNCHANGED_PRIOR_PUBLIC_DERIVATIVE; SHA_BOUND_IN_MANIFEST')
    js('pair_audit.json',dict(pairs=selected_pairs,full_CALIB_pair_count=len(pair_audit['pairs'])),
       [workspace/'runs/CALIB'/p['b0_run']/'result.json' for p in selected_pairs],'SELECTED8_FULL_PAIRS; ALL24_REAUDITED_CPU')
    js('source_audit.json',checked,[workspace/'runs/CALIB_candidates/library_manifest.json'],'CPU_RECOMPUTE_NOT_INDEPENDENT_GPT_REVIEW')
    js('sampling_plan.json',plan,[],'COMMITTED_PRE_EXPORT_PLAN')
    origin(workspace/'runs/calibration-candidates-v1.exit.started.json');origin(workspace/'runs/calibration-candidates-v1.exit.json')
    for name in ['calibration-candidates-v1.exit.started.json','calibration-candidates-v1.exit.json']:
        path=workspace/'runs'/name;js(name,read(path),[path],'ACTUAL_EXISTING_CONTROLLER_EXIT_NO_NEW_MODEL')
    manifest=dict(scope='CALIB_CPU_DERIVATIVE_NOT_TEST_OR_INDEPENDENT_APPROVAL',export_code_sha=code,
        exporter_sha256=sha256(Path(__file__)),parent_head=plan['parent_head'],
        plan_sha256=sha256(repo/'configs/e2_calib_export_plan.json'),
        prior_event_windows_sha256=sha256(repo/'reports/E2/calibration_first_event_windows.json'),
        library_manifest_sha256=sha256(workspace/'runs/CALIB_candidates/library_manifest.json'),
        runtime_lock_sha256=sha256(repo/'configs/runtime_lock_E2.json'),candidate_rows=488,
        selected_pair_count=8,artifacts=records,source_files=sorted(origins.values(),key=lambda r:r['source_path']),
        unavailable=[],excluded=['unsafe pickle bytes (hashed only)','source XML','observations/images','full video','weights','private operator logs'],
        limitations='Predeclared CALIB sample, not blinded or independent TEST. Full raw byte manifests are supplied as lineage; excluded bytes remain private, not independently verified by GPT.',
        new_model_requests=0,new_simulations=0,TEST_opened=False)
    write_json(out/'manifest.json',manifest)
    return dict(files=len(records),bytes=sum(r['bytes'] for r in records),manifest_sha256=sha256(out/'manifest.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.workspace,a.repo,a.output)))
