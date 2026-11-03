"""SYNTHETIC JSON-only readiness integrity; never deserialize fake pickles."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from tase.evidence import sha256
from scripts.e2_audit_validation import audit
from test_e2_audit import build,seal,write,REPO


def fixture(root):
    repo=root/'course-repo';(repo/'configs').mkdir(parents=True)
    for name in ['e2_dev.json','runtime_lock_E2.json']:shutil.copyfile(REPO/'configs'/name,repo/'configs'/name)
    cases=[];phases=['APPROACH_NO_CONTACT','CONTACT_OR_CLOSURE','AUTHORIZED_TRANSPORT','TERMINATION_BOUNDARY']
    original=build(root);template=root/'template';shutil.move(original,template)
    for offset,task in enumerate(['alphabet_soup','cream_cheese','ketchup']):
        source_id=f'e2-dev-{1+2*offset:04d}';source=root/'runs/DEV'/source_id
        shutil.copytree(template,source)
        frame=json.loads((source/'physical_frames.jsonl').read_text());frames=[];decisions=[]
        for index in range(4):
            f=copy.deepcopy(frame);f['step']=index+1;frames.append(f)
            decisions.append({'index':index,'inner_steps':1,'terminated':True,'truncated':False})
            (source/f'snapshot-{index:03d}.pkl').write_bytes(b'SYNTHETIC_NOT_PICKLE')
        (source/'physical_frames.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in frames))
        (source/'decisions.jsonl').write_text(''.join(json.dumps(d)+'\n' for d in decisions))
        seal(root,source);invocation='e2v1-'+source_id;ids=[]
        for index in range(4):
            c={'source_run':source_id,'decision':index,'task':task,'condition':'C0','repeats':2,
                'completed_controls':index,'snapshot_sha256':sha256(source/f'snapshot-{index:03d}.pkl'),
                'snapshot_digest':'2'*64,'source_manifest_sha256':sha256(source/'artifact_manifest.json'),'phases':[phases[index]]}
            cases.append(c)
            for repeat in range(2):
                case_id=f'{source_id}-d{index:03d}-r{repeat}';ids.append(case_id);case=root/'runs/consistency'/case_id
                write(case/'reservation.json',{'source_run':source_id,'decision':index,'repeat':repeat,
                    'source_snapshot_sha256':c['snapshot_sha256'],'policy_requests_permitted':False,'invocation_id':invocation})
                write(case/'started.json',{'controller_pid':123,'invocation_id':invocation})
                write(case/'prediction.json',{'status':'PASS','steps':1,'frames':[frames[index]],
                    'source_snapshot_hash':'2'*64,'restored_snapshot_hash':'2'*64,'terminated':True,'truncated':False})
                write(case/'result.json',{'controller_pid':123,'worker_pid':456,'invocation_id':invocation,
                    'new_model_calls':0,'roundtrip_exact':True,'termination_exact':True,'status':'PASS',
                    'discrete_exact':True,'position_m':0.,'orientation_rad':0.,'gripper_m':0.})
                seal(root,case)
        processes=root/'runs/consistency_processes'
        write(processes/f'{invocation}.exit.started.json',{'child_pid':123})
        write(processes/f'{invocation}.exit.json',{'child_pid':123,'child_returncode':0,'exit_code':0,'signal':None})
        write(processes/f'{invocation}.worker_exit.json',{'controller_pid':123,'worker_pid':456,'worker_returncode':0,'case_ids':ids})
    plan=repo/'configs/e2_shadow_plan.json'
    write(plan,{'epoch':'E2','new_model_requests_permitted':False,'config_sha256':sha256(repo/'configs/e2_dev.json'),
        'runtime_lock_sha256':sha256(repo/'configs/runtime_lock_E2.json'),'cases':cases,'planned_checks':24})
    return plan


class ValidationAuditTests(unittest.TestCase):
    def test_rehash_does_not_hide_physics_mismatch_or_failed_worker(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);plan=fixture(root)
            self.assertEqual(audit(root,plan)['checks_including_failures'],24)
            case=root/'runs/consistency/e2-dev-0001-d000-r0'
            prediction=json.loads((case/'prediction.json').read_text());prediction['frames'][0]['left_contacts']['other']=True
            write(case/'prediction.json',prediction);seal(root,case)
            with self.assertRaises((ValueError,RuntimeError)):audit(root,plan)
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);plan=fixture(root)
            path=root/'runs/consistency_processes/e2v1-e2-dev-0001.worker_exit.json'
            worker=json.loads(path.read_text());worker['worker_returncode']=-15;write(path,worker)
            with self.assertRaises((ValueError,RuntimeError)):audit(root,plan)

    def test_extra_partial_reservation_cannot_disappear_from_denominator(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);plan=fixture(root)
            write(root/'runs/consistency/interrupted/reservation.json',{'status':'STARTED'})
            with self.assertRaises((ValueError,RuntimeError)):audit(root,plan)


if __name__=='__main__':unittest.main()
