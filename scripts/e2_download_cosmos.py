"""Fetch pinned official backbone using an owner-provided credential file.

Credential contents stay in process memory; no token is emitted or persisted.
Run with the new server Python after installation. No model/GPU is loaded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json,now_sgt


def run(workspace,credential):
    from huggingface_hub import hf_hub_download,snapshot_download
    reference=json.loads((Path(__file__).resolve().parents[1]/'configs/runtime_lock_m2.json').read_text())['auxiliary_model']
    token=credential.read_text().strip()
    if not token:raise ValueError('empty credential file')
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1';os.environ['DO_NOT_TRACK']='1'
    cache=workspace/'cache/huggingface/hub'
    # Actual server-environment small-file access probe precedes any weight fetch.
    hf_hub_download(reference['repo'],'config.json',revision=reference['revision'],cache_dir=cache,token=token)
    root=Path(snapshot_download(reference['repo'],revision=reference['revision'],cache_dir=cache,
        allow_patterns=[r['path'] for r in reference['files']],token=token,max_workers=2))
    records=[]
    for expected in reference['files']:
        path=root/expected['path'];digest=sha256(path)
        if path.stat().st_size!=expected['bytes'] or digest!=expected['sha256']:
            raise ValueError('pinned Cosmos artifact identity mismatch: '+expected['path'])
        records.append({'path':expected['path'],'bytes':path.stat().st_size,'sha256':digest})
    local=workspace/'runtime/model-resolution/nvidia/Cosmos-Reason2-2B';local.parent.mkdir(parents=True,exist_ok=True)
    if local.exists() or local.is_symlink():
        if local.resolve()!=root.resolve():raise ValueError('existing resolution differs; refusing overwrite')
    else:local.symlink_to(root.resolve(),target_is_directory=True)
    receipt={'repo':reference['repo'],'revision':reference['revision'],'files':records,
             'status':'PINNED_OFFICIAL_FILES_VERIFIED_NOT_MODEL_LOAD','recorded_at_sgt':now_sgt(),
             'credential_content_recorded':False}
    write_json(workspace/'operator/cosmos-download-manifest.json',receipt)
    print(json.dumps({'status':receipt['status'],'verified_files':len(records),'credential_contents_emitted':False}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--token-file',type=Path,required=True)
    a=p.parse_args();run(a.workspace,a.token_file)
