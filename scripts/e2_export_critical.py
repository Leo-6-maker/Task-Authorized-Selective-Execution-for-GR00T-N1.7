"""Small public-safe DEV mechanism tables, finite arrays and event figure.

Two illustrative pairs are explicitly selected; all planned outcomes remain in
the complete public tables. No pickle, source XML or operator log is exported.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def export(workspace,repo,destination):
    sys.path.insert(0,str(repo))
    import numpy as np
    from scripts.audit_epoch import audit,read,lines
    from scripts.e2_export_review import validate_numpy,redact
    from tase.evidence import sha256,write_json
    checked=audit(workspace,repo/'configs/e2_dev.json');destination.mkdir();records=[]
    markers=[str(workspace),str(Path.home())]
    def save(source,name,data,selection):
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records.append({'export_path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'source_path':source.relative_to(workspace).as_posix(),'source_file_sha256':sha256(source),'selection':selection})
    for source_id,decision_count in [('e2-dev-0001',18),('e2-dev-0013',18),('e2-dev-0009',8),('e2-dev-0017',8)]:
        source=workspace/'runs/DEV'/source_id
        for name in ['result.json','reservation.json','task_spec.json','e2_identity.json','horizon.json','policy_reset.json','reset_parity.json']:
            value=redact(read(source/name),markers)
            save(source/name,source_id+'/'+name,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode(),'COMPLETE_REDACTED_JSON')
        for name in ['gate_decisions.jsonl','decisions.jsonl','snapshots.jsonl','gate_contact_views.jsonl','noninterference.jsonl','monitor_timing.jsonl']:
            path=source/name
            if not path.exists():continue
            selected=[r for r in lines(path) if r.get('index',r.get('decision',0))<decision_count]
            save(path,source_id+'/'+name,(''.join(json.dumps(redact(r,markers),allow_nan=False)+'\n' for r in selected)).encode(),'FIRST_'+str(decision_count)+'_DECISIONS')
        path=source/'physical_frames.jsonl';frames=lines(path)
        selected=[r for r in frames if 49<=r['step']<=72] if source_id in ['e2-dev-0009','e2-dev-0017'] else [r for r in frames if r['step']<=8 or r['step']>len(frames)-8]
        save(path,source_id+'/physical_frames_subset.jsonl',(''.join(json.dumps(r,allow_nan=False)+'\n' for r in selected)).encode(),'C2_CONTROLS_49_72_OR_NORMAL_FIRST_LAST8')
        for index in range(decision_count):
            path=source/f'action-{index:03d}.npz';validate_numpy(path)
            save(path,source_id+'/'+path.name,path.read_bytes(),'SAME_RAW_FINITE_NUMERIC_ARRAY_FILE')
        path=source/'control_trace.npz';validate_numpy(path)
        save(path,source_id+'/control_trace.npz',path.read_bytes(),'COMPLETE_MAIN_CONTROLLER_INPUT_AND_INTEGRATION_STATE_ARRAYS')
        for index in ([0,decision_count-1] if source_id=='e2-dev-0013' else [6,7] if source_id=='e2-dev-0017' else []):
            path=source/f'prediction-{index:03d}.json'
            save(path,source_id+'/'+path.name,(json.dumps(redact(read(path),markers),indent=2,allow_nan=False)+'\n').encode(),'SELECTED_PREDICTION_PREFIX')
        for suffix in ['exit.json','exit.started.json']:
            path=workspace/'runs'/f'{source_id}.{suffix}'
            save(path,source_id+'/'+suffix,(json.dumps(redact(read(path),markers),indent=2,allow_nan=False)+'\n').encode(),'REDACTED_PROCESS_RECEIPT')
    figure=workspace/'operator/challenge-media-20/first-event-contact-sheet.png'
    save(figure,'first-event-contact-sheet.png',figure.read_bytes(),'DECODED_SOURCE_VIDEO_FRAMES_WITH_CONTROL_LABELS_NO_GENERATED_CONTENT')
    result={'scope':'SMALL_NUMERIC_DEV_MECHANISM_DERIVATIVE_NOT_FULL_RAW_REPLAY_OR_TEST',
        'source_dev_attempts_including_failures':checked['dev_used'],'selected_pairs':[['e2-dev-0001','e2-dev-0013'],['e2-dev-0009','e2-dev-0017']],
        'excluded':'pickle, XML, weights, credentials, private operator logs, full videos, most observations/predictions',
        'limitation':'Original byte audit ran against complete trusted originals. This selected derivative cannot rerun the complete source artifact manifests or establish population-level performance. Full outcomes are in gate_dev_pairs and the complete ledger.',
        'exporter_sha256':sha256(Path(__file__)),'artifacts':records,'independent_review':'NOT_PERFORMED'}
    write_json(destination/'manifest.json',result)
    return {'files':len(records),'bytes':sum(r['bytes'] for r in records),'manifest_sha256':sha256(destination/'manifest.json')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.workspace,a.repo,a.output),indent=2))
