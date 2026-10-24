"""Temporary Git-only SYNTHETIC epochs. Never a real GPT grant or TEST run."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_e2_test_freeze import fixture,git
from tase.test_authorization import frozen,authorize
from tase.test_history import AuditVersions
from tase.evidence import sha256,write_json


def epochs(root):
    repo,rev,path,grant=fixture(root);cfg,cells,identity=authorize(repo,rev,path);old=identity['authorized_head']
    folder=root/'runs/TEST'/cells[0]['run_id'];folder.mkdir(parents=True)
    reservation=dict(cells[0],authorization=identity,repo_sha=old,config_hash=identity['test_config_sha256'],runtime_lock_hash=identity['runtime_lock_sha256'])
    write_json(folder/'reservation.json',reservation);write_json(folder/'result.json',dict(reservation,status='SUCCESS'))
    write_json(folder/'artifact_manifest.json',[]);write_json(folder/'task_spec.json',{'SYNTHETIC_IDENTITY_ONLY_NOT_NATIVE_EVIDENCE':True});write_json(folder/'supervisor_exit.json',{'complete_child_receipt':True})
    for suffix in ['exit.json','exit.started.json']:write_json(root/'runs'/(folder.name+'.'+suffix),{'child_pid':123,'exit_code':0})
    ledger=[dict(c,reserved=i==0) for i,c in enumerate(cells)];ledger[0].update(artifact_manifest_sha256=sha256(folder/'artifact_manifest.json'),trusted_task_spec_sha256=sha256(folder/'task_spec.json'))
    sources=[dict(path=p.relative_to(root).as_posix(),sha256=sha256(p),bytes=p.stat().st_size) for p in root.rglob('*') if p.is_file() and p.is_relative_to(root/'runs')]
    git(repo,'checkout','-q','--detach',rev)
    for name,value in [('ledger.json',ledger),('manifest.json',dict(source_files=sources)),('origins.json',dict(artifacts=[])),('proof.json',dict(status='ALL_SYNTHETIC_TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_VERIFIED',archives=[dict(sha256='a'*64,status='TWO_LOCATIONS_ARCHIVE_AND_EVERY_MEMBER_SHA256_VERIFIED')]))]:write_json(repo/'reports/synthetic'/name,value)
    git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC immutable closed prefix');report=git(repo,'rev-parse','HEAD')
    review_path='docs/reviews/SYNTHETIC_CLOSED.md';p=repo/review_path;p.write_text('SYNTHETIC fixture, no real authorization.\n**Reviewer:** GPT. SYNTHETIC ONLY. report '+report+' execution '+old+'\n')
    grant['disposition']='TEST_SUSPENDED';(repo/path).write_text(json.dumps(grant));git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC suspend and review prefix');review=git(repo,'rev-parse','HEAD');git(repo,'update-ref','refs/remotes/origin/main',review)
    # New engineering-only identity, no new machine grant yet.
    with (repo/'tase/shadow.py').open('a') as f:f.write('\n# SYNTHETIC CPU engineering identity delta\n')
    cfg2=copy.deepcopy(cfg);cfg2['frozen_sha256']['tase/shadow.py']=sha256(repo/'tase/shadow.py');(repo/'configs/e2_test.json').write_text(json.dumps(cfg2))
    anchor=dict(execution_head=old,grant_commit=rev,grant_path=path,review_commit=review,review_path=review_path,report_head=report,ledger_path='reports/synthetic/ledger.json',manifest_path='reports/synthetic/manifest.json',receipt_origins_path='reports/synthetic/origins.json',backup_proof_path='reports/synthetic/proof.json',consumed_count=1,original_archive_sha256='a'*64)
    write_json(repo/'reports/E2/automation/HISTORICAL_TEST_EPOCHS.json',dict(epochs=[anchor]));git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC next engineering head');new=git(repo,'rev-parse','HEAD')
    return repo,rev,path,identity,reservation,folder,cfg2,cells,new


class HistoricalAuditTests(unittest.TestCase):
    def test_still_active_old_identity_can_be_audited_on_cpu_repair_head_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo,rev,path,grant=fixture(root);cfg,cells,identity=authorize(repo,rev,path)
            with (repo/'tase/shadow.py').open('a') as f:f.write('\n# SYNTHETIC maintenance-only comment\n')
            cfg['frozen_sha256']['tase/shadow.py']=sha256(repo/'tase/shadow.py');(repo/'configs/e2_test.json').write_text(json.dumps(cfg));git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC CPU maintenance')
            res=dict(cells[0],authorization=identity,repo_sha=identity['authorized_head'],config_hash=identity['test_config_sha256'],runtime_lock_hash=identity['runtime_lock_sha256'])
            self.assertEqual(AuditVersions(repo,cfg,cells).resolve(res,root/'UNEXECUTED')[1],identity)
            with self.assertRaises(ValueError):authorize(repo,rev,path)
    def test_reformatted_main_grant_is_not_active_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,grant=fixture(Path(tmp));cfg,cells,identity=authorize(repo,rev,path);head=identity['authorized_head']
            git(repo,'checkout','-q','--detach',rev);(repo/path).write_text(json.dumps(grant,separators=(',',':')));git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC changed grant bytes');main=git(repo,'rev-parse','HEAD');git(repo,'update-ref','refs/remotes/origin/main',main);git(repo,'checkout','-q','--detach',head)
            res=dict(cells[0],authorization=identity,repo_sha=head,config_hash=identity['test_config_sha256'],runtime_lock_hash=identity['runtime_lock_sha256'])
            with self.assertRaises(ValueError):authorize(repo,rev,path)
            with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,Path(tmp)/'UNEXECUTED')
    def test_old_suspended_grant_checks_only_anchored_original_not_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));versions=AuditVersions(repo,cfg,cells)
            oldcfg,auth=versions.resolve(res,folder);self.assertEqual(auth,identity);self.assertNotEqual(oldcfg['frozen_sha256'],cfg['frozen_sha256'])
            with self.assertRaises(ValueError):authorize(repo,rev,path)
            self.assertTrue(versions.rows[res['run_id']]['closed_prefix_anchored']);self.assertFalse(versions.rows[res['run_id']]['grant_currently_active'])
    def test_old_grant_cannot_extend_closed_prefix_to_unstarted_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));res.update(cells[1])
            with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,folder)
    def test_corrupt_reservation_result_manifest_video_receipts_fail_closed(self):
        for name in ['reservation.json','result.json','artifact_manifest.json','task_spec.json','supervisor_exit.json','exit.json','exit.started.json']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));p=folder/name if not name.startswith('exit.') else folder.parent.parent/(folder.name+'.'+name);p.write_text('{}')
                with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,folder)
    def test_forged_grant_blob_or_code_or_config_identity_fails(self):
        for field in ['review_commit','review_blob','authorized_head','test_config_sha256']:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));res['authorization']=dict(identity,**{field:'0'*(40 if field in ['review_commit','review_blob','authorized_head'] else 64)})
                with self.assertRaises(ValueError):
                    AuditVersions(repo,cfg,cells).resolve(res,folder)
    def test_new_science_or_other_frozen_source_is_not_a_maintenance_delta(self):
        for mutate in ['gate_k','seed','source']:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as tmp:
                repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp))
                if mutate=='gate_k':cfg['gate_k']=2
                elif mutate=='seed':cfg['policy_seed_base']+=1
                else:cfg['frozen_sha256']['tase/event_oracle.py']='0'*64
                with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,folder)
    def test_missing_reviewed_two_copy_proof_or_prefix_anchor_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));(repo/'reports/E2/automation/HISTORICAL_TEST_EPOCHS.json').unlink()
            with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,folder)
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));p=repo/'reports/E2/automation/HISTORICAL_TEST_EPOCHS.json';a=json.loads(p.read_text());a['epochs'][0]['original_archive_sha256']='b'*64;p.write_text(json.dumps(a))
            with self.assertRaises(ValueError):AuditVersions(repo,cfg,cells).resolve(res,folder)
    def test_fresh_synthetic_current_grant_and_old_epoch_coexist(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo,rev,path,identity,res,folder,cfg,cells,new=epochs(Path(tmp));oldcheck=AuditVersions(repo,cfg,cells);oldcheck.resolve(res,folder)
            original=json.loads(git(repo,'show',rev+':'+path));new_grant=dict(original,authorized_head=new,test_config_sha256=sha256(repo/'configs/e2_test.json'))
            grantpath='docs/reviews/SYNTHETIC_NEW.json';write_json(repo/grantpath,new_grant);git(repo,'add','.');git(repo,'commit','-qm','SYNTHETIC new independent grant');review=git(repo,'rev-parse','HEAD');git(repo,'update-ref','refs/remotes/origin/main',review);git(repo,'checkout','-q','--detach',new)
            _,_,current=authorize(repo,review,grantpath);versions=AuditVersions(repo,cfg,cells)
            versions.resolve(res,folder)
            next_res=dict(cells[14],authorization=current,repo_sha=new,config_hash=current['test_config_sha256'],runtime_lock_hash=current['runtime_lock_sha256'])
            self.assertEqual(versions.resolve(next_res,Path(tmp)/'UNEXECUTED_SYNTHETIC_0015')[1],current)
            self.assertEqual(len({r['execution_head'] for r in versions.rows.values()}),2)
            with self.assertRaises(ValueError):authorize(repo,rev,path)
