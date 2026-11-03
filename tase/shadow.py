"""Isolated simulator worker; API accepts only snapshot and saved action prefix.

No policy object, endpoint, instruction override or GR00T call is available here.
"""
import copy
import multiprocessing as mp
import traceback
import os
import time
import uuid
import math
import json
from multiprocessing.connection import wait
from .snapshot import capture, restore, digest
from .m2_native import make_clone, sample


def worker(connection,task,init,contract,environment_seed=None):
    native=None;close_token=None;close_received=None
    try:
        native,raw,wrapped,spec,oracle=make_clone(task,init,contract,environment_seed)
        frames=[];progress={'policy_control_steps':0}
        original=raw.step
        def traced(action):
            import numpy as np
            value=original(action)
            progress['policy_control_steps']+=1
            frame=sample(raw,spec,progress['policy_control_steps'])
            frame['oracle']=oracle.consume(frame)
            frame['control_input']=np.array(action,copy=True)
            frames.append(frame)
            return value
        raw.step=traced
        import os,subprocess,xml.etree.ElementTree as ET
        from OpenGL import GL
        query=ET.fromstring(subprocess.check_output(['nvidia-smi','-q','-x'],text=True))
        indices=[i for i,g in enumerate(query.findall('gpu')) if any(p.findtext('pid')==str(os.getpid()) for p in g.findall('./processes/process_info'))]
        if indices!=[int(os.environ['MUJOCO_EGL_DEVICE_ID'])]:raise RuntimeError('shadow EGL device binding mismatch')
        connection.send({'status':'READY','environment_instances':1,'explicit_native_resets':1,'settling_steps':10,
            'constructor_internal_initialization':True,'hard_reset_rebuild':bool(raw.env.hard_reset),
            'egl_gpu_indices':indices,'gl_renderer':GL.glGetString(GL.GL_RENDERER).decode()})
        while True:
            message=connection.recv()
            if message['op']=='close':
                close_token=message['close_token'];close_received=time.monotonic()
                send_close_receipt(connection,{'status':'CLOSING','close_token':close_token,
                    'worker_pid':os.getpid(),'received_monotonic':close_received})
                break
            try:
                snapshot=message['snapshot'];progress=restore(raw,wrapped,oracle,snapshot)
                before=capture(raw,wrapped,oracle,progress)
                frames=[]
                observation,reward,done,truncated,info=wrapped.step(copy.deepcopy(message['prefix']))
                connection.send({'status':'PASS','frames':frames,'terminated':bool(done),'truncated':bool(truncated),
                    'success':bool(any(info['success'])),'steps':len(frames),
                    'restored_snapshot_hash':digest(before),'source_snapshot_hash':digest(snapshot),
                    'history_replay_steps':0})
            except BaseException as exc:
                connection.send({'status':'ERROR','error_type':type(exc).__name__,'traceback':traceback.format_exc(),
                    'partial_frames':frames,'completed_prediction_steps':len(frames)})
    except BaseException as exc:
        connection.send({'status':'ERROR','error_type':type(exc).__name__,'traceback':traceback.format_exc()})
    finally:
        finish_worker_close(connection,native,close_token,close_received)


def send_close_receipt(connection,value):
    data=json.dumps(value,allow_nan=False).encode()
    if len(data)>4096:raise ValueError('oversized close receipt')
    connection.send_bytes(data)


def read_close_receipts(connection,buffer):
    """Nonblocking framed JSON: even an interrupted partial frame cannot hang recv.

    The connection switches to nonblocking only AFTER the final episode/action;
    prediction transport, payloads and receive() remain byte-for-byte unchanged.
    """
    try:data=os.read(connection.fileno(),8192)
    except BlockingIOError:return [],False
    if not data:return [],True
    buffer.extend(data)
    if len(buffer)>8192:raise ValueError('oversized close stream')
    messages=[]
    while len(buffer)>=4:
        size=int.from_bytes(buffer[:4],'big',signed=True)
        if not 0<size<=4096:raise ValueError('invalid close frame size')
        if len(buffer)<size+4:break
        messages.append(json.loads(bytes(buffer[4:4+size])))
        del buffer[:4+size]
    return messages,False


def finish_worker_close(connection,native,token,received):
    """Only post-loop cleanup. A completion message proves native.close returned.

    The parent must ALSO observe a genuine zero process exit; a message alone
    never proves interpreter/device finalization or authorizes another action.
    """
    began=time.monotonic()
    try:
        if native is not None:native.close()
    except BaseException as exc:
        if token is not None:
            try:
                send_close_receipt(connection,dict(status='CLOSE_ERROR',close_token=token,
                    worker_pid=os.getpid(),native_finalized=False,error_type=type(exc).__name__,
                    received_monotonic=received,finalizer_started_monotonic=began,
                    finalizer_finished_monotonic=time.monotonic()))
            except (BrokenPipeError,EOFError,OSError) as transport:
                exc.add_note('close error receipt delivery failed: '+type(transport).__name__)
        raise
    else:
        if token is not None:
            send_close_receipt(connection,dict(status='CLOSED',close_token=token,worker_pid=os.getpid(),
                native_finalized=True,received_monotonic=received,
                finalizer_started_monotonic=began,finalizer_finished_monotonic=time.monotonic()))
    finally:
        connection.close()


class ShadowCloseError(RuntimeError):
    def __init__(self,receipt):
        self.receipt=receipt
        super().__init__('shadow lifecycle '+receipt['status'])


class Shadow:
    def __init__(self,task,init,contract,environment_seed=None):
        self.close_receipt=None;self._close_error=None;self.process=None
        context=mp.get_context('spawn')
        self.connection,child=context.Pipe()
        self.process=context.Process(target=worker,args=(child,task,init,contract,environment_seed),daemon=True)
        try:
            self.process.start();child.close()
            self.setup=self.receive(60)
            if self.setup['status']!='READY':raise RuntimeError(self.setup)
        except BaseException as exc:
            child.close()
            try:self.close()
            except ShadowCloseError as cleanup:
                exc.add_note('startup cleanup: '+cleanup.receipt['status'])
            exc.add_note('shadow startup close receipt: '+json.dumps(self.close_receipt,allow_nan=False))
            raise

    def receive(self,timeout=30):
        if not self.connection.poll(timeout):raise TimeoutError('bounded shadow response timeout')
        return self.connection.recv()

    def predict(self,snapshot,prefix):
        self.connection.send({'op':'predict','snapshot':snapshot,'prefix':prefix})
        return self.receive()

    def close(self,*,grace_seconds=10.,exit_seconds=2.,terminate_seconds=2.,kill_seconds=2.):
        """Cooperative bounded close, strict evidence, then owned TERM/KILL fallback.

        Separate deadlines cover native-finalizer completion and process exit.
        No is_alive/terminate observation can retroactively make a forced close
        clean. Cache both success and error for idempotent cleanup callers.
        """
        if self.close_receipt is not None:
            if self._close_error is not None:raise self._close_error
            return self.close_receipt
        for value,cap in [(grace_seconds,10.),(exit_seconds,2.),(terminate_seconds,2.),(kill_seconds,2.)]:
            if type(value) not in [int,float] or not math.isfinite(value) or not 0<value<=cap:
                raise ValueError('invalid bounded shadow cleanup deadline')
        receipt=dict(protocol='SHADOW_CLOSE_V1',status='CLOSING',worker_pid=None,
            worker_returncode=None,clean=False,forced=False,term_sent=False,kill_sent=False,
            pipe_closed=False,process_handle_closed=False,events=[],worker_receipts=[])
        def event(name,**extra):receipt['events'].append(dict(event=name,parent_monotonic=time.monotonic(),**extra))
        error=None;process=self.process;token=uuid.uuid4().hex
        def reap_until(deadline,phase):
            # POSIX spawn sentinel EOF can precede waitpid availability. A
            # positive Process.join(timeout) may use blocking waitpid after
            # that EOF, so ONLY nonblocking joins/polls are used here.
            observation=dict(phase=phase,started_monotonic=time.monotonic(),
                deadline_monotonic=deadline,initial_returncode=process.exitcode,polls=0)
            receipt.setdefault('exit_observations',[]).append(observation)
            while True:
                process.join(0);code=process.exitcode;observation['polls']+=1
                remaining=deadline-time.monotonic()
                if code is not None or remaining<=0:
                    observation.update(finished_monotonic=time.monotonic(),
                        returncode=code,timed_out=code is None)
                    return code
                # An early-ready sentinel stays readable; don't busy-spin or
                # treat readability as proof the actual process is dead.
                time.sleep(min(.002,remaining))
        try:
            if process is None or process.pid is None:
                receipt.update(status='NOT_STARTED',clean=True);event('NO_WORKER_STARTED')
            else:
                receipt['worker_pid']=process.pid;closing=False;closed=False;channel_open=True;buffer=bytearray();received=None
                event('CLOSE_REQUEST',close_token=token)
                os.set_blocking(self.connection.fileno(),False)
                try:self.connection.send({'op':'close','close_token':token})
                except (BrokenPipeError,EOFError,OSError) as exc:
                    error='PIPE_SEND_ERROR';event('SEND_ERROR',error_type=type(exc).__name__)
                deadline=time.monotonic()+grace_seconds
                while error is None:
                    remaining=max(0.,deadline-time.monotonic())
                    ready=wait(([self.connection] if channel_open else [])+[process.sentinel],remaining)
                    if channel_open and self.connection in ready:
                        try:messages,eof=read_close_receipts(self.connection,buffer)
                        except (EOFError,OSError,ValueError,UnicodeError) as exc:
                            error='INVALID_CLOSE_RECEIPT';messages=[];eof=True
                            event('INVALID_CLOSE_STREAM',error_type=type(exc).__name__)
                        if eof:
                            channel_open=False
                            if not closed:error=error or 'PIPE_EOF';event('EOF',partial_bytes=len(buffer))
                        for message in messages:
                            receipt['worker_receipts'].append(message)
                            if not isinstance(message,dict) or message.get('worker_pid')!=process.pid or message.get('close_token')!=token:
                                error='INVALID_CLOSE_RECEIPT'
                            elif message.get('status')=='CLOSING' and not closing and not closed:
                                received=message.get('received_monotonic')
                                if type(received) not in [int,float] or not math.isfinite(received):error='INVALID_CLOSE_RECEIPT'
                                else:closing=True;event('CLOSE_ACKNOWLEDGED')
                            elif message.get('status') in ['CLOSED','CLOSE_ERROR'] and closing and not closed:
                                stamps=[message.get(k) for k in ['received_monotonic','finalizer_started_monotonic','finalizer_finished_monotonic']]
                                if any(type(s) not in [float,int] or not math.isfinite(s) for s in stamps) or stamps!=sorted(stamps) or stamps[0]!=received:error='INVALID_CLOSE_RECEIPT'
                                elif message['status']=='CLOSE_ERROR':error='FINALIZER_ERROR';event('FINALIZER_ERROR')
                                elif message.get('native_finalized') is not True:error='INVALID_CLOSE_RECEIPT'
                                else:
                                    closed=True;deadline=time.monotonic()+exit_seconds;event('NATIVE_FINALIZER_COMPLETED')
                            else:error='INVALID_CLOSE_RECEIPT'
                    if process.sentinel in ready:
                        code=reap_until(deadline,'COOPERATIVE_EXIT')
                        if code is None:
                            error=error or 'EXIT_STATUS_TIMEOUT';event('EXIT_STATUS_TIMEOUT')
                            break
                        event('PROCESS_EXIT_OBSERVED',exit_code=code)
                        # Drain a completion receipt delivered concurrently with sentinel readiness.
                        if channel_open and self.connection.poll(0) and error is None:continue
                        if process.exitcode!=0:error=error or 'NONZERO_EXIT'
                        elif not closed:error=error or 'MISSING_CLOSE_RECEIPT'
                        break
                    if not ready or time.monotonic()>=deadline:
                        error=error or ('PROCESS_EXIT_TIMEOUT' if closed else 'FINALIZER_TIMEOUT');event('DEADLINE_EXPIRED')
                # A reported finalizer/protocol error gets a bounded chance to exit
                # on its own; retain the error even if that exit is zero.
                if error is not None and error not in ['PROCESS_EXIT_TIMEOUT','EXIT_STATUS_TIMEOUT']:reap_until(time.monotonic()+exit_seconds,'ERROR_EXIT')
                # Actual nonblocking waitpid, not sentinel EOF, is the pre-signal recheck.
                if process.exitcode is None:
                    receipt.update(forced=True,term_sent=True);event('TERM_SENT');process.terminate();reap_until(time.monotonic()+terminate_seconds,'TERM_EXIT')
                    if process.exitcode is None:
                        receipt['kill_sent']=True;event('KILL_SENT');process.kill();reap_until(time.monotonic()+kill_seconds,'KILL_EXIT')
                else:process.join(0)
                receipt['worker_returncode']=process.exitcode
                if process.exitcode is None:receipt['status']='WORKER_SURVIVED_KILL'
                elif receipt['forced']:receipt['status']='FORCED_KILL' if receipt['kill_sent'] else 'FORCED_TERM'
                elif error is not None:receipt['status']=error
                elif closed and process.exitcode==0:receipt.update(status='CLEAN',clean=True)
                else:receipt['status']='MISSING_CLOSE_RECEIPT'
                receipt['initial_failure']=error
        except BaseException as exc:
            receipt.update(status='PARENT_CLOSE_ERROR',parent_error=type(exc).__name__)
            event('PARENT_CLOSE_ERROR',error_type=type(exc).__name__)
            if process is not None and process.pid is not None:
                if process.exitcode is None:
                    receipt.update(forced=True,term_sent=True);event('TERM_SENT_AFTER_PARENT_ERROR')
                    process.terminate();reap_until(time.monotonic()+terminate_seconds,'TERM_EXIT')
                    if process.exitcode is None:
                        receipt['kill_sent']=True;event('KILL_SENT_AFTER_PARENT_ERROR')
                        process.kill();reap_until(time.monotonic()+kill_seconds,'KILL_EXIT')
                else:process.join(0)
                receipt['worker_returncode']=process.exitcode
                if process.exitcode is None:receipt['status']='WORKER_SURVIVED_KILL'
        finally:
            try:
                self.connection.close();receipt['pipe_closed']=True;event('PARENT_PIPE_CLOSED')
            except (OSError,ValueError) as exc:
                receipt.update(clean=False,status='PARENT_PIPE_CLOSE_ERROR',pipe_close_error=type(exc).__name__)
                event('PARENT_PIPE_CLOSE_ERROR',error_type=type(exc).__name__)
            finally:
                try:
                    if process is not None and (process.pid is None or process.exitcode is not None):
                        process.close();receipt['process_handle_closed']=True;event('PROCESS_HANDLE_CLOSED')
                except (OSError,ValueError) as exc:
                    receipt.update(clean=False,status='PROCESS_HANDLE_CLOSE_ERROR',handle_close_error=type(exc).__name__)
                    event('PROCESS_HANDLE_CLOSE_ERROR',error_type=type(exc).__name__)
                finally:self.close_receipt=receipt
        if not receipt['clean']:
            self._close_error=ShadowCloseError(receipt);raise self._close_error
        return receipt
