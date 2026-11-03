"""Derive complete epoch/init/selection identities without repeating video/sim.

Keep the original closed reconciliation CSV and receipt unchanged.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json
from tase.audit_contract import require


def enrich(workspace,source,destination):
    read=lambda p:json.loads(p.read_text())
    require(sha256(source)==read(source.parent/'ledger_reconciliation.json')['ledger_sha256'],'closed source ledger changed')
    with source.open() as f:rows=list(csv.DictReader(f))
    records=[]
    for row in rows:
        folder=workspace/'runs'/row['split']/row['run_id'];reserved=read(folder/'reservation.json')
        result=read(folder/'result.json') if (folder/'result.json').exists() else None
        for key in ['run_id','task','condition','system','repo_sha','config_hash','runtime_lock_hash']:
            require(row[key]==str(reserved[key]),'identity differs from reconciled original')
        init_hash=sha256(folder/'benchmark_init.npy')
        if result:require(result['init_hash']==init_hash,'saved initialization content differs')
        identity=read(folder/'e2_identity.json')
        gates=[json.loads(line) for line in (folder/'gate_decisions.jsonl').read_text().splitlines()] if (folder/'gate_decisions.jsonl').exists() else []
        ks={g['k'] for g in gates if 'k' in g}
        if row['system']=='G':require(len(ks)==1,'effective Gate candidate ambiguous')
        row.update(epoch=reserved['epoch'],protocol_id=reserved['protocol_id'],init_hash=init_hash,
            true_task_target=identity['true_task_target'],actual_policy_language=identity['actual_policy_language'],
            trusted_task_spec_sha256=sha256(folder/'task_spec.json'),effective_gate_k=next(iter(ks)) if ks else '',
            calibration_selection_hash=reserved.get('calibration_selection_hash',''),splits_hash=reserved.get('splits_hash',''))
        records.append({'run_id':row['run_id'],'reservation_sha256':sha256(folder/'reservation.json'),
            'result_sha256':sha256(folder/'result.json') if result else None,'init_hash':init_hash})
    destination.mkdir()
    with (destination/'attempt_identity_ledger.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    receipt={'scope':'DERIVED_IDENTITY_LEDGER_NO_NEW_EXPERIMENT','attempts':len(rows),
        'source_ledger_sha256':sha256(source),'derived_ledger_sha256':sha256(destination/'attempt_identity_ledger.csv'),
        'source_records':records,'original_reconciliation_overwritten':False,'new_model_requests':0}
    write_json(destination/'identity_reconciliation.json',receipt);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=enrich(a.workspace,a.source,a.output);print(json.dumps({k:v for k,v in r.items() if k!='source_records'},indent=2))
