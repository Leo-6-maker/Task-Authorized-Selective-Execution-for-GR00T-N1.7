"""Post-hoc E2 mechanics only. JSON/NPZ reads, no pickle, model or simulator.

Offline A0 is NOT a closed-loop reactive outcome and is never pooled with E2.
"""
import json,collections
from pathlib import Path
from tase.gate_features import contact_view,score_contacts
from .discovery import require,sha

def lines(f):return [json.loads(s) for s in f.read_text().splitlines() if s] if f.exists() else []
def analyze(workspace,audit):
    root=Path(workspace)/'runs/TEST';rows=audit['rows'];positive=[];sensitivity=[];consistency=[];sources={}
    def bind(f):
        if f.is_file():sources['runs/TEST/'+str(f.relative_to(root))]=sha(f)
    known_pairs={x['scenario_id'] for x in audit['pairs'] if x['status']=='PAIRED_PREFIX_EXACT'}
    for b in rows:
        if b['system']!='B0':continue
        g=next(r for r in rows if r['scenario_id']==b['scenario_id'] and r['system']=='G');bf=root/b['run_id'];gf=root/g['run_id']
        for folder in [bf,gf]:
            for name in ['reservation.json','result.json','physical_frames.jsonl','snapshots.jsonl','gate_decisions.jsonl','gate_contact_views.jsonl','noninterference.jsonl','task_spec.json']:bind(folder/name)
        frames=lines(bf/'physical_frames.jsonl');spec=json.loads((bf/'task_spec.json').read_text());names=list(spec['objects']);target=spec['target'];counts={n:0 for n in names};first_contact3=None;reactive_boundary=None;boundaries={d['completed_controls_before'] for d in lines(bf/'gate_decisions.jsonl')}
        for f in frames:
            v=contact_view(f,names)
            for n in names:counts[n]=counts[n]+1 if v['left_contacts'][n] and v['right_contacts'][n] else 0
            risk=any(counts[n]>=3 for n in names if n!=target)
            if risk and first_contact3 is None:first_contact3=f['step']
            if risk and reactive_boundary is None and f['step'] in boundaries:reactive_boundary=f['step']
        gd=lines(gf/'gate_decisions.jsonl');reject=next((d['completed_controls_before'] for d in gd if d['decision']=='REJECT'),None)
        if b['first_wrong_lift_step'] is not None:
            onset=b['first_wrong_lift_step'];positive.append(dict(B0=b['run_id'],G=g['run_id'],task=b['task'],init_index=b['init_index'],condition=b['condition'],baseline_first_event=onset,first_observed_bilateral_k3_step=first_contact3,next_native_boundary_reactive_stop=reactive_boundary,offline_reactive_lead_controls=None if reactive_boundary is None else onset-reactive_boundary,predictive_stop_controls=reject,predictive_lead_controls=None if reject is None else onset-reject,comparable_pair=b['scenario_id'] in known_pairs,reactive_scope='POST_HOC_B0_REPLAY_NOT_A0_CLOSED_LOOP_OUTCOME'))
        for item in lines(gf/'gate_contact_views.jsonl'):
            for k in [1,2,3]:
                last=item['views'][0]['step']-1;score=score_contacts(item['views'],names,target,item['actual_contact_history'],last,k)
                sensitivity.append(dict(run_id=g['run_id'],decision_index=item['index'],k=k,decision=score['decision'],risk=score['risk'],scope='POST_HOC_SAVED_PREDICTED_VIEWS_NOT_RETUNING_OR_CLOSED_LOOP'))
        if b['scenario_id'] in known_pairs:
            # Saved predicted physical frames can be checked against authentic B0 future
            # only while paired snapshot+raw-action identities have already matched.
            for d in gd:
                f=gf/f'prediction-{d["index"]:03d}.json'
                if not f.exists():continue
                bind(f);pred=json.loads(f.read_text());identical=True;checked=0
                for pf in pred.get('frames',[]):
                    st=pf['step']
                    if st>len(frames):continue
                    actual=frames[st-1];require(actual['step']==st,'B0 actual frame order differs')
                    fields=['eef_pos','eef_quat','gripper','objects','left_contacts','right_contacts','control_input','official_success']
                    identical=identical and all(pf.get(k)==actual.get(k) for k in fields);checked+=1
                consistency.append(dict(run_id=g['run_id'],index=d['index'],decision=d['decision'],actual_B0_controls_compared=checked,selected_physical_fields_exact=identical,scope='PAIRED_SOURCE_MATCHED_PREFIX_ONLY_NOT_ALL_NATIVE_STATE'))
    counts=[]
    for omitted in [None,'alphabet_soup','cream_cheese','ketchup']:
        part=[r for r in rows if r['condition']=='C2' and r['task']!=omitted]
        for arm in ['B0','G']:
            group=[r for r in part if r['system']==arm];counts.append(dict(leave_out_task=omitted,system=arm,planned=len(group),known=sum(r['outcome_known'] for r in group),observed_wrong_lifts=sum(r['first_wrong_lift_step'] is not None for r in group),unknown=sum(not r['outcome_known'] for r in group),scope='POST_HOC_HETEROGENEITY_FIXED_TASKS_NOT_NEW_CONFIRMATORY_TEST'))
    return dict(status='E3C_POST_HOC_EXPLORATORY_NOT_E2_PRIMARY',E2_reserved=audit['reserved'],E2_complete=audit['full_outcomes'],positive_B0_timelines=positive,leave_one_task_out=counts,predicted_contact_k_sensitivity=sensitivity,predicted_actual_checks=consistency,source_hashes=sources,E2_candidate_UAR=None,closed_loop_A0_outcomes='NOT_EXECUTED',new_model_calls=0,simulator_created=False)
