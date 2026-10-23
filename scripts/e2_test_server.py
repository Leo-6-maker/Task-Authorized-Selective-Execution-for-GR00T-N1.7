"""Future authorized TEST server lifecycle. NO grant => NO process/GPU inspection.

Never invoked by Issue10 delivery. Does not execute TEST cells; the per-cell
entry independently verifies the same grant and reserves the next fixed unit.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.test_authorization import authorize,require
from tase.test_runtime import verify
from tase.evidence import write_json,sha256


def serve(workspace,repo,review_commit,review_path,allocation_record,server_python,sim_python,
          session,gpu_index,port=5559):
    _,_,identity=authorize(repo,review_commit,review_path)
    workspace=workspace.resolve(strict=True)
    require(session.startswith('test-server-') and all(c.isalnum() or c in '-_' for c in session), 'TEST server session ID')
    allocation=json.loads(allocation_record.read_text())
    require(allocation.get('shared_gpu_inference_authorized') is True and allocation.get('gpu_index')==gpu_index,
            'explicit legal GPU allocation required')
    verified=verify(workspace,repo,server_python,sim_python)
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True)
    selected=next(row.split(',') for row in inventory.splitlines() if int(row.split(',')[0])==gpu_index)
    require(int(selected[2])>=16384,'insufficient free GPU memory; do not affect other tasks')
    require(allocation.get('gpu_uuid')==selected[1].strip(),'allocated GPU UUID differs')
    with socket.socket() as sock:sock.bind(('127.0.0.1',port))
    folder=workspace/'runs'/session;folder.mkdir()
    op=workspace/'operator'/session;op.mkdir()
    write_json(folder/'test_admission.json',dict(authorization=identity,preflight=verified,port=port,
        gpu_uuid=selected[1].strip(),egl_device_id=str(gpu_index),allocation_sha256=sha256(allocation_record)))
    up=workspace/'upstream/Isaac-GR00T'
    env=os.environ.copy();env.update(HOME=str(workspace/'runtime/home'),HF_HOME=str(workspace/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(workspace/'runtime/libero-config'),
        PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
        CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_EGL_DEVICE_ID=str(gpu_index),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WANDB_MODE='disabled',WANDB_DISABLED='true',
        PYTHONNOUSERSITE='1',DO_NOT_TRACK='1',HF_HUB_DISABLE_TELEMETRY='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    command=[str(server_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',
        str(workspace/'runs'/f'{session}.exit.json'),'--',str(server_python),'-u','-m','tase.server',
        '--model',str(workspace/'checkpoints/libero_object'),'--output',str(folder),
        '--allocation-record',str(allocation_record),'--audit-rng','--epoch','E2','--port',str(port)]
    with (op/'stdout.private.txt').open('x') as out,(op/'stderr.private.txt').open('x') as err:
        child=subprocess.Popen(command,cwd=workspace/'runtime/model-resolution',env=env,stdout=out,stderr=err)
        def forward(signum,frame):
            if child.poll() is None:child.send_signal(signum)
        old={sig:signal.signal(sig,forward) for sig in [signal.SIGTERM,signal.SIGINT]}
        try:
            code=child.wait()
        finally:
            if child.poll() is None:
                child.terminate();child.wait(timeout=30)
            for sig,handler in old.items():signal.signal(sig,handler)
            write_json(op/'supervisor_exit.json',dict(wrapper_returncode=child.returncode,TEST_cells_executed_by_server_launcher=0))
    return code


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','allocation-record','server-python','sim-python']:p.add_argument('--'+name,type=Path,required=True)
    for name in ['review-commit','review-path','session']:p.add_argument('--'+name,required=True)
    p.add_argument('--gpu-index',type=int,required=True);p.add_argument('--port',type=int,default=5559)
    a=p.parse_args();sys.exit(serve(a.workspace,a.repo,a.review_commit,a.review_path,a.allocation_record,
                                   a.server_python,a.sim_python,a.session,a.gpu_index,a.port))
