"""Check fixed runtime versions and native imports on CPU; no env/model creation.

Run separately with each isolated interpreter and CUDA_VISIBLE_DEVICES=-1.
Successful imports are not physical acceptance or inference evidence.
"""
import argparse
import importlib.metadata as metadata
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import write_json,now_sgt


def check(stage):
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='-1':raise ValueError('CPU-only import check requires hidden GPU')
    expected={'torch':'2.9.0','transformers':'4.57.3','numpy':'1.26.4'}
    if stage=='sim':expected.update(robosuite='1.4.0',mujoco='3.3.1',gymnasium='0.29.1')
    versions={name:metadata.version(name) for name in expected}
    if any(versions[name].split('+')[0]!=version for name,version in expected.items()):
        raise ValueError('core runtime version mismatch: '+repr(versions))
    import torch
    from gr00t.policy.server_client import PolicyClient
    if stage=='server':
        from gr00t.policy.gr00t_policy import Gr00tPolicy,Gr00tSimPolicyWrapper
        import gr00t.model
    else:
        from gr00t.eval.sim.LIBERO.libero_env import LiberoEnv
        from gr00t.eval.sim.wrapper.multistep_wrapper import MultiStepWrapper
        from libero.libero import benchmark
        suite=benchmark.get_benchmark_dict()['libero_object']()
        if len(suite.get_task_names())!=10:raise ValueError('unexpected Object task set')
    if torch.cuda.is_initialized():raise RuntimeError('CPU check unexpectedly initialized CUDA')
    return {'stage':stage,'status':'CPU_IMPORTS_PASS_NOT_RUNTIME_ACCEPTANCE','versions':versions,
            'torch_cuda_build':torch.version.cuda,'cuda_initialized':False,'model_or_env_created':False,
            'completed_at_sgt':now_sgt()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['server','sim'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();write_json(a.output,check(a.stage))
