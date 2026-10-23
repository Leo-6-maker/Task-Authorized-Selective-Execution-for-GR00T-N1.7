"""Explicit fresh CALIB reservation; legacy DEV authorization is unchanged."""
from pathlib import Path
import re
from .evidence import write_json,now_sgt


def reserve_calibration(root,run_id,metadata):
    root=Path(root)
    if root.name!='CALIB' or metadata.get('split')!='CALIB' or metadata.get('epoch')!='E2' or metadata.get('protocol_id')!='TASE-002-v1.0':
        raise ValueError('only fresh E2 CALIB is authorized by this entry')
    if not re.fullmatch('e2-calib-[0-9]{4}',run_id):raise ValueError('invalid CALIB ID')
    if not all(re.fullmatch('[0-9a-f]{64}',metadata.get(k,'')) for k in ['splits_hash','calibration_plan_hash']):
        raise ValueError('commit split and candidate plan identities before CALIB')
    root.mkdir(parents=True,exist_ok=True);lock=root/'.reservation-lock';lock.mkdir()
    try:
        existing=[p for p in root.iterdir() if p.is_dir() and p!=lock]
        if len(existing)>=48:raise RuntimeError('48 CALIB attempts including failures exhausted')
        folder=root/run_id;folder.mkdir()
        write_json(folder/'reservation.json',dict(metadata,run_id=run_id,status='STARTED',started_at_sgt=now_sgt(),budget_ordinal=len(existing)+1))
    finally:lock.rmdir()
    return folder


def reserve_candidate(root,run_id,metadata):
    root=Path(root)
    if root.name!='CALIB_candidates' or metadata.get('split')!='CALIB' or metadata.get('epoch')!='E2' or metadata.get('protocol_id')!='TASE-002-v1.0':
        raise ValueError('only P4 fixed CALIB candidates are authorized here')
    if not re.fullmatch('e2-calib-[0-9]{4}-d[0-9]{3}',run_id) or not re.fullmatch('[0-9a-f]{64}',metadata.get('calibration_plan_hash','')):
        raise ValueError('candidate requires frozen CALIB identity')
    source,index=run_id.rsplit('-d',1)
    if not 1<=int(source.rsplit('-',1)[1])<=24 or not 0<=int(index)<90 or metadata.get('new_model_requests_permitted') is not False:
        raise ValueError('only one of24 B0 sources, at most90 windows, with zero policy requests')
    root.mkdir(parents=True,exist_ok=True);lock=root/'.reservation-lock';lock.mkdir()
    try:
        existing=[p for p in root.iterdir() if p.is_dir() and p!=lock]
        if len(existing)>=2160:raise RuntimeError('fixed24x90 functional prediction cap exhausted')
        folder=root/run_id;folder.mkdir()
        write_json(folder/'reservation.json',dict(metadata,run_id=run_id,status='STARTED',started_at_sgt=now_sgt(),budget_ordinal=len(existing)+1))
    finally:lock.rmdir()
    return folder
