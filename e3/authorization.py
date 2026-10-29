"""New E3 grants only; old E2/R013 permits cannot launch or reserve E3."""
import json,re,subprocess
from pathlib import Path
from .discovery import require,sha
from .manifest import verify

def git(repo,*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()

def validate_grant(grant,lock,cells,identity):
    require(grant.get('disposition')=='E3_TEST_AUTHORIZED' and grant.get('protocol_id')=='E3-001-v1.0','new independent E3 grant required')
    require(lock.get('status')=='FROZEN_BY_INDEPENDENT_REVIEW' and lock.get('runtime_scene_binding_verified') is True,'proposed protocol/live scene blocker not frozen')
    for key in ['authorized_head','protocol_lock_sha256','cells_file_sha256','runtime_lock_sha256']:
        require(grant.get(key)==identity[key],'E3 grant code/lock/cells/runtime mismatch')
    require(grant.get('budgets')=={'E3A':112,'E3B':48} and len(cells)==160,'reviewed full candidate budgets required; reduced variant needs explicit protocol revision')
    require(grant.get('gate_k')==3 and grant.get('bootstrap_seed')==641500 and grant.get('maximum_controls')==720,'E3 grant scientific contract mismatch')
    require(grant.get('resource_authorization_required') is True,'fresh separate resource permit required')

def authorize(repo,review_commit,review_path):
    repo=Path(repo)
    require(type(review_commit) is str and re.fullmatch('[0-9a-f]{40}',review_commit),'full independent E3 review commit required')
    require(type(review_path) is str and re.fullmatch(r'docs/reviews/[A-Za-z0-9._-]+\.json',review_path),'explicit independent review path required')
    require(not git(repo,'status','--porcelain'),'E3 runtime needs clean exact committed tree')
    # Revoked or superseded historical grant never admits a new native execution.
    text=git(repo,'show',review_commit+':'+review_path)
    require(git(repo,'show','refs/remotes/origin/main:'+review_path)==text,'E3 grant no longer current on fetched main')
    source=json.loads((repo/'configs/e3_sources.proposed.json').read_text());cells=json.loads((repo/'configs/e3_cells.proposed.json').read_text())['cells'];verify(cells,source)
    lock=json.loads((repo/'configs/e3_protocol_lock.proposed.json').read_text());identity=dict(authorized_head=git(repo,'rev-parse','HEAD'),protocol_lock_sha256=sha(repo/'configs/e3_protocol_lock.proposed.json'),cells_file_sha256=sha(repo/'configs/e3_cells.proposed.json'),runtime_lock_sha256=sha(repo/'configs/runtime_lock_E2.json'))
    grant=json.loads(text);validate_grant(grant,lock,cells,identity)
    from .freeze import verify_freeze
    verify_freeze(repo)
    for name,digest in lock['source_sha256'].items():require(sha(repo/name)==digest,'E3 source lock differs: '+name)
    return lock,cells,dict(identity,review_commit=review_commit,review_path=review_path,review_blob=git(repo,'rev-parse',review_commit+':'+review_path),budgets=grant['budgets'],grant_protocol='E3-001-v1.0')

def resource(record,identity):
    require(record.get('protocol_id')=='E3-001-v1.0' and record.get('authorized_head')==identity['authorized_head'] and record.get('review_commit')==identity['review_commit'],'E2/stale resource permit cannot authorize E3')
    require(record.get('shared_gpu_inference_authorized') is True and type(record.get('gpu_index')) is int and record['gpu_index']==1 and record.get('gpu_uuid') and record.get('owner_approval_evidence'),'current explicit owner GPU1-only allocation required')
