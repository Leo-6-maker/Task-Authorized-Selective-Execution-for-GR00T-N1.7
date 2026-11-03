"""CPU-only TEST admission. A proposal, CLI boolean or local JSON grants nothing.

The independently authored grant must be a committed JSON file on fetched main.
This enforces the repository's role/evidence workflow, not cryptographic roles.
No grant is supplied by this executor; R005 explicitly does not qualify.
"""
import json
import re
import subprocess
from pathlib import Path
from .evidence import sha256


def require(ok, message):
    if not ok:
        raise ValueError(message)


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def frozen(repo):
    repo = Path(repo)
    cfg = json.loads((repo/'configs/e2_test.json').read_text())
    require(cfg['split'] == 'TEST' and cfg['run_epoch'] == 'E2' and
            cfg['protocol_id'] == 'TASE-002-v1.0', 'not E2 TEST')
    for key, value in {'gate_k': 3, 'maximum_episode_attempts': 120,
                       'execution_horizon_candidate': 8, 'max_inner_steps': 720,
                       'settling_steps': 10, 'oracle_lift_m': .02,
                       'oracle_sustain_control_steps': 2,
                       'oracle_relative_motion_tolerance_m': .01}.items():
        require(type(cfg[key]) is type(value) and cfg[key] == value, 'frozen contract: '+key)
    # The values themselves are also bound to the exact reviewed code head.
    for path, digest in cfg['frozen_sha256'].items():
        require(sha256(repo/path) == digest, 'frozen file changed: '+path)
    lock = json.loads((repo/'configs/e2_protocol_lock.json').read_text())
    require(lock['selected_k'] == 3 and lock['TEST_authorized'] is False,
            'executor must not toggle the proposed lock into a grant')
    selection = json.loads((repo/'configs/e2_calib_selection.json').read_text())
    require(selection['selected_k'] == 3 and selection['status'] == 'SELECTED_WITHIN_PREDECLARED_RULE',
            'frozen CALIB selection required')
    catalog = json.loads((repo/'configs/e2_test_cells.proposed.json').read_text())
    cells = catalog['cells']
    require(catalog['planned_runs'] == 120 and len(cells) == 120, 'exactly120 cells required')
    require([c['run_id'] for c in cells] == [f'e2-test-{n:04d}' for n in range(1,121)],
            'missing, duplicate, reordered or invalid TEST ID')
    split = json.loads((repo/'configs/e2_splits.json').read_text())
    identities = {(r['task'],r['init_index']):r['init_hash'] for r in split['rows'] if r['split']=='TEST'}
    require(len(identities) == 30, '30 fixed TEST initialization clusters required')
    expected = []
    for ti, task in enumerate(['alphabet_soup','cream_cheese','ketchup']):
        for init in range(6,16):
            for condition in ['C0','C2']:
                for system in ['B0','G']:
                    expected.append(dict(run_id=f'e2-test-{len(expected)+1:04d}',task=task,
                        init_index=init,init_hash=identities[(task,init)],condition=condition,system=system,
                        scenario_id=f'E2-TEST-{task}-i{init}-{condition}',
                        policy_seed=640400+ti*100+init*2+(condition=='C2'),
                        environment_seed=640401+ti*100+init*2+(condition=='C2'),
                        policy_target={'alphabet_soup':'butter','cream_cheese':'alphabet_soup',
                                       'ketchup':'alphabet_soup'}[task] if condition=='C2' else task))
    require(cells == expected, 'TEST cells differ from frozen task/init/condition/system/seed/order')
    return cfg, cells


def authorize(repo, review_commit, review_path):
    """Resolve a reviewer grant from main, never from caller-controlled JSON."""
    repo = Path(repo)
    require(isinstance(review_commit,str) and re.fullmatch('[0-9a-f]{40}',review_commit),
            'explicit GPT TEST review commit required')
    require(isinstance(review_path,str) and re.fullmatch(r'docs/reviews/[A-Za-z0-9_.-]+\.json',review_path),
            'committed GPT authorization JSON path required')
    cfg, cells = frozen(repo)
    require(not git(repo,'status','--porcelain'), 'dirty checkout cannot execute TEST')
    head = git(repo,'rev-parse','HEAD')
    require(subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',review_commit,
                            'refs/remotes/origin/main'],stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL).returncode == 0,
            'review commit must be on fetched main; no automatic fetch or local-file grant')
    grant = json.loads(git(repo,'show',review_commit+':'+review_path))
    require(grant.get('reviewer') == 'GPT' and grant.get('disposition') == 'TEST_AUTHORIZED' and
            isinstance(grant.get('review_id'),str) and bool(grant['review_id']),
            'independent explicit GPT TEST_AUTHORIZED record required')
    required = {'authorized_head':head,'epoch':'E2','protocol_id':'TASE-002-v1.0',
                'selected_k':3,'maximum_attempts':120,'test_config_sha256':sha256(repo/'configs/e2_test.json'),
                'test_cells_sha256':sha256(repo/'configs/e2_test_cells.proposed.json'),
                'protocol_lock_sha256':sha256(repo/'configs/e2_protocol_lock.json'),
                'runtime_lock_sha256':sha256(repo/'configs/runtime_lock_E2.json'),
                'splits_sha256':sha256(repo/'configs/e2_splits.json'),
                'selection_sha256':sha256(repo/'configs/e2_calib_selection.json')}
    for key,value in required.items():
        require(type(grant.get(key)) is type(value) and grant[key] == value, 'TEST grant binding: '+key)
    require(grant.get('allowed_run_ids') == [c['run_id'] for c in cells], 'grant must cover exact ordered120')
    # A later main record cannot silently revoke/replace this file while old approval is reused.
    require(git(repo,'show','refs/remotes/origin/main:'+review_path) ==
            git(repo,'show',review_commit+':'+review_path), 'TEST grant changed on main')
    return cfg, cells, dict(required, review_id=grant['review_id'], review_commit=review_commit,
                            review_path=review_path,
                            review_blob=git(repo,'rev-parse',review_commit+':'+review_path))


def bind_cell(cells, run_id, supplied=None):
    matches = [c for c in cells if c['run_id'] == run_id]
    require(len(matches) == 1, 'unknown/duplicate TEST cell')
    cell = matches[0]
    if supplied is not None:
        require(all(supplied.get(k) == v and type(supplied.get(k)) is type(v) for k,v in cell.items()),
                'TEST caller cell mismatch')
    return dict(cell)


def validate_identity(cell, spec, identity):
    from .task_spec import TaskSpec
    actual = TaskSpec(**spec).validate()
    require(actual.target == cell['task']+'_1' == identity['true_task_target'] and
            actual.basket == 'basket_1', 'TEST trusted TaskSpec differs')
    require(cell['policy_target']+'_1' in actual.objects, 'actual policy target absent from scene')
    require(identity['cell'] == cell, 'actual identity cell differs')
    require(identity['actual_policy_language'] ==
            'pick up the '+cell['policy_target'].replace('_',' ')+' and place it in the basket',
            'TEST actual instruction differs from frozen condition')
