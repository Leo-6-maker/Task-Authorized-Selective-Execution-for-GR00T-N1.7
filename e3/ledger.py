"""Append-only E3 reservations, exclusive claim, full-denominator read-only audit."""
import json,os
from pathlib import Path
from .discovery import require,sha
from tase.evidence import now_sgt

FULL={'SUCCESS','TIME_LIMIT','SEMANTIC_ABORT'}
ROOTS={'E3A':'E3A_TEST','E3B':'E3B_TEST'}

def write(path,value):
    # Durable and exclusive: never overwrite a partial or successful receipt.
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def inventory(root,cells):
    root=Path(root)
    require(root.name in ROOTS.values() and not root.is_symlink(),'independent real E3 ledger root required')
    entries=sorted(p for p in root.iterdir() if p.name!='.reservation-lock') if root.exists() else []
    require([p.name for p in entries]==[c['run_id'] for c in cells[:len(entries)]],'unknown/duplicate/reordered E3 reservation; preserve and stop')
    for f,c in zip(entries,cells):
        require(f.is_dir() and not f.is_symlink(),'invalid E3 reservation directory')
        if (f/'reservation.json').exists():require(json.loads((f/'reservation.json').read_text())['cell']==c,'original reservation/cell mismatch')
    return entries

def reserve(root,cell,cells,identity):
    root=Path(root);require(root.name==ROOTS[cell['epoch']],'cross-study ledger refused')
    require(identity.get('grant_protocol')=='E3-001-v1.0' and identity.get('review_commit') and identity.get('authorized_head') and identity.get('budgets')=={'E3A':112,'E3B':48},'validated independent E3 identity required')
    require(len(cells)==identity['budgets'][cell['epoch']] and all(c['epoch']==cell['epoch'] for c in cells),'wrong epoch/budget')
    root.mkdir(parents=True,exist_ok=True);require(not root.is_symlink(),'redirected E3 ledger')
    lock=root/'.reservation-lock';lock.mkdir()
    try:
        entries=inventory(root,cells);require(len(entries)<len(cells) and cell==cells[len(entries)],'reserve only next original ID, never retry')
        for previous in entries:
            require((previous/'reservation.json').is_file() and (previous/'supervisor_exit.json').is_file() and (previous/'result.json').is_file(),'partial consumed E3 slot blocks new reservation')
            ex=json.loads((previous/'supervisor_exit.json').read_text());result=json.loads((previous/'result.json').read_text())
            require(ex.get('complete_child_receipt') is True and ex.get('wrapper_returncode')==0 and result.get('status') in FULL,'prior error requires independently reviewed same-ID reconciliation; never replace')
        folder=root/cell['run_id'];folder.mkdir();record=dict(cell=cell,authorization=identity,budget_ordinal=len(entries)+1,status='RESERVED',started_at_sgt=now_sgt());write(folder/'reservation.json',record);return folder
    finally:lock.rmdir()

def claim(folder,record):
    require(json.loads((folder/'reservation.json').read_text())==record and not (folder/'result.json').exists(),'original reservation/result already consumed or changed')
    write(folder/'runner_claim.json',dict(run_id=record['cell']['run_id'],reservation_sha256=sha(folder/'reservation.json'),authorization=record['authorization']))

def audit(root,cells,verify_original=None):
    entries=inventory(root,cells);rows=[]
    for ordinal,cell in enumerate(cells):
        present=ordinal<len(entries);folder=Path(root)/cell['run_id'];known=False;authenticated=False;result={};exitcode=None
        if present:
            if (folder/'reservation.json').exists():
                reservation=json.loads((folder/'reservation.json').read_text())
                if verify_original is not None:
                    verify_original(folder,reservation);authenticated=True
            if (folder/'result.json').exists():result=json.loads((folder/'result.json').read_text())
            if (folder/'supervisor_exit.json').exists():
                ex=json.loads((folder/'supervisor_exit.json').read_text());exitcode=ex.get('wrapper_returncode')
                known=ex.get('complete_child_receipt') is True and exitcode==0 and result.get('status') in FULL
            # A result cannot be eligible without version/original source verification.
            known=known and authenticated
        rows.append(dict(cell,reserved=present,outcome_known=known,status=result.get('status','INTERRUPTED_OR_PARTIAL' if present else 'NOT_STARTED'),actual_exit=exitcode,observed_wrong_lift=result.get('first_wrong_lift_step') is not None,official_success=result.get('official_success') is True))
    return dict(planned=len(cells),consumed=len(entries),unstarted=len(cells)-len(entries),known=sum(x['outcome_known'] for x in rows),unknown=sum(not x['outcome_known'] for x in rows),rows=rows)
