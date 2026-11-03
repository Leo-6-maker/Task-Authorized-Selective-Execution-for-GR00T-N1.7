"""SYNTHETIC CPU contracts only. Real snapshot/physics is separately budgeted."""
import copy
import unittest
from types import SimpleNamespace
import numpy as np
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.snapshot import encode,decode,digest,fields,restore_fields
from tase.m2_context import compare_frames


def spec():
    return TaskSpec('target','basket',{n:{'geoms':[i+1],'geom_names':[n+'_geom'],
        'body_id':i+1,'body_name':n+'_body'} for i,n in enumerate(['target','other','basket'])},[20],[21]).validate()


def frame(step,name='other',height=0.03,both=True):
    names=spec().objects
    return {'step':step,'eef_pos':np.array([0.,0.,height]),'eef_quat':np.array([1.,0,0,0]),
        'gripper':np.zeros(2),'objects':{n:{'pos':np.array([0.,0.,height if n==name else 0.]),
                                         'quat':np.array([1.,0,0,0])} for n in names},
        'left_contacts':{n:n==name for n in names},'right_contacts':{n:n==name and both for n in names},'official_success':False}


class M2CPUContractTests(unittest.TestCase):
    def oracle(self):return EventOracle(spec(),{n:[0,0,0] for n in spec().objects})

    def test_cross_chunk_wrong_lift_and_first_event_sticky(self):
        oracle=self.oracle()
        for step in range(1,8):oracle.consume(frame(step,height=0.0,both=False))
        # Frames 8 and 9 both retain the same EEF/object relative position;
        # the second sustained sample is step 9, across the 8-step boundary.
        oracle.consume(frame(8));result=oracle.consume(frame(9))
        self.assertEqual(result['first_violation_step'],9)
        self.assertTrue(any(e['label']=='WRONG_OBJECT_LIFT' for e in result['events']))
        self.assertEqual(oracle.consume(frame(10,both=False))['first_violation_step'],9)

    def test_authorized_lift_never_wrong(self):
        oracle=self.oracle()
        for step in range(1,5):result=oracle.consume(frame(step,name='target'))
        self.assertIsNone(result['first_violation_step'])
        self.assertTrue(any(e['label']=='AUTHORIZED_LIFT' for e in result['events']))

    def test_bounce_one_finger_and_ambiguous(self):
        oracle=self.oracle()
        value=frame(1,both=False)
        self.assertEqual([e for e in oracle.consume(value)['events'] if e['object']=='other'][0]['label'],'AMBIGUOUS')
        value=frame(2,both=False);value['left_contacts']={n:False for n in spec().objects}
        self.assertEqual([e for e in oracle.consume(value)['events'] if e['object']=='other'][0]['label'],'BOUNCE_OR_UNSUPPORTED_LIFT')
        value=frame(3);value['objects']['other']['pos'][0]=np.nan
        with self.assertRaises(ValueError):oracle.consume(value)

    def test_oracle_rejects_fault_flag_and_missing_object(self):
        oracle=self.oracle();value=frame(1);value['fault_flag']=True
        with self.assertRaises(ValueError):oracle.consume(value)
        value=frame(1);del value['objects']['other']
        with self.assertRaises(ValueError):oracle.consume(value)

    def test_missing_target_and_overlapping_geometry_fail_closed(self):
        value=spec();del value.objects['target']
        with self.assertRaises(ValueError):value.validate()

    def test_body_identity_and_lift_threshold_boundary(self):
        value=spec();value.objects['other']['body_id']=value.objects['target']['body_id']
        with self.assertRaises(ValueError):value.validate()
        oracle=self.oracle()
        self.assertIsNone(oracle.first_violation_step)
        oracle.consume(frame(1,height=0.019999))
        oracle.consume(frame(2,height=0.02))
        result=oracle.consume(frame(3,height=0.02))
        self.assertEqual(result['first_violation_step'],3)
        oracle.consume(frame(4,height=0.019999))
        self.assertEqual(oracle.lift_counts['other'],0)
        value=spec();value.objects['other']['geoms']=value.left_geoms
        with self.assertRaises(ValueError):value.validate()

    def test_state_tree_roundtrip_has_independent_arrays(self):
        source=SimpleNamespace(goal=np.ones(3),history=[np.arange(2)],flag=True)
        state,_=fields(source)
        target=SimpleNamespace(goal=np.zeros(3),history=[],flag=False)
        restore_fields(target,state)
        self.assertEqual(digest(fields(target)[0]),digest(state))
        target.goal[0]=5;target.history[0][0]=5
        self.assertEqual(source.goal[0],1)
        self.assertEqual(state['goal'][0],1)
        self.assertEqual(source.history[0][0],0)
        with self.assertRaises(ValueError):fields(SimpleNamespace(unknown=object()))

    def test_discrete_or_numeric_mismatch_rejected(self):
        from pathlib import Path
        import json
        cfg=json.loads((Path(__file__).parents[1]/'configs/m2_validation.json').read_text())
        a=frame(1);a['oracle']={'events':[],'first_violation_step':None};a['control_input']=np.array([0.,0,0,0,0,0,1])
        b=copy.deepcopy(a)
        self.assertEqual(compare_frames([a],[b],cfg)['status'],'PASS')
        b['eef_pos'][0]+=0.001
        self.assertEqual(compare_frames([a],[b],cfg)['status'],'FAIL')
        self.assertEqual(compare_frames([a],[],cfg)['status'],'FAIL')
        self.assertEqual(compare_frames([],[],cfg)['status'],'FAIL')
        b=copy.deepcopy(a);b['eef_pos'][0]=np.nan
        self.assertEqual(compare_frames([a],[b],cfg)['status'],'FAIL')
