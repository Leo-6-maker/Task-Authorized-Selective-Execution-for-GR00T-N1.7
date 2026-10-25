"""Mandatory4/6-cell physics/custody checkpoints; no new model call."""
import json,re
from pathlib import Path
import numpy as np
from .discovery import require,sha,digest
from .ledger import ROOTS,write,inventory

def original_inventory(workspace,folders):
    rows=[]
    for folder in folders:
        paths=list(folder.iterdir())+[workspace/'runs'/(folder.name+'.exit.json'),workspace/'runs'/(folder.name+'.exit.started.json')]
        for f in sorted(paths):
            require(f.is_file() and not f.is_symlink(),'missing/non-file E3 checkpoint original')
            rows.append(dict(path=str(f.relative_to(workspace)),bytes=f.stat().st_size,sha256=sha(f)))
    return rows

def require_backup(proof,rows):
    require(proof.get('status')=='TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED' and proof.get('original_files')==rows,'E3 checkpoint backup missing complete exact original coverage')
    a=proof.get('primary_archive_sha256');require(type(a) is str and re.fullmatch('[0-9a-f]{64}',a) and proof.get('secondary_archive_sha256')==a,'E3 checkpoint secondary whole archive identity differs')

def paired(baseline,other):
    for n in ['benchmark_init.npy','settled_state.npy','scene.xml','task_spec.json','horizon.json']:require(sha(baseline/n)==sha(other/n),'E3 paired scene/state/TaskSpec/init/horizon differs')
    def lines(f):return [json.loads(x) for x in f.read_text().splitlines()]
    bs={x['decision']:x for x in lines(baseline/'snapshots.jsonl')}
    for s in lines(other/'snapshots.jsonl'):
        i=s['decision'];require(s['snapshot_hash']==bs[i]['snapshot_hash'],'E3 paired native state/RNG differs')
        with np.load(baseline/f'action-{i:03d}.npz',allow_pickle=False) as b,np.load(other/f'action-{i:03d}.npz',allow_pickle=False) as g:require(set(b.files)==set(g.files) and all(np.array_equal(b[k],g[k]) for k in b.files),'E3 paired raw action differs')
    with np.load(baseline/'control_trace.npz',allow_pickle=False) as b,np.load(other/'control_trace.npz',allow_pickle=False) as g:
        n=len(g['converted_actions']);require(n<=len(b['converted_actions']) and all(np.array_equal(b[k][:n],g[k]) for k in ['states','converted_actions']),'E3 paired executed trajectory differs')

def build(workspace,repo,epoch,cells,identity,proof):
    from .audit import original
    from .ledger import audit
    root=workspace/'runs'/ROOTS[epoch];part=[c for c in cells if c['epoch']==epoch];entries=inventory(root,part);size=4 if epoch=='E3A' else 6;through=len(entries)
    require(through>0 and through%size==0,'complete original cluster required for checkpoint')
    checked=audit(root,part,lambda f,r:original(workspace,repo,f,r));require(checked['known']==through,'error/partial E3 cluster cannot release next')
    block=entries[-size:];rows=original_inventory(workspace,block);require_backup(proof,rows)
    group=part[through-size:through]
    for condition in ['C0','C2']:
        b=root/next(c['run_id'] for c in group if c['condition']==condition and c['system']=='B0')
        for c in group:
            if c['condition']==condition and c['system']!='B0':paired(b,root/c['run_id'])
    return dict(status='CPU_AUDITED_COMPLETE_CLUSTER_CHECKPOINT',epoch=epoch,through=through,authorization=identity,source_rows_sha256=digest(rows),source_rows=rows,two_copy_proof=proof,paired_state_action_physics_verified=True,worker_lifecycle_verified=True)

def require_previous(workspace,epoch,cells,identity):
    part=[c for c in cells if c['epoch']==epoch];entries=inventory(workspace/'runs'/ROOTS[epoch],part);count=len(entries);size=4 if epoch=='E3A' else 6
    if count and count%size==0:
        path=workspace/'operator/e3-checkpoints'/f'{epoch}-{count:04d}.json';value=json.loads(path.read_text());require(value['status']=='CPU_AUDITED_COMPLETE_CLUSTER_CHECKPOINT' and value['epoch']==epoch and value['through']==count and value['authorization']==identity and value['paired_state_action_physics_verified'] is True and value['worker_lifecycle_verified'] is True,'mandatory cluster checkpoint missing/different')
        rows=original_inventory(workspace,entries[-size:]);require(value['source_rows_sha256']==digest(rows) and value['source_rows']==rows,'originals changed after checkpoint');require_backup(value['two_copy_proof'],rows)
    if epoch=='E3B' and count==0:
        ap=[c for c in cells if c['epoch']=='E3A'];require(len(inventory(workspace/'runs/E3A_TEST',ap))==112,'E3-A must close before E3-B');require_previous(workspace,'E3A',cells,identity)
