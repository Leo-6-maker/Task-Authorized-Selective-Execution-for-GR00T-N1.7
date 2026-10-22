"""Pinned native M2 snapshot adapter. Never loads or queries a policy.

Physics uses MuJoCo mjSTATE_INTEGRATION, not LIBERO's qpos/qvel-only flattening.
Construction references remain on each independent simulator; live numerical
state, controller caches, observable caches, history and RNG are copied.
"""
import copy
import hashlib
import json
import random
from collections import deque, defaultdict
import numpy as np


def digest(value):
    def canonical(v):
        if isinstance(v,np.ndarray):
            return {'dtype':str(v.dtype),'shape':list(v.shape),'sha256':hashlib.sha256(v.tobytes()).hexdigest()}
        if isinstance(v,np.generic):return canonical(v.item())
        if isinstance(v,dict):return {str(k):canonical(x) for k,x in sorted(v.items(),key=lambda x:str(x[0]))}
        if isinstance(v,(list,tuple,deque)):return [canonical(x) for x in v]
        if isinstance(v,bytes):return {'bytes_sha256':hashlib.sha256(v).hexdigest()}
        return v
    return hashlib.sha256(json.dumps(canonical(value),sort_keys=True,allow_nan=True).encode()).hexdigest()


def encode(value):
    if value is None or isinstance(value,(str,int,float,bool,bytes,np.generic,np.ndarray)):
        return copy.deepcopy(value)
    if isinstance(value,(list,tuple,deque)):
        return {'__sequence__':type(value).__name__,'maxlen':getattr(value,'maxlen',None),
                'items':[encode(v) for v in value]}
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    if isinstance(value,np.random.RandomState):return {'__randomstate__':value.get_state()}
    if isinstance(value,np.random.Generator):return {'__generator__':copy.deepcopy(value.bit_generator.state)}
    module=type(value).__module__
    if module.startswith(('robosuite.utils.buffers','robosuite.controllers.interpolators')):
        return {'__attrs__':fields(value,excluded={'sim'})[0]}
    raise TypeError(type(value).__module__+'.'+type(value).__name__)


def decode(value, existing=None):
    if isinstance(value,dict):
        if '__sequence__' in value:
            items=[decode(v) for v in value['items']]
            return deque(items,maxlen=value['maxlen']) if value['__sequence__']=='deque' else tuple(items) if value['__sequence__']=='tuple' else items
        if '__attrs__' in value:
            if existing is None:raise ValueError('missing native buffer/interpolator')
            restore_fields(existing,value['__attrs__']);return existing
        if '__randomstate__' in value:
            existing.set_state(value['__randomstate__']);return existing
        if '__generator__' in value:
            existing.bit_generator.state=copy.deepcopy(value['__generator__']);return existing
        return {k:decode(v) for k,v in value.items()}
    return copy.deepcopy(value)


def fields(obj, excluded=(), strict=True):
    values={};inventory={}
    for name,value in sorted(vars(obj).items()):
        if name in excluded or callable(value):
            inventory[name]='STATIC_CONSTRUCTION_REFERENCE:'+type(value).__name__;continue
        try:values[name]=encode(value);inventory[name]='COPIED'
        except TypeError:
            if strict:raise ValueError('unclassified native snapshot field '+type(obj).__name__+'.'+name+': '+type(value).__name__)
            inventory[name]='STATIC_REFERENCE_REQUIRES_SOURCE_AUDIT:'+type(value).__name__
    return values,inventory


def restore_fields(obj, data):
    for name,value in data.items():
        setattr(obj,name,decode(value,getattr(obj,name,None)))


ENV_STATIC={'sim','model','robots','viewer','_renderer','_observables',
    'objects','fixtures','objects_dict','fixtures_dict','object_sites_dict','object_states_dict',
    'tracking_object_states_change','placement_initializer','conditional_placement_initializer',
    'conditional_placement_on_objects_initializer','object_property_initializers',
    'mujoco_arena','mujoco_objects','sim_state_initial'}
ROBOT_STATIC={'sim','robot_model','controller','gripper','controller_config'}


def capture(raw, wrapped, oracle, progress):
    import mujoco
    import torch
    model=raw.sim.model._model;data=raw.sim.data._data
    spec=mujoco.mjtState.mjSTATE_INTEGRATION
    physics=np.empty(mujoco.mj_stateSize(model,spec),dtype=np.float64)
    mujoco.mj_getState(model,data,physics,spec)
    robot=raw.robots[0]
    env,env_inventory=fields(raw.env,ENV_STATIC)
    robot_data,robot_inventory=fields(robot,ROBOT_STATIC)
    controller,controller_inventory=fields(robot.controller,{'sim'})
    # Gripper XML/tree structures are construction data; current_action is the
    # mutable native gripper actuator memory used by format_action.
    gripper={'current_action':np.array(robot.gripper.current_action,copy=True)}
    observables={name:fields(obj)[0] for name,obj in raw.env._observables.items()}
    task_states={name:fields(obj,{'env','query_dict'})[0] for name,obj in raw.env.object_states_dict.items()}
    history={'obs':copy.deepcopy(list(wrapped.obs)),'obs_maxlen':wrapped.obs.maxlen,
        'reward':copy.deepcopy(wrapped.reward),'done':copy.deepcopy(wrapped.done),
        'info':{k:copy.deepcopy(list(v)) for k,v in wrapped.info.items()},
        'info_maxlen':wrapped.n_action_steps+1,'prefix_progress':0}
    return {'version':'M2-native-v1','model_xml_sha256':hashlib.sha256(raw.sim.model.get_xml().encode()).hexdigest(),
        'physics_spec':'mjSTATE_INTEGRATION','physics':physics,'env':env,'robot':robot_data,
        'controller':controller,'gripper':gripper,'observables':observables,'task_states':task_states,
        'history':history,'oracle':oracle.state(),'progress':copy.deepcopy(progress),
        'rng':{'numpy':np.random.get_state(),'python':random.getstate(),
               'torch_cpu':torch.get_rng_state().numpy().copy()},
        'field_inventory':{'env':env_inventory,'robot':robot_inventory,'controller':controller_inventory}}


def restore(raw, wrapped, oracle, snapshot):
    import mujoco
    import torch
    current=hashlib.sha256(raw.sim.model.get_xml().encode()).hexdigest()
    if current!=snapshot['model_xml_sha256']:raise ValueError('native model/XML identity mismatch')
    model=raw.sim.model._model;data=raw.sim.data._data
    spec=mujoco.mjtState.mjSTATE_INTEGRATION
    mujoco.mj_setState(model,data,snapshot['physics'],spec)
    mujoco.mj_forward(model,data)
    # Forward refreshes derived poses/contacts. Reapply integration state so
    # warm-start/control/applied-force state remains the captured boundary.
    mujoco.mj_setState(model,data,snapshot['physics'],spec)
    restore_fields(raw.env,snapshot['env'])
    robot=raw.robots[0]
    restore_fields(robot,snapshot['robot']);restore_fields(robot.controller,snapshot['controller'])
    robot.gripper.current_action=np.array(snapshot['gripper']['current_action'],copy=True)
    for name,values in snapshot['observables'].items():restore_fields(raw.env._observables[name],values)
    for name,values in snapshot['task_states'].items():restore_fields(raw.env.object_states_dict[name],values)
    h=snapshot['history']
    wrapped.obs=deque(copy.deepcopy(h['obs']),maxlen=h['obs_maxlen'])
    wrapped.reward=copy.deepcopy(h['reward']);wrapped.done=copy.deepcopy(h['done'])
    wrapped.info=defaultdict(lambda:deque(maxlen=h['info_maxlen']))
    for k,v in h['info'].items():wrapped.info[k]=deque(copy.deepcopy(v),maxlen=h['info_maxlen'])
    oracle.restore(snapshot['oracle'])
    np.random.set_state(snapshot['rng']['numpy']);random.setstate(snapshot['rng']['python'])
    torch.set_rng_state(torch.from_numpy(snapshot['rng']['torch_cpu'].copy()))
    return copy.deepcopy(snapshot['progress'])
