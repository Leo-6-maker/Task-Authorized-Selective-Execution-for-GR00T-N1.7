"""One next fixed TEST cell, only after a separate GPT grant on fetched main.

Uses an already started, task-owned pinned native policy server. This entry
never starts/downloads/installs a model. The future authorized operator starts
the server after grant validation, retaining its record_process receipts.
Every attempt is reserved before spawning the native child. No implicit retry.
"""
import argparse
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256, write_json, now_sgt
from tase.test_authorization import authorize, bind_cell, require, git
from tase.test_ledger import reserve


def run(workspace, repo, run_id, review_commit, review_path, allocation_record,
        sim_python, server_session, port=5559):
    # MUST precede all runtime imports, process creation, GPU inspection and reservations.
    cfg,cells,identity = authorize(repo,review_commit,review_path)
    cell = bind_cell(cells,run_id)
    workspace = Path(workspace).resolve(strict=True)
    from tase.e2_evidence import storage
    storage(workspace)
    require(git(repo,'rev-parse','HEAD') == identity['authorized_head'], 'head changed during admission')
    allocation = json.loads(Path(allocation_record).read_text())
    require(allocation.get('shared_gpu_inference_authorized') is True, 'separate legal GPU allocation required')
    require(sim_python.is_file(), 'fixed isolated sim interpreter required')
    # The supplied server is an owned E2 server; no borrowing another project endpoint.
    require(server_session and all(c.isalnum() or c in '-_' for c in server_session), 'invalid server session')
    server = workspace/'runs'/server_session
    admission=json.loads((server/'test_admission.json').read_text())
    require(admission['authorization']==identity and admission['port']==port and
            admission['allocation_sha256']==sha256(allocation_record), 'server was not admitted under this TEST grant')
    loaded = json.loads((server/'loaded.json').read_text())
    require(loaded.get('status')=='MODEL_LOADED' and loaded.get('port')==port and
            loaded.get('host')=='127.0.0.1', 'recorded local native policy server required')
    server_start=json.loads((workspace/'runs'/f'{server_session}.exit.started.json').read_text())
    require('--epoch' in server_start['command'] and
            server_start['command'][server_start['command'].index('--epoch')+1]=='E2',
            'owned scenario-reset E2 server required')
    require((workspace/'runs'/f'{server_session}.exit.started.json').is_file() and
            not (workspace/'runs'/f'{server_session}.exit.json').exists(), 'server not recorded as running')
    up = workspace/'upstream/Isaac-GR00T'
    require(git(up,'rev-parse','HEAD') == 'dac54b313160c201c450f97df0fd74ebd379c892' and
            git(up/'external_dependencies/LIBERO','rev-parse','HEAD') ==
            '8f1084e3132a39270c3a13ebe37270a43ece2a01', 'pinned native source differs')
    require(not git(up,'status','--porcelain','--untracked-files=no'), 'native tracked source dirty')
    if not sim_python.absolute().is_relative_to(workspace):
        marker = json.loads((sim_python.parent.parent/'e2-derived-environment.json').read_text())
        require(marker['workspace']==str(workspace), 'interpreter is not task-owned E2')
    folder = reserve(workspace/'runs/TEST',cell,cells,identity)
    process=None
    failure=None
    received_signal=None
    def forward(signum,frame):
        nonlocal received_signal
        received_signal=signum
        if process is not None and process.poll() is None:
            process.send_signal(signum)
        else:
            raise InterruptedError('TEST entry interrupted before child start')
    old_handlers={sig:signal.signal(sig,forward) for sig in [signal.SIGTERM,signal.SIGINT]}
    try:
        env = os.environ.copy()
        env.update(HOME=str(workspace/'runtime/home'),HF_HOME=str(workspace/'cache/huggingface'),
            LIBERO_CONFIG_PATH=str(workspace/'runtime/libero-config'),
            PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
            PYTHONNOUSERSITE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            WANDB_DISABLED='true',WANDB_MODE='disabled',DO_NOT_TRACK='1',HF_HUB_DISABLE_TELEMETRY='1',
            OPENBLAS_NUM_THREADS='1')
        # EGL/CUDA binding is supplied by the legal allocation, never guessed here.
        require(bool(env.get('CUDA_VISIBLE_DEVICES')) and bool(env.get('MUJOCO_EGL_DEVICE_ID')),
                'explicit allocated CUDA/EGL binding required (reservation retained if missing)')
        require(env['CUDA_VISIBLE_DEVICES']==admission['gpu_uuid'] and
                env['MUJOCO_EGL_DEVICE_ID']==admission['egl_device_id'], 'TEST client/server GPU binding differs')
        env.update(MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl')
        cmd=[str(sim_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',
             str(workspace/'runs'/f'{run_id}.exit.json'),'--',str(sim_python),'-u','-m','tase.epoch_runner',
             '--workspace',str(workspace),'--run-id',run_id,'--task',cell['task'],
             '--init-index',str(cell['init_index']),'--condition',cell['condition'],'--system',cell['system'],
             '--config',str(repo/'configs/e2_test.json'),'--allocation-record',str(allocation_record),
             '--port',str(port),'--test-review-commit',review_commit,'--test-review-path',review_path]
        write_json(folder/'supervisor_start.json',dict(run_id=run_id,started_at_sgt=now_sgt(),
            server_session=server_session,server_loaded_sha256=sha256(server/'loaded.json'),
            sim_interpreter_marker_sha256=sha256(sim_python.parent.parent/'e2-derived-environment.json')))
        logs=workspace/'operator'/('test-'+run_id)
        logs.mkdir(parents=True)
        with (logs/'stdout.private.txt').open('x') as out,(logs/'stderr.private.txt').open('x') as err:
            process=subprocess.Popen(cmd,cwd=repo,env=env,stdout=out,stderr=err)
            try:
                code=process.wait(timeout=900)
            except subprocess.TimeoutExpired:
                process.terminate()
                code=process.wait(timeout=30)
                raise TimeoutError('TEST child wall deadline; no replacement; audit original ID')
        require(code==0, 'TEST child failed; retain original reservation and actual exit')
        return code
    except BaseException as exc:
        failure=type(exc).__name__
        raise
    finally:
        try:
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
        finally:
            for sig,handler in old_handlers.items():signal.signal(sig,handler)
            write_json(folder/'supervisor_exit.json',dict(run_id=run_id,completed_at_sgt=now_sgt(),
                wrapper_returncode=None if process is None else process.poll(),
                signal_received=received_signal,failure_type=failure,
                complete_child_receipt=(workspace/'runs'/f'{run_id}.exit.json').is_file()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','allocation-record','sim-python']:
        p.add_argument('--'+name,type=Path,required=True)
    for name in ['run-id','review-commit','review-path','server-session']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--port',type=int,default=5559)
    a=p.parse_args()
    return run(a.workspace,a.repo,a.run_id,a.review_commit,a.review_path,a.allocation_record,
               a.sim_python,a.server_session,a.port)


if __name__=='__main__':
    sys.exit(main())
