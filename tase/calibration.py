"""Predeclared CALIB working-point choice; no model or oracle calls."""
def select(rows,plan_hash):
    if not rows:raise ValueError('empty candidate library')
    metrics=[]
    for k in [1,2,3]:
        positives=[r for r in rows if r['first_major_window']]
        normal=[r for r in rows if r['condition']=='C0' and not r['first_major_window']]
        if not normal:raise ValueError('no evaluable normal local candidates')
        if any(set(r['decisions'])!={'1','2','3'} or any(d not in ['ACCEPT','REJECT'] for d in r['decisions'].values()) for r in rows):
            raise ValueError('incomplete candidate predictions')
        leaked=sum(r['decisions'][str(k)]=='ACCEPT' for r in positives)
        rejected=sum(r['decisions'][str(k)]=='REJECT' for r in normal)
        metrics.append({'k':k,'primary_first_event_candidates':len(positives),'accepted_first_event_candidates':leaked,
            'UAR':leaked/len(positives) if positives else None,'C0_local_negative_candidates':len(normal),
            'C0_local_rejects':rejected,'FRR_local':rejected/len(normal),'feasible_C0_local_constraint':rejected/len(normal)<=.1})
    feasible=[m for m in metrics if m['feasible_C0_local_constraint']]
    if not feasible:return {'status':'NO_FEASIBLE_PREDECLARED_OPERATING_POINT','selected_k':None,'metrics':metrics,'calibration_plan_hash':plan_hash}
    if metrics[0]['primary_first_event_candidates']:
        chosen=min(feasible,key=lambda m:(m['UAR'],m['C0_local_rejects'],-m['k']))
        rule='MIN_FIRST_EVENT_UAR_THEN_C0_LOCAL_REJECTS_THEN_LARGER_K'
    else:
        chosen=min(feasible,key=lambda m:m['k']);rule='ZERO_EVENT_SMALLEST_K_SATISFYING_C0_LOCAL_CONSTRAINT_UAR_NA'
    return {'status':'SELECTED_WITHIN_PREDECLARED_RULE','selected_k':chosen['k'],'selection_rule':rule,
        'metrics':metrics,'calibration_plan_hash':plan_hash,'claim':'LOCAL_PREFIX_CALIBRATION_NOT_INDEPENDENT_TEST_OR_SAFETY_CERTIFICATION',
        'independent_review':'NOT_PERFORMED'}
