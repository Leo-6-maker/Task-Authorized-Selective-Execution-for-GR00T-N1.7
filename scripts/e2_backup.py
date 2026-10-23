"""Create a new hash-indexed evidence backup, never weights or caches.

Active install logs may be captured as a progress snapshot; finalized experiment
files must be backed up after child exit. A second location verifies archive hash.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import time


def backup(workspace,stage,base_stage=None):
    if not stage or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in stage):
        raise ValueError('invalid stage ID')
    base=None;previous={}
    if base_stage:
        if base_stage==stage or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in base_stage):
            raise ValueError('invalid base stage')
        base_dir=workspace/'evidence_exports'/base_stage
        receipt=json.loads((base_dir/'receipt.json').read_text());verified=json.loads((base_dir/'second-copy-verification.json').read_text())
        if verified['status']!='TWO_LOCATIONS_ARCHIVE_AND_EVERY_MEMBER_SHA256_VERIFIED' or any(verified[k]!=receipt[k] for k in ['bytes','sha256']):
            raise ValueError('incremental base must already have two independently verified copies')
        with (base_dir/'evidence.tar.gz').open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=receipt['sha256']:raise ValueError('base archive changed')
        with tarfile.open(base_dir/'evidence.tar.gz','r:gz') as archive:
            old=json.load(archive.extractfile('backup-manifest.json'))
        previous={r['path']:r for r in old.get('source_index',old['artifacts'])}
        base={'stage':base_stage,'bytes':receipt['bytes'],'sha256':receipt['sha256']}
    destination=workspace/'evidence_exports'/stage;destination.mkdir()
    pending=destination/'evidence.tar.gz.pending';records=[];source_index=[]
    files=[]
    for base in [workspace/'runs',workspace/'operator']:
        files.extend(p for p in base.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix not in ['.bundle','.gz'])
    files.extend(p for p in [workspace/'runtime-map.local.yaml',workspace/'checkpoints/download_manifest.json'] if p.is_file())
    with tarfile.open(pending,'w:gz') as archive:
        for path in sorted(set(files)):
            relative=path.relative_to(workspace).as_posix();data=path.read_bytes()
            record={'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            source_index.append(record)
            if previous.get(relative)==record:continue
            info=tarfile.TarInfo(relative);info.size=len(data);info.mode=0o600
            archive.addfile(info,io.BytesIO(data))
            records.append(record)
        data=json.dumps({'stage':stage,'created_unix':time.time(),'artifacts':records,
                         'source_index':source_index,'base_archive':base},indent=2).encode()
        info=tarfile.TarInfo('backup-manifest.json');info.size=len(data);info.mode=0o600;archive.addfile(info,io.BytesIO(data))
    final=destination/'evidence.tar.gz';os.replace(pending,final)
    with final.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'stage':stage,'bytes':final.stat().st_size,'sha256':digest,'artifacts':len(records),
             'status':'PRIMARY_BACKUP_CREATED_SECOND_COPY_VERIFICATION_REQUIRED'}
    if base:receipt.update(base_archive=base,source_artifacts=len(source_index),unchanged_in_verified_base=len(source_index)-len(records))
    (destination/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--stage',required=True)
    p.add_argument('--base-stage')
    a=p.parse_args();print(json.dumps(backup(a.workspace,a.stage,a.base_stage),indent=2))
