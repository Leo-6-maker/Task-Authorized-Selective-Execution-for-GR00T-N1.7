"""Pinned TEST environment/model preflight. CPU hashes/metadata, no installation."""
import json
import subprocess
from pathlib import Path
from .test_authorization import require,git
from .evidence import sha256


def verify(workspace,repo,server_python,sim_python):
    lock=json.loads((repo/'configs/runtime_lock_E2.json').read_text())
    up=workspace/'upstream/Isaac-GR00T'
    require(git(up,'rev-parse','HEAD')==lock['upstream_sha'] and
            git(up/'external_dependencies/LIBERO','rev-parse','HEAD')==lock['libero_sha'],
            'TEST native revision differs')
    for path,digest in lock['source_sha256'].items():
        require(sha256(up/path)==digest,'TEST pinned upstream file differs: '+path)
    packages={}
    probe='import importlib.metadata as m,json,platform;print(json.dumps(dict(python=platform.python_version(),packages={d.metadata["Name"].lower().replace("_","-"):d.version for d in m.distributions()})))'
    for role,python in [('server',server_python),('sim',sim_python)]:
        require(python.is_file(),'isolated TEST interpreter missing')
        marker=python.parent.parent/'e2-derived-environment.json'
        require(json.loads(marker.read_text())['workspace']==str(workspace),'interpreter not task-owned E2 copy')
        observed=json.loads(subprocess.check_output([str(python),'-I','-c',probe],text=True))
        expected=lock['environments'][role]
        require(observed['python']==expected['python'],'TEST Python identity differs')
        for name,version in expected['packages'].items():
            require(observed['packages'].get(name.lower().replace('_','-'))==version,'TEST package differs: '+role+'/'+name)
        packages[role]=dict(python=observed['python'],verified_packages=len(expected['packages']),marker_sha256=sha256(marker))
    files=[]
    # Use the frozen E2 lock, not a mutable download receipt.
    expected_files=lock['object_files']
    for row in expected_files:
        path=workspace/'checkpoints'/row['path']
        require(path.stat().st_size==row['bytes'] and sha256(path)==row['sha256'],'TEST Object artifact differs')
        files.append(dict(model='Object',**{k:row[k] for k in ['path','bytes','sha256']}))
    cosmos=lock['cosmos_files']
    for row in cosmos['files']:
        path=workspace/'runtime/model-resolution/nvidia/Cosmos-Reason2-2B'/row['path']
        require(path.stat().st_size==row['bytes'] and sha256(path)==row['sha256'],'TEST Cosmos artifact differs')
        files.append(dict(model='Cosmos',**{k:row[k] for k in ['path','bytes','sha256']}))
    return dict(environments=packages,files=files,runtime_lock_sha256=sha256(repo/'configs/runtime_lock_E2.json'))
