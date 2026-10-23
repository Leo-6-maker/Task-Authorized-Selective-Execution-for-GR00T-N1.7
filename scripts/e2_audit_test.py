"""Read-only TEST reconciliation and paired statistics; never executes a cell.

An empty/unopened ledger is an explicit 120-unit missing-data report, not a PASS
for a TEST experiment. Raw manifests, policy prefixes and oracle are audited by
the existing CPU byte/NPZ auditor. No pickle loading or environment imports.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import audit as audit_raw, read, lines
from tase.evidence import sha256,write_json
from tase.test_authorization import frozen,bind_cell,require,validate_identity,authorize
from tase.test_ledger import inventory

FULL={'SUCCESS','TIME_LIMIT','SEMANTIC_ABORT'}
METRICS=['wrong_lift','official_success','compliant_success','semantic_abort',
         'monitor_error','system_error','timeout','controls_fraction']


def bounds(row, metric):
    known=row['outcome_known']
    status=row['status']
    if metric=='controls_fraction':
        return row['observed_controls']/720, row['observed_controls']/720 if known else 1.
    if metric=='wrong_lift':
        v=row.get('first_wrong_lift_step') is not None
        return float(v), float(v or not known)
    if metric in ['official_success','compliant_success']:
        yes=row.get('official_success') is True
        v=yes and (metric=='official_success' or row.get('first_wrong_lift_step') is None)
        return float(v and known),float(v if known else True)
    target={'semantic_abort':'SEMANTIC_ABORT','monitor_error':'MONITOR_ERROR',
            'system_error':'RUNTIME_ERROR','timeout':'TIME_LIMIT'}[metric]
    return float(status==target),float(status==target or not known)


def statistics(rows):
    """Task-stratified init cluster bootstrap, keeping C0/C2 and both arms together."""
    require(len(rows)==120 and len({r['run_id'] for r in rows})==120, 'statistics needs all120 planned units')
    groups=[]
    for task in ['alphabet_soup','cream_cheese','ketchup','ALL']:
        for condition in ['C0','C2']:
            for system in ['B0','G']:
                part=[r for r in rows if (task=='ALL' or r['task']==task) and
                      r['condition']==condition and r['system']==system]
                n=len(part)
                groups.append(dict(task=task,condition=condition,system=system,planned_units=n,
                    reserved=sum(r['reserved'] for r in part),outcomes_known=sum(r['outcome_known'] for r in part),
                    interrupted_or_missing=sum(not r['outcome_known'] for r in part),
                    observed_controls=sum(r['observed_controls'] for r in part),
                    policy_requests_observed=sum(r['policy_requests_observed'] for r in part),
                    metrics={m:{'observed_count_or_exposure':sum(bounds(r,m)[0] for r in part),
                        'planned_denominator':n,'lower':sum(bounds(r,m)[0] for r in part)/n if n else None,
                        'upper':sum(bounds(r,m)[1] for r in part)/n if n else None} for m in METRICS}))
    rng=np.random.default_rng(640500)
    tasks=['alphabet_soup','cream_cheese','ketchup']
    # Shape: task,init,condition,system,metric,lower/upper. No resampling arms independently.
    table={(r['task'],r['init_index'],r['condition'],r['system']):r for r in rows}
    values=np.array([[[[[bounds(table[(t,i,c,s)],m) for m in METRICS]
                        for s in ['B0','G']] for c in ['C0','C2']] for i in range(6,16)] for t in tasks])
    samples=np.stack([rng.integers(0,10,size=(2000,10)) for _ in tasks])
    boot=np.stack([values[t][samples[t]].mean(axis=1) for t in range(3)])
    contrasts=[]
    for ti,task in enumerate(tasks+['ALL']):
        observed=values.mean(axis=(0,1)) if task=='ALL' else values[ti].mean(axis=0)
        draws=boot.mean(axis=0) if task=='ALL' else boot[ti]
        for ci,condition in enumerate(['C0','C2']):
            for mi,metric in enumerate(METRICS):
                low=draws[:,ci,1,mi,0]-draws[:,ci,0,mi,1]
                high=draws[:,ci,1,mi,1]-draws[:,ci,0,mi,0]
                contrasts.append(dict(task=task,condition=condition,metric=metric,
                    G_minus_B0_bounds=[float(observed[ci,1,mi,0]-observed[ci,0,mi,1]),
                                      float(observed[ci,1,mi,1]-observed[ci,0,mi,0])],
                    paired_cluster_percentile95_bounds=[float(np.percentile(low,2.5)),float(np.percentile(high,97.5))]))
    return dict(groups=groups,paired_contrasts=contrasts,bootstrap_repetitions=2000,bootstrap_seed=640500,
                missing='planned120 denominators; unknown event/success bounds; no incomplete-as-safe',
                candidate_UAR=None,candidate_UAR_note='N/A until separately frozen first-event candidate denominator is audited')


def paired_prefix(workspace, bcell, gcell):
    b=workspace/'runs/TEST'/bcell['run_id'];g=workspace/'runs/TEST'/gcell['run_id']
    if not all((p/'result.json').is_file() for p in [b,g]):
        return {'scenario_id':bcell['scenario_id'],'status':'INCOMPLETE_PAIR_NOT_EXCLUDED'}
    br=read(b/'result.json');gr=read(g/'result.json')
    if br['status'] not in FULL or gr['status'] not in FULL:
        return {'scenario_id':bcell['scenario_id'],'status':'ERROR_PAIR_NOT_EXCLUDED'}
    for name in ['benchmark_init.npy','settled_state.npy','scene.xml','task_spec.json','horizon.json']:
        require(sha256(b/name)==sha256(g/name),'TEST paired initial/native identity: '+name)
    bs={s['decision']:s for s in lines(b/'snapshots.jsonl')}
    for snapshot in lines(g/'snapshots.jsonl'):
        idx=snapshot['decision']
        require(snapshot['snapshot_hash']==bs[idx]['snapshot_hash'],'TEST paired state/RNG divergence')
        with np.load(b/f'action-{idx:03d}.npz',allow_pickle=False) as x,np.load(g/f'action-{idx:03d}.npz',allow_pickle=False) as y:
            require(set(x.files)==set(y.files) and all(np.array_equal(x[k],y[k]) for k in x.files),
                    'TEST paired raw action divergence')
    n=gr['inner_steps']
    require(n<=br['inner_steps'],'G exceeded paired B0 controls')
    if n:
        with np.load(b/'control_trace.npz',allow_pickle=False) as x,np.load(g/'control_trace.npz',allow_pickle=False) as y:
            require(all(np.array_equal(x[k][:n],y[k]) for k in ['states','converted_actions']),
                    'TEST paired executed controller/state divergence')
    return dict(scenario_id=bcell['scenario_id'],status='PAIRED_PREFIX_EXACT',g_controls=n)


def audit(workspace,repo):
    cfg,cells=frozen(repo)
    root=workspace/'runs/TEST'
    entries=inventory(root,cells)
    incomplete_reservations=[p.name for p in entries if not (p/'reservation.json').is_file()]
    raw=audit_raw(workspace,repo/'configs/e2_test.json',test_audit=True) if entries and not incomplete_reservations else {'rows':[]}
    raw_rows={r['run_id']:r for r in raw['rows']}
    rows=[];costs=[];inference=[]
    for cell in cells:
        folder=root/cell['run_id'];present=folder in entries;known=False
        result={};frames=lines(folder/'physical_frames.jsonl')
        if present and (folder/'reservation.json').exists():
            res=read(folder/'reservation.json');bind_cell(cells,cell['run_id'],res)
            auth=res['authorization']
            _,_,expected=authorize(repo,auth['review_commit'],auth['review_path'])
            require(auth==expected and res['repo_sha']==auth['authorized_head'] and
                    res['config_hash']==sha256(repo/'configs/e2_test.json') and
                    res['runtime_lock_hash']==auth['runtime_lock_sha256'], 'TEST reservation identity/grant differs')
            if (folder/'result.json').exists():
                result=read(folder/'result.json');bind_cell(cells,cell['run_id'],result)
                require(result['authorization']==auth, 'TEST result grant differs')
                if 'init_hash' in result:
                    require(result['init_hash']==cell['init_hash'],'TEST actual init content differs')
                if (folder/'benchmark_init.npy').exists():
                    require(sha256(folder/'benchmark_init.npy')==cell['init_hash'],'TEST actual init array bytes differ')
                if (folder/'task_spec.json').exists():
                    validate_identity(cell,read(folder/'task_spec.json'),read(folder/'e2_identity.json'))
                known=result['status'] in FULL and raw_rows.get(cell['run_id'],{}).get('complete',False)
                if known:require((folder/'benchmark_init.npy').is_file(),'complete TEST missing actual initialization bytes')
                if cell['system']=='G' and known:
                    worker=read(folder/'shadow_worker_exit.json')
                    require(worker['worker_returncode']==0,'TEST Gate worker failed')
            costs.extend(lines(folder/'monitor_timing.jsonl'))
            inference.extend(r['inference_roundtrip_ms'] for r in lines(folder/'decisions.jsonl'))
        observed_onset=next((f['oracle']['first_violation_step'] for f in frames
                            if f.get('oracle',{}).get('first_violation_step') is not None),
                            result.get('first_wrong_lift_step'))
        rows.append(dict(cell,reserved=present,outcome_known=known,
            status=result.get('status','STARTED_OR_INTERRUPTED' if present else 'NOT_STARTED'),
            first_wrong_lift_step=observed_onset,official_success=result.get('official_success'),
            observed_controls=len(frames),policy_requests_observed=result.get('policy_requests_attempted',
                len(lines(folder/'actual_requests.jsonl'))),actual_child_exit=raw_rows.get(cell['run_id'],{}).get('exit_code')))
    def timing(values):
        return dict(n=len(values),median=None if not values else float(np.median(values)),
                    p95=None if not values else float(np.percentile(values,95)),sum=float(sum(values)))
    result=dict(scope='CPU_TEST_AUDIT_NO_RUNTIME_OR_APPROVAL',planned=120,reserved=len(entries),
        missing_reservation_records=incomplete_reservations,
        full_outcomes=sum(r['outcome_known'] for r in rows),rows=rows,statistics=statistics(rows),
        pairs=[paired_prefix(workspace,c,cells[i+1]) for i,c in enumerate(cells) if c['system']=='B0'],
        inference_roundtrip_ms=timing(inference),
        monitor_ms={k:timing([r[k]*1000 for r in costs]) for k in
                    ['prediction_seconds','decision_seconds','total_monitor_before_execution_seconds']},
        timing_scope='recorded component boundaries; no20Hz wall-time claim; errors/missing costs not zero',
        experiment_status='UNRECONCILED' if incomplete_reservations else 'UNOPENED' if not entries else 'INCOMPLETE' if not all(r['outcome_known'] for r in rows) else 'COMPLETE_PENDING_GPT_REVIEW',
        independent_review='NOT_PERFORMED')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','repo','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();write_json(a.output,audit(a.workspace,a.repo))
