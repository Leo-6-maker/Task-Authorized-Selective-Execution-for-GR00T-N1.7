"""Future E3 one-shot native entry: new grant before any resource/process action."""
import argparse,json,os,subprocess,sys,signal
from pathlib import Path
from e3.authorization import authorize,resource
from e3.discovery import require,sha
from e3.ledger import reserve,write,ROOTS
from tase.e2_evidence import storage
from tase.resource_memory import require_free_memory
from e3.resource import binding,live_gpu1

def run(workspace,repo,run_id,review_commit,review_path,allocation_record,sim_python,server_session,port=5561):
    _,cells,identity=authorize(repo,review_commit,review_path)
    allocation=json.loads(allocation_record.read_text());resource(allocation,identity)
    workspace=workspace.resolve(strict=True);storage(workspace)
    from e3.scene import verify_inventory
    verify_inventory(workspace/'upstream/Isaac-GR00T/external_dependencies/LIBERO',json.loads((repo/'configs/e3_sources.proposed.json').read_text()))
    require(server_session.startswith('test-server-e3-') and all(c.isalnum() or c in '-_' for c in server_session),'new E3 server required')
    server=workspace/'runs'/server_session;admission=json.loads((server/'test_admission.json').read_text());require(admission['authorization']==identity and admission['allocation_sha256']==sha(allocation_record) and admission['port']==port,'E3 admitted server differs')
    require(not (workspace/'runs'/(server_session+'.exit.json')).exists() and (server/'loaded.json').is_file(),'E3 server closed/not loaded')
    start=json.loads((workspace/'runs'/(server_session+'.exit.started.json')).read_text());pid=start['child_pid'];proc=Path('/proc')/str(pid)
    require(proc.stat().st_uid==os.getuid() and [x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]==start['command'] and 'e3.server' in start['command'],'E3 server process not owned/exact')
    live=live_gpu1(allocation);require(live['gpu_uuid']==admission['gpu_uuid'] and admission['egl_device_id']=='1','E3 CUDA/EGL identity differs')
    cell=next((c for c in cells if c['run_id']==run_id),None);require(cell is not None,'unplanned E3 cell');epoch_cells=[c for c in cells if c['epoch']==cell['epoch']]
    # Every existing original must pass its historical versioned source audit.
    from e3.ledger import audit
    from e3.audit import original
    old=audit(workspace/'runs'/ROOTS[cell['epoch']],epoch_cells,lambda f,res:original(workspace,repo,f,res));require(old['consumed']==old['known'],'unclosed/error original blocks autonomous continuation')
    from e3.checkpoint import require_previous
    require_previous(workspace,cell['epoch'],cells,identity)
    folder=reserve(workspace/'runs'/ROOTS[cell['epoch']],cell,epoch_cells,identity);wrapper=None;failure=None
    try:
        up=workspace/'upstream/Isaac-GR00T';env=os.environ.copy();env.update(HOME=str(workspace/'runtime/home'),HF_HOME=str(workspace/'cache/huggingface'),LIBERO_CONFIG_PATH=str(workspace/'runtime/libero-config'),PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),CUDA_VISIBLE_DEVICES=allocation['gpu_uuid'],MUJOCO_EGL_DEVICE_ID=str(allocation['gpu_index']),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WANDB_MODE='disabled',WANDB_DISABLED='true',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',PYTHONNOUSERSITE='1',OPENBLAS_NUM_THREADS='1')
        binding(allocation,env)
        require(json.loads((sim_python.parent.parent/'e2-derived-environment.json').read_text())['workspace']==str(workspace),'non-owned fixed interpreter')
        cmd=[str(sim_python),'-u',str(repo/'scripts/record_process.py'),'--receipt',str(workspace/'runs'/(run_id+'.exit.json')),'--',str(sim_python),'-u','-m','e3.native_runner','--workspace',str(workspace),'--run-id',run_id,'--review-commit',review_commit,'--review-path',review_path,'--allocation-record',str(allocation_record),'--port',str(port)]
        write(folder/'supervisor_start.json',dict(run_id=run_id,server_session=server_session,server_loaded_sha256=sha(server/'loaded.json'),authorization=identity))
        logs=workspace/'operator'/('test-'+run_id);logs.mkdir()
        with (logs/'stdout.private.txt').open('x') as out,(logs/'stderr.private.txt').open('x') as err:
            wrapper=subprocess.Popen(cmd,cwd=repo,env=env,stdout=out,stderr=err,start_new_session=True)
            try:code=wrapper.wait(timeout=900)
            except subprocess.TimeoutExpired:
                wrapper.terminate();wrapper.wait(timeout=30);raise TimeoutError('E3 child deadline; consumed ID retained')
        require(code==0,'E3 native failure: stop and retain original ID');return code
    except BaseException as exc:failure=type(exc).__name__;raise
    finally:
        if wrapper is not None and wrapper.poll() is None:
            wrapper.terminate()
            try:wrapper.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(wrapper.pid,signal.SIGKILL);wrapper.wait(timeout=10);failure=failure or 'FORCED_OWNED_GROUP_KILL'
        write(folder/'supervisor_exit.json',dict(run_id=run_id,wrapper_returncode=None if wrapper is None else wrapper.poll(),failure_type=failure,complete_child_receipt=(workspace/'runs'/(run_id+'.exit.json')).is_file()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['workspace','repo','allocation-record','sim-python']:p.add_argument('--'+n,type=Path,required=True)
    for n in ['run-id','review-commit','review-path','server-session']:p.add_argument('--'+n,required=True)
    p.add_argument('--port',type=int,default=5561);a=p.parse_args();sys.exit(run(a.workspace,a.repo,a.run_id,a.review_commit,a.review_path,a.allocation_record,a.sim_python,a.server_session,a.port))
