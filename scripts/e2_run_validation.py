"""Execute the committed fresh-window plan once, with real process receipts.

No policy client/server or implicit retry. Failures retain their original IDs.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tase.evidence import sha256,write_json


def run(root,python,gpu_index):
    root=root.resolve(strict=True);repo=root/'course-repo';up=root/'upstream/Isaac-GR00T'
    plan_path=repo/'configs/e2_shadow_plan.json';plan=json.loads(plan_path.read_text())
    if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():
        raise ValueError('commit validation plan and code before simulator use')
    if plan['epoch']!='E2' or plan['new_model_requests_permitted'] is not False:
        raise ValueError('wrong plan authority')
    if plan['config_sha256']!=sha256(repo/'configs/e2_dev.json') or plan['runtime_lock_sha256']!=sha256(repo/'configs/runtime_lock_E2.json'):
        raise ValueError('plan runtime identity changed')
    cases=plan['cases'];groups={}
    if len({(c['source_run'],c['decision']) for c in cases})!=len(cases) or any(c['repeats']!=2 for c in cases):
        raise ValueError('duplicate cases or undeclared repetitions')
    used=list((root/'runs/consistency').glob('*/reservation.json'))
    if len(used)!=plan['existing_checks_including_failures'] or len(used)+2*len(cases)>96:
        raise ValueError('existing validation consumption differs; audit before recovery')
    for c in cases:
        source=root/'runs/DEV'/c['source_run']
        if sha256(source/'artifact_manifest.json')!=c['source_manifest_sha256'] or sha256(source/f"snapshot-{c['decision']:03d}.pkl")!=c['snapshot_sha256']:
            raise ValueError('source changed after plan commitment')
        groups.setdefault(c['source_run'],[]).append(c['decision'])
    if not python.is_file():raise ValueError('missing isolated sim Python')
    if not python.absolute().is_relative_to(root):
        marker=json.loads((python.parent.parent/'e2-derived-environment.json').read_text())
        if marker['workspace']!=str(root):raise ValueError('runtime not an E2-owned independent environment')
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True)
    selected=next(x.split(',') for x in inventory.splitlines() if int(x.split(',')[0])==gpu_index)
    if int(selected[2])<4096:raise RuntimeError('insufficient available simulation memory; preserve other tasks')
    env=os.environ.copy();env.update(HOME=str(root/'runtime/home'),HF_HOME=str(root/'cache/huggingface'),
        LIBERO_CONFIG_PATH=str(root/'runtime/libero-config'),PYTHONPATH=os.pathsep.join(map(str,[repo,up,up/'external_dependencies/LIBERO'])),
        PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES=selected[1].strip(),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',
        MUJOCO_EGL_DEVICE_ID=str(gpu_index),WANDB_MODE='disabled',WANDB_DISABLED='true',HF_HUB_OFFLINE='1',
        HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',NO_ALBUMENTATIONS_UPDATE='1',TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='2',NUMBA_NUM_THREADS='2')
    for source,decisions in groups.items():
        invocation='e2v1-'+source;operator=root/'operator'/invocation;operator.mkdir()
        write_json(operator/'plan_binding.json',{'plan_sha256':sha256(plan_path),'source_run':source,'decisions':decisions})
        command=[str(python),'-u',str(repo/'scripts/record_process.py'),'--receipt',
            str(root/'runs/consistency_processes'/f'{invocation}.exit.json'),'--',str(python),'-u',
            str(repo/'scripts/e2_validate_snapshots.py'),'--workspace',str(root),'--source-run',source,
            '--invocation-id',invocation,'--decisions',*map(str,decisions)]
        with (operator/'stdout.txt').open('x') as stdout,(operator/'stderr.txt').open('x') as stderr:
            child=subprocess.Popen(command,cwd=repo,env=env,stdout=stdout,stderr=stderr)
            try:code=child.wait(timeout=600)
            except subprocess.TimeoutExpired:
                child.terminate();child.wait(timeout=45)
                write_json(operator/'timeout.json',{'wall_cap_seconds':600,'wrapper_returncode':child.returncode})
                raise
        print(json.dumps({'source_run':source,'wrapper_exit':code,'planned_checks':2*len(decisions)}),flush=True)
        if code:raise RuntimeError('validation failed; retain IDs and submit precise recovery, no implicit retry')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--sim-python',type=Path,required=True);p.add_argument('--gpu-index',type=int,default=0)
    a=p.parse_args();run(a.workspace,a.sim_python,a.gpu_index)
