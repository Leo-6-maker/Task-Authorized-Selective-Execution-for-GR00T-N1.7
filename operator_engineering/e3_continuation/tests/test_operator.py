"""CPU fixtures + real subprocess/custody tests. No actual GPU/native execution."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from operator_engineering.e3_continuation.contract import (
    RUNTIME, LOCK, SGT, admission_contract, capacity, drive, blocks, validate_history)
from operator_engineering.e3_continuation.custody import archive, verify_archive, second_copy
from operator_engineering.e3_continuation.processes import Recorded, identity, live_same
from operator_engineering.e3_continuation.backup_agent import Copier

REPO = Path(__file__).resolve().parents[3]
APPROVED = Path(os.environ['E3_APPROVED_CPU_REPO'])
CELLS = json.loads((APPROVED/'configs/e3_cells.proposed.json').read_text())['cells']
AUDIT = json.loads((APPROVED/'reports/E3/R018/RECONCILED_ANALYSIS_v1.json').read_text())['audit']


def fixture_grant():
    # Synthetic unit input; never written into docs/reviews or operational files.
    return dict(disposition='E3_TEST_AUTHORIZED', authorized_head=RUNTIME,
                protocol_lock_sha256=LOCK,
                continuation=dict(release_prior_incident_stop=True,
                    first_new_id='e3a-test-0002', preserve_history_ids=['e3a-test-0001'],
                    remaining={'E3A':111,'E3B':48}, operator_source_sha256='SYNTHETIC_ONLY',
                    execution_window_sgt=dict(start='2026-10-31T00:00:00+08:00',
                        no_new_reservations_after='2026-10-31T04:00:00+08:00',
                        end='2026-10-31T05:00:00+08:00')))


class ContractTests(unittest.TestCase):
    def test_explicit_current_window_and_source_required(self):
        grant = fixture_grant()
        result = admission_contract(grant, dict(authorized_head=RUNTIME,
                                    protocol_lock_sha256=LOCK),
                                    dt.datetime(2026,10,31,1,tzinfo=SGT), 'SYNTHETIC_ONLY')
        self.assertEqual(result['last_supervisor_start'].isoformat(), '2026-10-31T03:42:20+08:00')

    def test_R019_does_not_grant_TEST(self):
        with self.assertRaisesRegex(ValueError, 'independent'):
            admission_contract(dict(disposition='APPROVED_CPU_REFREEZE_AND_0001_RECONCILIATION_NO_TEST'),
                               {}, dt.datetime.now(SGT), 'x')

    def test_old_head_wrong_lock_or_operator_digest_denied(self):
        identity = dict(authorized_head=RUNTIME, protocol_lock_sha256=LOCK)
        for change in ['head', 'lock', 'digest']:
            grant = fixture_grant()
            if change == 'head': grant['authorized_head'] = '8'*40
            elif change == 'lock': grant['protocol_lock_sha256'] = '0'*64
            else: grant['continuation']['operator_source_sha256'] = 'WRONG'
            with self.subTest(change=change), self.assertRaises(ValueError):
                admission_contract(grant, identity, dt.datetime(2026,10,31,1,tzinfo=SGT), 'SYNTHETIC_ONLY')

    def test_no_stop_release_or_replay_scope_denied(self):
        for key, bad in [('release_prior_incident_stop',False), ('first_new_id','e3a-test-0001'),
                         ('preserve_history_ids',[]), ('remaining',{'E3A':112,'E3B':48})]:
            grant=fixture_grant();grant['continuation'][key]=bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                admission_contract(grant,dict(authorized_head=RUNTIME,protocol_lock_sha256=LOCK),
                                   dt.datetime(2026,10,31,1,tzinfo=SGT),'SYNTHETIC_ONLY')

    def test_expired_naive_or_Nov6_window_denied(self):
        for start, cutoff, end in [('2026-10-30T00:00:00+08:00','2026-10-30T07:30:00+08:00','2026-10-30T08:00:00+08:00'),
                                   ('2026-10-31T00:00:00','2026-10-31T04:00:00','2026-10-31T05:00:00'),
                                   ('2026-11-06T00:00:00+08:00','2026-11-06T04:00:00+08:00','2026-11-06T05:00:00+08:00')]:
            grant=fixture_grant();grant['continuation']['execution_window_sgt']=dict(start=start,no_new_reservations_after=cutoff,end=end)
            with self.subTest(start=start), self.assertRaises(ValueError):
                admission_contract(grant,dict(authorized_head=RUNTIME,protocol_lock_sha256=LOCK),
                                   dt.datetime(2026,10,31,1,tzinfo=SGT),'SYNTHETIC_ONLY')

    def test_capacity10121_warns_without_lowering_floors(self):
        result=capacity(10121,16376)
        self.assertEqual(result['status'],'LIKELY_POSTLOAD_CAPACITY_BLOCKED')
        self.assertEqual(result['estimated_postload_free_MiB'],4025)
        self.assertEqual(result['scheduling_reference_MiB'],15312)
        self.assertEqual(result['postload_floor_MiB'],9216)
        self.assertIsNone(result['live_postload_pass'])

    def test_capacity15312_is_hint_not_actual_admission(self):
        result=capacity(15312,16376)
        self.assertEqual(result['status'],'SCHEDULING_HINT_ONLY')
        self.assertIsNone(result['live_postload_pass'])
        self.assertLessEqual(result['estimated_allocator_fraction'],.55)

    def test_invalid_resource_query_denied(self):
        for values in [(-1,16376),(20000,16376),(True,16376),(0,0)]:
            with self.subTest(values=values),self.assertRaises(ValueError):capacity(*values)

    def test_history_0001_exact_and_160_rows_required(self):
        self.assertEqual(validate_history(CELLS,AUDIT,'same','same'),1)
        self.assertEqual(len(blocks(CELLS)),36)
        self.assertEqual([c['run_id'] for c in blocks(CELLS)[0][2]],
                         [f'e3a-test-{i:04d}' for i in range(1,5)])

    def test_failed_interrupted_or_nonprefix_history_never_retried(self):
        for kind in ['failed','partial','nonprefix','changed_original']:
            value=copy.deepcopy(AUDIT)
            if kind=='failed':value['epochs'][0]['rows'][0]['status']='CLEANUP_ERROR'
            elif kind=='partial':value['epochs'][0]['rows'][0]['outcome_known']=False
            elif kind=='nonprefix':value['epochs'][0]['rows'][2]['reserved']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                validate_history(CELLS,value,'changed' if kind=='changed_original' else 'same','same')


class SyntheticBackend:
    """State-machine fixture only, never used by real CLI or native APIs."""
    def __init__(self):
        self.cells=CELLS;self.ids=[];self.checkpoints=[];self.saved=[];self.count=1
        self.closed=0;self.terminal=None;self.capacity=True;self.error_at=None
        self.reject_checkpoint=None;self.cutoff_at=None;self.scientific_status='SUCCESS'
    def admit(self):pass
    def progress(self):return self.count
    def capacity_ready(self):return self.capacity
    def start_server(self):self.saved.append('synthetic_server_start')
    def preserve_original(self):self.saved.append('readonly0001')
    def before_cell(self,cell):return cell['run_id']!=self.cutoff_at
    def run_cell(self,cell):
        self.ids.append(cell['run_id']);self.count+=1
        if cell['run_id']==self.error_at:raise RuntimeError('synthetic native failure')
        return dict(status=self.scientific_status,exit_code=0)
    def verify_cell(self,cell):pass
    def checkpoint(self,epoch,through,group):
        if (epoch,through)==self.reject_checkpoint:raise ValueError('synthetic missing paired/backup evidence')
        self.checkpoints.append((epoch,through))
    def retain_failure(self,error):self.saved.append(type(error).__name__)
    def close_server(self):self.closed+=1
    def retain_cleanup_failure(self,error):self.saved.append('cleanup_failure')
    def finish(self,terminal):self.terminal=terminal


class StateMachineTests(unittest.TestCase):
    def test_once_only159_and_all_36_checkpoints_automatic(self):
        backend=SyntheticBackend();drive(backend)
        self.assertEqual(backend.ids,[c['run_id'] for c in CELLS[1:]])
        self.assertEqual(len(set(backend.ids)),159)
        self.assertEqual(len(backend.checkpoints),36)
        self.assertEqual(backend.checkpoints[0],('E3A',4))
        self.assertEqual(backend.checkpoints[27],('E3A',112))
        self.assertEqual(backend.checkpoints[28],('E3B',6))
        self.assertEqual(backend.closed,1)

    def test_missing_first_checkpoint_blocks0005(self):
        backend=SyntheticBackend();backend.reject_checkpoint=('E3A',4)
        with self.assertRaises(ValueError):drive(backend)
        self.assertEqual(backend.ids,[f'e3a-test-{i:04d}' for i in range(2,5)])
        self.assertEqual(backend.terminal,'NATIVE_STOP_PRESERVE_CPU_DIAGNOSE')

    def test_native_error_stops_no_retry_consumed_id(self):
        backend=SyntheticBackend();backend.error_at='e3a-test-0003'
        with self.assertRaises(RuntimeError):drive(backend)
        self.assertEqual(backend.ids,['e3a-test-0002','e3a-test-0003'])
        self.assertEqual(backend.closed,1)

    def test_normal_negative_outcomes_continue(self):
        for status in ['TIME_LIMIT','SEMANTIC_ABORT']:
            backend=SyntheticBackend();backend.scientific_status=status
            drive(backend);self.assertEqual(len(backend.ids),159)

    def test_capacity_or_window_has_zero_additional_reserved_IDs(self):
        backend=SyntheticBackend();backend.capacity=False;drive(backend)
        self.assertEqual(backend.ids,[]);self.assertNotIn('synthetic_server_start',backend.saved)
        backend=SyntheticBackend();backend.cutoff_at='e3a-test-0002';drive(backend)
        self.assertEqual(backend.ids,[]);self.assertEqual(backend.terminal,'PARTIAL_TIMEBOX_CPU_WORK')

    def test_cleanup_error_is_not_complete_success(self):
        backend=SyntheticBackend()
        def close():raise RuntimeError('synthetic cleanup')
        backend.close_server=close
        with self.assertRaises(RuntimeError):drive(backend)
        self.assertIn('cleanup_failure',backend.saved)
        self.assertEqual(backend.terminal,'NATIVE_STOP_PRESERVE_CPU_DIAGNOSE')


class RealProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.record=Recorded(self.root,dict(os.environ,CUDA_VISIBLE_DEVICES=''),self.root)
    def test_real_success_and_nonzero_exit_preserved(self):
        a=self.record.run('success',[sys.executable,'-c','print(1)'],2)
        b=self.record.run('failure',[sys.executable,'-c','raise RuntimeError("CPU synthetic")'],2)
        self.assertEqual(a['exit_code'],0);self.assertEqual(b['child_returncode'],1)
        self.assertEqual(b['exit_code'],1)
    def test_real_spawn_failure_is_no_child_not_fake_exit0(self):
        with self.assertRaises(FileNotFoundError):self.record.start('missing',['/nonexistent-E3-CPU-test'])
        row=json.loads((self.root/'missing.spawn_error.json').read_text())
        self.assertFalse(row['actual_child_created']);self.assertIsNone(row['exit_code'])
    def test_real_timeout_TERM_is_recorded_and_raises(self):
        with self.assertRaises(TimeoutError):
            self.record.run('timeout',[sys.executable,'-c','import time;time.sleep(30)'],.15,term_timeout=.2,kill_timeout=.2)
        value=json.loads((self.root/'timeout.exit.json').read_text())
        self.assertTrue(value['deadline_exceeded']);self.assertEqual(value['signal'],signal.SIGTERM)
    def test_real_timeout_ignoring_TERM_requires_KILL_and_failure(self):
        code='import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)'
        with self.assertRaises(TimeoutError):
            self.record.run('kill',[sys.executable,'-c',code],.3,term_timeout=.1,kill_timeout=.2)
        value=json.loads((self.root/'kill.exit.json').read_text())
        self.assertEqual(value['signal'],signal.SIGKILL);self.assertNotEqual(value['exit_code'],0)
    def test_real_separate_group_descendant_is_not_orphaned(self):
        code='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"],start_new_session=True);time.sleep(30)'
        with self.assertRaises(TimeoutError):
            self.record.run('descendant',[sys.executable,'-c',code],.35,term_timeout=.3,kill_timeout=.3)
        value=json.loads((self.root/'descendant.exit.json').read_text())
        self.assertTrue(value['observed_descendants']);self.assertEqual(value['live_descendants_after_cleanup'],[])
    def test_parent_exit0_with_leaked_descendant_still_fails(self):
        code='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"],start_new_session=True);time.sleep(.3)'
        with self.assertRaisesRegex(ValueError,'leak'):
            self.record.run('leak',[sys.executable,'-c',code],2,term_timeout=.15,kill_timeout=.2)
        value=json.loads((self.root/'leak.exit.json').read_text())
        self.assertEqual(value['exit_code'],0);self.assertTrue(value['unexpected_descendant_after_parent_exit'])
        self.assertEqual(value['live_descendants_after_cleanup'],[])
    def test_exclusive_receipt_refuses_second_launch(self):
        self.record.run('once',[sys.executable,'-c','pass'],2)
        with self.assertRaises(FileExistsError):self.record.start('once',[sys.executable,'-c','raise RuntimeError()'])


class ActualAdmissionDenialTests(unittest.TestCase):
    def test_missing_map_field_does_not_create_attempt_directory(self):
        from operator_engineering.e3_continuation.native import NativeBackend
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config=root/'map.json';config.write_text('{}')
            with self.assertRaisesRegex(ValueError,'incomplete private runtime map'):
                NativeBackend(config,root/'operator','0'*40,'missing','test-server-e3-CPU-ONLY')
            self.assertFalse((root/'operator').exists())

    def test_actual_R019_and_stale_R017_deny_before_GPU_or_allocation(self):
        from operator_engineering.e3_continuation.native import NativeBackend
        for commit,path in [('266ce04507a6a430fade03f1dac4ce0f568aca22',
                             'docs/reviews/R019-E3-CPU-REFREEZE-APPROVED.json'),
                            ('ca979be10c00389ed57b77967c232d7a84132406',
                             'docs/reviews/R017-E3-TEST-AUTHORIZED.json')]:
            with self.subTest(commit=commit),tempfile.TemporaryDirectory() as t:
                root=Path(t);workspace=root/'workspace';workspace.mkdir()
                config=root/'map.json';config.write_text(json.dumps(dict(runtime_repo=str(APPROVED),
                    workspace=str(workspace),sim_python=sys.executable,server_python=sys.executable,port=5561)))
                backend=NativeBackend(config,root/'operator',commit,path,'test-server-e3-CPU-NOT-LAUNCHED')
                # Only network fetch is replaced. Genuine authorize() reads real Git history.
                with patch.object(backend,'fetch_main'),patch.object(backend,'gpu_apps',
                        side_effect=AssertionError('GPU must not be queried before authorization')):
                    with self.assertRaises(ValueError):drive(backend)
                self.assertFalse((workspace/'runs').exists())
                self.assertFalse((root/'operator/capacity-hint.json').exists())
                self.assertEqual(json.loads((root/'operator/operator-terminal.json').read_text())['status'],
                                 'CPU_ADMISSION_DENIED_NO_NATIVE_EXECUTION')


class NativeResourceAndSocketTests(unittest.TestCase):
    def test_real_new_and_retained_lock_exclusion_without_deletion(self):
        from operator_engineering.e3_continuation.processes import controller_lock
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'controller.lock'
            first=controller_lock(path)
            raw=path.read_bytes()
            try:
                with self.assertRaises(BlockingIOError):controller_lock(path)
                self.assertEqual(path.read_bytes(),raw)
            finally:first.close()
            with controller_lock(path):self.assertEqual(path.read_bytes(),raw)
            path.write_text('{"schema":"FOREIGN_MARKER"}\n')
            with self.assertRaises(ValueError):controller_lock(path)
            self.assertEqual(path.read_text(),'{"schema":"FOREIGN_MARKER"}\n')

    def test_native_memory_API_shape_and_second_query_floor(self):
        from operator_engineering.e3_continuation.native import NativeBackend
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name in ['runs','evidence_exports','operator']:(root/name).mkdir()
            backend=NativeBackend.__new__(NativeBackend)
            backend.workspace=root;backend.op=root/'operator';backend.sequence=0
            backend.native_server=None;backend.foreign_baseline=set()
            backend.allocation=dict(gpu_index=0,gpu_uuid='GPU-SYNTHETIC-CPU-ONLY')
            with patch('e3.resource.live_gpu',return_value=dict(gpu_index=0,
                    gpu_uuid='GPU-SYNTHETIC-CPU-ONLY',sampled_free_bytes=10121*1024**2)),\
                 patch.object(backend,'gpu_apps',return_value=set()),\
                 patch('operator_engineering.e3_continuation.native.subprocess.check_output',
                       return_value='0, GPU-SYNTHETIC-CPU-ONLY, 10121, 16376\n'):
                self.assertFalse(backend.capacity_ready())
            with patch('e3.resource.live_gpu',return_value=dict(sampled_free_bytes=9216*1024**2)),\
                 patch.object(backend,'gpu_apps',return_value=set()),\
                 patch('operator_engineering.e3_continuation.native.subprocess.check_output',
                       return_value='0, GPU-SYNTHETIC-CPU-ONLY, 9215, 16376\n'):
                with self.assertRaisesRegex(ValueError,'9GiB'):backend.resource_sample(postload=True)

    def test_foreign_process_growth_blocks_even_with_free_memory(self):
        from operator_engineering.e3_continuation.native import NativeBackend
        backend=NativeBackend.__new__(NativeBackend)
        backend.allocation=dict(gpu_index=0,gpu_uuid='GPU-SYNTHETIC-CPU-ONLY');backend.native_server=None
        backend.foreign_baseline={11}
        with patch('e3.resource.live_gpu',return_value=dict(sampled_free_bytes=16000*1024**2)),\
             patch.object(backend,'gpu_apps',return_value={11,12}):
            with self.assertRaisesRegex(ValueError,'foreign'):backend.resource_sample()

    def test_real_CPU_listener_must_belong_to_expected_process(self):
        from operator_engineering.e3_continuation.native import NativeBackend
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'runs').mkdir();portfile=root/'port'
            code='import socket,time;from pathlib import Path;s=socket.socket();s.bind(("127.0.0.1",0));s.listen();Path('+repr(str(portfile))+').write_text(str(s.getsockname()[1]));time.sleep(20)'
            child=subprocess.Popen([sys.executable,'-c',code])
            try:
                deadline=time.monotonic()+3
                while not portfile.exists() and time.monotonic()<deadline:time.sleep(.01)
                backend=NativeBackend.__new__(NativeBackend)
                backend.server=child;backend.native_server=identity(child.pid)
                backend.workspace=root;backend.session='CPU-ONLY-TEST'
                backend.port=int(portfile.read_text());backend.check_server()
                backend.port=0
                with self.assertRaisesRegex(ValueError,'loopback'):backend.check_server()
            finally:
                child.terminate();child.wait(timeout=3)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'original.bin').write_bytes(b'CPU-fixture')
        self.rows=[dict(path='original.bin',bytes=11,sha256=hashlib.sha256(b'CPU-fixture').hexdigest())]
        self.receipt=archive(self.root,'CPU-TEST',self.rows,[],self.root/'a.tar.gz')
    def test_whole_and_every_member_two_copies(self):
        shutil.copyfile(self.root/'a.tar.gz',self.root/'b.tar.gz')
        value=second_copy(self.root/'a.tar.gz',self.root/'b.tar.gz',self.receipt)
        self.assertEqual(value['original_files'],self.rows)
    def test_same_path_not_two_copies(self):
        with self.assertRaises(ValueError):second_copy(self.root/'a.tar.gz',self.root/'a.tar.gz',self.receipt)
    def test_changed_whole_hash_or_original_inventory_refused(self):
        receipt=copy.deepcopy(self.receipt);receipt['sha256']='0'*64
        with self.assertRaises(ValueError):verify_archive(self.root/'a.tar.gz',receipt)
        receipt=copy.deepcopy(self.receipt);receipt['original_files']=[]
        with self.assertRaises(ValueError):verify_archive(self.root/'a.tar.gz',receipt)
    def test_missing_source_symlink_or_path_escape_refused(self):
        for rows in [[dict(self.rows[0],path='missing')],[dict(self.rows[0],path='../escape')]]:
            with self.assertRaises(ValueError):archive(self.root,'x',rows,[],self.root/'new.tar.gz')
        (self.root/'alias').symlink_to(self.root/'original.bin')
        with self.assertRaises(ValueError):archive(self.root,'x',[dict(self.rows[0],path='alias')],[],self.root/'new.tar.gz')
    def test_duplicate_custody_rows_refused(self):
        with self.assertRaises(ValueError):archive(self.root,'x',self.rows*2,[],self.root/'new.tar.gz')


class LocalCPUTransport(Copier):
    """Explicitly substitutes same-host Python subprocess for SSH, data-only."""
    def remote(self,code,destination=None):
        value=subprocess.run([sys.executable,'-c',code],stdout=destination or subprocess.PIPE,
                             stderr=subprocess.PIPE,timeout=5)
        if value.returncode:raise ValueError(value.stderr.decode())
        return value.stdout


class BackupTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.workspace=self.root/'remote';self.workspace.mkdir()
        stage=self.workspace/'evidence_exports/CPU-TEST';stage.mkdir(parents=True)
        (self.workspace/'original').write_bytes(b'preserve')
        rows=[dict(path='original',bytes=8,sha256=hashlib.sha256(b'preserve').hexdigest())]
        self.receipt=archive(self.workspace,'CPU-TEST',rows,[],stage/'evidence.tar.gz')
        self.config=dict(workspace=str(self.workspace),operator_directory=str(self.workspace/'operator'),
            local_backup_root=str(self.root/'local'),
            transport_argv=['ssh','-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','CPU-NOT-CONNECTED'])
    def test_actual_generated_transfer_and_proof_programs(self):
        agent=LocalCPUTransport(self.config,self.root/'receipts')
        proof=agent.copy(self.receipt)
        primary=self.workspace/'evidence_exports/CPU-TEST/second-copy-proof.json'
        self.assertEqual(json.loads(primary.read_text()),proof)
        self.assertEqual(proof['primary_archive_sha256'],proof['secondary_archive_sha256'])
    def test_resume_partial_bytes_at_actual_offset(self):
        dest=self.root/'local/CPU-TEST';dest.mkdir(parents=True)
        source=(self.workspace/'evidence_exports/CPU-TEST/evidence.tar.gz').read_bytes()
        (dest/'evidence.tar.gz.pending').write_bytes(source[:51])
        agent=LocalCPUTransport(self.config,self.root/'receipts')
        agent.copy(self.receipt)
        self.assertEqual((dest/'evidence.tar.gz').read_bytes(),source)
    def test_wrong_partial_hash_is_not_overwritten_or_proven(self):
        dest=self.root/'local/CPU-TEST';dest.mkdir(parents=True)
        (dest/'evidence.tar.gz.pending').write_bytes(b'x'*self.receipt['bytes'])
        agent=LocalCPUTransport(self.config,self.root/'receipts')
        with self.assertRaises(ValueError):agent.copy(self.receipt)
        self.assertTrue((dest/'evidence.tar.gz.pending').exists())
        self.assertFalse((dest/'second-copy-proof.json').exists())
    def test_strict_host_verification_cannot_be_disabled(self):
        self.config['transport_argv']=['ssh','-o','StrictHostKeyChecking=no','-o','BatchMode=yes','CPU-ONLY']
        with self.assertRaises(ValueError):Copier(self.config,self.root/'receipts')
    def test_nested_transport_also_requires_strict_host_verification(self):
        self.config['nested_transport_argv']=['ssh','-o','StrictHostKeyChecking=no','CPU-ONLY']
        with self.assertRaises(ValueError):Copier(self.config,self.root/'receipts')


if __name__=='__main__':unittest.main()
