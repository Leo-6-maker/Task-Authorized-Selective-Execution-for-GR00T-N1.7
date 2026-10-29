"""Read-only E3 full native manifest coverage; not an execution authorization."""
import json
from pathlib import Path
from .discovery import require
from tase.e2_evidence import verify_manifest


def verify_complete_manifest(workspace, folder, required):
    """Check mandatory presence and the exact complete pre-close inventory.

    Native runner seals every file before writing artifact_manifest.json. The
    supervisor writes supervisor_exit.json only after that runner has exited;
    the ledger separately authenticates that later process receipt. Neither
    may be silently injected into the earlier runner manifest. All other native
    files must be manifest-covered, with their real size/hash/source identity.
    """
    workspace, folder = Path(workspace), Path(folder)
    entries = list(folder.iterdir())
    require(all(p.is_file() and not p.is_symlink() for p in entries),
            'E3 original directory contains non-file/symlink')
    names = {p.name for p in entries}
    require(set(required) <= names, 'complete E3 missing native originals')
    # Retain strict equality in the shared verifier. The mandatory subset is a
    # distinct check and must not be supplied as the complete original set.
    covered = {str(p.relative_to(workspace)) for p in entries
               if p.name not in {'artifact_manifest.json','supervisor_exit.json'}}
    records = json.loads((folder/'artifact_manifest.json').read_text())
    verify_manifest(workspace, records, covered, folder.name)

