"""Synthetic contact Gate/dispatch tests; no simulator/model."""
import copy
import unittest
import numpy as np
from tase.gate_features import contact_view, score_contacts
from tase.execution_gate import candidate, execute_checked, KEYS


class E2GateTests(unittest.TestCase):
    def frames(self,name='target',steps=2):
        return [{'step':i+1,'left_contacts':{n:n==name for n in ['target','other']},
                 'right_contacts':{n:n==name for n in ['target','other']}} for i in range(steps)]
    def score(self,frames,history=None):
        return score_contacts(frames,['target','other'],'target',history or {'target':0,'other':0},0,2)
    def test_authorized_and_single_touch_accept(self):
        self.assertEqual(self.score(self.frames())['decision'],'ACCEPT')
        self.assertEqual(self.score(self.frames('other',1))['decision'],'ACCEPT')
    def test_wrong_sustained_and_history_reject(self):
        self.assertEqual(self.score(self.frames('other'))['decision'],'REJECT')
        self.assertEqual(self.score(self.frames('other',1),{'target':0,'other':1})['decision'],'REJECT')
        self.assertEqual(self.score(self.frames('target',1),{'target':0,'other':20})['decision'],'ACCEPT')
    def test_projection_and_invalid_evidence(self):
        f=self.frames()[0];f.update(oracle={'first_violation_step':4},fault=True)
        view=contact_view(f,['target','other'])
        self.assertEqual(set(view),{'step','left_contacts','right_contacts'})
        with self.assertRaises(ValueError):self.score([f])
        for bad in ['False',0,float('nan'),None]:
            f=self.frames()[0];f['left_contacts']['other']=bad
            with self.assertRaises(ValueError):self.score([f])
        with self.assertRaises(ValueError):self.score([])
    def test_reject_error_zero_execution_and_accept_exact_once(self):
        actions={k:np.full((1,16,1),i/10,dtype=np.float32) for i,k in enumerate(KEYS)}
        prefix=candidate(actions);seen=[]
        for kind in ['REJECT','ERROR']:
            decision,value=execute_checked(prefix,lambda p:{'decision':kind},lambda p:seen.append(p))
            self.assertEqual(seen,[]);self.assertIsNone(value)
        def fail(p):raise ValueError('synthetic monitor')
        self.assertEqual(execute_checked(prefix,fail,lambda p:seen.append(p))[0]['decision'],'ERROR')
        decision,_=execute_checked(prefix,lambda p:{'decision':'ACCEPT'},lambda p:seen.append(p))
        self.assertEqual(len(seen),1)
        for k in KEYS:self.assertTrue(np.array_equal(seen[0][k],actions[k][0]))
    def test_predictor_cannot_mutate_executed_candidate(self):
        prefix={k:np.zeros((16,1),np.float32) for k in KEYS};seen=[]
        def check(p):p[KEYS[0]][0]=99;return {'decision':'ACCEPT'}
        decision,_=execute_checked(prefix,check,lambda p:seen.append(p))
        self.assertEqual(decision['decision'],'ERROR')
        self.assertEqual(seen,[])

