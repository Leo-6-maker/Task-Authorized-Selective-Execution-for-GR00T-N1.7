"""Download only the authorized Object inference artifacts, then verify LFS hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

REPO = 'nvidia/GR00T-N1.7-LIBERO'
REVISION = '2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21'
FILES = ['config.json', 'embodiment_id.json',
         'model-00001-of-00002.safetensors', 'model-00002-of-00002.safetensors',
         'model.safetensors.index.json', 'processor_config.json', 'statistics.json']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    # huggingface_hub is an installer dependency, never supplied a private token.
    from huggingface_hub import snapshot_download
    args.destination.mkdir(parents=True, exist_ok=True)
    endpoint = f'https://huggingface.co/api/models/{REPO}/tree/{REVISION}/libero_object'
    with urllib.request.urlopen(endpoint, timeout=60) as response:
        listing = json.load(response)
    selected = {item['path'].split('/')[-1]: item for item in listing
                if item['path'].split('/')[-1] in FILES}
    if set(selected) != set(FILES):
        raise ValueError('required Object files missing')
    snapshot_download(REPO, revision=REVISION, local_dir=args.destination,
                      allow_patterns=['libero_object/' + f for f in FILES],
                      max_workers=2)
    records = []
    for name in FILES:
        path = args.destination / 'libero_object' / name
        digest = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
        expected = selected[name].get('lfs', {}).get('oid')
        if expected and digest != expected:
            raise ValueError('LFS digest mismatch: ' + name)
        if path.stat().st_size != selected[name]['size']:
            raise ValueError('size mismatch: ' + name)
        records.append({'path': 'libero_object/' + name, 'bytes': path.stat().st_size,
                        'sha256': digest, 'upstream_lfs_sha256': expected})
    receipt = {'repo': REPO, 'revision': REVISION, 'files': records,
               'status': 'VERIFIED_DOWNLOAD_NOT_RUNTIME_VALIDATED'}
    target = args.destination / 'download_manifest.json'
    with target.open('x') as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
