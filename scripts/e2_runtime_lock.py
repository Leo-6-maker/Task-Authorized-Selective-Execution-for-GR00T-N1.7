"""Capture E2 source/dependency/model identity without loading policy or sim."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json,now_sgt


def environment(python):
    if not python.is_file():return {'status':'NOT_INSTALLED'}
    code="import sys,json,importlib.metadata as m;print(json.dumps({'python':sys.version.split()[0],'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))"
    proc=subprocess.run([str(python),'-c',code],capture_output=True,text=True,timeout=30)
    return json.loads(proc.stdout) if proc.returncode==0 else {'status':'ERROR','exit_code':proc.returncode}


def capture(root):
    upstream=root/'upstream/Isaac-GR00T';repo=root/'course-repo'
    git=lambda path,*args:subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
    sources=['pyproject.toml','uv.lock','gr00t/policy/gr00t_policy.py','gr00t/policy/server_client.py',
             'gr00t/eval/_horizon_contract.py','gr00t/eval/sim/LIBERO/libero_env.py',
             'gr00t/eval/sim/wrapper/multistep_wrapper.py']
    server=upstream/'.venv/bin/python';sim=upstream/'gr00t/eval/sim/LIBERO/libero_uv/.venv/bin/python'
    record={'epoch':'E2','protocol_id':'TASE-002-v1.0','captured_at_sgt':now_sgt(),
        'scope':'IDENTITY_ONLY_NOT_RUNTIME_ACCEPTANCE','repo_sha':git(repo,'rev-parse','HEAD'),
        'upstream_sha':git(upstream,'rev-parse','HEAD'),
        'libero_sha':git(upstream/'external_dependencies/LIBERO','rev-parse','HEAD'),
        'source_sha256':{p:sha256(upstream/p) for p in sources},
        'upstream_tracked_diff':git(upstream,'diff','--stat'),
        'environments':{'server':environment(server),'sim':environment(sim)},
        'model_revision':'2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21',
        'cosmos_revision':'9ce19a195e423419c349abfc86fd07178b230561',
        'object_files':None,'cosmos_files':None,'dev_cap':24,'consistency_cap':96,'conditional_calib_cap':48,
        'test_authorized':False,'legacy_raw':'TEMPORARILY_UNAVAILABLE / NOT_INDEPENDENTLY_VERIFIED'}
    manifest=root/'checkpoints/download_manifest.json'
    if manifest.is_file():
        receipt=json.loads(manifest.read_text());verified=[]
        for row in receipt['files']:
            path=root/'checkpoints'/row['path']
            if path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:raise ValueError('Object identity mismatch')
            verified.append(row)
        record['object_files']=verified
    cosmos=root/'operator/cosmos-download-manifest.json'
    if cosmos.is_file():record['cosmos_files']=json.loads(cosmos.read_text())
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();record=capture(a.workspace);write_json(a.output,record)
    print(json.dumps({'scope':record['scope'],'object_files_verified':record['object_files'] is not None,'cosmos_record_present':record['cosmos_files'] is not None}))
