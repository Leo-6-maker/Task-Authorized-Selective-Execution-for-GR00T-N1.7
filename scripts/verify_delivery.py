"""Verify public artifact bytes; private files remain unverified unless supplied."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import verify_manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=Path('reports/M2/artifact_manifest.json'))
    p.add_argument('--private-runtime',type=Path)
    p.add_argument('--private-operator',type=Path)
    p.add_argument('--private-audit',type=Path)
    p.add_argument('--private-m1',type=Path)
    p.add_argument('--private-bundle',type=Path)
    p.add_argument('--require-private',action='store_true',help='fail if any declared raw artifact is unavailable')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    data=json.loads(a.manifest.read_text())
    if not isinstance(data.get('artifacts'),list) or not data['artifacts']:
        raise ValueError('delivery manifest is empty')
    seen=set()
    for entry in data['artifacts']:
        identity=(entry['visibility'],entry['storage'],entry['artifact_id'])
        if identity in seen or entry['visibility'] not in ['public','private']:
            raise ValueError('duplicate or invalid delivery artifact')
        seen.add(identity)
    if a.require_private and not any(e['visibility']=='private' for e in data['artifacts']):
        raise ValueError('strict stage manifest has no private evidence')
    counts={'public_verified':0,'private_verified':0,'private_not_verified':0}
    for entry in data['artifacts']:
        if entry['visibility']=='public':
            location=root
        else:
            location={'runtime':a.private_runtime,'operator':a.private_operator,'audit':a.private_audit,
                      'm1-reference':a.private_m1,'bundle':a.private_bundle}.get(entry['storage'])
        if location is None:
            counts['private_not_verified']+=1
            continue
        verify_manifest(location,[entry])
        counts['public_verified' if entry['visibility']=='public' else 'private_verified']+=1
    print(json.dumps(counts,indent=2))
    if counts['private_not_verified']:
        print('Private contents: NOT_VERIFIED (only their declared identities are public).')
        if a.require_private:
            raise ValueError('strict stage audit requires all declared private evidence')


if __name__=='__main__':
    main()
