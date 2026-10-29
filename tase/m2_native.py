"""Native observation-independent state/contact sampling and clone construction."""
import copy
import numpy as np
from .task_spec import TaskSpec
from .event_oracle import EventOracle


def sample(raw, spec, step):
    import mujoco
    data=raw.sim.data
    contacts={frozenset((int(c.geom1),int(c.geom2))) for c in data.contact[:data.ncon]}
    def touch(fingers,geoms):
        return any(frozenset((a,b)) in contacts for a in fingers for b in geoms)
    objects={name:{'pos':np.array(data.body_xpos[item['body_id']],copy=True),
                   'quat':np.array(data.body_xquat[item['body_id']],copy=True)} for name,item in spec.objects.items()}
    robot=raw.robots[0];site=robot.eef_site_id
    quat=np.empty(4);mujoco.mju_mat2Quat(quat,np.asarray(data.site_xmat[site]).reshape(-1))
    return {'step':step,'eef_pos':np.array(data.site_xpos[site],copy=True),'eef_quat':quat,
        'gripper':np.array(data.qpos[robot._ref_gripper_joint_pos_indexes],copy=True),
        'objects':objects,'left_contacts':{n:touch(spec.left_geoms,o['geoms']) for n,o in spec.objects.items()},
        'right_contacts':{n:touch(spec.right_geoms,o['geoms']) for n,o in spec.objects.items()},
        'official_success':bool(raw.check_success())}


def make_clone(task_name, init_index, contract_dict, environment_seed=None):
    import torch
    import gymnasium as gym
    from pathlib import Path
    from libero.libero import benchmark, get_libero_path
    from gr00t.eval.sim.LIBERO.libero_env import LiberoEnv
    from gr00t.eval._horizon_contract import PolicyHorizonSpec
    from gr00t.eval.sim.wrapper.multistep_wrapper import MultiStepWrapper
    seed=640101 if environment_seed is None else environment_seed
    np.random.seed(seed)
    if environment_seed is not None:
        import random
        random.seed(seed);torch.manual_seed(seed)
    suite=benchmark.get_benchmark_dict()['libero_object']()
    full='pick_up_the_'+task_name+'_and_place_it_in_the_basket'
    task=suite.get_task(suite.get_task_names().index(full))
    native=LiberoEnv(str(Path(get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file),task.language)
    native.reset(seed=seed);raw=native._env
    initial=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
    safe=[np.core.multiarray._reconstruct,np.ndarray,np.dtype,type(np.dtype('float64')),type(np.dtype('float32'))]
    with torch.serialization.safe_globals(safe):states=torch.load(initial,map_location='cpu',weights_only=True)
    obs=raw.set_init_state(np.asarray(states[init_index],dtype=np.float64))
    for _ in range(10):obs,_,_,_=raw.step(np.array([0,0,0,0,0,0,-1.0]))
    processed=native._process_observation(obs)
    class FixedReset(gym.Wrapper):
        def reset(self,*,seed=None,options=None):return processed,{'success':raw.check_success()}
    contract=PolicyHorizonSpec(**contract_dict)
    wrapped=MultiStepWrapper(FixedReset(native),contract=contract,max_episode_steps=720,terminate_on_success=True)
    wrapped.reset()
    spec=TaskSpec.from_native(raw,task_name)
    frame=sample(raw,spec,0)
    oracle=EventOracle(spec,{k:v['pos'] for k,v in frame['objects'].items()})
    return native,raw,wrapped,spec,oracle
