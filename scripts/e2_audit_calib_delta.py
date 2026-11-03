"""Independently readable public CALIB derivative audit (CPU; no private paths).

Checks derivative hashes and source lineage, recomputes488 row statistics, replays
selected actual oracle sequences and compares raw actions, G predictions and
paired complete-state snapshot digests. Does not claim excluded raw bytes read.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json
from tase.test_authorization import require
from tase.task_spec import TaskSpec
from tase.event_oracle import EventOracle
from tase.gate_features import contact_view,score_contacts
from tase.calibration import select
from tase.m2_context import jsonable,compare_frames
from scripts.audit_epoch import read,lines
from scripts.e2_export_review import validate_numpy


def validate_package(root):
    m=read(root/'manifest.json')
    expected={r['export_path'] for r in m['artifacts']}
    require(len(expected)==len(m['artifacts']) and expected=={p.relative_to(root).as_posix() for p in root.rglob('*')
             if p.is_file() and p!=root/'manifest.json'},'public derivative coverage/duplicate mismatch')
    source_index={r['source_path']:r['source_sha256'] for r in m['source_files']}
    for r in m['artifacts']:
        p=root/r['export_path']
        require(not Path(r['export_path']).is_absolute() and '..' not in Path(r['export_path']).parts and
                p.resolve().is_relative_to(root.resolve()), 'unsafe derivative artifact ID')
        require(p.stat().st_size==r['bytes'] and sha256(p)==r['sha256'],'public derivative byte mismatch: '+r['export_path'])
        for origin in r['origins']:
            require(source_index[origin['source_path']]==origin['source_sha256'],'source hash lineage mismatch')
        if p.suffix in ['.npz','.npy']:validate_numpy(p)
    return m,source_index


def audit(root,repo):
    m,source_index=validate_package(root);rows=read(root/'candidate_decisions.json')
    with (root/'candidate_decisions.csv').open(newline='') as f:csv_rows=list(csv.DictReader(f))
    require(len(rows)==len(csv_rows)==488 and len({r['candidate_id'] for r in rows})==488,'all488 distinct candidate rows required')
    for row,csv_row in zip(rows,csv_rows):
        require({k:str(v) if v is not None else '' for k,v in row.items()}==csv_row,'typed JSON/CSV row differs')
        source='runs/CALIB/'+row['source_run']+'/'
        candidate='runs/CALIB_candidates/'+row['candidate_id']+'/'
        for key,path in [('source_result_sha256',source+'result.json'),('source_frames_sha256',source+'physical_frames.jsonl'),
                         ('source_manifest_sha256',source+'artifact_manifest.json'),
                         ('source_snapshot_file_sha256',source+f"snapshot-{row['decision']:03d}.pkl"),
                         ('raw_action_sha256',source+f"action-{row['decision']:03d}.npz"),
                         ('candidate_result_sha256',candidate+'result.json'),('prediction_sha256',candidate+'prediction.json'),
                         ('contact_views_sha256',candidate+'contact_views.json'),('candidate_manifest_sha256',candidate+'artifact_manifest.json')]:
            require(row[key]==source_index[path],'candidate/source identity differs: '+key)
        onset=row['first_actual_major_step'];before=row['completed_controls_before'];count=row['prediction_controls']
        require(type(count) is int and 1<=count<=8 and row['new_model_requests']==0,'candidate control/request count')
        require(row['first_major_window']==(onset is not None and before<onset<=before+count),'first event window label')
    selected=select([dict(condition=r['condition'],first_major_window=r['first_major_window'],
        decisions={str(k):r[f'k{k}_decision'] for k in [1,2,3]}) for r in rows],
        sha256(repo/'configs/e2_calibration_plan.json'))
    require(selected==read(root/'selection_recomputed.json') and selected['selected_k']==3,'selection differs from488 rows')
    cfg=read(repo/'configs/e2_test.json');pair_rows=read(root/'pair_audit.json')['pairs'];checked=[]
    require(len(pair_rows)==8, 'all8 predeclared pairs required')
    prior={r['run_id']:r for r in read(root/'previous_first_event_windows.json')['rows']}
    for pair in pair_rows:
        folders=[root/'pairs'/pair['b0_run'],root/'pairs'/pair['g_run']]
        actual={}
        for folder in folders:
            result=read(folder/'result.json');spec=TaskSpec(**read(folder/'task_spec.json')).validate()
            identity=read(folder/'e2_identity.json');frames=lines(folder/'physical_frames.jsonl')
            oracle=EventOracle(spec,identity['baseline_positions'],.02,2,.01)
            for frame in frames:
                computed=oracle.consume({k:v for k,v in frame.items() if k not in ['oracle','control_input']})
                require(jsonable(computed)==frame['oracle'],'complete actual event labels differ')
            require(len(frames)==result['inner_steps'] and oracle.first_violation_step==result['first_wrong_lift_step'],
                    'actual step/onset mismatch')
            start=read(folder/'exit.started.json');end=read(folder/'exit.json')
            require(start['child_pid']==end['child_pid'] and end['exit_code']==result['exit_code']==0,
                    'actual child exit mismatch')
            with np.load(folder/'raw_actions.npz',allow_pickle=False) as data:
                actions=np.array(data['actions']);require(actions.shape==(result['policy_calls'],7,1,16,1),'all raw16 actions required')
            with np.load(folder/'control_trace.npz',allow_pickle=False) as data:
                states=np.array(data['states']);controls=np.array(data['converted_actions'])
            require(np.array_equal(controls,np.asarray([f['control_input'] for f in frames])), 'controller/physical frame mismatch')
            gates=lines(folder/'gate_decisions.jsonl');snaps=lines(folder/'snapshots.jsonl')
            require(len(gates)==len(actions)==len(snaps),'all decision/snapshot/action records required')
            for gate in gates:
                idx=gate['index'];before=gate['completed_controls_before'];after=gate['completed_controls_after']
                require(0<=after-before<=8,'native executed prefix length')
                if gate['decision']!='ACCEPT':
                    require(gate==gates[-1] and before==after==len(frames),'reject/error stop or zero-execution failure')
                else:
                    expected=actions[idx,:,0,:after-before,0].T.copy();expected[:,-1]=-np.sign(2*expected[:,-1]-1)
                    require(np.array_equal(expected,controls[before:after]),'raw16/native executed prefix mismatch')
                if result['system']=='G':
                    prediction=read(folder/f'prediction-{idx:03d}.json')
                    view=next(v for v in lines(folder/'gate_contact_views.jsonl') if v['index']==idx)
                    require(prediction['status']=='PASS' and prediction['steps']==len(prediction['frames']) and
                            prediction['source_snapshot_hash']==prediction['restored_snapshot_hash']==snaps[idx]['snapshot_hash'],
                            'G prediction snapshot/length mismatch')
                    require(view['views']==[contact_view(f,spec.objects) for f in prediction['frames']], 'contact projection mismatch')
                    score=score_contacts(view['views'],list(spec.objects),spec.target,view['actual_contact_history'],before,3)
                    require(all(gate[k]==v for k,v in score.items()),'actual G was not frozen k3')
                    if gate['decision']=='ACCEPT':
                        convert=lambda f:{**f,'gripper':np.asarray(f['gripper'])}
                        require(compare_frames([convert(f) for f in prediction['frames']],
                            [convert(f) for f in frames[before:after]],cfg)['status']=='PASS','G ACCEPT predicted/actual differs')
            actual[result['system']]=dict(result=result,frames=frames,actions=actions,states=states,controls=controls,snaps=snaps)
            if folder.name in prior:
                old=prior[folder.name]
                require(old['first_wrong_lift_step']==oracle.first_violation_step,'prior published onset mismatch')
                for f in old['physical_frames']:
                    require(frames[f['step']-1]==f,'prior published physical frame differs')
        b,g=actual['B0'],actual['G'];n=len(g['controls'])
        require(np.array_equal(b['actions'][:len(g['actions'])],g['actions']) and
                np.array_equal(b['controls'][:n],g['controls']) and np.array_equal(b['states'][:n],g['states']),
                'selected pair raw action/state/controller prefixes differ')
        require(all(b['snaps'][i]['snapshot_hash']==s['snapshot_hash'] for i,s in enumerate(g['snaps'])),
                'selected pair full state/RNG snapshot hashes differ')
        checked.append(dict(b0=pair['b0_run'],g=pair['g_run'],B0_onset=b['result']['first_wrong_lift_step'],
                            G_onset=g['result']['first_wrong_lift_step'],G_controls=n,
                            B0_status=b['result']['status'],G_status=g['result']['status']))
    # Available selected candidate sources include raw prediction and contact inputs for all their fixed windows.
    source_specs={p['b0_run']:TaskSpec(**read(root/'pairs'/p['b0_run']/'task_spec.json')).validate() for p in pair_rows}
    available=0
    for case in sorted((root/'candidates').iterdir()):
        result=read(case/'result.json');spec=source_specs[result['source_run']]
        prediction=read(case/'prediction.json');views=read(case/'contact_views.json')
        require(views['views']==[contact_view(f,spec.objects) for f in prediction['frames']],'selected candidate projection mismatch')
        scores={str(k):score_contacts(views['views'],list(spec.objects),spec.target,views['actual_contact_history'],
                                    result['completed_controls_before'],k) for k in [1,2,3]}
        require(scores==result['scores'],'selected candidate full numeric score mismatch')
        available+=1
    return dict(status='PUBLIC_DERIVATIVE_CPU_RECOMPUTED_NOT_GPT_APPROVAL',candidate_rows=488,
        selected_k=selected['selected_k'],metrics=selected['metrics'],selected_pairs=checked,
        selected_candidate_numeric_inputs=available,exported_artifact_files=len(m['artifacts']),
        source_files_hashed_not_all_public_bytes=len(source_index),no_pickle_loaded=True,new_model_requests=0,
        new_simulations=0,TEST_executed=0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['package','repo','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();write_json(a.output,audit(a.package,a.repo))
