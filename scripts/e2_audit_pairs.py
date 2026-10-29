"""Audit declared DEV B0/G pairs and actual main-control prefixes, CPU only."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import audit,read,lines
from tase.evidence import sha256,write_json
from tase.audit_contract import require


def summarize(workspace,repo):
    audited=audit(workspace,repo/'configs/e2_dev.json')
    checked={r['run_id']:r for r in audited['rows']}
    cells=read(repo/'configs/e2_dev_cells.json')['planned_cells'];rows=[];timing=[]
    for cell in cells:
        if cell['system']!='G':continue
        other=next(c for c in cells if c['system']=='B0' and all(c[k]==cell[k] for k in ['task','init_index','condition','scenario_id','policy_seed','environment_seed']))
        b=workspace/'runs/DEV'/other['run_id'];g=workspace/'runs/DEV'/cell['run_id']
        before=read(b/'result.json');after=read(g/'result.json')
        require(checked[cell['run_id']]['complete'] and after['status'] in ['SUCCESS','TIME_LIMIT','SEMANTIC_ABORT'],'Gate pair incomplete or errored')
        for name in ['benchmark_init.npy','settled_state.npy','scene.xml','task_spec.json','horizon.json']:
            require(sha256(b/name)==sha256(g/name),'pair initialization/scene/native contract differs: '+name)
        base_snap={s['decision']:s for s in lines(b/'snapshots.jsonl')}
        for snapshot in lines(g/'snapshots.jsonl'):
            index=snapshot['decision'];require(snapshot['snapshot_hash']==base_snap[index]['snapshot_hash'],'paired main complete state/RNG differs')
            with np.load(b/f'action-{index:03d}.npz',allow_pickle=False) as x,np.load(g/f'action-{index:03d}.npz',allow_pickle=False) as y:
                require(set(x.files)==set(y.files) and all(np.array_equal(x[k],y[k]) for k in x.files),'paired raw model action differs')
        controls=after['inner_steps']
        with np.load(b/'control_trace.npz',allow_pickle=False) as x,np.load(g/'control_trace.npz',allow_pickle=False) as y:
            for key in ['states','converted_actions']:
                require(np.array_equal(x[key][:controls],y[key]),'paired actual control/state prefix differs')
        gates=lines(g/'gate_decisions.jsonl');reject=next((q for q in gates if q['decision']=='REJECT'),None)
        if reject is not None:require(reject['completed_controls_before']==reject['completed_controls_after']==controls,'rejected candidate physically executed')
        violation=before['first_wrong_lift_step']
        prevented=violation is not None and reject is not None and controls<violation and after['first_wrong_lift_step'] is None
        rows.append({'b0_run':other['run_id'],'g_run':cell['run_id'],'task':cell['task'],'condition':cell['condition'],
            'b0_status':before['status'],'g_status':after['status'],'b0_first_wrong_lift':violation,
            'g_first_wrong_lift':after['first_wrong_lift_step'],'b0_controls':before['inner_steps'],'g_controls':controls,
            'rejected_candidate_main_controls':0 if reject is not None else None,'paired_prefix_exact':True,
            'first_event_prevented_in_this_pair':prevented})
        timing.extend(lines(g/'monitor_timing.jsonl'))
    require(any(r['condition']=='C0' and r['g_status']=='SUCCESS' for r in rows),'no real normal Gate completion')
    require(all(r['first_event_prevented_in_this_pair'] for r in rows if r['b0_first_wrong_lift'] is not None),'observed major paired example was not prevented')
    costs={}
    for key in ['prediction_seconds','decision_seconds','total_monitor_before_execution_seconds','worker_setup_and_record_seconds']:
        values=[r[key]*1000 for r in timing]
        costs[key.removesuffix('_seconds')+'_ms']={'n':len(values),'median':float(np.median(values)),'p95':float(np.percentile(values,95)), 'sum':float(sum(values))}
    return {'scope':'EXECUTOR_DEV_PAIR_AUDIT_NOT_TEST_OR_GPT_APPROVAL','dev_used':audited['dev_used'],'rows':rows,
        'actual_gate_candidates':len(timing),'actual_gate_worker_instances':len(rows),'timing':costs,
        'runtime_lock_sha256':sha256(repo/'configs/runtime_lock_E2.json'),'independent_review':'NOT_PERFORMED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=summarize(a.workspace,a.repo);write_json(a.output,result);print(json.dumps(result,indent=2))
