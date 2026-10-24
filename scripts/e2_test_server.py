"""Future authorized TEST server lifecycle. NO grant => NO process/GPU inspection.

Never invoked by Issue10 delivery. Does not execute TEST cells; the per-cell
entry independently verifies the same grant and reserves the next fixed unit.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import stat
import time
import hashlib
import socket
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.test_authorization import authorize,require
from tase.test_runtime import verify
from tase.evidence import write_json,sha256


def _owned_directory(path):
    value=path.lstat()
    require(stat.S_ISDIR(value.st_mode) and value.st_uid==os.getuid(),
            'server path must be a real task-owner directory')
    return value


def _absent(path):
    require(not os.path.lexists(path), 'server output/receipt already exists; never reuse or remove it')


def _output_argument(command, folder):
    require(command.count('--output')==1 and command.index('--output')+1<len(command) and
            command[command.index('--output')+1]==str(folder), 'native child output command differs')


def _complete_json(path):
    # Native write_json opens exclusively before its buffered JSON is flushed.
    # Incomplete bytes may be observed; never accept them or wait past deadline.
    try:return json.loads(path.read_text())
    except json.JSONDecodeError:return None


def _process_identity(start, process, command, previous=None):
    require(type(start.get('child_pid')) is int and start['child_pid']>0 and
            start.get('wrapper_pid')==process.pid and start.get('command')==command,
            'native child PID/wrapper/command receipt differs')
    require(process.poll() is None, 'owned wrapper exited before startup completed')
    proc=Path('/proc')/str(start['child_pid'])
    require(proc.stat().st_uid==os.getuid(), 'native child has foreign owner')
    actual=[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
    fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
    require(actual==command and int(fields[1])==process.pid and fields[0] not in ['Z','X'],
            'native child command/parent/liveness differs')
    identity=dict(child_pid=start['child_pid'],wrapper_pid=process.pid,start_ticks=int(fields[19]),
                  command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest())
    require(previous is None or previous==identity, 'native child process identity changed')
    return identity


def _publish_admission(folder, staged, staged_hash, directory_identity, check_live):
    """Atomic, no-clobber link inside output; staging may be on a different mount.

    The publish-source file is deliberately retained, including on failure. No
    cleanup deletes evidence or changes native server directory creation.
    """
    check_live()
    fd=os.open(folder,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        opened=os.fstat(fd)
        current=_owned_directory(folder)
        require((opened.st_dev,opened.st_ino)==directory_identity==
                (current.st_dev,current.st_ino), 'native output directory was replaced')
        data=staged.read_bytes()
        require(not staged.is_symlink() and staged.stat().st_uid==os.getuid() and
                hashlib.sha256(data).hexdigest()==staged_hash, 'staged admission changed')
        with os.fdopen(os.open('test_admission.publish-source.json',
                os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd),'wb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        check_live()
        os.link('test_admission.publish-source.json','test_admission.json',
                src_dir_fd=fd,dst_dir_fd=fd,follow_symlinks=False)
        os.fsync(fd)
        require((folder/'test_admission.json').read_bytes()==data,
                'published admission bytes differ from staged original')
    finally:
        os.close(fd)


def _run_owned_server(workspace,repo,server_python,session,admission,command,env,
                      startup_timeout=180.,shutdown_timeout=15.):
    """Directory/receipt handshake, shared by runtime and honestly labeled CPU proxies.

    This private helper is not an alternate CLI or a grant. serve() must first
    validate the independent grant/resources and construct the native command.
    """
    require(session.startswith('test-server-') and all(c.isalnum() or c in '-_' for c in session),
            'invalid owned server session')
    require(startup_timeout>0 and shutdown_timeout>0, 'bounded positive timeouts required')
    _owned_directory(workspace);_owned_directory(workspace/'operator')
    from tase.e2_evidence import storage
    storage(workspace)  # Validate existing E2 runs alias; never create/redirect it.
    _owned_directory((workspace/'runs').resolve(strict=True))
    folder=workspace/'runs'/session
    op=workspace/'operator'/session
    receipt=workspace/'runs'/f'{session}.exit.json'
    started=receipt.with_suffix('.started.json')
    _absent(folder);_absent(op);_absent(receipt);_absent(started)
    _output_argument(command,folder)
    op.mkdir()  # This is the only session directory the launcher creates.
    staged=op/'test_admission.json';write_json(staged,admission)
    staged_hash=sha256(staged)
    wrapper=[str(server_python),'-u',str(repo/'scripts/record_process.py'),
             '--receipt',str(receipt),'--',*command]
    process=None;received=None;failure=None;published=False;ready=False;identity=None;forced=False;output_inode=None
    def forward(signum,frame):
        nonlocal received
        received=signum
        if process is not None and process.poll() is None:process.send_signal(signum)
    old={sig:signal.signal(sig,forward) for sig in [signal.SIGTERM,signal.SIGINT]}
    try:
        _absent(folder)  # Still absent at spawn, after staging and before native mkdir.
        with (op/'stdout.private.txt').open('x') as out,(op/'stderr.private.txt').open('x') as err:
            process=subprocess.Popen(wrapper,cwd=workspace/'runtime/model-resolution',env=env,
                                     stdout=out,stderr=err,start_new_session=True)
            write_json(op/'launcher_started.json',dict(wrapper_pid=process.pid,
                command=command,staged_admission_sha256=staged_hash,output_absent_at_spawn=True))
            deadline=time.monotonic()+startup_timeout
            def live():
                require(received is None, 'server launcher interrupted during startup')
                require(not receipt.exists() and process.poll() is None, 'native child exited during startup')
                if output_inode is not None:
                    st=_owned_directory(folder)
                    require((st.st_dev,st.st_ino)==output_inode,'native output directory changed after handoff')
                if published:
                    target=folder/'test_admission.json'
                    require(not target.is_symlink() and sha256(target)==staged_hash,
                            'published admission changed after handoff')
                return _process_identity(json.loads(started.read_text()),process,command,identity)
            while True:
                require(received is None, 'server launcher interrupted during startup')
                require(not receipt.exists() and process.poll() is None, 'native child exited before output handoff')
                if started.exists() and _complete_json(started) is not None:
                    identity=live()
                    if os.path.lexists(folder):
                        st=_owned_directory(folder)
                        output_inode=(st.st_dev,st.st_ino)
                        _publish_admission(folder,staged,staged_hash,output_inode,live)
                        published=True
                        # Record publication even if the following liveness check detects a failure.
                        write_json(op/'admission_published.json',dict(**identity,
                            admission_sha256=staged_hash,native_output_device=st.st_dev,
                            native_output_inode=st.st_ino,admission_is_model_loaded=False))
                        live()
                        break
                if time.monotonic()>=deadline:raise TimeoutError('native child did not create verified output before deadline')
                time.sleep(.02)
            while True:
                live()
                loaded=folder/'loaded.json'
                if os.path.lexists(loaded):
                    require(not loaded.is_symlink() and loaded.is_file() and loaded.stat().st_uid==os.getuid(),
                            'native loaded receipt is not an owned regular file')
                    value=_complete_json(loaded)
                    if value is not None:
                        require(value.get('status')=='MODEL_LOADED' and value.get('host')=='127.0.0.1' and
                                value.get('port')==admission['port'], 'native loaded loopback/port differs')
                        live();ready=True
                        write_json(op/'server_ready.json',dict(**identity,loaded_sha256=sha256(loaded),
                                   admission_sha256=staged_hash))
                        break
                if time.monotonic()>=deadline:raise TimeoutError('native child never produced valid loaded receipt')
                time.sleep(.02)
            while process.poll() is None:
                require(received is None, 'server launcher interrupted')
                time.sleep(.02)
            code=process.wait()
            require(code==0, 'native server exited with an error after readiness')
            require(received is None, 'server launcher interrupted')
            return code
    except BaseException as exc:
        failure=type(exc).__name__
        raise
    finally:
        try:
            if process is not None and process.poll() is None:
                # The handler already forwarded the original signal. Give that
                # owned wrapper a bounded exit window before escalating; an
                # immediate TERM here used to overwrite forwarded INT receipts.
                if received is not None:
                    try:process.wait(timeout=shutdown_timeout)
                    except subprocess.TimeoutExpired:forced=True
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=shutdown_timeout)
                    except subprocess.TimeoutExpired:
                        # Only the new session/process group created by this launcher.
                        forced=True;os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=shutdown_timeout)
            # A failed wrapper may leave its own child. Target only a still-matching
            # PID/start-ticks/command; never signal an unrelated or reused PID.
            if identity is not None:
                proc=Path('/proc')/str(identity['child_pid'])
                try:
                    fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
                    actual=[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
                    if fields[0] not in ['Z','X'] and int(fields[19])==identity['start_ticks'] and actual==command:
                        os.kill(identity['child_pid'],signal.SIGKILL);forced=True
                except (FileNotFoundError,ProcessLookupError):pass
            if failure is not None and process is not None:
                # Also close descendants when a wrapper died before its start
                # receipt could be authenticated. This is only our new session.
                try:os.killpg(process.pid,signal.SIGKILL);forced=True
                except ProcessLookupError:pass
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)
            write_json(op/'supervisor_exit.json',dict(wrapper_returncode=None if process is None else process.poll(),
                signal_received=received,failure_type=failure,admission_published=published,
                model_ready=ready,forced_owned_cleanup=forced,actual_child_exit_receipt_present=receipt.is_file(),
                TEST_cells_executed_by_server_launcher=0))


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
    folder=workspace/'runs'/session
    admission=dict(authorization=identity,preflight=verified,port=port,
        gpu_uuid=selected[1].strip(),egl_device_id=str(gpu_index),allocation_sha256=sha256(allocation_record))
    up=workspace/'upstream/Isaac-GR00T'
    env=os.environ.copy();env.update(HOME=str(workspace/'runtime/home'),HF_HOME=str(workspace/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(workspace/'runtime/libero-config'),
        PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
        CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_EGL_DEVICE_ID=str(gpu_index),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WANDB_MODE='disabled',WANDB_DISABLED='true',
        PYTHONNOUSERSITE='1',DO_NOT_TRACK='1',HF_HUB_DISABLE_TELEMETRY='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    command=[str(server_python),'-u','-m','tase.server',
        '--model',str(workspace/'checkpoints/libero_object'),'--output',str(folder),
        '--allocation-record',str(allocation_record),'--audit-rng','--epoch','E2','--port',str(port)]
    return _run_owned_server(workspace,repo,server_python,session,admission,command,env)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','allocation-record','server-python','sim-python']:p.add_argument('--'+name,type=Path,required=True)
    for name in ['review-commit','review-path','session']:p.add_argument('--'+name,required=True)
    p.add_argument('--gpu-index',type=int,required=True);p.add_argument('--port',type=int,default=5559)
    a=p.parse_args();sys.exit(serve(a.workspace,a.repo,a.review_commit,a.review_path,a.allocation_record,
                                   a.server_python,a.sim_python,a.session,a.gpu_index,a.port))
