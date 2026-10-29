"""Bounded CPU-only continuation of the new E2 environments, without deletion.

Server requirements retain the pinned upstream lock except optional TensorRT
and DeepSpeed distributions: E2 uses native PyTorch inference, not deployment
engines or training. The untouched source and complete exported lock are saved.
Sim requirements apply all known final constraints in one resolution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import now_sgt,write_json


def invoke(command,folder,env,cwd,index,timeout=1800):
    write_json(folder/f'{index}.start.json',{'command':command,'started_at_sgt':now_sgt(),
        'timeout_seconds':timeout,'gpu_allowed':False})
    start=time.monotonic()
    with (folder/f'{index}.stdout.txt').open('x') as out,(folder/f'{index}.stderr.txt').open('x') as err:
        child=subprocess.Popen(command,cwd=cwd,env=env,stdout=out,stderr=err)
        timed_out=False
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;child.terminate()
            try:code=child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();code=child.wait()
    receipt={'child_returncode':code,'timed_out':timed_out,'wall_seconds':time.monotonic()-start,
             'completed_at_sgt':now_sgt()}
    write_json(folder/f'{index}.exit.json',receipt)
    if code or timed_out:raise RuntimeError(f'install command {index} failed; preserve its receipts')


def install(root,stage,operation):
    root=root.resolve(strict=True);up=root/'upstream/Isaac-GR00T';repo=root/'course-repo'
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()!='dac54b313160c201c450f97df0fd74ebd379c892':
        raise ValueError('wrong upstream source')
    if not operation or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in operation):
        raise ValueError('invalid operation ID')
    folder=root/'runs/install'/operation;folder.mkdir()
    uv=str(root/'tools/uv');env=os.environ.copy();env.pop('UV_PYTHON',None)
    env.update(HOME=str(root/'runtime/home'),HF_HOME=str(root/'cache/huggingface'),
        XDG_CACHE_HOME=str(root/'cache'),UV_CACHE_DIR=str(root/('cache/uv' if stage=='server' else 'cache/uv-sim')),
        UV_PYTHON_DOWNLOADS='never',UV_LINK_MODE='copy',UV_CONCURRENT_DOWNLOADS='3',UV_CONCURRENT_BUILDS='1',
        CUDA_VISIBLE_DEVICES='-1',WANDB_MODE='disabled',WANDB_DISABLED='true',DO_NOT_TRACK='1',
        HF_HUB_DISABLE_TELEMETRY='1',NO_ALBUMENTATIONS_UPDATE='1',MAX_JOBS='2',OMP_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='1',LIBERO_CONFIG_PATH=str(root/'runtime/libero-config'))
    python=up/('.venv/bin/python' if stage=='server' else 'gr00t/eval/sim/LIBERO/libero_uv/.venv/bin/python')
    if not python.is_file():raise ValueError('new E2 venv must already exist')
    pip=[uv,'pip','install','--python',str(python)]
    if stage=='server':
        exported=subprocess.check_output([uv,'export','--frozen','--no-dev','--no-hashes','--no-emit-project'],cwd=up,env=env,text=True)
        (folder/'upstream-lock-requirements.txt').write_text(exported)
        selected=[];omitted=[]
        for line in exported.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            if line.startswith(('tensorrt-','deepspeed==')):omitted.append(line)
            else:selected.append(line)
        requirements=folder/'inference-requirements.txt';requirements.write_text('\n'.join(selected)+'\n')
        write_json(folder/'supporting-dependency-delta.json',{'omitted':omitted,
            'reason':'Native PyTorch inference only; no TensorRT engine or training imports in fixed model path',
            'upstream_source_modified':False,'upstream_uv_lock_modified':False,
            'requirements_sha256':hashlib.sha256(requirements.read_bytes()).hexdigest()})
        commands=[pip+['--no-deps','--index','https://download.pytorch.org/whl/cu128',
                      '--index-strategy','unsafe-best-match','-r',str(requirements)]]
    else:
        original=up/'gr00t/eval/sim/LIBERO/libero_uv/requirements-py312.txt'
        # The upstream script later upgrades einops and pins physics/Torch; apply
        # that final state now, avoiding downloads of temporary latest versions.
        lines=[line for line in original.read_text().splitlines() if not line.strip().startswith('einops==')]
        lines+=['torch==2.9.0','torchvision==0.24.0','einops==0.8.1','mujoco==3.3.1',
                'pydantic','av','tianshou==0.5.1','numba==0.65.1','llvmlite==0.47.0','tyro',
                'pandas','dm_tree','albumentations==1.4.18','pyzmq==27.0.1','msgpack==1.1.0',
                'msgpack-numpy==0.4.8','gymnasium==0.29.1','opencv-python-headless==4.10.0.84',
                'tifffile==2024.8.30','pettingzoo==1.24.3']
        requirements=folder/'final-sim-requirements.txt';requirements.write_text('\n'.join(lines)+'\n')
        commands=[pip+['-c',str(repo/'configs/sim_constraints.txt'),'-r',str(requirements)],
                  pip+['--no-deps','-e',str(up/'external_dependencies/LIBERO'),'--config-settings','editable_mode=compat']]
    commands += [[str(python),'-c',"import sysconfig,pathlib;pathlib.Path(sysconfig.get_path('purelib'),'gr00t.pth').write_text("+repr(str(up))+"+'\\n')"],
                 [uv,'pip','check','--python',str(python)]]
    for i,command in enumerate(commands):invoke(command,folder,env,up,i)
    write_json(folder/'result.json',{'stage':stage,'status':'DEPENDENCIES_INSTALLED_NOT_RUNTIME_VALIDATED',
        'completed_at_sgt':now_sgt(),'gpu_used':False})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--stage',choices=['server','sim'],required=True);p.add_argument('--operation',required=True)
    a=p.parse_args();install(a.workspace,a.stage,a.operation)
