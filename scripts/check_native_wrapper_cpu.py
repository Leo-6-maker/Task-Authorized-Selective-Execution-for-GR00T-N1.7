"""SYNTHETIC CPU env with the pinned upstream wrapper; no MuJoCo/model/GPU."""
import json
import numpy as np
import gymnasium as gym
from gr00t.eval._horizon_contract import PolicyHorizonSpec
from gr00t.eval.sim.wrapper.multistep_wrapper import MultiStepWrapper


class SyntheticEnv(gym.Env):
    def __init__(self,stop):
        self.stop=stop;self.actions=[]
        self.action_space=gym.spaces.Dict({'action.x':gym.spaces.Box(-1,1,(1,),dtype=np.float32)})
        self.observation_space=gym.spaces.Dict({'state.x':gym.spaces.Box(-100,100,(1,),dtype=np.float32),
            'video.image':gym.spaces.Box(0,255,(2,2,3),dtype=np.uint8)})
    def reset(self,*,seed=None,options=None):
        self.actions=[];return self.observation(),{'success':False}
    def observation(self):
        return {'state.x':np.array([len(self.actions)],dtype=np.float32),'video.image':np.zeros((2,2,3),dtype=np.uint8)}
    def step(self,action):
        self.actions.append(np.array(action['action.x'],copy=True))
        done=len(self.actions)==self.stop
        return self.observation(),0.0,done,False,{'success':done}


def execute(tail,stop):
    env=SyntheticEnv(stop)
    wrapped=MultiStepWrapper(env,contract=PolicyHorizonSpec(8,16,(0,),(0,)),max_episode_steps=720,terminate_on_success=True)
    wrapped.reset()
    values=np.linspace(-0.7,0.7,16,dtype=np.float32).reshape(16,1);values[8:]=tail
    _,_,done,_,info=wrapped.step({'action.x':values})
    return env.actions,bool(done),int(info['n_env_steps'])


def main():
    a=execute(0,100);b=execute(123,100);early=execute(123,3)
    if len(a[0])!=8 or not np.array_equal(a[0],b[0]) or a[2]!=8 or b[2]!=8:
        raise ValueError('native wrapper consumed or coupled future tail')
    if len(early[0])!=3 or not early[1] or early[2]!=3:
        raise ValueError('native early termination not preserved')
    print(json.dumps({'scope':'SYNTHETIC_CPU_NATIVE_WRAPPER_ONLY','new_dev_episodes':0,
        'physics_steps':0,'policy_calls':0,'future_tail_invariance':'PASS',
        'executed_prefix_steps':a[2],'early_termination_steps':early[2]}))


if __name__=='__main__':main()
