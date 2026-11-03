"""E2-only logical runs alias; legacy containment rules remain unchanged.

The concrete evidence directory must be inside the independently owned E2 cache.
Logical artifact IDs stay runs/... across a verified, closed-evidence migration.
"""
import json
import os
from pathlib import Path
from . import evidence


def storage(root):
    root=Path(root).resolve(strict=True)
    if not (root/'runs').is_symlink():return None
    record=json.loads((root/'operator/e2-storage-alias.json').read_text())
    cache=Path(record['cache_root']).resolve(strict=True)
    ownership=cache/'e2-cache-ownership.json';owner=json.loads(ownership.read_text())
    target=Path(record['target']).resolve(strict=True)
    if (record['epoch']!='E2' or Path(record['workspace']).resolve()!=root or
        owner['epoch']!='E2' or Path(owner['workspace']).resolve()!=root or
        ownership.stat().st_uid!=os.getuid() or cache.stat().st_uid!=os.getuid() or
        target.stat().st_uid!=os.getuid() or not target.is_relative_to(cache) or target==cache or
        evidence.sha256(ownership)!=record['ownership_marker_sha256'] or
        (root/'runs').resolve()!=target):
        raise ValueError('unverified external E2 evidence alias')
    return target


def identifier(value):
    if not isinstance(value,str) or not value.startswith('runs/') or '\\' in value or '..' in Path(value).parts:
        raise ValueError('E2 alias permits only logical runs artifact IDs')
    return value.removeprefix('runs/')


def manifest(root,paths,source_run,visibility='private'):
    root=Path(root).resolve(strict=True);target=storage(root)
    if target is None:return evidence.manifest(root,paths,source_run,visibility)
    concrete=[]
    for path in paths:
        logical=Path(path).absolute();relative=identifier(logical.relative_to(root).as_posix())
        actual=logical.resolve(strict=True)
        if actual!=target/relative or not actual.is_relative_to(target):raise ValueError('artifact escapes E2 storage')
        concrete.append(actual)
    rows=evidence.manifest(target,concrete,source_run,visibility)
    return [{**row,'artifact_id':'runs/'+row['artifact_id']} for row in rows]


def verify_manifest(root,records,required=None,source_run=None):
    root=Path(root).resolve(strict=True);target=storage(root)
    if target is None:return evidence.verify_manifest(root,records,required,source_run)
    mapped=[{**row,'artifact_id':identifier(row['artifact_id'])} for row in records]
    expected=None if required is None else {identifier(value) for value in required}
    return evidence.verify_manifest(target,mapped,expected,source_run)
