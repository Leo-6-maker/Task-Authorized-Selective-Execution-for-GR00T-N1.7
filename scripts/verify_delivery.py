"""Verify public artifact bytes; private files remain unverified unless supplied."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import verify_manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=Path('reports/M1/artifact_manifest_resume.json'))
    p.add_argument('--private-runtime',type=Path)
    p.add_argument('--private-operator',type=Path)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    data=json.loads(a.manifest.read_text())
    counts={'public_verified':0,'private_verified':0,'private_not_verified':0}
    for entry in data['artifacts']:
        if entry['visibility']=='public':
            location=root
        else:
            location={'runtime':a.private_runtime,'operator':a.private_operator}.get(entry['storage'])
        if location is None:
            counts['private_not_verified']+=1
            continue
        verify_manifest(location,[entry])
        counts['public_verified' if entry['visibility']=='public' else 'private_verified']+=1
    print(json.dumps(counts,indent=2))
    if counts['private_not_verified']:
        print('Private contents: NOT_VERIFIED (only their declared identities are public).')


if __name__=='__main__':
    main()
