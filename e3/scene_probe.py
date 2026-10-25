"""NOT EXECUTED. Bounded pre-freeze scene identity diagnostic, separate grant.

Requires independent E3_SCENE_INSPECTION_AUTHORIZED exact-Head permit AND fresh
owner resource approval; never uses an E2/TEST grant or creates a TEST slot.
Nine constructors,36 official init loads, zero policy/server/main action calls.
"""
import argparse,json,subprocess,traceback
from pathlib import Path
from .authorization import git,resource
from .discovery import require,sha
from .ledger import write

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['repo','workspace','allocation-record','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--review-commit',required=True);p.add_argument('--review-path',required=True);a=p.parse_args(argv)
    import re
    require(re.fullmatch('[0-9a-f]{40}',a.review_commit) and re.fullmatch(r'docs/reviews/[A-Za-z0-9._-]+\.json',a.review_path),'full independent scene inspection grant required')
    require(not git(a.repo,'status','--porcelain'),'scene inspection exact clean Head required')
    text=git(a.repo,'show',a.review_commit+':'+a.review_path);require(git(a.repo,'show','refs/remotes/origin/main:'+a.review_path)==text,'scene grant no longer current')
    grant=json.loads(text);head=git(a.repo,'rev-parse','HEAD');require(grant.get('disposition')=='E3_SCENE_INSPECTION_AUTHORIZED' and grant.get('authorized_head')==head and grant.get('source_inventory_sha256')==sha(a.repo/'configs/e3_sources.proposed.json') and grant.get('maximum_environment_constructors')==9 and grant.get('maximum_initialization_loads')==36 and grant.get('maximum_policy_calls')==0,'separate bounded pre-freeze scene grant missing/different')
    identity={'authorized_head':head,'review_commit':a.review_commit};allocation=json.loads(a.allocation_record.read_text());resource(allocation,identity)
    import os
    require(os.environ.get('MUJOCO_EGL_DEVICE_ID')==str(allocation['gpu_index']) and os.environ.get('CUDA_VISIBLE_DEVICES')==allocation['gpu_uuid'],'explicit fresh allocated EGL/CUDA binding required')
    selected=next(row.split(',') for row in subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True).splitlines() if int(row.split(',')[0])==allocation['gpu_index'])
    require(selected[1].strip()==allocation['gpu_uuid'],'fresh scene allocation UUID differs')
    from tase.resource_memory import require_free_memory
    require_free_memory(int(selected[2])*1024**2)
    a.output.mkdir(parents=True,exist_ok=False);result=dict(status='STARTED',authorized_head=head,grant_commit=a.review_commit,constructors=0,init_loads=0,model_calls=0,TEST_reservations=0,bindings=[],actual_exit=1)
    try:
        import numpy as np
        import torch
        from gr00t.eval.sim.LIBERO.libero_env import LiberoEnv
        from tase.task_spec import TaskSpec
        from e3.scene import verify_files,validate
        import io,hashlib
        source=json.loads((a.repo/'configs/e3_sources.proposed.json').read_text());lib=a.workspace/'upstream/Isaac-GR00T/external_dependencies/LIBERO';safe=[np.core.multiarray._reconstruct,np.ndarray,np.dtype,type(np.dtype('float64')),type(np.dtype('float32'))]
        require(git(lib,'rev-parse','HEAD')==source['libero_head'],'actual LIBERO changed')
        for row in source['tasks']:
            native=None;result['constructors']+=1
            try:
                from .discovery import instruction
                # Verify official init/BDDL before creating an environment.
                verify_files(lib,{'bddl_sha256':row['bddl_sha256'],'init_file_sha256':row['init_file_sha256']},row)
                native=LiberoEnv(task_bddl_file=str(lib/row['bddl_path']),task_description=instruction(row['task']));raw=native._env
                with torch.serialization.safe_globals(safe):states=torch.load(lib/row['init_file_path'],map_location='cpu',weights_only=True)
                for item in row['initializations']:
                    value=np.asarray(states[item['index']],dtype=np.float64);buf=io.BytesIO();np.save(buf,value,allow_pickle=False);require(hashlib.sha256(buf.getvalue()).hexdigest()==item['sha256'],'actual official initialization bytes changed')
                    result['init_loads']+=1;raw.set_init_state(value);spec=TaskSpec.from_native(raw,row['task']);validate(spec,{'trusted_target':row['task']+'_1','basket':'basket_1','policy_target':row['c2_target']},row)
                    result['bindings'].append(dict(task=row['task'],init_index=item['index'],init_hash=item['sha256'],TaskSpec=vars(spec),compiled_scene_sha256=hashlib.sha256(raw.sim.model.get_xml().encode()).hexdigest()))
            finally:
                if native is not None:native.close()
        result.update(status='SCENE_IDENTITY_INSPECTED_NOT_TEST_AUTHORIZATION',actual_exit=0)
    except BaseException as exc:result.update(status='SCENE_INSPECTION_ERROR',error_type=type(exc).__name__,traceback=traceback.format_exc());raise
    finally:write(a.output/'scene-inspection-result.json',result)

if __name__=='__main__':main()
