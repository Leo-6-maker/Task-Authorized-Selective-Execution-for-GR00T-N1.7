"""CPU-only R007 integration: real subprocess receipts, synthetic server proxy.

No model/torch/CUDA/MuJoCo/policy import, GPU query or TEST reservation. The
proxy implements native exclusive mkdir only, not model/runtime acceptance.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from scripts import e2_test_server as server

REPO=Path(__file__).resolve().parents[1]
EVIDENCE=os.environ.get('TASE_CPU_STARTUP_EVIDENCE')
PROXY='''import argparse,json,time,os,signal
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,required=True);p.add_argument('--mode',required=True);a=p.parse_args()
if a.mode=='early_exit':raise SystemExit(7)
if a.mode=='no_mkdir':time.sleep(30)
if a.mode=='ignore_signal':
 signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
if a.mode=='symlink':
 target=a.output.parent/'foreign-proxy-dir';target.mkdir();(target/'keep').write_text('DO NOT TOUCH');a.output.symlink_to(target,target_is_directory=True);time.sleep(30)
a.output.mkdir(parents=True,exist_ok=False)
with (a.output/'creation.json').open('x') as f:json.dump(dict(scope='CPU_PROXY_ONLY_NOT_MODEL',creator_pid=os.getpid(),output_absent_before_exclusive_mkdir=True),f)
if a.mode=='die_after_mkdir':time.sleep(.1);raise SystemExit(8)
if a.mode=='duplicate':
 with (a.output/'test_admission.json').open('x') as f:f.write('ORIGINAL_FOREIGN_ADMISSION')
 time.sleep(30)
while not (a.output/'test_admission.json').exists():time.sleep(.01)
v=json.loads((a.output/'test_admission.json').read_text())
if v.get('scope')!='SYNTHETIC_CPU_ADMISSION':raise SystemExit(9)
if a.mode=='no_loaded':time.sleep(30)
if a.mode=='wrong_loaded':
 with (a.output/'loaded.json').open('x') as f:json.dump(dict(status='MODEL_LOADED',host='foreign-host.invalid',port=a.port),f)
 time.sleep(30)
if a.mode=='partial_loaded':
 with (a.output/'loaded.json').open('x') as f:
  f.write('{');f.flush();time.sleep(.1);f.write('"status":"MODEL_LOADED","host":"127.0.0.1","port":'+str(a.port)+'}');f.flush()
 time.sleep(.2);raise SystemExit(0)
with (a.output/'loaded.json').open('x') as f:json.dump(dict(status='MODEL_LOADED',host='127.0.0.1',port=a.port,scope='SYNTHETIC_CPU_PROXY_NOT_MODEL'),f)
if a.mode in ['hold','ignore_signal']:time.sleep(30)
time.sleep(.2)
'''


class StartupTests(unittest.TestCase):
    @contextlib.contextmanager
    def fixture(self, label):
        if EVIDENCE:
            root=Path(EVIDENCE)/label;root.mkdir(parents=True)
            cleanup=contextlib.nullcontext()
        else:
            cleanup=tempfile.TemporaryDirectory();root=None
        with cleanup as temporary:
            root=root or Path(temporary)
            (root/'runs').mkdir();(root/'operator').mkdir();(root/'runtime/model-resolution').mkdir(parents=True)
            proxy=root/'cpu_proxy.py';proxy.write_text(PROXY)
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',PYTHONNOUSERSITE='1',OPENBLAS_NUM_THREADS='1')
            env.pop('TASE_CPU_STARTUP_EVIDENCE',None)
            yield root,proxy,env
            self.assertFalse((root/'runs/TEST').exists())
            if EVIDENCE:
                records=[]
                for p in sorted(root.rglob('*')):
                    if p.is_file() and not p.is_symlink():
                        data=p.read_bytes();records.append(dict(path=p.relative_to(root).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
                (root/'cpu_case_manifest.json').write_text(json.dumps(dict(scope='SYNTHETIC_CPU_PROXY_NO_MODEL_SIM_TEST',artifacts=records,TEST_reservations=0),indent=2)+'\n')

    def run_server(self,root,proxy,env,mode='success',session='test-server-cpu',**kwargs):
        command=[sys.executable,'-u',str(proxy),'--output',str(root/'runs'/session),'--port','5562','--mode',mode]
        return server._run_owned_server(root,REPO,Path(sys.executable),session,
            dict(scope='SYNTHETIC_CPU_ADMISSION',port=5562),command,env,startup_timeout=kwargs.get('startup_timeout',3.),shutdown_timeout=1.)

    def receipt(self,root):return json.loads((root/'runs/test-server-cpu.exit.json').read_text())
    def supervisor(self,root):return json.loads((root/'operator/test-server-cpu/supervisor_exit.json').read_text())

    def test_absent_output_child_exclusive_creation_then_atomic_identical_admission(self):
        with self.fixture('normal') as (root,proxy,env):
            self.assertEqual(self.run_server(root,proxy,env),0)
            native=root/'runs/test-server-cpu';op=root/'operator/test-server-cpu'
            start=json.loads((root/'runs/test-server-cpu.exit.started.json').read_text())
            self.assertEqual(json.loads((native/'creation.json').read_text())['creator_pid'],start['child_pid'])
            self.assertEqual((native/'test_admission.json').read_bytes(),(op/'test_admission.json').read_bytes())
            self.assertEqual((native/'test_admission.json').stat().st_ino,(native/'test_admission.publish-source.json').stat().st_ino)
            self.assertTrue(json.loads((op/'launcher_started.json').read_text())['output_absent_at_spawn'])
            self.assertEqual(self.receipt(root)['child_returncode'],0)
            self.assertEqual(self.supervisor(root)['wrapper_returncode'],0)
            self.assertTrue(self.supervisor(root)['model_ready'])  # CPU proxy readiness only.

    def test_child_exits_before_output_no_admission_and_actual_exit7(self):
        with self.fixture('early-exit') as (root,proxy,env):
            with self.assertRaises((ValueError,FileNotFoundError,ProcessLookupError)):
                self.run_server(root,proxy,env,'early_exit')
            self.assertFalse((root/'runs/test-server-cpu').exists())
            self.assertFalse(self.supervisor(root)['admission_published'])
            self.assertEqual(self.receipt(root)['child_returncode'],7)

    def test_child_mkdir_then_fails_before_loaded_is_not_success(self):
        with self.fixture('post-mkdir-failure') as (root,proxy,env):
            with self.assertRaises((ValueError,FileNotFoundError,ProcessLookupError)):
                self.run_server(root,proxy,env,'die_after_mkdir')
            self.assertEqual(self.receipt(root)['child_returncode'],8)
            self.assertFalse((root/'runs/test-server-cpu/loaded.json').exists())
            self.assertFalse(self.supervisor(root)['model_ready'])

    def test_preexisting_output_refuses_before_popen_and_keeps_original(self):
        with self.fixture('preexisting') as (root,proxy,env):
            folder=root/'runs/test-server-cpu';folder.mkdir();(folder/'original').write_text('KEEP')
            with patch('scripts.e2_test_server.subprocess.Popen') as spawn,self.assertRaises(ValueError):
                self.run_server(root,proxy,env)
            spawn.assert_not_called();self.assertEqual((folder/'original').read_text(),'KEEP')
            self.assertFalse((root/'operator/test-server-cpu').exists())

    def test_preexisting_or_broken_symlink_refuses_before_popen(self):
        with self.fixture('preexisting-symlink') as (root,proxy,env):
            folder=root/'runs/test-server-cpu';folder.symlink_to(root/'absent-target')
            with patch('scripts.e2_test_server.subprocess.Popen') as spawn,self.assertRaises(ValueError):
                self.run_server(root,proxy,env)
            spawn.assert_not_called();self.assertTrue(folder.is_symlink())

    def test_child_output_symlink_refuses_publication_keeps_target(self):
        with self.fixture('child-symlink') as (root,proxy,env):
            with self.assertRaises(ValueError):self.run_server(root,proxy,env,'symlink')
            self.assertEqual((root/'runs/foreign-proxy-dir/keep').read_text(),'DO NOT TOUCH')
            self.assertFalse((root/'runs/foreign-proxy-dir/test_admission.json').exists())
            self.assertFalse(self.supervisor(root)['admission_published'])

    def test_foreign_output_owner_refuses_publication_without_chown(self):
        # CPU injected stat UID, never chown a real directory or impersonate owner.
        original=server._owned_directory
        def reject_foreign(path):
            value=original(path)
            if path.name=='test-server-cpu' and path.parent.name=='runs':
                fake=list(value);fake[4]=os.getuid()+1
                value=os.stat_result(fake)
                server.require(value.st_uid==os.getuid(),'synthetic foreign output owner')
            return value
        with self.fixture('foreign-owner') as (root,proxy,env),patch.object(server,'_owned_directory',side_effect=reject_foreign):
            with self.assertRaises(ValueError):self.run_server(root,proxy,env,'hold')
            self.assertFalse((root/'runs/test-server-cpu/test_admission.json').exists())
            self.assertFalse(self.supervisor(root)['admission_published'])

    def test_mismatched_output_argument_rejected_before_process(self):
        with self.fixture('bad-output-path') as (root,proxy,env):
            command=[sys.executable,str(proxy),'--output',str(root/'wrong'),'--port','5562','--mode','success']
            with patch('scripts.e2_test_server.subprocess.Popen') as spawn,self.assertRaises(ValueError):
                server._run_owned_server(root,REPO,Path(sys.executable),'test-server-cpu',{},command,env)
            spawn.assert_not_called();self.assertFalse((root/'wrong').exists())

    def test_mismatched_pid_wrapper_and_recorded_command_refused(self):
        for key in ['child_pid','wrapper_pid','command']:
            with self.subTest(key=key),self.fixture('bad-'+key) as (root,proxy,env):
                original=server._process_identity
                def corrupt(start,process,command,previous=None):
                    start=dict(start)
                    start[key]=os.getpid() if key=='child_pid' else process.pid+1 if key=='wrapper_pid' else ['SYNTHETIC_WRONG_COMMAND']
                    return original(start,process,command,previous)
                with patch.object(server,'_process_identity',side_effect=corrupt),self.assertRaises(ValueError):
                    self.run_server(root,proxy,env,'hold')
                self.assertFalse(self.supervisor(root)['admission_published'])
                self.assertFalse((root/'runs/test-server-cpu/test_admission.json').exists())

    def test_replaced_directory_or_changed_staging_refuses_atomic_publication(self):
        for mode in ['replaced-directory','changed-stage']:
            with self.subTest(mode=mode),self.fixture(mode) as (root,proxy,env):
                original=server._publish_admission
                def changed(folder,staged,digest,inode,live):
                    if mode=='replaced-directory':
                        folder.rename(folder.with_name('preserved-original-native-dir'))
                        folder.mkdir()  # Simulated foreign replacement, old contents retained.
                    else:staged.write_text('SYNTHETIC_CHANGED_STAGE')
                    return original(folder,staged,digest,inode,live)
                with patch.object(server,'_publish_admission',side_effect=changed),self.assertRaises(ValueError):
                    self.run_server(root,proxy,env,'hold')
                self.assertFalse((root/'runs/test-server-cpu/test_admission.json').exists())
                self.assertFalse(self.supervisor(root)['admission_published'])

    def test_actual_process_identity_change_before_publication_refused(self):
        with self.fixture('process-identity-changed') as (root,proxy,env):
            original=server._process_identity
            def changed(start,process,command,previous=None):
                if previous is not None:previous=dict(previous,start_ticks=previous['start_ticks']+1)
                return original(start,process,command,previous)
            with patch.object(server,'_process_identity',side_effect=changed),self.assertRaises(ValueError):
                self.run_server(root,proxy,env,'hold')
            self.assertFalse(self.supervisor(root)['admission_published'])

    def test_partial_native_loaded_write_waits_boundedly_then_wrong_identity_refuses(self):
        with self.fixture('partial-loaded-json') as (root,proxy,env):
            self.assertEqual(self.run_server(root,proxy,env,'partial_loaded'),0)
            self.assertTrue(self.supervisor(root)['model_ready'])
        with self.fixture('wrong-loaded-identity') as (root,proxy,env):
            with self.assertRaises(ValueError):self.run_server(root,proxy,env,'wrong_loaded')
            self.assertFalse(self.supervisor(root)['model_ready'])

    def test_staged_and_published_admission_can_cross_filesystems(self):
        if not Path('/dev/shm').is_dir():self.skipTest('Linux shared-memory filesystem absent')
        with self.fixture('cross-filesystem-publication') as (root,proxy,env),tempfile.TemporaryDirectory(dir='/dev/shm') as staging:
            folder=root/'runs/test-server-cpu';folder.mkdir()
            staged=Path(staging)/'test_admission.json';data=b'{"scope":"SYNTHETIC_CPU_ADMISSION"}\n';staged.write_bytes(data)
            if staged.stat().st_dev==folder.stat().st_dev:self.skipTest('fixture mounts are identical')
            st=folder.stat()
            server._publish_admission(folder,staged,hashlib.sha256(data).hexdigest(),(st.st_dev,st.st_ino),lambda:None)
            self.assertEqual((folder/'test_admission.json').read_bytes(),data)

    def test_duplicate_admission_never_overwrites_original(self):
        with self.fixture('duplicate-admission') as (root,proxy,env):
            with self.assertRaises(FileExistsError):self.run_server(root,proxy,env,'duplicate')
            self.assertEqual((root/'runs/test-server-cpu/test_admission.json').read_text(),'ORIGINAL_FOREIGN_ADMISSION')
            self.assertFalse(self.supervisor(root)['admission_published'])
            self.assertFalse(self.supervisor(root)['model_ready'])

    def test_session_and_process_receipts_cannot_be_reused(self):
        with self.fixture('duplicate-session') as (root,proxy,env):
            self.assertEqual(self.run_server(root,proxy,env),0)
            before=(root/'operator/test-server-cpu/test_admission.json').read_bytes()
            with self.assertRaises(ValueError):self.run_server(root,proxy,env)
            self.assertEqual((root/'operator/test-server-cpu/test_admission.json').read_bytes(),before)

    def test_timeout_before_mkdir_and_before_loaded_preserves_actual_exits(self):
        for mode in ['no_mkdir','no_loaded']:
            with self.subTest(mode=mode),self.fixture('timeout-'+mode) as (root,proxy,env):
                with self.assertRaises(TimeoutError):self.run_server(root,proxy,env,mode,startup_timeout=.5)
                self.assertEqual(self.receipt(root)['child_returncode'],-signal.SIGTERM)
                self.assertEqual(self.receipt(root)['exit_code'],128+signal.SIGTERM)
                self.assertFalse(self.supervisor(root)['model_ready'])
                self.assertFalse((root/'runs/test-server-cpu/loaded.json').exists())

    def test_term_and_int_forward_only_to_owned_cpu_child_with_actual_receipts(self,*,delayed_int=False):
        for sig in [signal.SIGTERM,signal.SIGINT]:
            with self.subTest(signal=sig),self.fixture(('slow-signal-' if delayed_int else 'signal-')+str(sig)) as (root,proxy,env):
                if delayed_int and sig==signal.SIGINT:
                    # Deterministic cooperative signal latency. Old finally sent
                    # TERM immediately, replacing this actual INT exit with -15.
                    handler="def slow_int(s,f):\n time.sleep(.2);signal.signal(s,signal.SIG_DFL);os.kill(os.getpid(),s)\nsignal.signal(signal.SIGINT,slow_int)\n"
                    proxy.write_text(PROXY.replace("a.output.mkdir(parents=True,exist_ok=False)",handler+"a.output.mkdir(parents=True,exist_ok=False)"))
                # A separate CPU launcher process permits real OS signal delivery.
                driver=root/'driver.py'
                driver.write_text('import sys,os\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(REPO))+')\nfrom scripts.e2_test_server import _run_owned_server\nr=Path('+repr(str(root))+')\n_run_owned_server(r,Path('+repr(str(REPO))+'),Path(sys.executable),"test-server-cpu",dict(scope="SYNTHETIC_CPU_ADMISSION",port=5562),[sys.executable,"-u",str(r/"cpu_proxy.py"),"--output",str(r/"runs/test-server-cpu"),"--port","5562","--mode","hold"],os.environ.copy(),startup_timeout=3.,shutdown_timeout=1.)\n')
                with (root/'driver.stdout.raw.txt').open('xb') as out,(root/'driver.stderr.raw.txt').open('xb') as err:
                    p=subprocess.Popen([sys.executable,str(driver)],env=env,stdout=out,stderr=err)
                    try:
                        deadline=time.monotonic()+5
                        while not (root/'operator/test-server-cpu/server_ready.json').exists():
                            if p.poll() is not None:raise RuntimeError('CPU signal driver exited early')
                            if time.monotonic()>deadline:raise TimeoutError('CPU signal fixture not ready')
                            time.sleep(.01)
                        p.send_signal(sig);code=p.wait(timeout=5)
                    finally:
                        if p.poll() is None:p.terminate();p.wait(timeout=5)
                self.assertEqual(code,1)
                self.assertEqual(self.supervisor(root)['signal_received'],sig)
                self.assertEqual(self.receipt(root)['child_returncode'],-sig if sig==signal.SIGTERM else -sig)
                self.assertEqual(self.receipt(root)['exit_code'],128+sig)
                if EVIDENCE:(root/'driver.actual_exit.json').write_text(json.dumps(dict(actual_driver_exit=code,signal_sent=sig))+'\n')

    def test_delayed_cooperative_int_is_not_overwritten_by_cleanup_term(self):
        self.test_term_and_int_forward_only_to_owned_cpu_child_with_actual_receipts(delayed_int=True)

    def test_signal_ignoring_child_is_boundedly_closed_without_fake_exit_receipt(self):
        with self.fixture('ignored-signal') as (root,proxy,env):
            original=server._complete_json
            sent=False
            def stop_after_ready(path):
                nonlocal sent
                value=original(path)
                if path.name=='loaded.json' and value is not None and not sent:
                    # Signal handler will forward to only the owned wrapper; the
                    # CPU child ignores TERM, exercising bounded group cleanup.
                    sent=True;signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
                return value
            with patch.object(server,'_complete_json',side_effect=stop_after_ready),self.assertRaises(ValueError):
                self.run_server(root,proxy,env,'ignore_signal')
            closed=self.supervisor(root)
            self.assertEqual(closed['signal_received'],signal.SIGTERM)
            self.assertTrue(closed['forced_owned_cleanup'])
            self.assertEqual(closed['wrapper_returncode'],-signal.SIGKILL)
            self.assertFalse(closed['actual_child_exit_receipt_present'])
            self.assertFalse((root/'runs/test-server-cpu.exit.json').exists())


if __name__=='__main__':unittest.main()
