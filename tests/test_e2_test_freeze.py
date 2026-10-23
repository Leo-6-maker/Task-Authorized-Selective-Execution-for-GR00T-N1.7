"""SYNTHETIC CPU admission/denominator tests. No model, simulator or TEST unit.

The temporary git repository and GPT-looking fixture are test data, never a real
review. No authorization fixture is committed in docs/reviews or used remotely.
"""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tase.test_authorization import frozen,authorize,bind_cell,validate_identity
from tase.test_ledger import reserve,claim,inventory
from tase.evidence import sha256,write_json
from tase.execution_gate import KEYS,execute_checked
from tase.test_execution import TestBoundary
from scripts.e2_audit_test import statistics,audit as audit_test
from scripts.e2_run_test import run

REPO=Path(__file__).resolve().parents[1]


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.DEVNULL).strip()


def fixture(root):
    repo=root/'repo';repo.mkdir()
    shutil.copytree(REPO/'configs',repo/'configs')
    shutil.copytree(REPO/'tase',repo/'tase',ignore=shutil.ignore_patterns('__pycache__'))
    git(repo,'init','-q');git(repo,'config','user.name','Synthetic fixture')
    git(repo,'config','user.email','fixture@example.invalid');git(repo,'add','.')
    git(repo,'commit','-qm','SYNTHETIC code; never an actual TEST authorization')
    head=git(repo,'rev-parse','HEAD');_,cells=frozen(repo)
    grant=dict(reviewer='GPT',review_id='SYNTHETIC_ONLY',disposition='TEST_AUTHORIZED',authorized_head=head,
        epoch='E2',protocol_id='TASE-002-v1.0',selected_k=3,maximum_attempts=120,
        test_config_sha256=sha256(repo/'configs/e2_test.json'),
        test_cells_sha256=sha256(repo/'configs/e2_test_cells.proposed.json'),
        protocol_lock_sha256=sha256(repo/'configs/e2_protocol_lock.json'),
        runtime_lock_sha256=sha256(repo/'configs/runtime_lock_E2.json'),
        splits_sha256=sha256(repo/'configs/e2_splits.json'),selection_sha256=sha256(repo/'configs/e2_calib_selection.json'),
        allowed_run_ids=[c['run_id'] for c in cells])
    path='docs/reviews/SYNTHETIC_ONLY.json';write_json(repo/path,grant)
    git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC reviewer fixture')
    review=git(repo,'rev-parse','HEAD');git(repo,'update-ref','refs/remotes/origin/main',review)
    git(repo,'checkout','-q','--detach',head)
    return repo,review,path,grant


class TestFreezeTests(unittest.TestCase):
    def test_current_frozen_catalog_and_valid_synthetic_main_grant(self):
        _,cells=frozen(REPO);self.assertEqual(len(cells),120)
        self.assertEqual(cells[40]['policy_seed'],640512)  # TEST *100, not DEV *10.
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,_=fixture(Path(tmp))
            _,cc,identity=authorize(repo,rev,path)
            self.assertEqual(cc,cells);self.assertEqual(identity['review_id'],'SYNTHETIC_ONLY')

    def test_missing_permission_never_creates_process_or_reservation(self):
        with tempfile.TemporaryDirectory() as tmp,patch('subprocess.Popen') as popen:
            root=Path(tmp)
            with self.assertRaises(ValueError):
                run(root,REPO,'e2-test-0001',None,None,root/'missing',root/'no-python','no-server')
            popen.assert_not_called();self.assertFalse((root/'runs').exists())

    def test_direct_native_entry_cannot_bypass_permission(self):
        from tase.epoch_runner import main
        with tempfile.TemporaryDirectory() as tmp,patch('subprocess.Popen') as popen:
            with self.assertRaises(ValueError):
                main(['--workspace',tmp,'--run-id','e2-test-0001','--task','alphabet_soup',
                      '--init-index','6','--config',str(REPO/'configs/e2_test.json'),
                      '--allocation-record',str(Path(tmp)/'nonexistent')])
            popen.assert_not_called();self.assertFalse((Path(tmp)/'runs').exists())

    def test_server_launcher_missing_permission_never_inspects_gpu_or_loads_model(self):
        from scripts.e2_test_server import serve
        with tempfile.TemporaryDirectory() as tmp,patch('subprocess.Popen') as popen:
            root=Path(tmp)
            with self.assertRaises(ValueError):serve(root,REPO,None,None,root/'no-allocation',
                root/'no-python',root/'no-python','test-server-fixture',0)
            popen.assert_not_called();self.assertFalse((root/'runs').exists())

    def test_grant_wrong_head_scope_k_hash_or_disposition_refused(self):
        for key,value in [('authorized_head','0'*40),('selected_k',2),('selected_k',True),
                          ('maximum_attempts',121),('runtime_lock_sha256','0'*64),
                          ('disposition','CONDITIONAL_SCIENTIFIC_FREEZE__TEST_NOT_AUTHORIZED'),
                          ('reviewer','Codex'),('allowed_run_ids',[])]:
            with self.subTest(key=key,value=value),tempfile.TemporaryDirectory() as tmp:
                repo,rev,path,grant=fixture(Path(tmp));head=git(repo,'rev-parse','HEAD')
                git(repo,'checkout','-q','--detach',rev)
                grant[key]=value;(repo/path).write_text(json.dumps(grant))
                git(repo,'add','.');git(repo,'commit','-qm','invalid synthetic grant')
                bad=git(repo,'rev-parse','HEAD');git(repo,'update-ref','refs/remotes/origin/main',bad)
                git(repo,'checkout','-q','--detach',head)
                with self.assertRaises(ValueError):authorize(repo,bad,path)

    def test_unreachable_review_dirty_checkout_and_changed_main_grant_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,_=fixture(Path(tmp));head=git(repo,'rev-parse','HEAD')
            git(repo,'update-ref','refs/remotes/origin/main',head)
            with self.assertRaises(ValueError):authorize(repo,rev,path)
            git(repo,'update-ref','refs/remotes/origin/main',rev)
            (repo/'dirty.txt').write_text('dirty')
            with self.assertRaises(ValueError):authorize(repo,rev,path)

    def test_bad_cell_fields_and_unknown_ids_refused(self):
        _,cells=frozen(REPO);cell=cells[0]
        for key,value in [('task','ketchup'),('init_hash','0'*64),('init_index',7),('condition','C2'),
                          ('system','G'),('policy_seed',1),('environment_seed',1),
                          ('scenario_id','different'),('policy_target','butter'),('run_id','e2-test-9999')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                bind_cell(cells,cell['run_id'],dict(cell,**{key:value}))
        for bad in ['../e2-test-0001','e2-test-0121','e2-dev-0001','e2-test-1','']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):bind_cell(cells,bad)

    def test_missing_duplicate_corrupt_and_reordered_manifest_refused(self):
        for mutate in ['missing','duplicate','corrupt','reorder']:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as tmp:
                repo,_,_,_=fixture(Path(tmp));path=repo/'configs/e2_test_cells.proposed.json'
                data=json.loads(path.read_text())
                if mutate=='missing':data['cells'].pop()
                if mutate=='duplicate':data['cells'][1]=data['cells'][0]
                if mutate=='reorder':data['cells'].reverse()
                path.write_text('' if mutate=='corrupt' else json.dumps(data))
                with self.assertRaises(ValueError):frozen(repo)

    def test_frozen_contract_and_oracle_source_changes_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,_,_,_=fixture(Path(tmp));path=repo/'configs/e2_test.json';old=path.read_text()
            for key,value in [('gate_k',2),('max_inner_steps',721),('execution_horizon_candidate',16),
                              ('oracle_lift_m',.03),('maximum_episode_attempts',121)]:
                data=json.loads(old);data[key]=value;path.write_text(json.dumps(data))
                with self.subTest(key=key),self.assertRaises(ValueError):frozen(repo)
            path.write_text(old)
            with (repo/'tase/event_oracle.py').open('a') as f:f.write('\n# changed\n')
            with self.assertRaises(ValueError):frozen(repo)

    def test_failed_interrupted_reservations_consume_all120_and_no_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo,rev,path,_=fixture(root)
            _,cells,identity=authorize(repo,rev,path);ledger=root/'TEST'
            for cell in cells:
                folder=reserve(ledger,cell,cells,identity)
                # No result at all: an interrupted/failed cell still counts.
                write_json(folder/'supervisor_exit.json',{'wrapper_returncode':143,'complete_child_receipt':False})
            self.assertEqual(len(inventory(ledger,cells)),120)
            with self.assertRaises(ValueError):reserve(ledger,cells[-1],cells,identity)
            self.assertEqual(len(list(ledger.glob('*/reservation.json'))),120)

    def test_partial_empty_folder_locks_next_cell_and_cannot_be_reclaimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo,rev,path,_=fixture(root);_,cells,identity=authorize(repo,rev,path)
            ledger=root/'TEST';(ledger/cells[0]['run_id']).mkdir(parents=True)
            self.assertEqual(len(inventory(ledger,cells)),1)
            for cell in cells[:2]:
                with self.assertRaises(ValueError):reserve(ledger,cell,cells,identity)
            lock=ledger/'.reservation-lock';lock.mkdir()
            with self.assertRaises(FileExistsError):reserve(ledger,cells[1],cells,identity)
            self.assertTrue(lock.exists())

    def test_empty_reservation_audit_counts_slot_without_claiming_clean_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runs/TEST/e2-test-0001').mkdir(parents=True)
            report=audit_test(root,REPO)
            self.assertEqual(report['reserved'],1);self.assertEqual(report['experiment_status'],'UNRECONCILED')
            self.assertEqual(report['missing_reservation_records'],['e2-test-0001'])
            self.assertEqual(report['full_outcomes'],0)

    def test_test_numeric_manifest_passes_and_empty_corrupt_manifest_fails(self):
        from test_e2_audit import build,seal
        from scripts.audit_epoch import audit
        for corruption in [None,[],[{'bad':'manifest'}]]:
            with self.subTest(corruption=corruption),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);folder=build(root);run='e2-test-0001'
                target=root/'runs/TEST'/run;target.parent.mkdir();folder.rename(target)
                for name in ['reservation.json','result.json']:
                    p=target/name;r=json.loads(p.read_text());r.update(run_id=run,split='TEST',config_hash=sha256(REPO/'configs/e2_test.json'))
                    p.write_text(json.dumps(r))
                for suffix in ['exit.json','exit.started.json']:
                    (root/'runs'/f'e2-dev-0001.{suffix}').rename(root/'runs'/f'{run}.{suffix}')
                (root/'runs/DEV').rmdir();seal(root,target)
                if corruption is None:
                    self.assertEqual(audit(root,REPO/'configs/e2_test.json',test_audit=True)['test_used'],1)
                else:
                    (target/'artifact_manifest.json').write_text(json.dumps(corruption))
                    with self.assertRaises((ValueError,KeyError)):audit(root,REPO/'configs/e2_test.json',test_audit=True)

    def test_trusted_task_and_actual_language_are_independently_checked(self):
        from test_e2_audit import build
        with tempfile.TemporaryDirectory() as tmp:
            folder=build(Path(tmp));spec=json.loads((folder/'task_spec.json').read_text())
            # This synthetic scene has a synthetic basket; it must not pass TEST binding.
            _,cells=frozen(REPO)
            with self.assertRaises(ValueError):validate_identity(cells[0],spec,
                dict(true_task_target='alphabet_soup_1',cell=cells[0],actual_policy_language='wrong'))

    def test_exclusive_child_claim_and_original_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo,rev,path,_=fixture(root);_,cells,identity=authorize(repo,rev,path)
            folder=reserve(root/'TEST',cells[0],cells,identity);record=json.loads((folder/'reservation.json').read_text())
            claim(folder,record)
            with self.assertRaises(FileExistsError):claim(folder,record)
            with self.assertRaises(ValueError):reserve(root/'TEST',cells[0],cells,identity)

    def test_invalid_prediction_reject_error_zero_steps_accept_same_prefix(self):
        prefix={key:np.zeros((16,1),np.float32) for key in KEYS};executed=[]
        for score in [{'decision':'REJECT'},{'decision':'ERROR'},{'decision':'invalid'},{}]:
            decision,_=execute_checked(prefix,lambda p:score,lambda p:executed.append(p))
            self.assertNotEqual(decision['decision'],'ACCEPT');self.assertEqual(executed,[])
        def fail(p):raise ValueError('synthetic bad prediction')
        decision,_=execute_checked(prefix,fail,lambda p:executed.append(p))
        self.assertEqual(decision['decision'],'ERROR');self.assertEqual(executed,[])
        execute_checked(prefix,lambda p:{'decision':'ACCEPT'},lambda p:executed.append(p))
        self.assertEqual(len(executed),1)
        self.assertTrue(all(np.array_equal(executed[0][k],prefix[k]) for k in KEYS))

    def test_stop_after_reject_or_monitor_error_blocks_next_prediction_and_step(self):
        for output in [{'decision':'REJECT'},{'decision':'ERROR'},
                       {'decision':'ACCEPT','checked_controls':0},
                       {'decision':'ACCEPT','checked_controls':9}]:
            with self.subTest(output=output):
                boundary=TestBoundary('G');steps=[];calls=[]
                prefix={key:np.zeros((16,1),np.float32) for key in KEYS}
                def monitor(p):calls.append(1);return output
                decision,_=boundary.execute(prefix,monitor,steps.append)
                self.assertNotEqual(decision['decision'],'ACCEPT');self.assertEqual(steps,[])
                with self.assertRaises(ValueError):boundary.execute(prefix,monitor,steps.append)
                self.assertEqual(len(calls),1);self.assertEqual(steps,[])

    def test_test_boundary_accepts_same_native_prefix_and_bad_numeric_fails_closed(self):
        boundary=TestBoundary('G');steps=[]
        prefix={key:np.zeros((16,1),np.float32) for key in KEYS}
        decision,_=boundary.execute(prefix,lambda p:{'decision':'ACCEPT','checked_controls':8},steps.append)
        self.assertEqual(decision['decision'],'ACCEPT');self.assertEqual(len(steps),1)
        self.assertTrue(all(np.array_equal(steps[0][k],prefix[k]) for k in KEYS))
        prefix[KEYS[0]][0,0]=np.nan
        decision,_=boundary.execute(prefix,lambda p:{'decision':'ACCEPT','checked_controls':8},steps.append)
        self.assertEqual(decision['decision'],'ERROR');self.assertEqual(len(steps),1)

    def test_invalid_prediction_lengths_snapshot_sequence_and_terminal_flags(self):
        from tase.test_context import validate_prediction_envelope
        normal=dict(status='PASS',steps=8,frames=[dict(step=i) for i in range(57,65)],
            source_snapshot_hash='1'*64,restored_snapshot_hash='1'*64,terminated=False,truncated=False)
        validate_prediction_envelope(normal,'1'*64,56)
        for key,value in [('steps',7),('steps',True),('frames',[]),('status','ERROR'),
                          ('restored_snapshot_hash','2'*64),('terminated',1),
                          ('frames',[dict(step=i) for i in range(1,9)])]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_prediction_envelope(dict(normal,**{key:value}),'1'*64,56)
        short=dict(normal,steps=1,frames=[dict(step=57)])
        with self.assertRaises(ValueError):validate_prediction_envelope(short,'1'*64,56)
        validate_prediction_envelope(dict(short,terminated=True),'1'*64,56)
        with self.assertRaises(ValueError):validate_prediction_envelope(normal,'1'*64,720)

    def test_unopened_audit_keeps120_unknowns_and_no_zero_event_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=audit_test(Path(tmp),REPO)
            self.assertEqual(report['reserved'],0);self.assertEqual(report['experiment_status'],'UNOPENED')
            self.assertEqual(len(report['rows']),120);self.assertIsNone(report['statistics']['candidate_UAR'])
            for group in report['statistics']['groups']:
                self.assertEqual(group['metrics']['wrong_lift']['lower'],0)
                self.assertEqual(group['metrics']['wrong_lift']['upper'],1)
            self.assertFalse((Path(tmp)/'runs').exists())

    def test_bootstrap_is_paired_reproducible_with_missing_units_retained(self):
        _,cells=frozen(REPO)
        rows=[dict(c,reserved=True,outcome_known=True,status='SUCCESS',official_success=True,
            first_wrong_lift_step=None,observed_controls=100,policy_requests_observed=13) for c in cells]
        rows[0].update(outcome_known=False,status='STARTED_OR_INTERRUPTED')
        first=statistics(rows);self.assertEqual(first,statistics(rows))
        group=next(g for g in first['groups'] if (g['task'],g['condition'],g['system'])==('alphabet_soup','C0','B0'))
        self.assertEqual(group['planned_units'],10);self.assertEqual(group['interrupted_or_missing'],1)
        self.assertEqual(group['metrics']['wrong_lift']['upper'],.1)
        contrast=next(c for c in first['paired_contrasts'] if c['task']=='ketchup' and c['metric']=='official_success')
        self.assertEqual(contrast['paired_cluster_percentile95_bounds'],[0.,0.])


if __name__=='__main__':unittest.main()
