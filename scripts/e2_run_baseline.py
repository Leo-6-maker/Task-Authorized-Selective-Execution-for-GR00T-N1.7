"""Run committed E2 DEV cells; default to the six C0 B0 baseline cells.

No TEST/CALIB or implicit retry. C2 requires P1; Gate requires recomputed P2.
Requires pinned artifacts; a credential is
only needed when verified Cosmos files are absent. Shuts down its own server.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import write_json,sha256


def run(root,token_file,gpu_index,port,session,server_python=None,sim_python=None,cell_ids=None,phase='DEV'):
    root=root.resolve(strict=True)
    if not session or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in session):
        raise ValueError('invalid server session ID')
    repo=root/'course-repo';up=root/'upstream/Isaac-GR00T'
    server_python=server_python or up/'.venv/bin/python'
    sim_python=sim_python or up/'gr00t/eval/sim/LIBERO/libero_uv/.venv/bin/python'
    if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():
        raise ValueError('commit code before runtime')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()!='dac54b313160c201c450f97df0fd74ebd379c892':
        raise ValueError('wrong upstream source')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=up/'external_dependencies/LIBERO',text=True).strip()!='8f1084e3132a39270c3a13ebe37270a43ece2a01':
        raise ValueError('wrong LIBERO source')
    for python in [server_python,sim_python]:
        if not python.is_file():raise ValueError('isolated runtime missing')
        if not python.absolute().is_relative_to(root):
            ownership=python.parent.parent/'e2-derived-environment.json'
            if not ownership.is_file() or json.loads(ownership.read_text())['workspace']!=str(root):
                raise ValueError('external runtime must be an independent task-owned E2 copy')
    if not (root/'runtime/libero-config/config.yaml').is_file():
        raise ValueError('isolated LIBERO configuration not prepared')
    if phase not in ['DEV','CALIB']:raise ValueError('TEST is not authorized')
    catalog=json.loads((repo/'configs'/('e2_dev_cells.json' if phase=='DEV' else 'e2_calib_cells.json')).read_text())
    cells=catalog['planned_cells'][:6] if phase=='DEV' else catalog['planned_cells'][:24]
    if cell_ids:
        declared={c['run_id']:c for c in catalog['planned_cells']+catalog.get('diagnostic_cells',[])}
        if len(set(cell_ids))!=len(cell_ids) or not set(cell_ids)<=set(declared):raise ValueError('undeclared or duplicate cells')
        cells=[declared[name] for name in cell_ids]
    if any(c['system'] not in ['B0','G'] for c in cells):raise ValueError('undeclared system')
    if any(c['system']=='G' for c in cells):
        audit_env=os.environ.copy();audit_env.update(CUDA_VISIBLE_DEVICES='-1',PYTHONNOUSERSITE='1')
        subprocess.run([str(sim_python),str(repo/'scripts/e2_audit_validation.py'),'--workspace',str(root),
            '--plan',str(repo/'configs/e2_shadow_plan.json'),'--output',str(root/'operator'/f'{session}.p2-audit.json')],
            cwd=repo,env=audit_env,check=True,stdout=subprocess.DEVNULL)
    if any((root/'runs'/phase/cell['run_id']).exists() for cell in cells):
        raise ValueError('baseline already started; audit existing IDs before explicit continuation')
    if any(c['condition']=='C2' for c in cells):
        # The lightweight operator interpreter need not contain NumPy. Audit
        # with the isolated sim Python, hiding GPUs and creating no environment.
        audit_path=root/'operator'/f'{session}.p1-audit.json'
        audit_env=os.environ.copy();audit_env.update(CUDA_VISIBLE_DEVICES='-1',PYTHONNOUSERSITE='1')
        subprocess.run([str(sim_python),str(repo/'scripts/audit_epoch.py'),'--workspace',str(root),
                        '--config',str(repo/'configs/e2_dev.json'),'--output',str(audit_path)],
                       cwd=repo,env=audit_env,check=True,stdout=subprocess.DEVNULL)
        checked=json.loads(audit_path.read_text());successes={}
        for row in checked['rows']:
            if row.get('condition')=='C0' and row.get('system')=='B0' and row['status']=='SUCCESS' and row['complete']:
                successes.setdefault(row['task'],set()).add(row['init_index'])
        if sum({0,1}<=indices for indices in successes.values())<2:
            raise ValueError('P1 needs at least two tasks completing both declared normal initializations')
        dev_catalog=json.loads((repo/'configs/e2_dev_cells.json').read_text())
        for cell in dev_catalog['planned_cells'][:6]:
            if not (root/'runs'/f"{cell['run_id']}.exit.json").exists():raise ValueError('close baseline attempts before C2')
    if phase=='CALIB':
        env_audit=os.environ.copy();env_audit.update(CUDA_VISIBLE_DEVICES='-1',PYTHONNOUSERSITE='1')
        subprocess.run([str(sim_python),str(repo/'scripts/e2_audit_pairs.py'),'--workspace',str(root),'--repo',str(repo),
            '--output',str(root/'operator'/f'{session}.p3-audit.json')],cwd=repo,env=env_audit,check=True,stdout=subprocess.DEVNULL)
    model=json.loads((root/'checkpoints/download_manifest.json').read_text())
    for row in model['files']:
        path=root/'checkpoints'/row['path']
        if sha256(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Object artifacts changed')
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True)
    selected=next(row.split(',') for row in inventory.splitlines() if int(row.split(',')[0])==gpu_index)
    if int(selected[2])<16384:raise RuntimeError('insufficient currently free memory; preserve other tasks')
    env=os.environ.copy();env.update(HOME=str(root/'runtime/home'),HF_HOME=str(root/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(root/'runtime/libero-config'),PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
        PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_GL='egl',
        PYOPENGL_PLATFORM='egl',MUJOCO_EGL_DEVICE_ID=str(gpu_index),WANDB_MODE='disabled',WANDB_DISABLED='true',
        HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',NO_ALBUMENTATIONS_UPDATE='1',TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='2',NUMBA_NUM_THREADS='2')
    if not (root/'operator/cosmos-download-manifest.json').is_file():
        if token_file is None:raise ValueError('verified Cosmos cache or owner credential file required')
        # This probes access with the actual server interpreter before any model load.
        subprocess.run([str(server_python),str(repo/'scripts/e2_download_cosmos.py'),'--workspace',str(root),
                        '--token-file',str(token_file)],cwd=repo,env=env,check=True)
    cosmos=json.loads((root/'operator/cosmos-download-manifest.json').read_text())
    expected=json.loads((repo/'configs/runtime_lock_m2.json').read_text())['auxiliary_model']
    fixed_files=[{key:row[key] for key in ['path','bytes','sha256']} for row in expected['files']]
    if cosmos['revision']!=expected['revision'] or cosmos['files']!=fixed_files:
        raise ValueError('Cosmos manifest does not match fixed identity')
    for row in cosmos['files']:
        path=root/'runtime/model-resolution/nvidia/Cosmos-Reason2-2B'/row['path']
        if path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:
            raise ValueError('Cosmos artifact changed')
    env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    permission=root/'runs/gpu-authorization.json'
    if not permission.exists():
        write_json(permission,{'shared_gpu_inference_authorized':True,'epoch':'E2','protocol_id':'TASE-002-v1.0',
            'authority':'Owner Issue #8 instruction and GPT R004; existing legal account only',
            'gpu_index':gpu_index,'gpu_uuid':selected[1].strip(),'fresh_free_mib':int(selected[2]),
            'exclusive_allocation':False})
    with socket.socket() as probe:probe.bind(('127.0.0.1',port))
    operator=root/'operator'/session;operator.mkdir()
    receipt=root/'runs'/f'{session}.exit.json'
    cmd=[str(server_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',str(receipt),'--',
        str(server_python),'-u','-m','tase.server','--model',str(root/'checkpoints/libero_object'),
        '--output',str(root/'runs'/session),'--allocation-record',str(permission),'--audit-rng','--epoch','E2','--port',str(port)]
    out=(operator/'stdout.txt').open('x');err=(operator/'stderr.txt').open('x')
    child=subprocess.Popen(cmd,cwd=root/'runtime/model-resolution',env=env,stdout=out,stderr=err)
    rows=[]
    try:
        deadline=time.monotonic()+180
        while not (root/'runs'/session/'loaded.json').exists():
            if child.poll() is not None:raise RuntimeError('policy startup failed; inspect captured child exit and logs')
            if time.monotonic()>deadline:raise TimeoutError('bounded policy load timeout')
            time.sleep(1)
        for index,cell in enumerate(cells):
            if cell['system'] not in ['B0','G'] or cell['condition'] not in ['C0','C2']:raise ValueError('DEV cell contract changed')
            run_id=cell['run_id'];folder=root/'operator'/run_id;folder.mkdir()
            command=[str(sim_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',str(root/'runs'/f'{run_id}.exit.json'),'--',
                str(sim_python),'-u','-m','tase.epoch_runner','--workspace',str(root),'--run-id',run_id,
                '--task',cell['task'],'--init-index',str(cell['init_index']),'--condition',cell['condition'],'--system',cell['system'],
                '--allocation-record',str(permission),'--port',str(port)]
            if phase=='CALIB':command.extend(['--config',str(repo/'configs/e2_calib.json')])
            if run_id=='e2-dev-0001':command.append('--verify-reset')
            with (folder/'stdout.txt').open('x') as stdout,(folder/'stderr.txt').open('x') as stderr:
                process=subprocess.Popen(command,cwd=repo,env=env,stdout=stdout,stderr=stderr)
                try:process.wait(timeout=900)
                except subprocess.TimeoutExpired:
                    # record_process forwards SIGTERM to its owned runner and
                    # retains the actual child exit. Never kill unrelated jobs.
                    process.terminate()
                    try:process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        raise RuntimeError('owned runner did not terminate; retain receipts and stop')
                    write_json(folder/'operator_timeout.json',{'timeout_seconds':900,
                        'wrapper_returncode':process.returncode})
                    raise
            result=json.loads((root/'runs'/phase/run_id/'result.json').read_text())
            rows.append({'run_id':run_id,'status':result['status'],'exit_code':process.returncode,
                         'inner_steps':result['inner_steps'],'official_success':result['official_success']})
            write_json(folder/'operator_exit.json',rows[-1]);print(json.dumps(rows[-1]),flush=True)
            if process.returncode:raise RuntimeError('baseline attempt failed; no implicit replacement')
    finally:
        if child.poll() is None:
            code="from gr00t.policy.server_client import PolicyClient;c=PolicyClient(host='127.0.0.1',port="+str(port)+",timeout_ms=5000);c.kill_server();c.close()"
            try:subprocess.run([str(server_python),'-c',code],cwd=repo,env=env,timeout=15,check=True)
            except Exception:
                # Only this owned process receives termination after shutdown failure.
                child.terminate()
        try:code=child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            child.terminate();code=child.wait(timeout=15)
        out.close();err.close()
        write_json(operator/'operator_exit.json',{'wrapper_returncode':code,'baseline_rows':rows})
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--token-file',type=Path);p.add_argument('--gpu-index',type=int,default=0);p.add_argument('--port',type=int,default=5559)
    p.add_argument('--session-id',required=True)
    p.add_argument('--server-python',type=Path);p.add_argument('--sim-python',type=Path)
    p.add_argument('--cells',nargs='+')
    p.add_argument('--phase',choices=['DEV','CALIB'],default='DEV')
    a=p.parse_args();run(a.workspace,a.token_file,a.gpu_index,a.port,a.session_id,a.server_python,a.sim_python,a.cells,a.phase)
