"""Export audited E2 numeric/media evidence without deserializing any pickle.

Private operator logs, source XML, credentials and model weights are excluded.
Derived JSON redactions and original byte hashes are explicit in the manifest.
The resulting private review archive still requires an actual reviewer read.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import audit
from tase.evidence import sha256,write_json,now_sgt


def validate_numpy(path):
    value=np.load(path,allow_pickle=False)
    try:
        arrays=[value[name] for name in value.files] if isinstance(value,np.lib.npyio.NpzFile) else [value]
        if any(array.dtype.kind not in 'biuf' or not np.isfinite(array).all() for array in arrays):
            raise ValueError('review export requires finite numeric arrays')
    finally:
        if isinstance(value,np.lib.npyio.NpzFile):value.close()


def redact(value,markers):
    if isinstance(value,dict):return {key:redact(item,markers) for key,item in value.items()}
    if isinstance(value,list):return [redact(item,markers) for item in value]
    if isinstance(value,str):
        for marker in sorted(set(markers),key=len,reverse=True):
            if marker:value=value.replace(marker,'<PRIVATE>')
        return re.sub(r'/(?:home|var/cache|mnt|media|srv)/[^\s\"\']+', '<PRIVATE_PATH>',value)
    return value


def export(workspace,destination,config,private_map):
    report=audit(workspace,config)
    destination.mkdir();records=[];markers=[str(workspace),str(Path.home())]
    if private_map:
        private=json.loads(private_map.read_text())
        markers += [private.get(key,'') for key in ['login_alias','compute_alias','home','home_resolved','workspace','workspace_resolved']]
    archive_path=destination/'review.tar.gz'
    originals=[]
    for folder in ['DEV','consistency']:
        originals += list((workspace/'runs'/folder).rglob('*'))
    for row in report['rows']:
        for suffix in ['exit.json','exit.started.json']:
            originals.append(workspace/'runs'/f"{row['run_id']}.{suffix}")
    with tarfile.open(archive_path,'x:gz') as archive:
        def add(name,data):
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o600
            archive.addfile(info,io.BytesIO(data))
        for path in sorted(set(originals)):
                if not path.is_file() or path.is_symlink():continue
                if path.suffix not in ['.json','.jsonl','.npz','.npy','.png','.mp4']:continue
                # No arbitrary path selection or pickle fallbacks for numeric data.
                if path.suffix in ['.npz','.npy']:validate_numpy(path)
                data=path.read_bytes();original=hashlib.sha256(data).hexdigest()
                if path.suffix=='.json':data=(json.dumps(redact(json.loads(data),markers),indent=2,allow_nan=False)+'\n').encode()
                if path.suffix=='.jsonl':data=(''.join(json.dumps(redact(json.loads(line),markers),allow_nan=False)+'\n' for line in data.splitlines() if line)).encode()
                name=path.relative_to(workspace).as_posix();add(name,data)
                records.append({'path':name,'original_sha256':original,'export_sha256':hashlib.sha256(data).hexdigest(),
                                'bytes':len(data),'derived_json':path.suffix in ['.json','.jsonl']})
        add('audit.json',(json.dumps(report,indent=2,allow_nan=False)+'\n').encode())
        add('protocol-config.json',config.read_bytes())
        manifest={'scope':'SAFE_NUMERIC_MEDIA_DERIVATIVE_NO_PICKLE_EXECUTION','created_at_sgt':now_sgt(),
            'artifacts':records,'source_dev_used':report['dev_used'],
            'all_process_receipts_complete':report['all_process_receipts_complete'],
            'excluded':'pickle, XML, text traceback, private operator logs, weights, credentials',
            'limitation':'Original complete-state byte audit ran in the trusted workspace; this archive alone cannot rerun the full original-file manifest audit. Reviewers can inspect numeric controls/frames/labels, media and process receipts without loading pickle.',
            'independent_review':'NOT_PERFORMED; owner must actually provide archive to reviewer'}
        add('review-manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
    receipt={'archive':'review.tar.gz','bytes':archive_path.stat().st_size,'sha256':sha256(archive_path),
             'artifacts':len(records),'source_dev_used':report['dev_used'],'independent_review':'NOT_PERFORMED'}
    write_json(destination/'receipt.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--config',type=Path,default=Path('configs/e2_dev.json'))
    p.add_argument('--private-map',type=Path);a=p.parse_args();print(json.dumps(export(a.workspace,a.output,a.config,a.private_map),indent=2))
