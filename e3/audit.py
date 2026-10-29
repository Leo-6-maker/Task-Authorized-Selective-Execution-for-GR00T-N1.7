"""Historical E3 source authentication; a revoked grant only verifies originals."""
import json
from pathlib import Path
from .authorization import git,validate_grant
from .discovery import require,sha
from .audit_manifest import verify_complete_manifest
from tase.test_history import verify_lifecycle

def original(workspace,repo,folder,reservation):
    auth=reservation['authorization'];head=auth['authorized_head'];grant=json.loads(git(repo,'show',auth['review_commit']+':'+auth['review_path']))
    require(git(repo,'rev-parse',auth['review_commit']+':'+auth['review_path'])==auth['review_blob'],'historical E3 grant blob changed')
    lock=json.loads(git(repo,'show',head+':configs/e3_protocol_lock.proposed.json'));cells=json.loads(git(repo,'show',head+':configs/e3_cells.proposed.json'))['cells']
    import hashlib
    identity=dict(authorized_head=head,**{key:hashlib.sha256(subprocess_blob(repo,head,path)).hexdigest() for key,path in [('protocol_lock_sha256','configs/e3_protocol_lock.proposed.json'),('cells_file_sha256','configs/e3_cells.proposed.json'),('runtime_lock_sha256','configs/runtime_lock_E2.json')]})
    validate_grant(grant,lock,cells,identity);require(all(auth[k]==v for k,v in identity.items()),'historical original source binding differs')
    require(reservation['cell']==next(c for c in cells if c['run_id']==folder.name),'historical cell differs')
    # Partial/failed results remain consumed/unknown; never pretend missing evidence passes.
    if not (folder/'result.json').exists():return
    result=json.loads((folder/'result.json').read_text());require(result['authorization']==auth and result['repo_sha']==head,'historical result code/grant differs')
    if result['status'] not in ['SUCCESS','TIME_LIMIT','SEMANTIC_ABORT']:return
    cell=reservation['cell']
    from e3.physics_audit import verify_physics
    verify_physics(folder,cell,result)
    child=json.loads((workspace/'runs'/(folder.name+'.exit.json')).read_text());require(child.get('exit_code')==0,'complete E3 lacks actual native exit0')
    claim=json.loads((folder/'runner_claim.json').read_text());require(claim['reservation_sha256']==sha(folder/'reservation.json') and claim['authorization']==auth,'E3 claim does not authenticate original reservation')
    required=['reservation.json','runner_claim.json','result.json','task_spec.json','benchmark_init.npy','settled_state.npy','scene.xml','reset_parity.json','horizon.json','gate_decisions.jsonl','snapshots.jsonl','actual_requests.jsonl','control_trace.npz','rollout.mp4','supervisor_start.json']
    verify_complete_manifest(workspace,folder,required)
    require(sha(folder/'benchmark_init.npy')==cell['init_hash'],'historical heldout bytes changed')
    from .scene import validate
    from tase.task_spec import TaskSpec
    source=json.loads(git(repo,'show',head+':configs/e3_sources.proposed.json'));validate(TaskSpec(**json.loads((folder/'task_spec.json').read_text())),cell,next(t for t in source['tasks'] if t['task']==cell['task']))
    decisions=[json.loads(x) for x in (folder/'gate_decisions.jsonl').read_text().splitlines()]
    require(bool(decisions),'complete E3 missing boundary evidence')
    for row in decisions:
        if row['decision']!='ACCEPT':require(row['completed_controls_before']==row['completed_controls_after'],'rejected E3 executed controls')
    if cell['system']=='G':verify_lifecycle(json.loads((folder/'shadow_close.json').read_text()),json.loads((folder/'shadow_worker_exit.json').read_text()))
    if cell['system'] in ['A0','G']:
        guards=[json.loads(x) for x in (folder/'noninterference.jsonl').read_text().splitlines()];require(len(guards)==len(decisions) and all(x['main_state_unchanged'] is True and x['policy_rng_unchanged'] is True and x['before_hash']==x['after_hash'] and x['policy_rng_before']==x['policy_rng_after'] for x in guards),'missing/failed E3 state/RNG guard')

def subprocess_blob(repo,head,path):
    import subprocess
    return subprocess.check_output(['git','show',head+':'+path],cwd=repo)
