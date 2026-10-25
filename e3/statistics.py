"""Proposed E3 fixed-task paired cluster bootstrap; no E2 pooling or retuning."""
import numpy as np
from .discovery import require

METRICS=['wrong_lift','official_success','semantic_abort']
def bounds(row,metric):
    if not row['outcome_known']:return 0.,1.
    value={'wrong_lift':row['observed_wrong_lift'],'official_success':row['official_success'],'semantic_abort':row['status']=='SEMANTIC_ABORT'}[metric]
    return float(value),float(value)

def summarize(rows,cells):
    require(len(rows)==len(cells)==160 and [r['run_id'] for r in rows]==[c['run_id'] for c in cells],'all160 planned rows/order required; never shrink denominator')
    for r,c in zip(rows,cells):require(all(r[k]==v for k,v in c.items()),'statistics cell identity differs')
    rng=np.random.default_rng(641500);groups=[];contrasts=[]
    for epoch,arms in [('E3A',['B0','G']),('E3B',['B0','A0','G'])]:
        selected=[r for r in rows if r['epoch']==epoch];tasks=list(dict.fromkeys(r['task'] for r in selected));table={(r['task'],r['init_index'],r['condition'],r['system']):r for r in selected}
        values=np.array([[[[[bounds(table[t,i,c,a],m) for m in METRICS] for a in arms] for c in ['C0','C2']] for i in [16,17,18,19]] for t in tasks]);samples=np.stack([rng.integers(0,4,size=(2000,4)) for _ in tasks]);boot=np.stack([values[t][samples[t]].mean(axis=1) for t in range(len(tasks))])
        for ti,task in enumerate(tasks+['MACRO_FIXED_TASKS']):
            observed=values.mean(axis=(0,1)) if ti==len(tasks) else values[ti].mean(axis=0);draws=boot.mean(axis=0) if ti==len(tasks) else boot[ti]
            for ci,condition in enumerate(['C0','C2']):
                for ai,arm in enumerate(arms):
                    groups.append(dict(epoch=epoch,task=task,condition=condition,system=arm,planned_denominator=4*len(tasks) if ti==len(tasks) else 4,metrics={m:dict(bounds=observed[ci,ai,mi].tolist(),paired_cluster_percentile95_bounds=[float(np.percentile(draws[:,ci,ai,mi,0],2.5)),float(np.percentile(draws[:,ci,ai,mi,1],97.5))]) for mi,m in enumerate(METRICS)}))
                for first,second in ([('G','B0')] if epoch=='E3A' else [('G','A0'),('A0','B0'),('G','B0')]):
                    x,y=arms.index(first),arms.index(second)
                    for mi,m in enumerate(METRICS):contrasts.append(dict(epoch=epoch,task=task,condition=condition,metric=m,contrast=first+'-'+second,bounds=[float(observed[ci,x,mi,0]-observed[ci,y,mi,1]),float(observed[ci,x,mi,1]-observed[ci,y,mi,0])],paired_cluster_percentile95_bounds=[float(np.percentile(draws[:,ci,x,mi,0]-draws[:,ci,y,mi,1],2.5)),float(np.percentile(draws[:,ci,x,mi,1]-draws[:,ci,y,mi,0],97.5))]))
    return dict(status='PROPOSED_STATISTICAL_IMPLEMENTATION_NOT_REAL_E3_RESULTS',groups=groups,contrasts=contrasts,bootstrap_repetitions=2000,bootstrap_seed=641500,missing='all planned cells retained with conservative0–1 unknown bounds',candidate_UAR=None,prevention_ratio='N/A until baseline-positive matched comparable closed-loop cases exist',E2_pooled=False)
