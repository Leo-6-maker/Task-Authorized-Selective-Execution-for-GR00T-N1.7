"""Append-only TEST reservations; interrupted/empty folders still consume a cell."""
import json
from pathlib import Path
from .evidence import write_json, now_sgt, sha256
from .test_authorization import bind_cell, require


def inventory(root, cells):
    root = Path(root)
    if not root.exists():
        return []
    entries = sorted(p for p in root.iterdir() if p.name != '.reservation-lock')
    require(len(entries) <= 120, '120 TEST attempt budget exceeded')
    require([p.name for p in entries] == [c['run_id'] for c in cells[:len(entries)]],
            'unknown, duplicate, noncontiguous or reordered ledger entries; retain and investigate')
    for ordinal,folder in enumerate(entries,1):
        require(folder.is_dir() and not folder.is_symlink(), 'invalid TEST reservation folder')
        if (folder/'reservation.json').exists():
            record = json.loads((folder/'reservation.json').read_text())
            bind_cell(cells,folder.name,record)
            require(record['budget_ordinal'] == ordinal, 'TEST ordinal mismatch')
    return entries


def reserve(root, cell, cells, identity):
    root = Path(root)
    require(root.name == 'TEST', 'TEST ledger requires independent TEST root')
    require(not root.is_symlink(), 'TEST root must not redirect another checkout')
    bind_cell(cells,cell['run_id'],cell)
    require(identity['selected_k']==3 and identity['maximum_attempts']==120 and
            identity['authorized_head'] and identity['review_id'], 'validated GPT grant required')
    root.mkdir(parents=True,exist_ok=True)
    lock = root/'.reservation-lock'
    lock.mkdir()  # Never delete a pre-existing/stale lock.
    try:
        existing = inventory(root,cells)
        require(len(existing) < 120, '120 TEST attempts including failures exhausted')
        require(cell == cells[len(existing)], 'only next frozen cell may be reserved; no retries/replacement IDs')
        # A partially written reservation blocks further execution, while still consuming its slot.
        require(all((p/'reservation.json').is_file() and (p/'supervisor_exit.json').is_file()
                    for p in existing), 'unclosed TEST reservation; audit/reconcile before next cell')
        for previous in existing:
            closed=json.loads((previous/'supervisor_exit.json').read_text())
            if closed.get('complete_child_receipt') is not True:
                recovery=previous/'reconciliation.json'
                require(recovery.is_file(), 'partial TEST child requires explicit original-ID reconciliation')
                record=json.loads(recovery.read_text())
                require(record.get('run_id')==previous.name and
                        record.get('status')=='CLOSED_INTERRUPTED_NO_RETRY' and
                        record.get('reservation_sha256')==sha256(previous/'reservation.json') and
                        isinstance(record.get('reason'),str) and bool(record['reason']),
                        'invalid TEST reconciliation; never rerun or replace original ID')
        folder = root/cell['run_id']
        folder.mkdir()
        record = dict(cell, epoch='E2',protocol_id='TASE-002-v1.0',split='TEST',
            repo_sha=identity['authorized_head'],config_hash=identity['test_config_sha256'],
            runtime_lock_hash=identity['runtime_lock_sha256'],splits_hash=identity['splits_sha256'],
            calibration_selection_hash=identity['selection_sha256'],planned_init_hash=cell['init_hash'],
            authorization=identity,status='RESERVED',budget_ordinal=len(existing)+1,started_at_sgt=now_sgt())
        write_json(folder/'reservation.json',record)
        return folder
    finally:
        lock.rmdir()


def claim(folder, record):
    """Exclusive child admission before any native import/reset or model request."""
    require(json.loads((folder/'reservation.json').read_text()) == record, 'reservation changed')
    require(not (folder/'result.json').exists(), 'TEST result already exists')
    write_json(folder/'runner_claim.json',{'run_id':record['run_id'],'repo_sha':record['repo_sha'],
                                         'claimed_at_sgt':now_sgt()})
