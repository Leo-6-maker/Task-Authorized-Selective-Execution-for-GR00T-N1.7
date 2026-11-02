"""Exact archive custody; no inference, native imports or permission changes."""
import hashlib
import io
import json
from pathlib import Path
import tarfile

from .contract import require, sha
from .processes import write


def archive(workspace, stage, original_rows, extras, destination):
    workspace, destination = Path(workspace), Path(destination)
    require(not destination.exists(), 'exclusive new archive required')
    require(len({row['path'] for row in original_rows}) == len(original_rows),
            'duplicate original custody row')
    entries = {}
    for row in original_rows:
        path = Path(row['path'])
        require(not path.is_absolute() and '..' not in path.parts,
                'original custody path escapes workspace')
        f = workspace/path
        require(f.is_file() and not f.is_symlink() and f.stat().st_size == row['bytes'] and
                sha(f) == row['sha256'], 'original custody source changed')
        entries[str(path)] = f.read_bytes()
    for f in extras:
        f = Path(f)
        require(f.is_file() and not f.is_symlink(), 'non-regular archive extra')
        name = str(f.relative_to(workspace))
        b = f.read_bytes()
        require(name not in entries or entries[name] == b, 'archive key conflict')
        entries[name] = b
    rows = [dict(path=n, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
            for n, b in sorted(entries.items())]
    meta = dict(stage=stage, artifacts=rows, original_files=original_rows)
    with tarfile.open(destination, 'x:gz', compresslevel=1) as t:
        for name, b in {**entries, 'backup-manifest.json':
                        (json.dumps(meta, indent=2)+'\n').encode()}.items():
            item = tarfile.TarInfo(name)
            item.size, item.mode = len(b), 0o600
            t.addfile(item, io.BytesIO(b))
    destination.chmod(0o600)
    receipt = dict(stage=stage, bytes=destination.stat().st_size,
                   sha256=sha(destination), artifacts=len(rows), original_files=original_rows)
    verify_archive(destination, receipt)
    return receipt


def verify_archive(path, receipt):
    path = Path(path)
    require(path.stat().st_size == receipt['bytes'] and sha(path) == receipt['sha256'],
            'archive whole hash/size conflict')
    observed = {}
    meta = None
    with tarfile.open(path, 'r|gz') as t:
        for member in t:
            name = Path(member.name)
            require(member.isfile() and not name.is_absolute() and '..' not in name.parts,
                    'archive links or escaping paths refused')
            b = t.extractfile(member).read()
            if member.name == 'backup-manifest.json':
                require(meta is None, 'duplicate backup manifest')
                meta = json.loads(b)
            else:
                require(member.name not in observed, 'duplicate archive member')
                observed[member.name] = (len(b), hashlib.sha256(b).hexdigest())
    require(meta is not None and meta['stage'] == receipt['stage'] and
            len(meta['artifacts']) == len(observed) == receipt['artifacts'],
            'archive member set/identity differs')
    expected = {r['path']: (r['bytes'], r['sha256']) for r in meta['artifacts']}
    require(len(expected) == len(meta['artifacts']) and expected == observed,
            'exact archive manifest coverage/hash mismatch')
    require(meta['original_files'] == receipt['original_files'], 'original inventory changed')
    for row in receipt['original_files']:
        require(observed.get(row['path']) == (row['bytes'], row['sha256']),
                'original not actually archived')
    return meta


def second_copy(source, destination, receipt):
    """Transfer done elsewhere; no proof until destination bytes fully verified."""
    verify_archive(source, receipt)
    verify_archive(destination, receipt)
    require(Path(source).resolve() != Path(destination).resolve(), 'two distinct copies required')
    return dict(status='TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED',
                stage=receipt['stage'], original_files=receipt['original_files'],
                primary_archive_sha256=receipt['sha256'], secondary_archive_sha256=receipt['sha256'],
                archive_bytes=receipt['bytes'], actual_copied_artifacts=receipt['artifacts'],
                private_verification_by='EXECUTOR', independent_scientific_review=False)
