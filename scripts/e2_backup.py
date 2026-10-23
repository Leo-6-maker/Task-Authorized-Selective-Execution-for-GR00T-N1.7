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


def backup(workspace,stage):
    if not stage or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in stage):
        raise ValueError('invalid stage ID')
    destination=workspace/'evidence_exports'/stage;destination.mkdir()
    pending=destination/'evidence.tar.gz.pending';records=[]
    files=[]
    for base in [workspace/'runs',workspace/'operator']:
        files.extend(p for p in base.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix not in ['.bundle','.gz'])
    files.extend(p for p in [workspace/'runtime-map.local.yaml',workspace/'checkpoints/download_manifest.json'] if p.is_file())
    with tarfile.open(pending,'w:gz') as archive:
        for path in sorted(set(files)):
            relative=path.relative_to(workspace).as_posix();data=path.read_bytes()
            info=tarfile.TarInfo(relative);info.size=len(data);info.mode=0o600
            archive.addfile(info,io.BytesIO(data))
            records.append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        data=json.dumps({'stage':stage,'created_unix':time.time(),'artifacts':records},indent=2).encode()
        info=tarfile.TarInfo('backup-manifest.json');info.size=len(data);info.mode=0o600;archive.addfile(info,io.BytesIO(data))
    final=destination/'evidence.tar.gz';os.replace(pending,final)
    with final.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'stage':stage,'bytes':final.stat().st_size,'sha256':digest,'artifacts':len(records),
             'status':'PRIMARY_BACKUP_CREATED_SECOND_COPY_VERIFICATION_REQUIRED'}
    (destination/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--stage',required=True)
    a=p.parse_args();print(json.dumps(backup(a.workspace,a.stage),indent=2))
