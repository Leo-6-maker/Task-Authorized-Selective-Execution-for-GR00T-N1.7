"""Deterministic proposed160 cells from real CPU-verified source identities."""
import re
from .discovery import A,B,require,instruction,digest

def build(source):
    require(source['status']=='CPU_SOURCE_AND_INIT_VERIFIED_RUNTIME_SCENE_BINDING_PENDING','verified CPU source required')
    tasks={t['task']:t for t in source['tasks']}
    require(len(tasks)==len(source['tasks'])==9 and set(tasks)=={a for a,b in A+B},'complete unique nine-task source set required')
    expected=['f83758a229d7a098eaaa1b2c1bd33093aa7c8e33','543355b1164f931cc6da9be8131e6b8924992397','d48e7b34ce9325a9ba9f16aaf5bafb210ee1d028','358024afc867808122cf9ea9dfbbdb82c86ad703','6b10f254cd992cdb1da1b2382b4dff396d43fc35','1df6bc98ea2e209103a43d5dd2c23620fea4f12c','517bb4eef4fb1ee89f85cfef4a200eb2a88d175a']
    for (task,wrong),blob in zip(A,expected):require(tasks[task]['bddl_git_blob']==blob,'pinned task BDDL Git identity differs')
    require(digest(source['asset_XML_inventory'])==source['asset_XML_fingerprint'],'asset XML source fingerprint differs')
    for target,wrong in A+B:
        row=tasks[target];require({target+'_1',wrong+'_1','basket_1'}<=set(row['objects']),'required planned scene objects missing')
        require([x['index'] for x in row['initializations']]==[16,17,18,19],'fixed init set/order unavailable; never substitute')
        require(row['scene_source_fingerprint']==digest({'bddl':row['bddl_sha256'],'assets':source['asset_XML_inventory']}),'scene source fingerprint differs')
    cells=[];scenario=0
    for epoch,pairs,arms in [('E3A',A,['B0','G']),('E3B',B,['B0','A0','G'])]:
        ordinal=0
        for task,wrong in pairs:
            row=tasks[task];require(row['c2_target']==wrong,'fixed mapping differs')
            for initial in row['initializations']:
                require(initial['index'] in [16,17,18,19] and re.fullmatch('[0-9a-f]{64}',initial['sha256']),'real init identity required')
                for condition in ['C0','C2']:
                    for arm in arms:
                        ordinal+=1;cells.append(dict(run_id=f'{epoch.lower()}-test-{ordinal:04d}',epoch=epoch,protocol_id='E3-001-v1.0',split='TEST',task=task,init_index=initial['index'],init_hash=initial['sha256'],init_file_sha256=row['init_file_sha256'],bddl_sha256=row['bddl_sha256'],bddl_git_blob=row['bddl_git_blob'],scene_source_fingerprint=row['scene_source_fingerprint'],condition=condition,system=arm,scenario_id=f'{epoch}-{task}-i{initial["index"]}-{condition}',policy_target=task if condition=='C0' else wrong,actual_policy_language=instruction(task if condition=='C0' else wrong),trusted_target=task+'_1',basket='basket_1',policy_seed=641000+scenario,environment_seed=641001+scenario))
                    scenario+=1
    return cells

def verify(cells,source):
    require(type(cells) is list and cells==build(source),'E3 cells changed, incomplete, reordered or forged')
    require(len(cells)==160 and len({c['run_id'] for c in cells})==160,'full candidate count/identity mismatch')
    inits={(c['task'],c['init_index']):c['init_hash'] for c in cells};require(len(inits)==36 and len(set(inits.values()))==36,'init byte overlap')
    old={h for t in source['tasks'] for h in t['previous0_15_hashes']};require(not set(inits.values())&old,'overlap with old0–15 contents')
    return dict(status='PROPOSED160_MANIFEST_VERIFIED_NOT_FROZEN',cells_sha256=digest(cells),A=112,B=48,independent_task_init_clusters=36,model_calls=0)
