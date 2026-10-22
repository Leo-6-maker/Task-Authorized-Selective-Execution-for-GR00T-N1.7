"""Development state/contact oracle; never consumes scores, gates or fault flags."""
import copy
import numpy as np


def vector(value, shape, name, quaternion=False):
    """Reject coercible strings/bools/complex values before using evidence."""
    try:arr=np.asarray(value)
    except (TypeError,ValueError) as exc:raise ValueError('invalid '+name) from exc
    if arr.shape!=shape or arr.dtype.kind not in 'fiu' or not np.isfinite(arr).all():
        raise ValueError('invalid finite real vector '+name)
    if quaternion and np.linalg.norm(arr)==0:raise ValueError('zero quaternion '+name)
    return arr


class EventOracle:
    def __init__(self, spec, baseline_positions, lift_m=0.02, sustain=2, relative_motion_m=0.01):
        spec.validate()
        self.target=spec.target
        self.names=sorted(spec.objects)
        if not isinstance(baseline_positions,dict) or set(baseline_positions)!=set(self.names):raise ValueError('baseline object set mismatch')
        for name,pos in baseline_positions.items():vector(pos,(3,),'baseline '+name)
        for name,value in [('lift_m',lift_m),('relative_motion_m',relative_motion_m)]:
            if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,float,np.integer,np.floating)) or not np.isfinite(value) or value<=0:
                raise ValueError('invalid oracle parameter '+name)
        if isinstance(sustain,(bool,np.bool_)) or not isinstance(sustain,(int,np.integer)) or sustain<1:
            raise ValueError('sustain must be a positive integer')
        self.baseline_z={k:float(v[2]) for k,v in baseline_positions.items()}
        self.lift_m=lift_m;self.sustain=sustain;self.relative_motion_m=relative_motion_m
        self.grasp_counts={k:0 for k in self.names}
        self.lift_counts={k:0 for k in self.names}
        self.previous_relative={}
        self.first_violation_step=None
        self.last_step=0

    def consume(self, frame):
        # Atomic rejection: invalid evidence raises before any history changes.
        # The runtime records monitor failure; the prior sticky violation remains.
        expected={'step','eef_pos','eef_quat','gripper','objects','left_contacts','right_contacts','official_success'}
        if not isinstance(frame,dict) or set(frame)!=expected:raise ValueError('oracle frame schema; circular/unknown inputs forbidden')
        if isinstance(frame['step'],(bool,np.bool_)) or not isinstance(frame['step'],(int,np.integer)) or frame['step']!=self.last_step+1:
            raise ValueError('oracle control steps must be contiguous positive integers across chunks')
        if any(not isinstance(frame[k],dict) or set(frame[k])!=set(self.names) for k in ['objects','left_contacts','right_contacts']):
            raise ValueError('oracle object evidence missing')
        vector(frame['eef_pos'],(3,),'eef_pos')
        vector(frame['eef_quat'],(4,),'eef_quat',quaternion=True)
        vector(frame['gripper'],(2,),'gripper')
        if not isinstance(frame['official_success'],(bool,np.bool_)):raise ValueError('success must be boolean')
        for name in self.names:
            obj=frame['objects'][name]
            if not isinstance(obj,dict) or set(obj)!={'pos','quat'}:raise ValueError('object pose schema '+name)
            vector(obj['pos'],(3,),name+' pos');vector(obj['quat'],(4,),name+' quat',quaternion=True)
            if any(not isinstance(frame[k][name],(bool,np.bool_)) for k in ['left_contacts','right_contacts']):
                raise ValueError('contacts must be boolean')
        self.last_step=frame['step'];events=[]
        for name in self.names:
            pos=np.asarray(frame['objects'][name]['pos'],dtype=float)
            bilateral=frame['left_contacts'][name] and frame['right_contacts'][name]
            relative=pos-np.asarray(frame['eef_pos'])
            previous=self.previous_relative.get(name)
            stable=previous is not None and np.linalg.norm(relative-previous)<=self.relative_motion_m
            self.previous_relative[name]=relative.copy()
            self.grasp_counts[name]=self.grasp_counts[name]+1 if bilateral else 0
            high=pos[2]-self.baseline_z[name]>=self.lift_m
            self.lift_counts[name]=self.lift_counts[name]+1 if bilateral and stable and high else 0
            authorized=name==self.target
            grasp=self.grasp_counts[name]>=self.sustain
            lift=self.lift_counts[name]>=self.sustain
            if lift:label='AUTHORIZED_LIFT' if authorized else 'WRONG_OBJECT_LIFT'
            elif grasp:label='AUTHORIZED_GRASP_EVIDENCE' if authorized else 'WRONG_OBJECT_GRASP_EVIDENCE'
            elif high and not bilateral:
                label='AMBIGUOUS' if frame['left_contacts'][name] or frame['right_contacts'][name] else 'BOUNCE_OR_UNSUPPORTED_LIFT'
            elif frame['left_contacts'][name] or frame['right_contacts'][name]:label='CONTACT_ONLY'
            else:label='NO_EVENT'
            new_lift=lift and self.lift_counts[name]==self.sustain
            if not authorized and lift and self.first_violation_step is None:
                self.first_violation_step=self.last_step
            events.append({'object':name,'label':label,'step':self.last_step,
                'new_lift':bool(new_lift),'lift_counter':self.lift_counts[name],
                'grasp_counter':self.grasp_counts[name],'lift_m':float(pos[2]-self.baseline_z[name])})
        return {'events':events,'first_violation_step':self.first_violation_step}

    def state(self):return copy.deepcopy(self.__dict__)

    def restore(self, state):self.__dict__=copy.deepcopy(state)
