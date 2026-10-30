"""External orchestration of unchanged native entry points; never a policy runner.

Native initialization is impossible before a current independent exact grant,
the operator-source binding and a new permitted window have all passed.
"""
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import traceback

from .contract import (RUNTIME, LOCK, SGT, HISTORICAL_HEAD, HISTORICAL_GRANT,
                       admission_contract, capacity, require, sha, source_digest,
                       validate_history)
from .custody import archive, verify_archive
from .processes import Recorded, identity, live_same, stamp, write


class NativeBackend:
    def __init__(self, runtime_map, operator_directory, review_commit, review_path, session):
        self.map = json.loads(Path(runtime_map).read_text())
        self.repo = Path(self.map['runtime_repo']).resolve(strict=True)
        self.workspace = Path(self.map['workspace']).resolve(strict=True)
        self.op = Path(operator_directory).resolve()
        require(not self.op.is_relative_to(self.repo) and
                not self.op.is_relative_to(self.workspace/'runs'),
                'operator output must be outside exact runtime and originals')
        self.op.mkdir(mode=0o700)  # Existing directory/attempt never reused.
        self.review_commit, self.review_path, self.session = review_commit, review_path, session
        require(session.startswith('test-server-e3-') and
                all(c.isalnum() or c in '-_' for c in session), 'exclusive E3 server session required')
        self.sim, self.server_python = [Path(self.map[n]) for n in ['sim_python', 'server_python']]
        self.port = self.map['port']
        self.env = dict(os.environ, HOME=str(self.workspace/'runtime/home'),
                        LIBERO_CONFIG_PATH=str(self.workspace/'runtime/libero-config'),
                        PYTHONPATH=str(self.repo), CUDA_VISIBLE_DEVICES='',
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1',
                        WANDB_DISABLED='true', WANDB_MODE='disabled', PYTHONNOUSERSITE='1',
                        OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        self.record = Recorded(self.op, self.env, self.repo)
        self.server = self.server_expected = self.native_server = None
        self.lock_handle = None
        self.cells, self.auth, self.window, self.allocation = [], None, None, None
        self.sequence = 0
        self.last_progress = None  # Expected history is not an observed/audited count.
        self.sample = None
        self.current_cell = None
        write(self.op/'operator-started.json', dict(at=stamp(), controller=identity(os.getpid()),
              runtime_repo=str(self.repo), review_commit=review_commit, review_path=review_path,
              operator_source_sha256=source_digest(), native_process_started=False))

    def label(self, prefix):
        self.sequence += 1
        return f'{self.sequence:04d}-{prefix}'

    def event(self, event, **values):
        with (self.op/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(at=stamp(), event=event, **values), allow_nan=False)+'\n')
            f.flush()
            os.fsync(f.fileno())

    def fetch_main(self):
        for attempt in range(3):
            row = self.record.run(self.label('main-fetch'), ['git', 'fetch', 'origin', 'main'], 60)
            if row['exit_code'] == 0:
                return
            self.event('READONLY_TRANSPORT_FAILURE', actual_exit=row['exit_code'], attempt=attempt+1)
            if attempt < 2:
                time.sleep([30, 120][attempt])
        raise RuntimeError('three bounded current-main fetch attempts failed; CPU fallback')

    def admit(self):
        import sys
        require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.repo,
                                       text=True).strip() == RUNTIME and
                not subprocess.check_output(['git', 'status', '--porcelain'], cwd=self.repo),
                'clean exact approved runtime required, never report branch')
        self.fetch_main()
        sys.path.insert(0, str(self.repo))
        from e3.authorization import authorize, resource
        _, self.cells, self.auth = authorize(self.repo, self.review_commit, self.review_path)
        grant = json.loads(subprocess.check_output(['git', 'show', self.review_commit+':'+
                                                    self.review_path], cwd=self.repo))
        self.window = admission_contract(grant, self.auth, dt.datetime.now(SGT), source_digest())
        require(dt.datetime.now(SGT) + dt.timedelta(seconds=240) <
                self.window['last_supervisor_start'], 'insufficient authorized window to load and finish')
        self.reconciliation = json.loads((self.repo/
            'reports/E3/R018/RECONCILIATION_0001_v1.json').read_text())
        self.preserve_original()
        self.allocation_path = Path(self.map['allocation_record'])
        self.allocation = json.loads(self.allocation_path.read_text())
        resource(self.allocation, self.auth)
        require(self.allocation.get('egl_device_id') == '1' and
                self.allocation.get('created_for_execution_window') ==
                grant['continuation']['execution_window_sgt'], 'new actual window/EGL resource binding required')
        owner = Path(self.allocation['owner_approval_evidence']['path'])
        require(sha(owner) == self.allocation['owner_approval_evidence']['sha256'],
                'retained direct owner GPU1 evidence changed')
        for root in ['runs', 'operator', 'evidence_exports']:
            require((self.workspace/root).is_dir(), 'existing project storage required')
        lock = self.workspace/'operator/e3-continuation-single-controller.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.write(fd, b'{"schema":"E3_EXTERNAL_CONTROLLER_FLOCK_V1"}\n')
        except FileExistsError:
            fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
        self.lock_handle = os.fdopen(fd, 'r+')
        require(json.loads(self.lock_handle.read()) == {'schema':'E3_EXTERNAL_CONTROLLER_FLOCK_V1'},
                'unknown controller lock; preserve without deletion')
        fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.require_no_native_process()
        write(self.op/'controller-lock-owner.json', dict(at=stamp(), controller=identity(os.getpid()),
              native_authorization=self.auth, lock_retained_after_exit=True))
        self.foreign_baseline = self.gpu_apps()
        self.event('ADMISSION_VERIFIED', authorization=self.auth,
                   independent_window=grant['continuation']['execution_window_sgt'])

    def require_no_native_process(self):
        for folder in Path('/proc').iterdir():
            if not folder.name.isdigit():
                continue
            try:
                observed = identity(int(folder.name))
            except (OSError, ValueError):
                continue
            if observed['uid'] == os.getuid():
                require(not any(t in observed['command'] for t in
                                ['e3.server', 'e3.server_launcher', 'e3.native_runner',
                                 'e3.scene_probe', 'tase.shadow_worker']) and
                        not any(t.endswith('overnight_operator.py') for t in observed['command']),
                        'existing native/controller process; do not create duplicate')

    def preserve_original(self):
        from e3.checkpoint import original_inventory
        rec = self.reconciliation
        require(rec['acquisition']['execution_head'] == HISTORICAL_HEAD and
                rec['acquisition']['review_commit'] == HISTORICAL_GRANT and
                rec['protocol_lock_sha256'] == LOCK and
                rec['eligibility']['old_frozen_audit_PASS'] is False and
                [x['actual_exit'] for x in rec['old_frozen_audit_failures']] == [1, 1],
                'reviewed original history cannot be rewritten')
        self.old_rows = original_inventory(self.workspace,
                          [self.workspace/'runs/E3A_TEST/e3a-test-0001'])
        require(self.old_rows == rec['original_files'] and len(self.old_rows) == 78,
                'original78 changed; never replay or replace0001')

    def audit(self):
        from e3.audit import original
        from e3.ledger import audit, ROOTS
        return dict(epochs=[audit(self.workspace/'runs'/ROOTS[epoch],
                                [c for c in self.cells if c['epoch'] == epoch],
                                lambda f, r: original(self.workspace, self.repo, f, r))
                            for epoch in ['E3A', 'E3B']])

    def progress(self):
        self.preserve_original()
        audit = self.audit()
        self.last_progress = validate_history(self.cells, audit, self.old_rows,
                                              self.reconciliation['original_files'])
        return self.last_progress

    def gpu_apps(self):
        text = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory',
                                        '--format=csv,noheader,nounits'], text=True)
        return {int(row.split(',')[1]) for row in text.splitlines()
                if row.strip() and row.split(',')[0].strip() == self.allocation['gpu_uuid']}

    def resource_sample(self, postload=False):
        from e3.resource import live_gpu1
        live = live_gpu1(self.allocation)  # Unchanged actual9GiB physicalGPU1 check.
        apps = self.gpu_apps()
        own = set() if self.native_server is None else {self.native_server['pid']}
        require(apps - own == self.foreign_baseline, 'foreign GPU1 process set changed')
        import shutil
        require(all(shutil.disk_usage(self.workspace/r).free >= 3*1024**3
                    for r in ['runs', 'evidence_exports']), 'project storage below3GiB')
        self.sample = dict(at=stamp(), live=live, apps=sorted(apps), postload=postload)
        write(self.op/(self.label('resource')+'.json'), self.sample)
        raw = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.free,memory.total',
                                       '--format=csv,noheader,nounits'], text=True)
        selected = [[s.strip() for s in row.split(',')] for row in raw.splitlines()
                    if row.split(',')[0].strip() == '1']
        require(len(selected) == 1 and selected[0][1] == self.allocation['gpu_uuid'],
                'capacity query physicalGPU1 UUID differs')
        free_mib, total_mib = map(int, selected[0][2:])
        require(free_mib >= 9216, 'second actual GPU1 sample below unchanged9GiB')
        return dict(free_MiB=free_mib, total_MiB=total_mib, native_live_check=live)

    def capacity_ready(self):
        live = self.resource_sample()
        hint = capacity(live['free_MiB'], live['total_MiB'])
        write(self.op/'capacity-hint.json', dict(at=stamp(), **hint))
        # Scheduling reference does not replace or lower either actual9GiB guard.
        return hint['status'] != 'LIKELY_POSTLOAD_CAPACITY_BLOCKED'

    def check_server(self):
        require(self.server is not None and self.server.poll() is None and
                self.native_server is not None and live_same(self.native_server),
                'owned server exited or PID identity changed')
        require(not (self.workspace/'runs'/(self.session+'.exit.json')).exists(),
                'native server already has terminal receipt')
        inodes = set()
        for row in Path('/proc/net/tcp').read_text().splitlines()[1:]:
            fields = row.split()
            if fields[1] == '0100007F:'+format(self.port, '04X') and fields[3] == '0A':
                inodes.add(fields[9])
        observed = set()
        for fd in (Path('/proc')/str(self.native_server['pid'])/'fd').iterdir():
            try:
                value = os.readlink(fd)
                if value.startswith('socket:['):
                    observed.add(value[8:-1])
            except OSError:
                pass
        require(bool(inodes & observed), 'native PID does not own expected loopback listener')

    def start_server(self):
        for name in [self.workspace/'runs'/self.session,
                     self.workspace/'operator'/self.session]:
            require(not name.exists(), 'exclusive new session directory required')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', self.port))
        command = [str(self.server_python), '-u', '-m', 'e3.server_launcher',
                   '--workspace', str(self.workspace), '--repo', str(self.repo),
                   '--review-commit', self.review_commit, '--review-path', self.review_path,
                   '--allocation-record', str(self.allocation_path), '--server-python',
                   str(self.server_python), '--sim-python', str(self.sim),
                   '--session', self.session, '--gpu-index', '1', '--port', str(self.port)]
        self.server_label = self.label('server-launcher')
        self.server, self.server_expected = self.record.start(self.server_label, command)
        ready = self.workspace/'operator'/self.session/'server_ready.json'
        deadline = time.monotonic() + 240
        while not ready.exists():
            require(self.server.poll() is None, 'real native server startup failed')
            require(time.monotonic() < deadline, 'real native server startup deadline')
            time.sleep(.25)
        value = json.loads(ready.read_text())
        self.native_server = identity(value['child_pid'])
        self.check_server()
        loaded = json.loads((self.workspace/'runs'/self.session/'loaded.json').read_text())
        require(loaded['physical_resource_preflight']['gpu_index'] == 1 and
                loaded['physical_resource_preflight']['gpu_uuid'] == self.allocation['gpu_uuid'],
                'actual loaded GPU binding differs')
        self.resource_sample(postload=True)
        self.event('SERVER_READY', native=self.native_server, health_policy_calls=0)

    def before_cell(self, cell):
        if dt.datetime.now(SGT) >= self.window['last_supervisor_start']:
            self.event('WINDOW_CUTOFF_NO_NEW_ID', requested_id=cell['run_id'])
            return False
        self.check_server()
        self.preserve_original()
        self.resource_sample(postload=True)
        require(self.progress() == self.cells.index(cell),
                'next original ID differs; unknown/extra consumption never skipped')
        return True

    def run_cell(self, cell):
        self.current_cell = cell['run_id']
        command = [str(self.sim), '-u', '-m', 'e3.supervisor', '--workspace', str(self.workspace),
                   '--repo', str(self.repo), '--run-id', cell['run_id'], '--review-commit',
                   self.review_commit, '--review-path', self.review_path,
                   '--allocation-record', str(self.allocation_path), '--sim-python', str(self.sim),
                   '--server-session', self.session, '--port', str(self.port)]
        exit = self.record.run(self.label(cell['run_id']), command, 1000)
        require(exit['exit_code'] == 0, 'actual supervisor/native failure; do not retry')
        from e3.ledger import ROOTS
        return json.loads((self.workspace/'runs'/ROOTS[cell['epoch']]/cell['run_id']/'result.json').read_text())

    def verify_cell(self, cell):
        from e3.audit import original
        from e3.ledger import ROOTS
        folder = self.workspace/'runs'/ROOTS[cell['epoch']]/cell['run_id']
        original(self.workspace, self.repo, folder, json.loads((folder/'reservation.json').read_text()))
        require(self.progress() == self.cells.index(cell)+1, 'new cell is not fully eligible')
        self.event('NATIVE_CELL_COMPLETE', run_id=cell['run_id'], actual_audit_pass=True)
        self.current_cell = None

    def checkpoint(self, epoch, through, group):
        from e3.checkpoint import build, original_inventory, require_backup
        from e3.ledger import ROOTS
        from .physics_checks import check_block
        self.fetch_main()
        from e3.authorization import authorize
        require(authorize(self.repo, self.review_commit, self.review_path)[2] == self.auth,
                'current native grant changed; no next checkpoint release')
        audits = []
        for mode, flags in [('normal', []), ('optimized', ['-O'])]:
            output = self.op/(self.label('audit-'+mode)+'.json')
            exit = self.record.run(self.label('audit-'+mode),
                       [str(self.sim), *flags, '-m', 'e3.cli', 'audit', '--repo', str(self.repo),
                        '--workspace', str(self.workspace), '--output', str(output)], 600)
            require(exit['exit_code'] == 0, 'real checkpoint audit failed')
            audits.append(json.loads(output.read_text()))
        require(audits[0] == audits[1], 'normal/optimized full audit disagreement')
        write(self.op/(self.label('physics')+'.json'), check_block(self.workspace, self.repo, group))
        folders = [self.workspace/'runs'/ROOTS[c['epoch']]/c['run_id'] for c in group]
        rows = original_inventory(self.workspace, folders)
        stage = self.op.name.lower()+'-'+epoch.lower()+'-'+str(through).zfill(4)
        dest = self.workspace/'evidence_exports'/stage
        dest.mkdir(mode=0o700)
        extras = [f for f in self.op.rglob('*') if f.is_file()]
        receipt = archive(self.workspace, stage, rows, extras, dest/'evidence.tar.gz')
        write(dest/'receipt.json', receipt)
        write(self.op/(self.label('backup-request')+'.backup-request.json'),
              dict(kind='CHECKPOINT', epoch=epoch, through=through, receipt=receipt))
        self.event('SECOND_COPY_PENDING_NO_NEW_ID', stage=stage)
        proof_path = dest/'second-copy-proof.json'
        seconds_left = (self.window['end'] - dt.datetime.now(SGT)).total_seconds()
        deadline = time.monotonic() + max(0, min(900, seconds_left))
        while not proof_path.exists():
            require(time.monotonic() < deadline, 'bounded second-copy deadline; no next ID')
            require(not (self.op/'BACKUP_INTEGRITY_ERROR.json').exists(),
                    'real backup integrity conflict; preserve and stop')
            self.check_server()
            time.sleep(1)
        proof = json.loads(proof_path.read_text())
        require_backup(proof, rows)
        verify_archive(dest/'evidence.tar.gz', receipt)
        require(proof['primary_archive_sha256'] == receipt['sha256'], 'archive identity changed')
        result = build(self.workspace, self.repo, epoch, self.cells, self.auth, proof)
        checkpoints = self.workspace/'operator/e3-checkpoints'
        checkpoints.mkdir(exist_ok=True)
        write(checkpoints/f'{epoch}-{through:04d}.json', result)
        self.event('REAL_CHECKPOINT_RELEASED_AUTOMATICALLY', epoch=epoch, through=through)

    def close_server(self):
        if self.server is None:
            return
        if self.server.poll() is None:
            if self.native_server is not None:
                require(live_same(self.native_server), 'refuse signaling replaced native server')
                os.kill(self.native_server['pid'], signal.SIGINT)
            else:
                from .processes import signal_owned
                signal_owned(self.server, self.server_expected, signal.SIGINT, group=True)
        receipt = self.record.finish(self.server_label, self.server, self.server_expected, 50)
        native_path = self.workspace/'runs'/(self.session+'.exit.json')
        require(native_path.is_file(), 'native close missing actual process exit receipt')
        native = json.loads(native_path.read_text())
        self.event('SERVER_ACTUAL_EXIT', launcher=receipt, native=native)
        require(native['exit_code'] in [0, 130] and
                (native['exit_code'] != 130 or native['signal'] == int(signal.SIGINT)) and
                (self.native_server is None or not live_same(self.native_server)),
                'abnormal server/resource cleanup; stop and preserve literal exits')
        require(receipt['exit_code'] == 0 or
                (receipt['exit_code'] == 1 and native['exit_code'] == 130),
                'unexpected launcher failure during close; literal receipt retained')
        self.require_no_native_process()

    def retain_failure(self, error):
        write(self.op/'STOPPED.json', dict(at=stamp(), type=type(error).__name__,
              message=str(error), active_or_consumed_id=self.current_cell,
              new_TEST_stopped=True, next_activity='CPU_DIAGNOSE_E2_SUBMISSION'))
        (self.op/'traceback.private.txt').open('x').write(traceback.format_exc())

    def retain_cleanup_failure(self, error):
        write(self.op/'CLEANUP_ERROR.json', dict(at=stamp(), type=type(error).__name__,
              message=str(error), new_TEST_stopped=True, no_silent_success=True))

    def finish(self, terminal):
        write(self.op/'operator-terminal.json', dict(at=stamp(), status=terminal,
              runtime_head=RUNTIME, report_head_is_not_runtime=True,
              review_commit=self.review_commit, last_fully_audited_consumed=self.last_progress,
              consumed_count_may_exceed_last_audit_after_failure=True,
              active_or_consumed_id=self.current_cell, scientific_result_self_approved=False,
              next_activity='CPU_DIAGNOSTICS_E2_SUBMISSION_OR_INDEPENDENT_RESULTS_REVIEW'))
        if self.lock_handle is not None:
            self.lock_handle.close()  # Unlock kernel lease; never delete historical lock.
