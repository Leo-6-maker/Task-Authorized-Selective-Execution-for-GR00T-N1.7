"""Synthetic CPU evidence. No native environment/model or real E3 reservation."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tase.task_spec import TaskSpec
from tase.execution_gate import KEYS
from e3.reactive_gate import ReactiveGate
from e3.boundary import Boundary
from e3.manifest import build,verify
from e3.authorization import validate_grant,resource,authorize
from e3.ledger import reserve,inventory,audit,claim,write
from e3.scene import validate
from e3.statistics import summarize

REPO=Path(__file__).resolve().parents[1]
def spec():
    names=['target_1','wrong_1','basket_1'];return TaskSpec('target_1','basket_1',{n:{'body_id':i+1,'body_name':n,'geoms':[i],'geom_names':[n+'_geom']} for i,n in enumerate(names)},[10],[11]).validate()
def frame(i,object=None):return dict(step=i,left_contacts={n:n==object for n in spec().objects},right_contacts={n:n==object for n in spec().objects})
def action():return {k:np.full((16,1),.25,dtype=np.float32) for k in KEYS}
def source():return json.loads((REPO/'configs/e3_sources.proposed.json').read_text())
def identity():return dict(grant_protocol='E3-001-v1.0',authorized_head='a'*40,review_commit='b'*40,budgets={'E3A':112,'E3B':48})

class ReactiveTests(unittest.TestCase):
    def test_initial_accept(self):self.assertEqual(ReactiveGate(spec()).decide(0)['decision'],'ACCEPT')
    def test_non_target_boundary_reject(self):
        g=ReactiveGate(spec())
        for i in range(1,9):g.observe(frame(i,'wrong_1' if i>=6 else None))
        self.assertEqual(g.decide(8)['decision'],'REJECT')
    def test_target_contacts_accept(self):
        g=ReactiveGate(spec())
        for i in range(1,9):g.observe(frame(i,'target_1'))
        self.assertEqual(g.decide(8)['decision'],'ACCEPT')
    def test_basket_same_non_target_rule(self):
        g=ReactiveGate(spec())
        for i in range(1,9):g.observe(frame(i,'basket_1'))
        self.assertEqual(g.decide(8)['decision'],'REJECT')
    def test_no_within_chunk_decision(self):
        g=ReactiveGate(spec())
        for i in range(1,4):g.observe(frame(i,'wrong_1'))
        with self.assertRaises(ValueError):g.decide(3)
    def test_cross_chunk_history(self):
        g=ReactiveGate(spec())
        for i in range(1,9):g.observe(frame(i,'wrong_1' if i>=7 else None))
        self.assertEqual(g.decide(8)['decision'],'ACCEPT')
        for i in range(9,17):g.observe(frame(i,'wrong_1'))
        self.assertEqual(g.decide(16)['decision'],'REJECT')
    def test_past_transient_resets(self):
        g=ReactiveGate(spec())
        for i in range(1,9):g.observe(frame(i,'wrong_1' if i<7 else None))
        self.assertEqual(g.decide(8)['decision'],'ACCEPT')
    def test_history_gap_latches_failure(self):
        g=ReactiveGate(spec())
        with self.assertRaises(ValueError):g.observe(frame(2))
        with self.assertRaises(ValueError):g.decide(0)
    def test_duplicate_frame(self):
        g=ReactiveGate(spec());g.observe(frame(1))
        with self.assertRaises(ValueError):g.observe(frame(1))
    def test_oracle_fault_instruction_not_accepted(self):
        for key in ['oracle','condition','policy_instruction','fault']:
            with self.subTest(key=key):
                g=ReactiveGate(spec());v=frame(1);v[key]='leak'
                with self.assertRaises(ValueError):g.observe(v)
    def test_boolean_contacts_only(self):
        g=ReactiveGate(spec());f=frame(1);f['left_contacts']['wrong_1']=1
        with self.assertRaises(ValueError):g.observe(f)
    def test_wrong_object_set(self):
        g=ReactiveGate(spec());f=frame(1);del f['right_contacts']['basket_1']
        with self.assertRaises(ValueError):g.observe(f)
    def test_no_k_retune(self):
        for k in [1,2,True]:
            with self.assertRaises(ValueError):ReactiveGate(spec(),k)
    def test_spec_copy_immutable(self):
        s=spec();g=ReactiveGate(s);s.target='wrong_1';self.assertEqual(g.target,'target_1')
    def test_wrong_scene_spec(self):
        s=spec();s.target='absent'
        with self.assertRaises(ValueError):ReactiveGate(s)

class BoundaryTests(unittest.TestCase):
    def test_three_arm_exact_passthrough(self):
        for arm in ['B0','A0','G']:
            a=action();seen=[];b=Boundary(arm);d,result=b.execute(a,lambda p:{'decision':'ACCEPT','checked_controls':8},lambda p:seen.append(p));self.assertEqual(d['decision'],'ACCEPT');self.assertTrue(all(np.array_equal(a[k],seen[0][k]) for k in KEYS))
    def test_reject_error_zero_and_latch(self):
        for status in ['REJECT','ERROR']:
            b=Boundary('A0');calls=[];b.execute(action(),lambda p:{'decision':status},lambda p:calls.append(p));self.assertEqual(calls,[])
            with self.assertRaises(ValueError):b.execute(action(),lambda p:{'decision':'ACCEPT'},lambda p:None)
    def test_malformed_nonfinite_zero(self):
        for value in [float('nan'),float('inf')]:
            a=action();a[KEYS[0]][0,0]=value;calls=[];b=Boundary('B0');d,_=b.execute(a,lambda p:{'decision':'ACCEPT'},lambda p:calls.append(p));self.assertEqual(d['decision'],'ERROR');self.assertEqual(calls,[])
    def test_shape_dtype_key_contract(self):
        for mutation in ['shape','dtype','keys']:
            a=action()
            if mutation=='shape':a[KEYS[0]]=a[KEYS[0]][:8]
            elif mutation=='dtype':a[KEYS[0]]=a[KEYS[0]].astype(np.float64)
            else:del a[KEYS[0]]
            d,_=Boundary('G').execute(a,lambda p:{'decision':'ACCEPT','checked_controls':8},lambda p:self.fail('must not execute'));self.assertEqual(d['decision'],'ERROR')
    def test_monitor_mutation_zero(self):
        def mutate(p):p[KEYS[0]][0,0]=4;return {'decision':'ACCEPT'}
        d,_=Boundary('A0').execute(action(),mutate,lambda p:self.fail('mutated'));self.assertEqual(d['decision'],'ERROR')
    def test_monitor_exception_zero(self):
        def error(p):raise RuntimeError('synthetic')
        d,_=Boundary('G').execute(action(),error,lambda p:self.fail('error'));self.assertEqual(d['decision'],'ERROR')
    def test_G_requires_checked_prefix(self):
        d,_=Boundary('G').execute(action(),lambda p:{'decision':'ACCEPT'},lambda p:self.fail('unchecked'));self.assertEqual(d['decision'],'ERROR')
    def test_executor_exception_latches(self):
        b=Boundary('B0')
        with self.assertRaises(RuntimeError):b.execute(action(),lambda p:{'decision':'ACCEPT'},lambda p:(_ for _ in ()).throw(RuntimeError('CPU execution error')))
        self.assertTrue(b.stopped)

class ManifestGrantTests(unittest.TestCase):
    def setUp(self):self.source=source();self.cells=build(self.source)
    def test_160_deterministic_arms_seeds(self):
        self.assertEqual(verify(self.cells,self.source)['A'],112)
        groups={}
        for c in self.cells:groups.setdefault(c['scenario_id'],[]).append(c)
        self.assertEqual(len(groups),72)
        for rows in groups.values():self.assertEqual(len({(c['init_hash'],c['policy_seed'],c['environment_seed']) for c in rows}),1)
    def test_manifest_tamper_rejected(self):
        for field,value in [('init_hash','0'*64),('policy_seed',42),('policy_target','butter'),('system','A0')]:
            cells=copy.deepcopy(self.cells);cells[0][field]=value
            with self.assertRaises(ValueError):verify(cells,self.source)
    def test_reorder_and_short_manifest(self):
        for cells in [self.cells[::-1],self.cells[:-1]]:
            with self.assertRaises(ValueError):verify(cells,self.source)
    def test_missing_init_not_fabricated(self):
        del self.source['tasks'][0]['initializations'][0]
        with self.assertRaises(ValueError):verify(build(self.source),self.source)
    def test_resource_old_E2_not_reused(self):
        with self.assertRaises(ValueError):resource({'shared_gpu_inference_authorized':True,'gpu_index':1},identity())
    def test_old_or_proposed_grant_refused(self):
        for status in ['TEST_AUTHORIZED','PROPOSED','E3_TEST_AUTHORIZED']:
            with self.assertRaises(ValueError):validate_grant({'disposition':status,'protocol_id':'E3-001-v1.0'},{'status':'PROPOSED'},self.cells,{})
    def test_positive_synthetic_grant_and_identity_mismatch(self):
        ident=dict(authorized_head='a'*40,protocol_lock_sha256='b'*64,cells_file_sha256='c'*64,runtime_lock_sha256='d'*64);g=dict(ident,disposition='E3_TEST_AUTHORIZED',protocol_id='E3-001-v1.0',budgets={'E3A':112,'E3B':48},gate_k=3,bootstrap_seed=641500,maximum_controls=720,resource_authorization_required=True);lock=dict(status='FROZEN_BY_INDEPENDENT_REVIEW',runtime_scene_binding_verified=True);validate_grant(g,lock,self.cells,ident)
        g['authorized_head']='f'*40
        with self.assertRaises(ValueError):validate_grant(g,lock,self.cells,ident)
    def test_no_grant_no_native_entry_side_effect(self):
        with tempfile.TemporaryDirectory() as d:
            from e3.native_runner import main
            with self.assertRaises(ValueError):main(['--workspace',d,'--allocation-record',d+'/absent','--run-id','e3a-test-0001','--review-commit','old-E2','--review-path','docs/reviews/R013.json'])
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_scene_wrong_missing_ambiguous(self):
        s=spec();cell={'trusted_target':'target_1','basket':'basket_1','policy_target':'wrong'};row={'objects':dict(s.objects)};validate(s,cell,row)
        for field in ['target','basket']:
            changed=copy.deepcopy(s);setattr(changed,field,'wrong_1')
            with self.assertRaises(ValueError):validate(changed,cell,row)
        row['objects'].pop('wrong_1')
        with self.assertRaises(ValueError):validate(s,cell,row)

class LedgerTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'E3A_TEST';self.cells=[c for c in build(source()) if c['epoch']=='E3A'];self.ident=identity()
    def test_once_claim_no_duplicate(self):
        f=reserve(self.root,self.cells[0],self.cells,self.ident);res=json.loads((f/'reservation.json').read_text());claim(f,res)
        with self.assertRaises(FileExistsError):claim(f,res)
        with self.assertRaises(ValueError):reserve(self.root,self.cells[0],self.cells,self.ident)
    def test_partial_empty_folder_consumed_unknown(self):
        (self.root/self.cells[0]['run_id']).mkdir(parents=True);a=audit(self.root,self.cells);self.assertEqual((a['consumed'],a['known'],a['unknown']),(1,0,112))
        with self.assertRaises(ValueError):reserve(self.root,self.cells[1],self.cells,self.ident)
    def test_error_consumed_blocks_next(self):
        f=reserve(self.root,self.cells[0],self.cells,self.ident);write(f/'result.json',{'status':'CLEANUP_ERROR'});write(f/'supervisor_exit.json',{'complete_child_receipt':True,'wrapper_returncode':1})
        with self.assertRaises(ValueError):reserve(self.root,self.cells[1],self.cells,self.ident)
    def test_closed_synthetic_resumption_next_id(self):
        f=reserve(self.root,self.cells[0],self.cells,self.ident);write(f/'result.json',{'status':'SUCCESS'});write(f/'supervisor_exit.json',{'complete_child_receipt':True,'wrapper_returncode':0});next_folder=reserve(self.root,self.cells[1],self.cells,self.ident);self.assertEqual(next_folder.name,self.cells[1]['run_id']);self.assertTrue((f/'result.json').exists())
    def test_stale_lock_not_deleted(self):
        self.root.mkdir();(self.root/'.reservation-lock').mkdir()
        with self.assertRaises(FileExistsError):reserve(self.root,self.cells[0],self.cells,self.ident)
        self.assertTrue((self.root/'.reservation-lock').exists())
    def test_wrong_root_and_E2_ID_refused(self):
        with self.assertRaises(ValueError):reserve(self.root.parent/'TEST',self.cells[0],self.cells,self.ident)
        bad=copy.deepcopy(self.cells[0]);bad['run_id']='e2-test-0001'
        with self.assertRaises(ValueError):reserve(self.root,bad,self.cells,self.ident)
    def test_missing_reservation_never_known(self):
        f=self.root/self.cells[0]['run_id'];f.mkdir(parents=True);write(f/'result.json',{'status':'SUCCESS'});write(f/'supervisor_exit.json',{'complete_child_receipt':True,'wrapper_returncode':0});self.assertEqual(audit(self.root,self.cells,lambda f,r:None)['known'],0)
    def test_source_callback_failure_not_silenced(self):
        reserve(self.root,self.cells[0],self.cells,self.ident)
        with self.assertRaises(RuntimeError):audit(self.root,self.cells,lambda f,r:(_ for _ in ()).throw(RuntimeError('bad historical source')))
    def test_unknown_name_and_symlink_refused(self):
        self.root.mkdir();(self.root/'e2-test-0001').mkdir()
        with self.assertRaises(ValueError):inventory(self.root,self.cells)

class StatisticsTests(unittest.TestCase):
    def test_unknown_all_planned_bounds(self):
        cells=build(source());rows=[dict(c,reserved=False,outcome_known=False,status='NOT_STARTED',observed_wrong_lift=False,official_success=False) for c in cells];s=summarize(rows,cells);self.assertFalse(s['E2_pooled']);self.assertEqual(s['bootstrap_seed'],641500);self.assertTrue(all(x['bounds']==[-1.,1.] for x in s['contrasts']));self.assertIsNone(s['candidate_UAR'])
    def test_cannot_drop_planned_cell(self):
        cells=build(source())
        with self.assertRaises(ValueError):summarize([],cells)


class PhysicsAuditTests(unittest.TestCase):
    def make(self,folder):
        from dataclasses import asdict
        from tase.event_oracle import EventOracle
        s=spec();cell={'epoch':'E3B','system':'A0','actual_policy_language':'synthetic CPU instruction'};baseline={n:[0.,0.,0.] for n in s.objects};oracle=EventOracle(s,baseline);frames=[];actions=action();converted=np.stack([actions[k][:8,0] for k in KEYS],axis=-1);converted[:,-1]=-np.sign(2*converted[:,-1]-1)
        for i in range(1,9):
            f=frame(i);f.update(eef_pos=[0.,0.,0.],eef_quat=[1.,0.,0.,0.],gripper=[0.,0.],objects={n:{'pos':[0.,0.,0.],'quat':[1.,0.,0.,0.]} for n in s.objects},official_success=i==8);f['oracle']=oracle.consume(f);f['control_input']=converted[i-1].tolist();frames.append(f)
        write(folder/'task_spec.json',asdict(s));write(folder/'e2_identity.json',dict(epoch='E3B',protocol_id='E3-001-v1.0',actual_policy_language=cell['actual_policy_language'],baseline_positions=baseline));(folder/'physical_frames.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in frames));(folder/'gate_decisions.jsonl').write_text(json.dumps(dict(index=0,decision='ACCEPT',completed_controls_before=0,completed_controls_after=8))+'\n');np.savez_compressed(folder/'action-000.npz',**{k:v[None] for k,v in actions.items()});np.savez_compressed(folder/'control_trace.npz',states=np.zeros((8,2)),converted_actions=converted);result=dict(status='SUCCESS',inner_steps=8,first_wrong_lift_step=None,official_success=True);return cell,result
    def test_full_synthetic_physics_source_no_sim(self):
        from e3.physics_audit import verify_physics
        with tempfile.TemporaryDirectory() as d:
            f=Path(d);cell,result=self.make(f);verify_physics(f,cell,result)
    def test_oracle_or_wrong_lift_tamper_refused(self):
        from e3.physics_audit import verify_physics
        with tempfile.TemporaryDirectory() as d:
            f=Path(d);cell,result=self.make(f);result['first_wrong_lift_step']=1
            with self.assertRaises(ValueError):verify_physics(f,cell,result)
    def test_control_mapping_tamper_refused(self):
        from e3.physics_audit import verify_physics
        with tempfile.TemporaryDirectory() as d:
            f=Path(d);cell,result=self.make(f);np.savez_compressed(f/'control_trace.npz',states=np.zeros((8,2)),converted_actions=np.zeros((8,7)))
            with self.assertRaises(ValueError):verify_physics(f,cell,result)
    def test_false_time_limit_refused(self):
        from e3.physics_audit import verify_physics
        with tempfile.TemporaryDirectory() as d:
            f=Path(d);cell,result=self.make(f);result['status']='TIME_LIMIT'
            with self.assertRaises(ValueError):verify_physics(f,cell,result)
    def test_false_reject_main_execution_refused(self):
        from e3.physics_audit import verify_physics
        with tempfile.TemporaryDirectory() as d:
            f=Path(d);cell,result=self.make(f);(f/'gate_decisions.jsonl').write_text(json.dumps(dict(index=0,decision='REJECT',completed_controls_before=0,completed_controls_after=8))+'\n')
            with self.assertRaises(ValueError):verify_physics(f,cell,result)


class SceneProbeAdmissionTests(unittest.TestCase):
    def test_no_scene_grant_no_directory_or_native_import(self):
        from e3.scene_probe import main
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):main(['--repo',str(REPO),'--workspace',d,'--allocation-record',d+'/absent','--output',d+'/scene','--review-commit','R013','--review-path','docs/reviews/R013.json'])
            self.assertEqual(list(Path(d).iterdir()),[])


class CheckpointTests(unittest.TestCase):
    def test_missing_or_partial_backup_does_not_release(self):
        from e3.checkpoint import require_backup
        rows=[dict(path='runs/E3A_TEST/e3a-test-0001/result.json',bytes=5,sha256='a'*64)]
        for p in [{},{'status':'TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED','original_files':[],'primary_archive_sha256':'b'*64,'secondary_archive_sha256':'b'*64}]:
            with self.assertRaises(ValueError):require_backup(p,rows)
    def test_wrong_whole_archive_rejected(self):
        from e3.checkpoint import require_backup
        p={'status':'TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED','original_files':[],'primary_archive_sha256':'a'*64,'secondary_archive_sha256':'b'*64}
        with self.assertRaises(ValueError):require_backup(p,[])
    def test_first_cluster_requires_checkpoint_before_next(self):
        from e3.checkpoint import require_previous
        cells=build(source())
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);root=w/'runs/E3A_TEST'
            for c in cells[:4]:(root/c['run_id']).mkdir(parents=True)
            with self.assertRaises(FileNotFoundError):require_previous(w,'E3A',cells,identity())
    def test_E3B_cannot_skip_A(self):
        from e3.checkpoint import require_previous
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):require_previous(Path(d),'E3B',build(source()),identity())

if __name__=='__main__':unittest.main()
