"""Stage closed E2 evidence on task-owned node storage, retaining the NFS copy.

All byte hashes and reservation IDs must agree before the logical runs path is
switched. No old checkout, record or lock is deleted. Active native jobs block.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json,now_sgt


def stage(root,cache,operation,resume=False):
    root=root.resolve(strict=True);cache=cache.resolve(strict=True)
    owner=json.loads((cache/'e2-cache-ownership.json').read_text())
    if owner['epoch']!='E2' or Path(owner['workspace']).resolve()!=root:raise ValueError('not the task-owned cache')
    if not operation or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in operation):
        raise ValueError('invalid operation ID')
    source=root/'runs'
    if source.is_symlink():raise ValueError('runs already staged; inspect existing evidence, do not repeat')
    if list(source.rglob('.reservation-lock')):raise RuntimeError('reservation lock exists; do not remove it')
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            if proc.stat().st_uid!=os.getuid():continue
            command=(proc/'cmdline').read_bytes().decode(errors='replace')
        except OSError:continue
        if str(root) in command and ('tase.server' in command or 'tase.epoch_runner' in command or 'e2_run_baseline.py' in command):
            raise RuntimeError('owned native execution still active; stage only after process exits')
    folder=root/'operator'/operation
    if not resume:folder.mkdir()
    destination=cache/operation;retained=root/('runs.network-copy-'+operation)
    if retained.exists() or (destination.exists() and not resume):raise FileExistsError('staging paths must be new')
    paths=sorted(p for p in source.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in paths):raise ValueError('unexpected symlink inside run evidence')
    if resume:
        before=json.loads((folder/'source-manifest.json').read_text())['artifacts']
        if not destination.is_dir():raise ValueError('resume requires the retained partial copy')
    else:
        before={str(p.relative_to(source)):{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in paths}
        write_json(folder/'source-manifest.json',{'created_at_sgt':now_sgt(),'artifacts':before})
        # NFS ACL metadata cannot always be copied to node storage. Preserve
        # scientific bytes and use private task-local modes, not foreign ACLs.
        previous_umask=os.umask(0o077)
        try:subprocess.run(['cp','-R','--reflink=auto','--no-preserve=mode,ownership,xattr',str(source),str(destination)],check=True,timeout=300)
        finally:os.umask(previous_umask)
    copied=sorted(p for p in destination.rglob('*') if p.is_file())
    if {str(p.relative_to(destination)) for p in copied}!=set(before):raise ValueError('copied file set differs')
    for path in copied:
        expected=before[str(path.relative_to(destination))]
        if path.stat().st_size!=expected['bytes'] or sha256(path)!=expected['sha256']:raise ValueError('evidence byte mismatch')
    # Recheck the source index to catch any concurrent writer before switching.
    if {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}!=set(before):raise ValueError('source changed during copy')
    for path in paths:
        if sha256(path)!=before[str(path.relative_to(source))]['sha256']:raise ValueError('source bytes changed during copy')
    write_json(root/'operator/e2-storage-alias.json',{'epoch':'E2','workspace':str(root),
        'cache_root':str(cache),'target':str(destination.resolve()),
        'ownership_marker_sha256':sha256(cache/'e2-cache-ownership.json')})
    source.rename(retained)
    try:source.symlink_to(destination,target_is_directory=True)
    except Exception:
        if not source.exists() and not source.is_symlink():retained.rename(source)
        raise
    receipt={'status':'ALL_RUN_FILES_VERIFIED_LOCAL_STAGE_NFS_COPY_RETAINED','artifacts':len(before),
        'resumed_existing_copy':resume,'source_acl_preservation_required':False,
        'dev_reservations':len(list((source/'DEV').glob('*/reservation.json'))),
        'source_retained':str(retained),'local_evidence':str(destination),'completed_at_sgt':now_sgt()}
    write_json(folder/'result.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--local-cache',type=Path,required=True);p.add_argument('--operation',required=True)
    p.add_argument('--resume-verified-copy',action='store_true')
    a=p.parse_args();print(json.dumps(stage(a.workspace,a.local_cache,a.operation,a.resume_verified_copy),indent=2))
