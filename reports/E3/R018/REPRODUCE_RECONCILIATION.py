"""R018 bounded CPU-only reconciliation of preserved0001. Never reserves/runs TEST."""
import argparse,datetime,hashlib,json,subprocess,tarfile
from pathlib import Path
from e3.audit import original
from e3.authorization import git
from e3.checkpoint import original_inventory,require_backup
from e3.discovery import require,sha,digest
from e3.ledger import audit,write

R018='9a81613ff7af768ded32f5ac23a5034e222fed52'
R018_PATH='docs/reviews/R018-E3-INCIDENT-CPU-REVIEW.json'
OLD_HEAD='859e40b5f460365a8853bf3486969e9f8e28951c'
OLD_GRANT='ca979be10c00389ed57b77967c232d7a84132406'
OLD_PATH='docs/reviews/R017-E3-TEST-AUTHORIZED.json'

def file_record(path,label):return dict(label=label,bytes=path.stat().st_size,sha256=sha(path))
def js(path):return json.loads(path.read_text())

def reconcile(workspace,repo,old_operator,new_operator,secondary,output):
    workspace=workspace.resolve(strict=True);repo=repo.resolve(strict=True)
    folder=workspace/'runs/E3A_TEST/e3a-test-0001'
    require(not output.resolve().is_relative_to((workspace/'runs').resolve()) and not output.exists(),
            'new reconciliation must be exclusive outside original runs')
    review_bytes=subprocess.check_output(['git','show',R018+':'+R018_PATH],cwd=repo)
    require(subprocess.check_output(['git','show','origin/main:'+R018_PATH],cwd=repo)==review_bytes,'R018 decision differs from current fetched main')
    review=json.loads(review_bytes);permit=review['CPU_reconciliation']
    require(review['disposition']=='CHANGES_REQUIRED' and
            permit['decision']=='CONDITIONALLY_AUTHORIZED_READ_ONLY_NO_REPLAY' and
            review['new_TEST_authorized'] is False,'R018 CPU-only reconciliation authority required')
    require(sha(repo/'e3/audit.py')==permit['reviewed_audit_integration_sha256'] and
            sha(repo/'e3/audit_manifest.py')==permit['reviewed_manifest_module_sha256'],
            'R018 reviewed audit correction bytes differ')
    require(sha(folder/'result.json')==permit['result_sha256'] and
            sha(folder/'artifact_manifest.json')==permit['original_manifest_sha256'],
            'R018 result/manifest identity differs')
    reservation=js(folder/'reservation.json');auth=reservation['authorization'];result=js(folder/'result.json')
    require(auth['authorized_head']==OLD_HEAD and auth['review_commit']==OLD_GRANT and
            auth['review_path']==OLD_PATH and result['repo_sha']==OLD_HEAD,
            'historical acquisition Head/grant must not be rewritten')
    rows=original_inventory(workspace,[folder]);require(len(rows)==78,'full78-file original custody required')
    archive_dir=workspace/'evidence_exports/r017-final-handoff-01'
    proof=js(archive_dir/'second-copy-proof.json');require_backup(proof,rows)
    local=js(secondary)
    require(local['status']=='R018_SECONDARY_WHOLE_AND_EVERY_MEMBER_FRESHLY_REVERIFIED' and
            local['archive_sha256']==proof['secondary_archive_sha256'] and local['original_files']==rows,
            'fresh local secondary evidence must bind every original')
    archive=archive_dir/'evidence.tar.gz'
    h=hashlib.sha256()
    with archive.open('rb') as src:
        for b in iter(lambda:src.read(8*1024*1024),b''):h.update(b)
    require(h.hexdigest()==proof['primary_archive_sha256'],'primary archive changed')
    observed={};manifest=None
    with tarfile.open(archive,'r|gz') as t:
        for member in t:
            require(member.isfile(),'non-regular primary member')
            b=t.extractfile(member).read()
            if member.name=='backup-manifest.json':manifest=json.loads(b)
            else:observed[member.name]=(len(b),hashlib.sha256(b).hexdigest())
    require(manifest is not None and len(observed)==len(manifest['artifacts']), 'primary member set changed')
    for row in manifest['artifacts']:
        require(observed.get(row['path'])==(row['bytes'],row['sha256']),'primary member hash changed')
    require(manifest['original_files']==rows,'primary full-original inventory changed')
    for row in rows:require(observed.get(row['path'])==(row['bytes'],row['sha256']), 'original absent in primary')
    failed=[]
    for name in ['final-normal','frozen-final-optimized']:
        receipt=js(old_operator/(name+'.exit.json'));log=old_operator/(name+'.stderr.private.txt')
        require(receipt['exit_code']==1 and 'manifest coverage mismatch' in log.read_text(),
                'historical frozen failure must remain1')
        failed.append(dict(actual_exit=1,exit_source=file_record(old_operator/(name+'.exit.json'),'OLD_OPERATOR/'+name+'.exit.json'),
                           error_log=file_record(log,'OLD_OPERATOR/'+name+'.stderr.private.txt')))
    cells=json.loads(git(repo,'show',OLD_HEAD+':configs/e3_cells.proposed.json'))['cells']
    require(reservation['cell']==cells[0],'original0001 is not the planned first cell')
    # The full historical auditor authenticates source, claim, official init,
    # TaskSpec, physical controls/Oracle/actions, manifest and native actual exit.
    original(workspace,repo,folder,reservation)
    checked=audit(workspace/'runs/E3A_TEST',[c for c in cells if c['epoch']=='E3A'],
                  lambda f,res:original(workspace,repo,f,res))
    require(checked['consumed']==checked['known']==1,'full ledger eligibility not established')
    native_exit=js(workspace/'runs/e3a-test-0001.exit.json');native_start=js(workspace/'runs/e3a-test-0001.exit.started.json')
    supervisor=js(folder/'supervisor_exit.json');claim=js(folder/'runner_claim.json')
    require(native_exit['child_pid']==native_start['child_pid'] and
            native_exit['child_returncode']==native_exit['exit_code']==result['exit_code']==0 and
            supervisor['wrapper_returncode']==0 and supervisor['complete_child_receipt'] is True,
            'actual late process exit chain differs')
    cmd=native_start['command']
    for arg,value in [('--run-id','e3a-test-0001'),('--review-commit',OLD_GRANT),('--review-path',OLD_PATH)]:
        require(cmd.count(arg)==1 and cmd[cmd.index(arg)+1]==value,'native start identity differs')
    require(claim['reservation_sha256']==sha(folder/'reservation.json') and claim['authorization']==auth,
            'claim no longer authenticates original reservation')
    decisions=[json.loads(x) for x in (folder/'gate_decisions.jsonl').read_text().splitlines()]
    increments=[d['completed_controls_after']-d['completed_controls_before'] for d in decisions]
    require(len(decisions)==16 and increments==[8]*15+[1] and
            all(d['decision']=='ACCEPT' for d in decisions) and result['inner_steps']==121 and
            result['policy_requests_attempted']==result['policy_calls']==16 and result['settling_steps']==10 and
            result['status']=='SUCCESS' and result['official_success'] is True,
            'preserved raw native success/control evidence differs')
    require(not list(folder.glob('prediction-*')) and not (folder/'shadow_close.json').exists(),
            'unexpected G/Shadow evidence in B0 original')
    audits=[]
    for prefix in ['candidate-readonly', 'refrozen-readonly']:
        where=old_operator if prefix=='candidate-readonly' else new_operator
        values=[]
        for mode in ['normal','optimized']:
            name=prefix+'-'+mode
            exit=js(where/(name+'.exit.json'));data=js(where/(name+'.audit.json'))
            require(exit['exit_code']==0,'read-only audit actual exit not0')
            values.append(data)
            audits.append(dict(label=('OLD_OPERATOR/' if where==old_operator else 'NEW_OPERATOR/')+name,
                               actual_exit=0,output=file_record(where/(name+'.audit.json'),name+'.audit.json'),
                               exit_receipt=file_record(where/(name+'.exit.json'),name+'.exit.json')))
        require(values[0]==values[1],'ordinary/optimized read-only audit differs')
        if prefix=='candidate-readonly':old_value=values[0]
        else:require(values[0]==old_value,'new refrozen audit differs from exact existing repair audit')
    require(original_inventory(workspace,[folder])==rows,'original changed during read-only reconciliation')
    value=dict(schema_version=1,reconciliation_id='R018-0001-v1',
               disposition='ELIGIBLE_SUCCESS_IN_NEW_R018_RECONCILED_ANALYSIS',
               authority=dict(review_commit=R018,review_path=R018_PATH,review_blob=git(repo,'rev-parse',R018+':'+R018_PATH),
                              decision_sha256=hashlib.sha256(review_bytes).hexdigest(),
                              condition='CONDITIONALLY_AUTHORIZED_READ_ONLY_NO_REPLAY'),
               acquisition=dict(run_id='e3a-test-0001',execution_head=OLD_HEAD,review_commit=OLD_GRANT,review_path=OLD_PATH,
                                authorization=auth,cell=reservation['cell']),
               original_result=file_record(folder/'result.json','runs/E3A_TEST/e3a-test-0001/result.json'),
               original_manifest=file_record(folder/'artifact_manifest.json','runs/E3A_TEST/e3a-test-0001/artifact_manifest.json'),
               original_files=rows,original_inventory_sha256=digest(rows),
               reviewed_audit_sources={n:sha(repo/n) for n in ['e3/audit.py','e3/audit_manifest.py','e3/physics_audit.py','e3/ledger.py']},
               current_CPU_head=git(repo,'rev-parse','HEAD'),protocol_lock_sha256=sha(repo/'configs/e3_protocol_lock.proposed.json'),
               checks=dict(sealed_file_count=74,mandatory_native_files_present=15,full_original_custody_count=78,
                           complete_historical_original_audit=True,actual_physics_oracle_action_checks=True,
                           claim_and_native_supervisor_exit_chain=True,source_identity_preserved=True,
                           primary_archive_all_members_verified=len(observed),secondary_archive_all_members_verified=local['all_archive_members'],
                           ordinary_optimized_and_old_new_readonly_audits_equal=True,
                           controls=121,policy_requests=16,official_success=True,G_A0_Shadow_validation='NOT_RUN_NOT_APPLICABLE_B0',
                           first_A4_checkpoint_complete=False),
               old_frozen_audit_failures=failed,repaired_readonly_evidence=audits,
               eligibility=dict(original_status='SUCCESS',new_analysis_outcome_known=True,new_analysis_status='SUCCESS',
                                old_frozen_audit_PASS=False,original_bytes_rewritten=False),
               custody=dict(stage=proof['stage'],primary_archive_sha256=proof['primary_archive_sha256'],
                            secondary_archive_sha256=proof['secondary_archive_sha256']),
               private_checks_attested_by='EXECUTOR',independent_reviewer_private_rehash=False,
               new_native_execution_authorized=False,nightly_stop_remains_latched=True,
               new_model_simulator_Shadow_calls=0,new_TEST_reservations=0,conditional_prevention='N/A',
               script_sha256=sha(Path(__file__)),timestamp_sgt=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
    write(output,value)
    return value

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','old-operator','new-operator','secondary','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();v=reconcile(a.workspace,a.repo,a.old_operator,a.new_operator,a.secondary,a.output)
    print(json.dumps(dict(status=v['disposition'],run_id=v['acquisition']['run_id'],sealed=74,custody_originals=78,
                         source_head=OLD_HEAD,new_TEST_reservations=0,private_checks_attested_by='EXECUTOR')))
