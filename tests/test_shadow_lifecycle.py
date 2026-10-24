"""Real CPU spawn processes, never models/MuJoCo/TEST IDs or GPU contexts."""
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import time
import unittest
import struct
import copy
from unittest.mock import patch
from tase.shadow import Shadow,ShadowCloseError,finish_worker_close,send_close_receipt
from tase.test_history import verify_lifecycle


class NativeProxy:
    def __init__(self,mode,delay):self.mode=mode;self.delay=delay
    def close(self):
        time.sleep(self.delay)
        if self.mode=='finalizer_error':raise RuntimeError('SYNTHETIC_NATIVE_FINALIZER_ERROR')
        if self.mode=='hang':
            while True:time.sleep(1)


def cpu_worker(connection,mode,delay):
    if mode=='ignore_term':signal.signal(signal.SIGTERM,signal.SIG_IGN)
    connection.send({'status':'READY'})
    if mode=='no_read':
        while True:time.sleep(1)
    if mode=='early_nonzero':connection.close();raise SystemExit(7)
    if mode=='early_zero':connection.close();return
    msg=connection.recv();token=msg['close_token'];received=time.monotonic()
    if mode=='bad_token':send_close_receipt(connection,{'status':'CLOSING','close_token':'wrong','worker_pid':os.getpid()});connection.close();return
    if mode=='partial':send_close_receipt(connection,{'status':'CLOSING','close_token':token,'worker_pid':os.getpid(),'received_monotonic':received});connection.close();return
    if mode=='malformed':send_close_receipt(connection,'NOT_A_RECEIPT');connection.close();return
    if mode=='partial_frame_hang':
        os.write(connection.fileno(),struct.pack('!i',100)+b'{')
        while True:time.sleep(1)
    if mode=='ignore_term':
        while True:time.sleep(1)
    send_close_receipt(connection,{'status':'CLOSING','close_token':token,'worker_pid':os.getpid(),'received_monotonic':received})
    finish_worker_close(connection,NativeProxy(mode,delay),token,received)
    if mode=='nonzero_after_ack':raise SystemExit(7)
    if mode=='exit_delay':time.sleep(.25)


def startup_failure_worker(connection,*args):
    connection.send({'status':'ERROR','error_type':'SYNTHETIC_STARTUP_FAILURE'})
    msg=connection.recv();received=time.monotonic()
    send_close_receipt(connection,dict(status='CLOSING',close_token=msg['close_token'],worker_pid=os.getpid(),received_monotonic=received))
    finish_worker_close(connection,NativeProxy('normal',0),msg['close_token'],received)


def make_shadow(mode='normal',delay=0):
    ctx=mp.get_context('spawn');parent,child=ctx.Pipe();p=ctx.Process(target=cpu_worker,args=(child,mode,delay),daemon=True);p.start();child.close()
    if not parent.poll(8):p.kill();p.join(2);parent.close();p.close();raise RuntimeError('CPU proxy startup failed')
    if parent.recv()!={'status':'READY'}:raise RuntimeError('CPU proxy not ready')
    shadow=Shadow.__new__(Shadow);shadow.process=p;shadow.connection=parent;shadow.close_receipt=None;shadow._close_error=None
    return shadow,p.pid


class ShadowLifecycleTests(unittest.TestCase):
    def close(self,s,**extra):return s.close(grace_seconds=.3,exit_seconds=.4,terminate_seconds=.15,kill_seconds=.25,**extra)
    def check_reaped(self,s,pid):
        self.assertTrue(s.connection.closed);self.assertTrue(s.close_receipt['process_handle_closed'])
        self.assertFalse((Path('/proc')/str(pid)).exists())
        self.assertNotIn(pid,[p.pid for p in mp.active_children()])
        json.dumps(s.close_receipt,allow_nan=False)
        if s.close_receipt['status']=='CLEAN':
            verify_lifecycle(s.close_receipt,dict(worker_pid=pid,worker_returncode=0,clean_close=True))
        directory=os.environ.get('TASE_CPU_LIFECYCLE_RECEIPTS')
        if directory:
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            with (folder/(str(pid)+'.json')).open('x') as f:
                json.dump(dict(scope='REAL_CPU_PROXY_NOT_MODEL_OR_SIM',test=self.id(),receipt=s.close_receipt),f,indent=2)
    def test_clean_zero_actual_worker_and_native_completion(self):
        s,pid=make_shadow();r=self.close(s);self.assertTrue(r['clean']);self.assertEqual(r['worker_returncode'],0)
        self.assertEqual([x['status'] for x in r['worker_receipts']],['CLOSING','CLOSED']);self.check_reaped(s,pid)
    def test_slow_native_finalizer_is_cooperative_not_force(self):
        s,pid=make_shadow(delay=.12);r=self.close(s);self.assertEqual(r['status'],'CLEAN');self.assertFalse(r['forced']);self.check_reaped(s,pid)
    def test_receipt_does_not_mean_process_exit(self):
        s,pid=make_shadow('exit_delay');r=self.close(s);self.assertEqual(r['status'],'CLEAN');self.check_reaped(s,pid)
    def test_exit_deadline_even_with_good_ack_is_error(self):
        s,pid=make_shadow('exit_delay')
        with self.assertRaises(ShadowCloseError):s.close(grace_seconds=.3,exit_seconds=.03,terminate_seconds=.15,kill_seconds=.2)
        self.assertFalse(s.close_receipt['clean']);self.assertTrue(s.close_receipt['term_sent']);self.check_reaped(s,pid)
    def test_finalizer_failure_preserves_nonzero_exit_and_receipt(self):
        s,pid=make_shadow('finalizer_error')
        with self.assertRaises(ShadowCloseError):self.close(s)
        r=s.close_receipt;self.assertEqual(r['status'],'FINALIZER_ERROR');self.assertEqual(r['worker_returncode'],1);self.assertFalse(r['forced']);self.check_reaped(s,pid)
    def test_ack_then_nonzero_exit_never_clean(self):
        s,pid=make_shadow('nonzero_after_ack')
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertEqual(s.close_receipt['worker_returncode'],7);self.assertFalse(s.close_receipt['clean']);self.check_reaped(s,pid)
    def test_hung_native_requires_term_and_remains_error(self):
        s,pid=make_shadow('hang');started=time.monotonic()
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertLess(time.monotonic()-started,2);self.assertEqual(s.close_receipt['status'],'FORCED_TERM');self.assertEqual(s.close_receipt['worker_returncode'],-signal.SIGTERM);self.check_reaped(s,pid)
    def test_ignored_term_requires_kill_and_remains_error(self):
        s,pid=make_shadow('ignore_term');started=time.monotonic()
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertLess(time.monotonic()-started,2);self.assertEqual(s.close_receipt['status'],'FORCED_KILL');self.assertEqual(s.close_receipt['worker_returncode'],-signal.SIGKILL);self.check_reaped(s,pid)
    def test_zero_exit_without_complete_receipt_is_error(self):
        for mode in ['early_zero','partial','bad_token','malformed']:
            with self.subTest(mode=mode):
                s,pid=make_shadow(mode)
                with self.assertRaises(ShadowCloseError):self.close(s)
                self.assertFalse(s.close_receipt['clean']);self.check_reaped(s,pid)
    def test_early_nonzero_and_eof_retains_actual_exit(self):
        s,pid=make_shadow('early_nonzero')
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertEqual(s.close_receipt['worker_returncode'],7);self.check_reaped(s,pid)
    def test_duplicate_success_and_failure_close_are_idempotent(self):
        s,pid=make_shadow();r=self.close(s);self.assertIs(self.close(s),r);self.check_reaped(s,pid)
        s,pid=make_shadow('partial')
        with self.assertRaises(ShadowCloseError) as one:self.close(s)
        with self.assertRaises(ShadowCloseError) as two:self.close(s)
        self.assertIs(one.exception,two.exception);self.check_reaped(s,pid)
    def test_worker_not_created_is_explicit_no_resource_case(self):
        ctx=mp.get_context('spawn');parent,child=ctx.Pipe();child.close();s=Shadow.__new__(Shadow);s.process=None;s.connection=parent;s.close_receipt=None;s._close_error=None
        self.assertEqual(self.close(s)['status'],'NOT_STARTED');self.assertTrue(parent.closed)
    def test_invalid_deadlines_cannot_create_unbounded_wait(self):
        for value in [0,-1,True,float('inf'),float('nan'),999]:
            s=Shadow.__new__(Shadow);s.close_receipt=None
            with self.assertRaises(ValueError):s.close(grace_seconds=value)
    def test_jitter_repeated_real_spawn_exit_boundary_no_orphans(self):
        for i in range(12):
            s,pid=make_shadow(delay=(i%4)*.003);r=self.close(s);self.assertEqual(r['status'],'CLEAN');self.check_reaped(s,pid)
    def test_real_ten_second_boundary_finalizer_ack_then_exit(self):
        # Actual wall clock > original join10: native close completes within10,
        # interpreter exit follows. Explicit ack+separate exit phase is required.
        s,pid=make_shadow('exit_delay',9.9);started=time.monotonic();r=s.close()
        self.assertGreater(time.monotonic()-started,10.)
        self.assertEqual(r['status'],'CLEAN');self.assertFalse(r['forced']);self.check_reaped(s,pid)
    def test_partial_transport_frame_cannot_block_parent_recv(self):
        s,pid=make_shadow('partial_frame_hang');started=time.monotonic()
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertLess(time.monotonic()-started,2);self.check_reaped(s,pid)
    def test_startup_error_preserved_and_owned_worker_closed(self):
        s=Shadow.__new__(Shadow)
        with patch('tase.shadow.worker',startup_failure_worker):
            with self.assertRaisesRegex(RuntimeError,'SYNTHETIC_STARTUP_FAILURE') as error:Shadow.__init__(s,'SYNTHETIC',0,{})
        self.assertTrue(any('shadow startup close receipt:' in n for n in error.exception.__notes__))
        self.assertEqual(s.close_receipt['status'],'CLEAN');self.check_reaped(s,s.close_receipt['worker_pid'])
    def test_backpressured_close_request_cannot_block_parent_send(self):
        s,pid=make_shadow('no_read');os.set_blocking(s.connection.fileno(),False)
        try:
            for _ in range(1000):os.write(s.connection.fileno(),b'x'*4096)
        except BlockingIOError:pass
        os.set_blocking(s.connection.fileno(),True);started=time.monotonic()
        with self.assertRaises(ShadowCloseError):self.close(s)
        self.assertLess(time.monotonic()-started,2);self.assertEqual(s.close_receipt['initial_failure'],'PIPE_SEND_ERROR');self.check_reaped(s,pid)
    def test_forged_clean_receipt_cannot_hide_force_missing_ack_or_bad_time(self):
        s,pid=make_shadow();r=self.close(s);worker=dict(worker_pid=pid,worker_returncode=0,clean_close=True)
        for mode in ['term','kill','missing_ack','bad_token','nan_time','wrong_pid','missing_exit']:
            with self.subTest(mode=mode):
                bad=copy.deepcopy(r)
                if mode=='term':bad['term_sent']=True
                elif mode=='kill':bad['kill_sent']=True
                elif mode=='missing_ack':bad['worker_receipts'].pop()
                elif mode=='bad_token':bad['worker_receipts'][1]['close_token']='0'*32
                elif mode=='nan_time':bad['worker_receipts'][1]['finalizer_finished_monotonic']=float('nan')
                elif mode=='wrong_pid':bad['worker_pid']+=1
                else:bad['events']=[e for e in bad['events'] if e['event']!='PROCESS_EXIT_OBSERVED']
                with self.assertRaises(ValueError):verify_lifecycle(bad,worker)
        self.check_reaped(s,pid)
