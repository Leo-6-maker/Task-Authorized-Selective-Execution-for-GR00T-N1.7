"""E3-only launcher using frozen exclusive native-output handshake."""
import argparse,json,os,socket,subprocess,sys
from pathlib import Path
from scripts.e2_test_server import _run_owned_server
from e3.authorization import authorize,resource
from e3.discovery import require,sha
from tase.test_runtime import verify
from tase.resource_memory import require_free_memory
def serve(workspace,repo,review_commit,review_path,allocation_record,server_python,sim_python,
          session,gpu_index,port=5561):
    _,_,identity=authorize(repo,review_commit,review_path)
    resource(json.loads(allocation_record.read_text()),identity)
    workspace=workspace.resolve(strict=True)
    require(session.startswith('test-server-e3-') and all(c.isalnum() or c in '-_' for c in session), 'TEST server session ID')
    allocation=json.loads(allocation_record.read_text())
    require(allocation.get('shared_gpu_inference_authorized') is True and allocation.get('gpu_index')==gpu_index,
            'explicit legal GPU allocation required')
    from e3.scene import verify_inventory
    verify_inventory(workspace/'upstream/Isaac-GR00T/external_dependencies/LIBERO',json.loads((repo/'configs/e3_sources.proposed.json').read_text()))
    verified=verify(workspace,repo,server_python,sim_python)
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True)
    selected=next(row.split(',') for row in inventory.splitlines() if int(row.split(',')[0])==gpu_index)
    require_free_memory(int(selected[2])*1024**2)
    require(allocation.get('gpu_uuid')==selected[1].strip(),'allocated GPU UUID differs')
    with socket.socket() as sock:sock.bind(('127.0.0.1',port))
    folder=workspace/'runs'/session
    admission=dict(authorization=identity,preflight=verified,port=port,
        gpu_uuid=selected[1].strip(),egl_device_id=str(gpu_index),allocation_sha256=sha(allocation_record))
    up=workspace/'upstream/Isaac-GR00T'
    env=os.environ.copy();env.update(HOME=str(workspace/'runtime/home'),HF_HOME=str(workspace/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(workspace/'runtime/libero-config'),
        PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
        CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_EGL_DEVICE_ID=str(gpu_index),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WANDB_MODE='disabled',WANDB_DISABLED='true',
        PYTHONNOUSERSITE='1',DO_NOT_TRACK='1',HF_HUB_DISABLE_TELEMETRY='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    command=[str(server_python),'-u','-m','e3.server',
        '--model',str(workspace/'checkpoints/libero_object'),'--output',str(folder),
        '--allocation-record',str(allocation_record),'--audit-rng','--epoch','E3','--port',str(port),'--repo',str(repo),'--review-commit',review_commit,'--review-path',review_path]
    return _run_owned_server(workspace,repo,server_python,session,admission,command,env)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','allocation-record','server-python','sim-python']:p.add_argument('--'+name,type=Path,required=True)
    for name in ['review-commit','review-path','session']:p.add_argument('--'+name,required=True)
    p.add_argument('--gpu-index',type=int,required=True);p.add_argument('--port',type=int,default=5561)
    a=p.parse_args();sys.exit(serve(a.workspace,a.repo,a.review_commit,a.review_path,a.allocation_record,
                                   a.server_python,a.sim_python,a.session,a.gpu_index,a.port))
