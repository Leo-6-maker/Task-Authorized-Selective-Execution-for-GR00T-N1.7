"""Pure CPU rechecks of actual native controls/oracle/A0/G decisions. No pickle."""
import json
import numpy as np
from tase.execution_gate import KEYS,candidate
from tase.event_oracle import EventOracle
from tase.task_spec import TaskSpec
from tase.gate_features import score_contacts
from tase.test_context import validate_prediction_envelope
from .reactive_gate import ReactiveGate
from .discovery import require

def lines(f):return [json.loads(x) for x in f.read_text().splitlines()]
def verify_physics(folder,cell,result):
    spec=TaskSpec(**json.loads((folder/'task_spec.json').read_text())).validate();identity=json.loads((folder/'e2_identity.json').read_text());require(identity['epoch']==cell['epoch'] and identity['protocol_id']=='E3-001-v1.0' and identity['actual_policy_language']==cell['actual_policy_language'],'E3 actual instruction/study identity differs')
    oracle=EventOracle(spec,identity['baseline_positions'],.02,2,.01);frames=lines(folder/'physical_frames.jsonl') if (folder/'physical_frames.jsonl').exists() else [];require(len(frames)==result['inner_steps']<=720,'E3 main control count differs')
    reactive=ReactiveGate(spec);histories=[dict(reactive.counts)]
    for i,f in enumerate(frames,1):
        require(f['step']==i,'actual physical frame order differs');value={k:f[k] for k in ['step','eef_pos','eef_quat','gripper','objects','left_contacts','right_contacts','official_success']}
        for k in ['eef_pos','eef_quat','gripper']:value[k]=np.asarray(f[k])
        value['objects']={n:{'pos':np.asarray(o['pos']),'quat':np.asarray(o['quat'])} for n,o in f['objects'].items()}
        require(oracle.consume(value)==f['oracle'],'E3 actual oracle label mismatch')
        reactive.observe({k:f[k] for k in ['step','left_contacts','right_contacts']});histories.append(dict(reactive.counts))
    require(result.get('first_wrong_lift_step')==oracle.first_violation_step,'E3 primary wrong-lift onset changed')
    decisions=lines(folder/'gate_decisions.jsonl');cursor=0;stopped=False
    with np.load(folder/'control_trace.npz',allow_pickle=False) as trace:
        require(trace['converted_actions'].shape==(len(frames),7) and trace['states'].shape[0]==len(frames),'actual native trace length differs')
        for index,d in enumerate(decisions):
            require(not stopped and d['index']==index and d['completed_controls_before']==cursor and cursor%8==0,'decision order or boundary differs')
            with np.load(folder/f'action-{index:03d}.npz',allow_pickle=False) as raw:
                actions=candidate({k:raw[k] for k in raw.files})
            after=d['completed_controls_after'];require(cursor<=after<=min(cursor+8,720),'native prefix count differs')
            if d['decision']=='ACCEPT':
                expected=np.stack([actions[k][:after-cursor,0] for k in KEYS],axis=-1);expected[:,-1]=-np.sign(2*expected[:,-1]-1)
                require(after>cursor and np.array_equal(trace['converted_actions'][cursor:after],expected),'inspected/executed action or single native gripper mapping differs')
            else:require(after==cursor,'reject/error executed main controls');stopped=True
            if cell['system']=='A0':
                triggered=any(n!=spec.target and ncount>=3 for n,ncount in histories[cursor].items());require(d['decision']==('REJECT' if triggered else 'ACCEPT'),'A0 not past-contact k3 at native boundary')
            if cell['system']=='G':
                pred=json.loads((folder/f'prediction-{index:03d}.json').read_text());snapshot=next(x for x in lines(folder/'snapshots.jsonl') if x['decision']==index);validate_prediction_envelope(pred,snapshot['snapshot_hash'],cursor)
                from tase.gate_features import contact_view
                decision=score_contacts([contact_view(f,spec.objects) for f in pred['frames']],list(spec.objects),spec.target,histories[cursor],cursor,3);require(d['decision']==decision['decision'],'G frozen decision differs')
            cursor=after
    require(cursor==len(frames),'unaccounted main controls')
    require(result['official_success']==any(f['official_success'] for f in frames),'official task success evidence differs')
    if result['status']=='SUCCESS':require(result['official_success'] is True and decisions[-1]['decision']=='ACCEPT','SUCCESS lacks completed official goal')
    elif result['status']=='TIME_LIMIT':require(len(frames)==720 and result['official_success'] is False and decisions[-1]['decision']=='ACCEPT','TIME_LIMIT lacks full720 control cap')
    elif result['status']=='SEMANTIC_ABORT':require(decisions[-1]['decision']=='REJECT' and result['official_success'] is False,'semantic abort lacks terminal reject')
    else:raise ValueError('only full scientific outcomes enter physics audit')
