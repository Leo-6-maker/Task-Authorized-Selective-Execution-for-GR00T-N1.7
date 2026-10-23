"""Synthetic authorization, denominator and frozen calibration-rule checks."""
import tempfile
import unittest
from pathlib import Path
from tase.e2_ledger import reserve_calibration
from tase.calibration import select


class CalibrationTests(unittest.TestCase):
    def test_no_test_permission_and_failures_consume_48_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'CALIB';meta={'split':'CALIB','epoch':'E2','protocol_id':'TASE-002-v1.0','splits_hash':'1'*64,'calibration_plan_hash':'2'*64}
            with self.assertRaises(ValueError):reserve_calibration(root,'e2-calib-0001',dict(meta,split='TEST'))
            for index in range(1,49):reserve_calibration(root,f'e2-calib-{index:04d}',meta)
            self.assertEqual(len(list(root.glob('*/reservation.json'))),48)
            with self.assertRaises(RuntimeError):reserve_calibration(root,'e2-calib-0049',meta)

    def test_zero_event_is_na_and_ties_prefer_larger_k(self):
        normal={'condition':'C0','first_major_window':False,'decisions':{'1':'ACCEPT','2':'ACCEPT','3':'ACCEPT'}}
        a=select([normal],'1'*64)
        self.assertEqual(a['selected_k'],1);self.assertIsNone(a['metrics'][0]['UAR'])
        positive={'condition':'C2','first_major_window':True,'decisions':{'1':'REJECT','2':'REJECT','3':'REJECT'}}
        self.assertEqual(select([normal,positive],'1'*64)['selected_k'],3)

    def test_cost_constraint_cannot_be_ignored(self):
        rows=[{'condition':'C0','first_major_window':False,'decisions':{'1':'REJECT','2':'REJECT','3':'REJECT'}}]
        self.assertEqual(select(rows,'1'*64)['status'],'NO_FEASIBLE_PREDECLARED_OPERATING_POINT')


if __name__=='__main__':unittest.main()
