"""CPU-only reader for the public stopped-TEST numeric derivative.

No model, simulator, pickle deserialization or new experiment. This checks
selected actual arrays/labels/prefixes and preserves cleanup failure status.
"""
import argparse
import json
import hashlib
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tase.event_oracle import EventOracle
from tase.task_spec import TaskSpec
from tase.gate_features import score_contacts
from tase.execution_gate import KEYS
from tase.m2_context import jsonable

def require(ok,message):
    if not ok:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check(root):
    root=root.resolve();m=read(root/'manifest.json');expected=set()
    for row in m['artifacts']:
        name=row['export_path'];path=root/name
        require(name not in expected and not Path(name).is_absolute() and '..' not in Path(name).parts,'invalid duplicate/escaping derivative path')
        expected.add(name);require(path.is_file() and path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],'derived bytes mismatch: '+name)
        if path.suffix in ['.npz','.npy']:
            data=np.load(path,allow_pickle=False)
            try:
                arrays=[data[k] for k in data.files] if hasattr(data,'files') else [data]
                require(all(a.dtype.kind in 'biuf' and np.isfinite(a).all() for a in arrays),'unsafe/nonfinite numeric artifact')
            finally:
                if hasattr(data,'close'):data.close()
    require(expected=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=root/'manifest.json'},'derivative file coverage mismatch')
    ledger=read(root/'attempt_ledger_120.json');require(len(ledger)==120 and len({r['run_id'] for r in ledger})==120,'planned denominator differs')
    require(sum(r['reserved'] for r in ledger)==m['observed_reserved_units'] and sum(r['status']=='CLEANUP_ERROR' for r in ledger)==m['cleanup_error_units'] and sum(r['status']=='NOT_STARTED' for r in ledger)==m['unstarted_units'] and ledger[9]['status']=='CLEANUP_ERROR' and ledger[9]['outcome_known'] is False,'stopped statuses were changed')
    episodes={};checks=[]
    for folder in sorted((root/'episodes').iterdir()):
        res=read(folder/'result.json');identity=read(folder/'e2_identity.json');spec=TaskSpec(**read(folder/'task_spec.json')).validate();schema=read(folder/'schema.json');names=schema['objects'];labels=schema['oracle_label_codes']
        oracle=EventOracle(spec,identity['baseline_positions'],.02,2,.01)
        with np.load(folder/'physical_frames.npz',allow_pickle=False) as v:
            frame_arrays={k:np.array(v[k]) for k in v.files}
        count=len(frame_arrays['step']);require(count==res['inner_steps'],'actual physical count differs')
        history={n:0 for n in names};histories=[dict(history)]
        for i in range(count):
            frame=dict(step=int(frame_arrays['step'][i]),eef_pos=frame_arrays['eef_pos'][i],eef_quat=frame_arrays['eef_quat'][i],gripper=frame_arrays['gripper'][i],official_success=bool(frame_arrays['official_success'][i]),objects={n:dict(pos=frame_arrays['object_pos'][i,j],quat=frame_arrays['object_quat'][i,j]) for j,n in enumerate(names)},left_contacts={n:bool(frame_arrays['left_contacts'][i,j]) for j,n in enumerate(names)},right_contacts={n:bool(frame_arrays['right_contacts'][i,j]) for j,n in enumerate(names)})
            actual=oracle.consume(frame)
            expected_events=[dict(object=n,label=labels[int(frame_arrays['oracle_label'][i,j])],step=i+1,new_lift=bool(frame_arrays['oracle_new_lift'][i,j]),lift_counter=int(frame_arrays['oracle_lift_counter'][i,j]),grasp_counter=int(frame_arrays['oracle_grasp_counter'][i,j]),lift_m=float(frame_arrays['oracle_lift_m'][i,j])) for j,n in enumerate(names)]
            onset=int(frame_arrays['first_violation_step'][i]);expected_oracle=dict(events=expected_events,first_violation_step=None if onset<0 else onset)
            require(jsonable(actual)==expected_oracle,'selected actual wrong-lift labels differ')
            for n in names:history[n]=history[n]+1 if frame['left_contacts'][n] and frame['right_contacts'][n] else 0
            histories.append(dict(history))
        require(oracle.first_violation_step==res['first_wrong_lift_step'],'first onset differs')
        with np.load(folder/'raw_actions.npz',allow_pickle=False) as v:actions=np.array(v['actions'])
        with np.load(folder/'control_trace.npz',allow_pickle=False) as v:states=np.array(v['states']);controls=np.array(v['converted_actions'])
        require(actions.shape==(res['policy_calls'],7,1,16,1) and np.array_equal(controls,frame_arrays['control_input']),'raw16/control evidence differs')
        gates=lines(folder/'gate_decisions.jsonl');snaps=lines(folder/'snapshots.jsonl');require(len(gates)==len(actions)==len(snaps),'decision/action/snapshot count differs')
        for g in gates:
            i=g['index'];before=g['completed_controls_before'];after=g['completed_controls_after'];require(0<=after-before<=8,'native8 prefix limit changed')
            if g['decision']=='ACCEPT':
                wanted=actions[i,:,0,:after-before,0].T.copy();wanted[:,-1]=-np.sign(2*wanted[:,-1]-1)
                require(np.array_equal(wanted,controls[before:after]),'ACCEPT did not execute same native-converted prefix')
            else:require(g==gates[-1] and before==after==count,'non-ACCEPT executed/continued')
        if res['system']=='G':
            views=lines(folder/'gate_contact_views.jsonl');require(len(views)==len(gates),'complete Gate contacts required')
            for view,g in zip(views,gates):
                require(view['actual_contact_history']==histories[g['completed_controls_before']] and view['trusted_target']==spec.target,'contact history/TaskSpec differs')
                score=score_contacts(view['views'],list(spec.objects),spec.target,view['actual_contact_history'],g['completed_controls_before'],3)
                require(all(g[k]==x for k,x in score.items()),'Gate output is not frozen contact-only k3')
        start=read(folder/'exit.started.json');exit=read(folder/'exit.json');require(start['child_pid']==exit['child_pid'] and exit['exit_code']==res['exit_code'],'actual child exit binding differs')
        if res['status']=='CLEANUP_ERROR':
            errors=read(folder/'cleanup_errors.json');worker=read(folder/'shadow_worker_exit.json')
            require(res['exit_code']==1 and bool(errors) and errors[0]['resource']=='m2_shadow' and type(worker['worker_returncode']) is int,'cleanup failure was relabeled or lost')
        episodes[folder.name]=dict(result=res,actions=actions,states=states,controls=controls,snaps=snaps)
        checks.append(dict(run_id=folder.name,status=res['status'],actual_child_exit=exit['exit_code'],controls=count,oracle_replayed=True,k3_contacts_checked=res['system']=='G'))
    pairs=[]
    for run,b in episodes.items():
        if b['result']['system']!='B0':continue
        matches=[(n,g) for n,g in episodes.items() if g['result']['system']=='G' and g['result']['scenario_id']==b['result']['scenario_id']]
        require(len(matches)==1,'selected pair arm unavailable')
        gn,g=matches[0];n=len(g['controls']);require(np.array_equal(b['actions'][:len(g['actions'])],g['actions']) and np.array_equal(b['controls'][:n],g['controls']) and np.array_equal(b['states'][:n],g['states']),'selected pair actual prefix differs')
        require(all(s['snapshot_hash']==b['snaps'][i]['snapshot_hash'] for i,s in enumerate(g['snaps'])),'paired full state/RNG digest differs')
        pairs.append(dict(B0=run,G=gn,observed_prefix_exact=True,cleanup_outcome_not_overridden=g['result']['status']=='CLEANUP_ERROR'))
    return dict(status='PUBLIC_R009_DERIVATIVE_CPU_CHECK_NOT_GPT_R3_APPROVAL',planned=120,reserved=m['observed_reserved_units'],normal_outcomes=m['normal_complete_outcomes'],cleanup_error=m['cleanup_error_units'],unstarted=m['unstarted_units'],files_verified=len(expected),selected_actual_episodes=checks,selected_actual_pairs=pairs,unavailable_predeclared_controls=read(root/'selection.json')['unavailable_predeclared_controls'],GPU_model_sim_TEST_calls=0)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=check(a.package)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
