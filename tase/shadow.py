"""Isolated simulator worker; API accepts only snapshot and saved action prefix.

No policy object, endpoint, instruction override or GR00T call is available here.
"""
import copy
import multiprocessing as mp
import traceback
from .snapshot import capture, restore, digest
from .m2_native import make_clone, sample


def worker(connection,task,init,contract,environment_seed=None):
    native=None
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
            if message['op']=='close':break
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
        if native is not None:native.close()
        connection.close()


class Shadow:
    def __init__(self,task,init,contract,environment_seed=None):
        context=mp.get_context('spawn')
        self.connection,child=context.Pipe()
        self.process=context.Process(target=worker,args=(child,task,init,contract,environment_seed),daemon=True)
        self.process.start();child.close()
        self.setup=self.receive(60)
        if self.setup['status']!='READY':
            self.process.join(5);self.connection.close()
            raise RuntimeError(self.setup)

    def receive(self,timeout=30):
        if not self.connection.poll(timeout):raise TimeoutError('bounded shadow response timeout')
        return self.connection.recv()

    def predict(self,snapshot,prefix):
        self.connection.send({'op':'predict','snapshot':snapshot,'prefix':prefix})
        return self.receive()

    def close(self):
        if self.process.is_alive():
            self.connection.send({'op':'close'})
            self.process.join(10)
        if self.process.is_alive():
            self.process.terminate();self.process.join(5)
            raise RuntimeError('owned shadow worker required termination')
        self.connection.close()
        if self.process.exitcode:raise RuntimeError('owned shadow worker exit '+str(self.process.exitcode))
