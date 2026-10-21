"""Append-only run reservations and byte-verifiable artifact identities."""
import hashlib
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone, timedelta


def now_sgt():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def append_json(path, value):
    line = json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n'
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def reserve_episode(root, run_id, metadata):
    """Reserve before imports/reset; failed and interrupted runs consume budget.

    A task-wide atomic directory lock prevents concurrent budget overbooking.
    A stale lock fails closed and requires operator investigation, never deletion.
    """
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', run_id):
        raise ValueError('invalid relative run ID')
    if metadata.get('split') != 'DEV':
        raise ValueError('only DEV is authorized')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.reservation-lock'
    lock.mkdir()
    try:
        existing = [p for p in root.iterdir() if p.is_dir() and p.name != lock.name]
        if len(existing) >= 24:
            raise RuntimeError('development episode budget exhausted (24)')
        folder = root / run_id
        folder.mkdir()
        write_json(folder / 'reservation.json', dict(metadata, run_id=run_id,
                   started_at_sgt=now_sgt(), status='STARTED', budget_ordinal=len(existing)+1))
    finally:
        lock.rmdir()
    return folder


def manifest(root, paths, source_run, visibility='private'):
    root = Path(root).resolve()
    records = []
    for item in paths:
        path = Path(item).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('artifact escapes root or is not a file')
        records.append({'artifact_id': path.relative_to(root).as_posix(),
                        'bytes': path.stat().st_size, 'sha256': sha256(path),
                        'source_run': source_run, 'visibility': visibility,
                        'verification': 'bytes_and_sha256'})
    return records


def verify_manifest(root, records):
    root = Path(root).resolve()
    for record in records:
        path = (root / record['artifact_id']).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError('manifest path escapes root')
        if path.stat().st_size != record['bytes'] or sha256(path) != record['sha256']:
            raise ValueError('artifact content mismatch: ' + record['artifact_id'])
