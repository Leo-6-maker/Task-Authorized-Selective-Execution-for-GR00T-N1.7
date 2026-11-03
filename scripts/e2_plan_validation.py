"""Predeclare bounded DEV snapshot checks from audited fresh E2 originals.

Selection by observed DEV phase/event is diagnostic, never an independent TEST.
At least12 distinct normal snapshots plus first-event/followup windows; two
restores each. No model, simulator or pickle is loaded by this planner.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_epoch import audit,read,lines
from tase.evidence import sha256,write_json


def build(workspace,config):
    audited=audit(workspace,config);selected={};exceptions=[]
    def add(source,index,phase):
        folder=workspace/'runs/DEV'/source;records=lines(folder/'snapshots.jsonl')
        record=next(r for r in records if r['decision']==index);result=read(folder/'result.json')
        key=(source,index)
        if key not in selected:
            selected[key]={'source_run':source,'decision':index,'task':result['task'],'init_index':result['init_index'],
                'condition':result['condition'],'source_manifest_sha256':sha256(folder/'artifact_manifest.json'),
                'snapshot_sha256':record['file_sha256'],'snapshot_digest':record['snapshot_hash'],
                'completed_controls':record['completed_controls'],'phases':[],'repeats':2}
        if phase not in selected[key]['phases']:selected[key]['phases'].append(phase)
    for source in ['e2-dev-0001','e2-dev-0003','e2-dev-0005']:
        folder=workspace/'runs/DEV'/source;result=read(folder/'result.json')
        if result['status']!='SUCCESS':raise ValueError('normal phase source incomplete')
        frames=lines(folder/'physical_frames.jsonl');gates=lines(folder/'gate_decisions.jsonl');n=len(gates)
        containing=lambda step:next(g['index'] for g in gates if g['completed_controls_before']<step<=g['completed_controls_after'])
        contact=next(f['step'] for f in frames if any(f['left_contacts'].values()) or any(f['right_contacts'].values()))
        lift=next(f['step'] for f in frames if any(e['label']=='AUTHORIZED_LIFT' for e in f['oracle']['events']))
        add(source,0,'APPROACH_NO_CONTACT')
        add(source,containing(contact),'CONTACT_OR_CLOSURE')
        add(source,min(containing(lift)+1,n-1),'AUTHORIZED_TRANSPORT')
        add(source,n-1,'TERMINATION_BOUNDARY')
        for index in [n//3,2*n//3,*range(n)]:
            if sum(s==source for s,i in selected)>=4:break
            add(source,index,'ADDITIONAL_DISTINCT_NORMAL_STATE')
    normal_count=len(selected)
    for row in audited['rows']:
        if row.get('condition')!='C2' or row.get('system')!='B0':continue
        source=row['run_id'];folder=workspace/'runs/DEV'/source
        if not row['complete'] or row['status'] not in ['SUCCESS','TIME_LIMIT']:raise ValueError('close C2 source before selecting validation')
        onset=row.get('first_wrong_lift_step')
        if onset is None:continue
        gates=lines(folder/'gate_decisions.jsonl')
        index=next(g['index'] for g in gates if g['completed_controls_before']<onset<=g['completed_controls_after'])
        add(source,index,'FIRST_MAJOR_EVENT_WINDOW')
        if index+1<len(gates):add(source,index+1,'FOLLOWUP_AFTER_FIRST_MAJOR_EVENT')
        else:exceptions.append({'source_run':source,'reason':'FIRST_EVENT_AT_TERMINAL_PREFIX_NO_FOLLOWUP_EXISTS'})
    cases=sorted(selected.values(),key=lambda r:(r['source_run'],r['decision']))
    consumed=len(list((workspace/'runs/consistency').glob('*/reservation.json')))
    if normal_count<12 or len(cases)*2+consumed>96:raise ValueError('coverage insufficient or validation budget exceeded')
    return {'epoch':'E2','protocol_id':'TASE-002-v1.0','classification':'DEV_DIAGNOSTIC_NOT_INDEPENDENT_TEST',
        'config_sha256':sha256(config),'runtime_lock_sha256':sha256(config.parent/'runtime_lock_E2.json'),
        'normal_distinct_snapshots':normal_count,'distinct_snapshots':len(cases),'planned_checks':2*len(cases),
        'existing_checks_including_failures':consumed,'maximum_total_checks':96,
        'new_model_requests_permitted':False,'cases':cases,'boundary_exceptions':exceptions,
        'independent_review':'NOT_PERFORMED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path('configs/e2_dev.json'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();plan=build(a.workspace,a.config);write_json(a.output,plan)
    print(json.dumps({k:plan[k] for k in ['normal_distinct_snapshots','distinct_snapshots','planned_checks','boundary_exceptions']}))
