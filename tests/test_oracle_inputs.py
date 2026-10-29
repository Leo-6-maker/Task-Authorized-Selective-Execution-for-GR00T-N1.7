"""Synthetic R003 invalid-evidence regression, no simulator/model."""
import copy
import unittest
import numpy as np
from test_m2_cpu import spec,frame
from tase.event_oracle import EventOracle
from tase.snapshot import digest


class OracleInputTests(unittest.TestCase):
    def test_invalid_frame_is_atomic_including_sticky_violation(self):
        mutations=[]
        for key,size in [('eef_pos',3),('eef_quat',4),('gripper',2)]:
            for bad in [np.full(size,np.nan),np.full(size,np.inf),np.zeros(size+1),['0']*size,[False]*size]:
                mutations.append((key,lambda f,k=key,v=bad:f.__setitem__(k,v)))
        for key,size in [('pos',3),('quat',4)]:
            for bad in [np.full(size,np.nan),np.zeros(size+1),['0']*size]:
                mutations.append(('object '+key,lambda f,k=key,v=bad:f['objects']['other'].__setitem__(k,v)))
        for key in ['left_contacts','right_contacts']:
            for bad in ['False',0,1,None,[],np.array([True])]:
                mutations.append((key,lambda f,k=key,v=bad:f[k].__setitem__('other',v)))
        for bad in [True,4.0,'4',0,5]:mutations.append(('step',lambda f,v=bad:f.__setitem__('step',v)))
        mutations += [('success',lambda f:f.__setitem__('official_success','False')),
            ('zero eef quaternion',lambda f:f.__setitem__('eef_quat',np.zeros(4))),
            ('zero object quaternion',lambda f:f['objects']['other'].__setitem__('quat',np.zeros(4))),
            ('unknown field',lambda f:f.__setitem__('gate',True)),
            ('missing object',lambda f:f['objects'].pop('other'))]
        for name,mutate in mutations:
            with self.subTest(name=name,mutation=str(mutate)):
                oracle=EventOracle(spec(),{n:[0,0,0] for n in spec().objects})
                oracle.consume(frame(1));oracle.consume(frame(2));oracle.consume(frame(3))
                self.assertEqual(oracle.first_violation_step,3)
                before=digest(oracle.state());value=frame(4);mutate(value)
                with self.assertRaises(ValueError):oracle.consume(value)
                self.assertEqual(digest(oracle.state()),before)
                self.assertEqual(oracle.consume(frame(4))['first_violation_step'],3)

    def test_baseline_and_parameters(self):
        baseline={n:[0,0,0] for n in spec().objects}
        for bad in [[0,0,np.nan],[0,0],['0']*3,[True]*3]:
            value=copy.deepcopy(baseline);value['other']=bad
            with self.assertRaises(ValueError):EventOracle(spec(),value)
        for key in ['lift_m','relative_motion_m']:
            for bad in [np.nan,np.inf,0,-1,True,'0.02']:
                with self.assertRaises(ValueError):EventOracle(spec(),baseline,**{key:bad})
        for bad in [True,0,-1,2.0,np.nan,'2']:
            with self.assertRaises(ValueError):EventOracle(spec(),baseline,sustain=bad)

    def test_numpy_and_json_native_valid_evidence(self):
        oracle=EventOracle(spec(),{n:[0,0,0] for n in spec().objects})
        value=frame(1);value['step']=np.int64(1);value['official_success']=np.bool_(False)
        value['left_contacts']={n:np.bool_(v) for n,v in value['left_contacts'].items()}
        oracle.consume(value)
        oracle.consume(frame(2));result=oracle.consume(frame(3))
        self.assertEqual(result['first_violation_step'],3)
