"""Enumerate fixed official initializations without model/simulation/effects.

Select by official index order, excluding all DEV content and duplicate content.
TEST rows are a proposal only; R2 is still required before execution.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from libero.libero import benchmark,get_libero_path
from tase.evidence import sha256,write_json


def build(workspace,repo):
    if torch.cuda.is_initialized():raise RuntimeError('split enumeration must remain CPU-only')
    suite=benchmark.get_benchmark_dict()['libero_object']();tasks=['alphabet_soup','cream_cheese','ketchup'];rows=[]
    allow=[np.core.multiarray._reconstruct,np.ndarray,np.dtype,type(np.dtype('float64')),type(np.dtype('float32'))]
    for task_name in tasks:
        task=suite.get_task(suite.get_task_names().index(f'pick_up_the_{task_name}_and_place_it_in_the_basket'))
        path=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
        with torch.serialization.safe_globals(allow):states=torch.load(path,map_location='cpu',weights_only=True)
        dev={sha256(p) for p in (workspace/'runs/DEV').glob('*/benchmark_init.npy')
             if json.loads((p.parent/'reservation.json').read_text())['task']==task_name}
        identities=[]
        for index,state in enumerate(states):
            buffer=io.BytesIO();np.save(buffer,np.asarray(state,dtype=np.float64),allow_pickle=False)
            identities.append((index,hashlib.sha256(buffer.getvalue()).hexdigest()))
        # Old declared development indices are excluded even if an E2 run failed
        # before writing its initialization; no old raw evidence is required.
        dev.update(h for i,h in identities if i in [0,1]);used=set(dev);eligible=[]
        for index,content_hash in identities:
            if content_hash in used:continue
            used.add(content_hash);eligible.append((index,content_hash))
        if len(eligible)<14:raise RuntimeError('insufficient unique official initialization content; no silent resizing')
        for position,(index,content_hash) in enumerate(eligible[:14]):
            rows.append({'task':task_name,'init_index':index,'init_hash':content_hash,
                         'split':'CALIB' if position<4 else 'TEST','init_file_sha256':sha256(path)})
    return {'epoch':'E2','protocol_id':'TASE-002-v1.0','selection':'FIRST_OFFICIAL_INDEX_UNIQUE_CONTENT_EXCLUDING_OLD_0_1_AND_ALL_E2_DEV',
        'rows':rows,'calib_initializations_per_task':4,'test_initializations_per_task':10,
        'test_execution_authorized':False,'runtime_lock_sha256':sha256(repo/'configs/runtime_lock_E2.json'),
        'classification':'GOVERNANCE_HOLDOUT_NOT_A_PRETRAINING_UNSEEN_CLAIM','model_or_sim_created':False,
        'independent_review':'NOT_PERFORMED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=build(a.workspace,a.repo);write_json(a.output,data)
    print(json.dumps({'rows':len(data['rows']),'CALIB':12,'TEST_PROPOSED_NOT_AUTHORIZED':30,'model_or_sim_created':False}))
