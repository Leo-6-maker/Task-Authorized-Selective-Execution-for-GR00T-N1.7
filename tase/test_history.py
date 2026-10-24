"""Read-only historical provenance. NEVER imported by TEST admission/runner.

    Immutable Git grant/code/config bindings authenticate acquisition identity.
    Revoked/changed-head epochs additionally require a reviewed closed-prefix
    anchor: old permission must never expand into unstarted historical IDs.
    Existing admission authorize() remains strict and is not relaxed here.
"""
import hashlib
import json
from pathlib import Path
import re
import math
import subprocess
from .test_authorization import require,git,bind_cell
from .evidence import sha256

ENGINEERING={'tase/shadow.py','tase/e2_context.py'}
HEX=re.compile(r'[0-9a-f]{40}')


def verify_lifecycle(receipt,worker):
    """Static proof for future full G outcomes, never changes old eligibility."""
    require(receipt.get('protocol')=='SHADOW_CLOSE_V1' and receipt.get('status')=='CLEAN' and
        receipt.get('clean') is True and receipt.get('forced') is False and
        receipt.get('term_sent') is False and receipt.get('kill_sent') is False and
        receipt.get('pipe_closed') is True and receipt.get('process_handle_closed') is True,
        'missing/forced/incomplete clean lifecycle')
    pid=receipt.get('worker_pid');require(type(pid) is int and pid>0 and pid==worker.get('worker_pid') and
        type(receipt.get('worker_returncode')) is int and receipt['worker_returncode']==0 and
        worker.get('worker_returncode')==0 and worker.get('clean_close') is True,
        'lifecycle actual worker identity/exit differs')
    messages=receipt.get('worker_receipts')
    require(isinstance(messages,list) and len(messages)==2 and all(isinstance(m,dict) for m in messages),
        'incomplete lifecycle handshake')
    ack,closed=messages;token=ack.get('close_token')
    require(ack.get('status')=='CLOSING' and closed.get('status')=='CLOSED' and
        isinstance(token,str) and re.fullmatch('[0-9a-f]{32}',token) is not None and
        closed.get('close_token')==token and ack.get('worker_pid')==closed.get('worker_pid')==pid and
        closed.get('native_finalized') is True,'invalid native-finalizer completion proof')
    stamps=[closed.get(k) for k in ['received_monotonic','finalizer_started_monotonic','finalizer_finished_monotonic']]
    require(all(type(s) in [int,float] and math.isfinite(s) for s in stamps) and
        stamps==sorted(stamps) and ack.get('received_monotonic')==stamps[0], 'invalid finalizer chronology')
    events=receipt.get('events',[]);names=[e.get('event') for e in events]
    required=['CLOSE_REQUEST','CLOSE_ACKNOWLEDGED','NATIVE_FINALIZER_COMPLETED','PARENT_PIPE_CLOSED','PROCESS_HANDLE_CLOSED']
    exits=[e for e in events if e.get('event')=='PROCESS_EXIT_OBSERVED']
    require([n for n in names if n!='PROCESS_EXIT_OBSERVED']==required and exits and
        events[0].get('close_token')==token and all(e.get('exit_code')==0 for e in exits),
        'lifecycle parent process exit/cleanup chronology differs')
    clocks=[e.get('parent_monotonic') for e in events]
    require(all(type(t) in [int,float] and math.isfinite(t) for t in clocks) and clocks==sorted(clocks) and
        clocks[0]<=stamps[0] and stamps[-1]<=next(e['parent_monotonic'] for e in events if e['event']=='NATIVE_FINALIZER_COMPLETED') and
        all(stamps[-1]<=e['parent_monotonic'] for e in exits), 'invalid parent/worker close chronology')


class AuditVersions:
    def __init__(self,repo,cfg,cells):
        self.repo=Path(repo);self.cfg=cfg;self.cells=cells;self.objects={};self.epochs={};self.rows={}
        path=self.repo/'reports/E2/automation/HISTORICAL_TEST_EPOCHS.json'
        self.anchors=json.loads(path.read_text())['epochs'] if path.exists() else []

    def blob(self,commit,path):
        require(HEX.fullmatch(commit) is not None and not Path(path).is_absolute() and
                '..' not in Path(path).parts and '\\' not in path,'invalid historical Git identity')
        key=(commit,path)
        if key not in self.objects:
            self.objects[key]=subprocess.check_output(['git','-C',str(self.repo),'show',commit+':'+path],stderr=subprocess.DEVNULL)
        return self.objects[key]

    def js(self,commit,path):return json.loads(self.blob(commit,path))
    def digest(self,commit,path):return hashlib.sha256(self.blob(commit,path)).hexdigest()
    def ancestor(self,a,b):
        require(HEX.fullmatch(a) is not None,'full historical commit required')
        require(subprocess.run(['git','-C',str(self.repo),'merge-base','--is-ancestor',a,b],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,'historical commit not on trusted main ancestry')

    def resolve(self,reservation,folder):
        auth=reservation['authorization'];key=json.dumps(auth,sort_keys=True)
        if key not in self.epochs:
            review=auth['review_commit'];path=auth['review_path'];head=auth['authorized_head']
            require(isinstance(review,str) and isinstance(head,str) and isinstance(path,str) and
                HEX.fullmatch(review) is not None and HEX.fullmatch(head) is not None and
                re.fullmatch(r'docs/reviews/[A-Za-z0-9_.-]+\.json',path),'invalid historical review reference')
            self.ancestor(review,'refs/remotes/origin/main')
            # Signed grants deliberately reference unmerged stacked code: the
            # code commit need not be an ancestor of the main review commit.
            kind=subprocess.run(['git','-C',str(self.repo),'cat-file','-t',head],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            require(kind.returncode==0 and kind.stdout.strip()==b'commit','historical code commit unavailable')
            grant=self.js(review,path)
            require(grant.get('reviewer')=='GPT' and grant.get('disposition')=='TEST_AUTHORIZED' and
                isinstance(grant.get('review_id'),str) and bool(grant['review_id']),'not an originally authorized reviewer grant')
            cfg=self.js(head,'configs/e2_test.json')
            # JSON canonical form distinguishes bool/int and preserves all semantic values.
            semantic=lambda c:json.dumps({k:v for k,v in c.items() if k!='frozen_sha256'},sort_keys=True)
            require(semantic(cfg)==semantic(self.cfg),'historical science/config semantics changed')
            require(set(cfg['frozen_sha256'])==set(self.cfg['frozen_sha256']),'historical frozen path set differs')
            for name,digest in cfg['frozen_sha256'].items():
                require(self.digest(head,name)==digest,'historical source blob differs: '+name)
                if name not in ENGINEERING:require(digest==self.cfg['frozen_sha256'][name],'non-engineering historical source changed')
            require(self.js(head,'configs/e2_test_cells.proposed.json')['cells']==self.cells,'historical planned cells differ')
            bindings={'authorized_head':head,'epoch':'E2','protocol_id':'TASE-002-v1.0','selected_k':3,'maximum_attempts':120,
                'test_config_sha256':self.digest(head,'configs/e2_test.json'),
                'test_cells_sha256':self.digest(head,'configs/e2_test_cells.proposed.json'),
                'protocol_lock_sha256':self.digest(head,'configs/e2_protocol_lock.json'),
                'runtime_lock_sha256':self.digest(head,'configs/runtime_lock_E2.json'),
                'splits_sha256':self.digest(head,'configs/e2_splits.json'),
                'selection_sha256':self.digest(head,'configs/e2_calib_selection.json')}
            for k,v in bindings.items():require(type(grant.get(k)) is type(v) and grant[k]==v,'historical grant binding: '+k)
            require(grant.get('allowed_run_ids')==[c['run_id'] for c in self.cells],'historical120 grant IDs differ')
            expected=dict(bindings,review_id=grant['review_id'],review_commit=review,review_path=path,
                review_blob=git(self.repo,'rev-parse',review+':'+path))
            require(auth==expected and all(type(auth[k]) is type(v) for k,v in expected.items()),'historical authorization receipt differs')
            current=git(self.repo,'rev-parse','HEAD');main_bytes=subprocess.run(['git','-C',str(self.repo),'show','refs/remotes/origin/main:'+path],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            active=main_bytes.returncode==0 and main_bytes.stdout.strip()==self.blob(review,path).strip()
            anchor=None
            if head!=current or not active:
                found=[a for a in self.anchors if a['execution_head']==head and a['grant_commit']==review and a['grant_path']==path]
                require(len(found)==1,'closed historical epoch requires one reviewed prefix anchor')
                anchor=self._anchor(found[0])
            self.epochs[key]=dict(cfg=cfg,identity=expected,anchor=anchor,grant_currently_active=active)
        item=self.epochs[key];identity=item['identity'];cfg=item['cfg'];run=reservation['run_id']
        bind_cell(self.cells,run,reservation)
        require(reservation['repo_sha']==identity['authorized_head'] and reservation['config_hash']==identity['test_config_sha256'] and
            reservation['runtime_lock_hash']==identity['runtime_lock_sha256'],'historical reservation code/config differs')
        if item['anchor'] is not None:
            a=item['anchor'];row=a['rows'].get(run)
            require(row is not None and row['reserved'] is True,'run outside reviewed consumed historical prefix')
            expected_hashes=dict(a['sources'])
            expected_hashes['runs/TEST/'+run+'/artifact_manifest.json']=row['artifact_manifest_sha256']
            expected_hashes['runs/TEST/'+run+'/task_spec.json']=row['trusted_task_spec_sha256']
            for name in ['reservation.json','result.json','artifact_manifest.json','task_spec.json','supervisor_exit.json']:
                p=folder/name;logical='runs/TEST/'+run+'/'+name
                require(logical in expected_hashes and p.is_file() and sha256(p)==expected_hashes[logical],'closed epoch original hash differs: '+logical)
            for suffix in ['exit.json','exit.started.json']:
                p=folder.parent.parent/(run+'.'+suffix);logical='runs/'+run+'.'+suffix
                require(logical in expected_hashes and p.is_file() and sha256(p)==expected_hashes[logical],'closed epoch actual process receipt differs')
        self.rows[run]=dict(run_id=run,execution_head=identity['authorized_head'],config_sha256=identity['test_config_sha256'],
            grant_commit=identity['review_commit'],grant_blob=identity['review_blob'],historical_only=True,
            grant_currently_active=item['grant_currently_active'],closed_prefix_anchored=item['anchor'] is not None)
        return cfg,identity

    def _anchor(self,a):
        review=a['review_commit'];report=a['report_head'];self.ancestor(review,'refs/remotes/origin/main')
        require(re.fullmatch(r'docs/reviews/[A-Za-z0-9_.-]+\.md',a['review_path']) is not None,
                'closed epoch must cite an independent review path')
        text=self.blob(review,a['review_path']).decode()
        require('**Reviewer:** GPT.' in text and report in text and a['execution_head'] in text,
                'historical epoch not bound by independent main review')
        ledger=self.js(report,a['ledger_path']);manifest=self.js(report,a['manifest_path']);origins=self.js(report,a['receipt_origins_path'])
        require(len(ledger)==120 and [r['run_id'] for r in ledger]==[c['run_id'] for c in self.cells],'reviewed ledger is not original120')
        consumed=[r for r in ledger if r['reserved']]
        require([r['run_id'] for r in consumed]==[c['run_id'] for c in self.cells[:a['consumed_count']]],'reviewed historical prefix differs')
        proof=self.js(report,a['backup_proof_path'])
        require(proof['status'].startswith('ALL') and proof['status'].endswith('TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_VERIFIED') and
            any(v['sha256']==a['original_archive_sha256'] and v['status']=='TWO_LOCATIONS_ARCHIVE_AND_EVERY_MEMBER_SHA256_VERIFIED' for v in proof['archives']),
            'historical original backup provenance missing')
        sources={r['path']:r['sha256'] for r in manifest['source_files']}
        for r in origins['artifacts']:
            if r['original_id'].startswith('runs/'):
                require(r['original_id'] not in sources or sources[r['original_id']]==r['original_sha256'],'conflicting reviewed original hashes')
                sources[r['original_id']]=r['original_sha256']
        return dict(rows={r['run_id']:r for r in consumed},sources=sources)

    def validate_inventory(self,entries):
        """A known closed prefix cannot silently become NOT_STARTED after loss."""
        by_id={p.name:p for p in entries}
        for epoch in self.epochs.values():
            if epoch['anchor'] is None:continue
            for run in epoch['anchor']['rows']:
                require(run in by_id and (by_id[run]/'reservation.json').is_file(),
                    'reviewed historically consumed TEST unit missing')
                self.resolve(json.loads((by_id[run]/'reservation.json').read_text()),by_id[run])
