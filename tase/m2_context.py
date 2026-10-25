"""Always-accept M2 instrumentation around the unmodified native executor."""
import copy
import json
import pickle
import traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from .evidence import append_json, reserve_episode, write_json, sha256
from .snapshot import capture, digest
from .shadow import Shadow
from .task_spec import TaskSpec
from .event_oracle import EventOracle
from .m2_native import sample


def jsonable(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:jsonable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [jsonable(v) for v in value]
    return value


def compare_frames(predicted, actual, cfg):
    errors={'position_m':0.0,'orientation_rad':0.0,'gripper_m':0.0}
    exact=True
    if not predicted or not actual:return dict(status='FAIL',reason='empty_prediction_or_reference',**errors)
    if len(predicted)!=len(actual):return dict(status='FAIL',reason='step_count',**errors)
    for p,a in zip(predicted,actual):
        for frame in [p,a]:
            arrays=[frame['eef_pos'],frame['eef_quat'],frame['gripper'],frame['control_input']]
            arrays += [v for obj in frame['objects'].values() for v in [obj['pos'],obj['quat']]]
            if not frame['objects'] or any(not np.isfinite(v).all() for v in arrays):
                return dict(status='FAIL',reason='nonfinite_or_missing_physics',**errors)
        exact &= np.array_equal(p['control_input'],a['control_input'])
        exact &= p['official_success']==a['official_success'] and p['step']==a['step']
        exact &= p['left_contacts']==a['left_contacts'] and p['right_contacts']==a['right_contacts']
        def event_labels(frame):
            return [(e['object'],e['label'],e.get('new_lift'),e.get('lift_counter'),e.get('grasp_counter')) for e in frame['oracle']['events']]
        exact &= event_labels(p)==event_labels(a) and p['oracle']['first_violation_step']==a['oracle']['first_violation_step']
        poses=[(p['eef_pos'],p['eef_quat'],a['eef_pos'],a['eef_quat'])]
        poses += [(p['objects'][n]['pos'],p['objects'][n]['quat'],a['objects'][n]['pos'],a['objects'][n]['quat']) for n in a['objects']]
        for xp,qp,xa,qa in poses:
            errors['position_m']=max(errors['position_m'],float(np.max(np.abs(np.asarray(xp)-xa))))
            dot=abs(float(np.dot(qp,qa)/(np.linalg.norm(qp)*np.linalg.norm(qa))))
            if not np.isfinite(dot):return dict(status='FAIL',reason='invalid_quaternion',**errors)
            errors['orientation_rad']=max(errors['orientation_rad'],float(2*np.arccos(np.clip(dot,-1,1))))
        errors['gripper_m']=max(errors['gripper_m'],float(np.max(np.abs(p['gripper']-a['gripper']))))
    passed=exact and errors['position_m']<=cfg['position_tolerance_m'] and errors['orientation_rad']<=cfg['orientation_tolerance_rad'] and errors['gripper_m']<=cfg['gripper_tolerance_m']
    return dict(status='PASS' if passed else 'FAIL',discrete_exact=bool(exact),**errors)


class M2Context:
    def __init__(self, raw, wrapped, client, folder, workspace, cell):
        self.raw=raw;self.wrapped=wrapped;self.client=client;self.folder=folder;self.workspace=workspace;self.cell=cell
        self.cfg=json.loads(Path('configs/m2_validation.json').read_text())
        self.spec=TaskSpec.from_native(raw,cell['task'])
        first=sample(raw,self.spec,0)
        self.oracle=EventOracle(self.spec,{n:o['pos'] for n,o in first['objects'].items()},
            self.cfg['oracle_lift_m'],self.cfg['oracle_sustain_control_steps'],self.cfg['oracle_relative_motion_tolerance_m'])
        self.frames=[];self.shadow=None
        self.policy_language='pick up the '+cell['policy_target'].replace('_',' ')+' and place it in the basket'
        if cell['policy_target']+'_1' not in self.spec.objects:raise ValueError('predeclared instruction target missing')
        from libero.libero import benchmark
        suite=benchmark.get_benchmark_dict()['libero_object']()
        if self.policy_language.replace(' ','_') not in suite.get_task_names():raise ValueError('instruction not an official Object task')
        write_json(folder/'task_spec.json',asdict(self.spec))
        write_json(folder/'m2_identity.json',{'cell':cell,'validation_sha256':sha256('configs/m2_validation.json'),
            'true_task_spec_target':self.spec.target,'policy_language':self.policy_language,
            'condition_is_not_an_oracle_input':True})

    def frame(self,action):
        value=sample(self.raw,self.spec,len(self.frames)+1)
        value['oracle']=self.oracle.consume(value)
        value['control_input']=np.array(action,copy=True)
        self.frames.append(value)
        append_json(self.folder/'physical_frames.jsonl',jsonable(value))

    def _capture(self):
        return capture(self.raw,self.wrapped,self.oracle,{'policy_control_steps':len(self.frames)})

    def predict(self,index,prefix):
        indices=self.cfg['c0_snapshot_decisions'] if self.cell['condition']=='C0' else self.cfg['c2_snapshot_decisions']
        if index not in indices:return []
        captured=sum(len(p.read_text().splitlines()) for p in (self.workspace/'runs/episodes').glob('dev-m2-*/snapshots.jsonl'))
        if captured>=self.cfg['max_distinct_snapshots']:return []
        snapshot=self._capture();snapshot_hash=digest(snapshot)
        snapshot_id=self.cell['run_id']+f'-d{index:03d}'
        path=self.folder/f'snapshot-{index:03d}.pkl'
        with path.open('xb') as f:pickle.dump(snapshot,f,protocol=5)
        np.savez_compressed(self.folder/f'prefix-{index:03d}.npz',**prefix)
        frame=sample(self.raw,self.spec,len(self.frames))
        contact=any(frame['left_contacts'].values()) or any(frame['right_contacts'].values())
        lifted=any(frame['objects'][n]['pos'][2]-self.oracle.baseline_z[n]>=self.cfg['oracle_lift_m'] for n in self.spec.objects)
        phase='BOUNDARY' if len(self.frames)>=712 else 'LIFT_OR_TRANSPORT' if lifted else 'CONTACT' if contact else 'APPROACH_NO_CONTACT'
        append_json(self.folder/'snapshots.jsonl',{'id':snapshot_id,'decision':index,'source_steps':len(self.frames),
            'snapshot_hash':snapshot_hash,'file_sha256':sha256(path),'phase':phase,
            'field_inventory':snapshot['field_inventory']})
        records=[]
        category='CONTACT' if contact else 'NO_CONTACT'
        previous=[]
        for p in (self.workspace/'runs/m2_shadow').glob('*/reservation.json'):
            previous.append(json.loads(p.read_text()).get('always_accept_category'))
        repeat_count=self.cfg['shadow_repeats']+(1 if category not in previous else 0)
        for repeat in range(repeat_count):
            extra=repeat>=self.cfg['shadow_repeats']
            case_id=snapshot_id+f'-r{repeat}'
            case=reserve_episode(self.workspace/'runs/m2_shadow',case_id,{
                'split':'DEV','source_episode':self.cell['run_id'],'snapshot_id':snapshot_id,
                'repeat':repeat,'phase':phase,'always_accept_category':category if extra else None,
                'model_calls_permitted':False},limit=self.cfg['max_shadow_cases'])
            rng_before=self.client.call_endpoint('rng_digest',requires_input=False)
            before_hash=digest(self._capture())
            try:
                if self.shadow is None:
                    self.shadow=Shadow(self.cell['task'],self.cell['init_index'],vars(self.wrapped.contract))
                    write_json(case/'worker_setup.json',self.shadow.setup)
                prediction=self.shadow.predict(snapshot,prefix)
            except BaseException as exc:
                prediction={'status':'ERROR','error_type':type(exc).__name__,'traceback':traceback.format_exc()}
            after_hash=digest(self._capture())
            rng_after=self.client.call_endpoint('rng_digest',requires_input=False)
            unchanged=before_hash==after_hash==snapshot_hash and rng_before==rng_after
            guard={'main_complete_state_unchanged':unchanged,'before_hash':before_hash,'after_hash':after_hash,
                'policy_rng_before':rng_before,'policy_rng_after':rng_after,'policy_calls_from_shadow':0}
            write_json(case/'noninterference.json',guard)
            with (case/'prediction.pkl').open('xb') as f:pickle.dump(prediction,f,protocol=5)
            records.append((case,prediction,guard))
            if not unchanged:raise RuntimeError('shadow changed complete main state or policy RNG')
        return records

    def compare(self,records,start,done,truncated):
        actual=self.frames[start:]
        for case,prediction,guard in records:
            if prediction['status']=='ERROR':
                result={'status':'ERROR','error_type':prediction['error_type']}
            else:
                result=compare_frames(prediction['frames'],actual,self.cfg)
                result['roundtrip_exact']=prediction['restored_snapshot_hash']==prediction['source_snapshot_hash']
                result['termination_exact']=prediction['terminated']==bool(done) and prediction['truncated']==bool(truncated)
                if not result['roundtrip_exact'] or not result['termination_exact']:result['status']='FAIL'
            result.update(control_steps=len(actual),history_replay_steps=0,
                prediction_control_steps=prediction.get('steps',prediction.get('completed_prediction_steps',0)),
                main_noninterference=guard['main_complete_state_unchanged'],policy_calls_from_shadow=0)
            write_json(case/'result.json',result)

    def close(self):
        if self.shadow is not None:self.shadow.close()
