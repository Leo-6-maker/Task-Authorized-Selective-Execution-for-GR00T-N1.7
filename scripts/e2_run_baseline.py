"""Run the six committed E2 C0 baseline cells in the isolated workspace.

No TEST/CALIB/C2 or implicit retry. Requires pinned artifacts and an owner-issued
Cosmos credential file. Always shuts down this script's own policy server.
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


def run(root,token_file,gpu_index,port,session):
    root=root.resolve(strict=True)
    if not session or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in session):
        raise ValueError('invalid server session ID')
    repo=root/'course-repo';up=root/'upstream/Isaac-GR00T'
    server_python=up/'.venv/bin/python';sim_python=up/'gr00t/eval/sim/LIBERO/libero_uv/.venv/bin/python'
    if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():
        raise ValueError('commit code before runtime')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()!='dac54b313160c201c450f97df0fd74ebd379c892':
        raise ValueError('wrong upstream source')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=up/'external_dependencies/LIBERO',text=True).strip()!='8f1084e3132a39270c3a13ebe37270a43ece2a01':
        raise ValueError('wrong LIBERO source')
    for python in [server_python,sim_python]:
        if not python.is_file():raise ValueError('isolated runtime missing')
    if not (root/'runtime/libero-config/config.yaml').is_file():
        raise ValueError('isolated LIBERO configuration not prepared')
    cells=json.loads((repo/'configs/e2_dev_cells.json').read_text())['planned_cells'][:6]
    if any((root/'runs/DEV'/cell['run_id']).exists() for cell in cells):
        raise ValueError('baseline already started; audit existing IDs before explicit continuation')
    model=json.loads((root/'checkpoints/download_manifest.json').read_text())
    for row in model['files']:
        path=root/'checkpoints'/row['path']
        if sha256(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Object artifacts changed')
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True)
    selected=next(row.split(',') for row in inventory.splitlines() if int(row.split(',')[0])==gpu_index)
    if int(selected[2])<16384:raise RuntimeError('insufficient currently free memory; preserve other tasks')
    env=os.environ.copy();env.update(HOME=str(root/'runtime/home'),HF_HOME=str(root/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(root/'runtime/libero-config'),PYTHONPATH=str(repo)+os.pathsep+str(up),
        PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_GL='egl',
        PYOPENGL_PLATFORM='egl',MUJOCO_EGL_DEVICE_ID=str(gpu_index),WANDB_MODE='disabled',WANDB_DISABLED='true',
        HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',NO_ALBUMENTATIONS_UPDATE='1',TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='2',NUMBA_NUM_THREADS='2')
    if not (root/'operator/cosmos-download-manifest.json').is_file():
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
            if cell['system']!='B0' or cell['condition']!='C0':raise ValueError('baseline list changed')
            run_id=cell['run_id'];folder=root/'operator'/run_id;folder.mkdir()
            command=[str(sim_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',str(root/'runs'/f'{run_id}.exit.json'),'--',
                str(sim_python),'-u','-m','tase.epoch_runner','--workspace',str(root),'--run-id',run_id,
                '--task',cell['task'],'--init-index',str(cell['init_index']),'--condition','C0','--system','B0',
                '--allocation-record',str(permission),'--port',str(port)]
            if index==0:command.append('--verify-reset')
            with (folder/'stdout.txt').open('x') as stdout,(folder/'stderr.txt').open('x') as stderr:
                process=subprocess.Popen(command,cwd=repo,env=env,stdout=stdout,stderr=stderr)
                try:process.wait(timeout=360)
                except subprocess.TimeoutExpired:
                    # record_process forwards SIGTERM to its owned runner and
                    # retains the actual child exit. Never kill unrelated jobs.
                    process.terminate()
                    try:process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        raise RuntimeError('owned runner did not terminate; retain receipts and stop')
                    write_json(folder/'operator_timeout.json',{'timeout_seconds':360,
                        'wrapper_returncode':process.returncode})
                    raise
            result=json.loads((root/'runs/DEV'/run_id/'result.json').read_text())
            rows.append({'run_id':run_id,'status':result['status'],'exit_code':process.returncode,
                         'inner_steps':result['inner_steps'],'official_success':result['official_success']})
            write_json(folder/'operator_exit.json',rows[-1]);print(json.dumps(rows[-1]),flush=True)
            if process.returncode:raise RuntimeError('baseline attempt failed; no implicit replacement')
    finally:
        if child.poll() is None:
            code="from gr00t.policy.server_client import PolicyClient;c=PolicyClient(host='127.0.0.1',port="+str(port)+",timeout_ms=5000);c.call_endpoint('shutdown',requires_input=False);c.close()"
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
    p.add_argument('--token-file',type=Path,required=True);p.add_argument('--gpu-index',type=int,default=0);p.add_argument('--port',type=int,default=5559)
    p.add_argument('--session-id',required=True)
    a=p.parse_args();run(a.workspace,a.token_file,a.gpu_index,a.port,a.session_id)
