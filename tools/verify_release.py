"""Read-only verification of the final coursework source ZIP, without Git/GPU.

Default: authenticate E2 ledger and E3 exported audit/CSV, then recount outcomes.
--full-e3: additionally check the original E3 exports and paired bootstrap using
          the unchanged repository analyze() function (NumPy is required).
--self-test: synthetic unit tests only, not a claim about original experiments.
Never reserves an ID, executes a model, accesses CUDA or imports a simulator.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

E3_DIR = 'reports/E3/FINAL_160_20261102'
E2_LEDGER_BLOB = 'e4b532df81f34f84f512e1b03fe1f86228997e09'
E3_SHA = {
    'AUDIT_FINAL_ORIGINAL.json': '2b4cb9612392814caf9878feb7f4077e529a20b0c5f682ab348893d5f7995ac9',
    'LEDGER.csv': '24b904303b434399527d9bde070459ec04eda8f95cbf535549265dd0974d9168',
    'INDEPENDENT_FORMULA_CROSSCHECK.json': '11406609cd29cfda8f2b8b8610753a9fff4081b00c7b5b9232f6fb594c4ed955'
}

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def bounded_rate(rows: list[dict], field: str) -> dict:
    require(bool(rows), 'Empty denominator')
    unknown = sum(not row['outcome_known'] for row in rows)
    positives = sum(bool(row[field]) for row in rows if row['outcome_known'])
    return {'planned': len(rows), 'known': len(rows)-unknown,
            'observed_positive': positives,
            'rate_bounds': [positives/len(rows), (positives+unknown)/len(rows)]}

def check_rows(e2: list[dict], e3: list[dict]) -> dict:
    require(len(e2)==120 and len({r['run_id'] for r in e2})==120, 'E2 must have 120 distinct original IDs')
    require({r['run_id'] for r in e2}=={f'e2-test-{i:04d}' for i in range(1,121)}, 'E2 ID coverage')
    require({r['run_id'] for r in e2 if not r['outcome_known']}==
            {'e2-test-0010','e2-test-0014','e2-test-0016'}, 'E2 censoring changed')
    e2_status = dict(collections.Counter(r['status'] for r in e2))
    require(e2_status=={'SUCCESS':89,'TIME_LIMIT':18,'SEMANTIC_ABORT':10,'CLEANUP_ERROR':3}, 'E2 statuses changed')
    expected_ids=[f'e3a-test-{i:04d}' for i in range(1,113)]+[f'e3b-test-{i:04d}' for i in range(1,49)]
    require([r['run_id'] for r in e3]==expected_ids, 'E3 160 original IDs or order changed')
    require(all(r['reserved'] and r['outcome_known'] and r['actual_exit']==0 for r in e3), 'E3 eligibility changed')
    require(dict(collections.Counter(r['status'] for r in e3))==
            {'SUCCESS':114,'TIME_LIMIT':24,'SEMANTIC_ABORT':22}, 'E3 status counts changed')
    expected={('E3A','C0','B0'):(28,0,28,0),('E3A','C0','G'):(28,0,28,0),
              ('E3A','C2','B0'):(28,14,11,0),('E3A','C2','G'):(28,0,11,14),
              ('E3B','C0','B0'):(8,0,8,0),('E3B','C0','A0'):(8,0,8,0),('E3B','C0','G'):(8,0,8,0),
              ('E3B','C2','B0'):(8,4,4,0),('E3B','C2','A0'):(8,3,4,4),('E3B','C2','G'):(8,0,4,4)}
    groups={}
    for key,want in expected.items():
        part=[r for r in e3 if (r['epoch'],r['condition'],r['system'])==key]
        got=(len(part),sum(r['observed_wrong_lift'] for r in part),
             sum(r['official_success'] for r in part),sum(r['status']=='SEMANTIC_ABORT' for r in part))
        require(got==want, 'E3 group differs: '+str(key))
        groups['/'.join(key)]=dict(zip(('planned','wrong_lift','official_success','semantic_abort'),got))
    e2_groups={}
    for cond in ('C0','C2'):
        for arm in ('B0','G'):
            part=[dict(r,wrong_lift=r['first_wrong_lift_step'] is not None)
                  for r in e2 if r['condition']==cond and r['system']==arm]
            e2_groups[f'{cond}/{arm}']={'wrong_lift':bounded_rate(part,'wrong_lift'),
                                      'official_success':bounded_rate(part,'official_success')}
    return {'scope':'PUBLIC_EXPORTED_DATA_ONLY_NOT_PRIVATE_RAW_VERIFICATION',
            'E2':{'planned':120,'eligible':117,'censored':3,'statuses':e2_status,'groups':e2_groups},
            'E3':{'planned':160,'eligible':160,'unknown':0,'groups':groups},
            'pooled_analysis':False,'model_calls':0,'simulator_calls':0,'new_TEST':0}

def verify(repo: Path, full_e3: bool=False) -> dict:
    e2data=(repo/'results/e2/attempt_ledger_120.json').read_bytes()
    require(git_blob(e2data)==E2_LEDGER_BLOB, 'Immutable E2 ledger bytes changed')
    package=repo/E3_DIR
    for name,expected in E3_SHA.items():
        require(hashlib.sha256((package/name).read_bytes()).hexdigest()==expected, 'Immutable E3 bytes changed: '+name)
    audit=json.loads((package/'AUDIT_FINAL_ORIGINAL.json').read_text())
    rows=[r for ep in audit['epochs'] for r in ep['rows']]
    result=check_rows(json.loads(e2data),rows)
    csvrows=list(csv.DictReader(io.StringIO((package/'LEDGER.csv').read_text())))
    require(len(csvrows)==160, 'CSV denominator differs')
    for csvrow,row in zip(csvrows,rows):
        require(csvrow['run_id']==row['run_id'] and csvrow['status']==row['status'] and
                (csvrow['official_success'].lower()=='true')==row['official_success'] and
                bool(csvrow['first_wrong_lift_step'])==row['observed_wrong_lift'], 'CSV/audit mismatch')
    result['CSV_consistent']=True
    result['paired_bootstrap']='NOT_RECOMPUTED; use --full-e3 with NumPy'
    if full_e3:
        for name,expected in json.loads((package/'SOURCE_BINDING.json').read_text())['public_data_sha256'].items():
            require(hashlib.sha256((package/name).read_bytes()).hexdigest()==expected, 'Export binding differs: '+name)
        sys.path.insert(0,str(repo))
        from review_tools.recheck_e3_final import analyze
        cells=json.loads((repo/'configs/e3_cells.proposed.json').read_text())['cells']
        result['full_E3']=analyze(audit,json.loads((package/'LEDGER.json').read_text()),cells,
                                 json.loads((package/'CHECKPOINTS.json').read_text()),
                                 json.loads((package/'ORIGINAL_INVENTORY.json').read_text()))
        result['paired_bootstrap']='RECOMPUTED_FROM_PUBLIC_EXPORT; 2000 / seed641500'
    return result

class HelperTests(unittest.TestCase):
    def test_unknown_not_safe(self):
        out=bounded_rate([{'outcome_known':True,'risk':False},{'outcome_known':False,'risk':False}],'risk')
        self.assertEqual(out['rate_bounds'],[0.0,0.5])
    def test_saved_success_not_eligibility(self):
        out=bounded_rate([{'outcome_known':False,'success':True}],'success')
        self.assertEqual(out['observed_positive'],0)
        self.assertEqual(out['rate_bounds'],[0.0,1.0])
    def test_no_empty_denominator(self):
        with self.assertRaises(ValueError): bounded_rate([],'risk')
    def test_git_blob_known_empty(self):
        self.assertEqual(git_blob(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
    def test_bad_counts_rejected(self):
        with self.assertRaises(ValueError): check_rows([],[])

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.cwd())
    p.add_argument('--full-e3',action='store_true')
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.self_test:
        r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HelperTests))
        return 0 if r.wasSuccessful() else 1
    try:
        out=json.dumps(verify(a.repo.resolve(),a.full_e3),indent=2,allow_nan=False)+'\n'
        if a.output:
            with a.output.open('x',encoding='utf-8') as f:f.write(out)
        else:print(out,end='')
        return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as exc:
        print('Verification failed: '+str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
