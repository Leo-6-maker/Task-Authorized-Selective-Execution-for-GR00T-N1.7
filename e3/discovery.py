"""CPU-only pinned source/asset/restricted official initialization inspection.

No simulator, LIBERO package import, policy, unsafe pickle, CUDA or EGL call.
Runtime compiled IDs remain UNKNOWN; static XML names are not live geom IDs.
"""
import ast
import hashlib
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

LIBERO_PIN='8f1084e3132a39270c3a13ebe37270a43ece2a01'
A=[('salad_dressing','cream_cheese'),('bbq_sauce','ketchup'),('tomato_sauce','milk'),('butter','orange_juice'),('milk','chocolate_pudding'),('chocolate_pudding','alphabet_soup'),('orange_juice','butter')]
B=[('cream_cheese','alphabet_soup'),('ketchup','alphabet_soup')]

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def instruction(task):return 'pick up the '+task.replace('_',' ')+' and place it in the basket'

def objects(text):
    match=re.search(r'\(:objects\s+(.*?)\)',text,re.S)
    require(match is not None,'BDDL objects missing')
    tokens=match[1].split();out={};pending=[]
    while tokens:
        token=tokens.pop(0)
        if token=='-':
            require(pending and tokens,'malformed object declaration');kind=tokens.pop(0)
            for name in pending:
                require(name not in out,'duplicate scene object');out[name]=kind
            pending=[]
        else:pending.append(token)
    require(not pending,'untyped object declaration')
    return out

def inspect(lib,workspace):
    import numpy as np
    import torch
    lib=Path(lib);workspace=Path(workspace)
    require(not torch.cuda.is_initialized(),'CPU-only inspection requires uninitialized CUDA')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=lib,text=True).strip()==LIBERO_PIN,'LIBERO pin differs')
    source=lib/'libero/libero';mapfile=source/'benchmark/libero_suite_task_map.py'
    tree=ast.parse(mapfile.read_text());mapping=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='libero_task_map' for t in n.targets)))
    official=mapping['libero_object'];require(len(official)==10 and len(set(official))==10,'official ten tasks differ')
    old={sha(f) for split in ['DEV','CALIB','TEST'] for f in (workspace/'runs'/split).glob('*/benchmark_init.npy')}
    rows=[];allnew=set();safe=[np.core.multiarray._reconstruct,np.ndarray,np.dtype,type(np.dtype('float64')),type(np.dtype('float32'))]
    # XML source fingerprint covers every local asset XML (not compiled IDs).
    xmlrows=[]
    for f in sorted((source/'assets').rglob('*.xml')):
        xml=ET.parse(f).getroot();xmlrows.append(dict(path=str(f.relative_to(lib)),sha256=sha(f),body_names=[x.get('name') for x in xml.iter('body') if x.get('name')],geom_names=[x.get('name') for x in xml.iter('geom') if x.get('name')]))
    for target,wrong in A+B:
        name=instruction(target).replace(' ','_');require(name in official and instruction(wrong).replace(' ','_') in official,'unofficial task instruction')
        bddl=source/'bddl_files/libero_object'/(name+'.bddl');initial=source/'init_files/libero_object'/(name+'.pruned_init');relative=str(bddl.relative_to(lib))
        blob=subprocess.check_output(['git','rev-parse',LIBERO_PIN+':'+relative],cwd=lib,text=True).strip();require(subprocess.check_output(['git','show',LIBERO_PIN+':'+relative],cwd=lib)==bddl.read_bytes(),'active BDDL differs from pinned Git bytes')
        obj=objects(bddl.read_text());require({target+'_1',wrong+'_1','basket_1'}<=set(obj),'planned object absent')
        with torch.serialization.safe_globals(safe):states=torch.load(initial,map_location='cpu',weights_only=True)
        identities=[]
        for index,state in enumerate(states):
            arr=np.asarray(state,dtype=np.float64);require(arr.ndim==1 and arr.size>0 and np.isfinite(arr).all(),'invalid initialization')
            buf=io.BytesIO();np.save(buf,arr,allow_pickle=False);identities.append(dict(index=index,sha256=hashlib.sha256(buf.getvalue()).hexdigest(),shape=list(arr.shape),dtype=str(arr.dtype)))
        require(len(states)>=20,'official init16–19 unavailable; no substitution')
        before={x['sha256'] for x in identities[:16]}|old
        for value in identities[16:20]:
            require(value['sha256'] not in before and value['sha256'] not in allnew,'heldout initialization bytes overlap E2/prior/new identity');allnew.add(value['sha256'])
        rows.append(dict(task=target,c2_target=wrong,official_task_name=name,official_language=instruction(target),bddl_declared_language=re.search(r'\(:language\s+([^)]*)\)',bddl.read_text()).group(1),bddl_path=relative,bddl_git_blob=blob,bddl_sha256=sha(bddl),objects=obj,init_file_path=str(initial.relative_to(lib)),init_file_sha256=sha(initial),official_init_count=len(states),initializations=identities[16:20],previous0_15_hashes=[x['sha256'] for x in identities[:16]],scene_source_fingerprint=digest({'bddl':sha(bddl),'assets':xmlrows}),runtime_objects_dict='UNKNOWN_NOT_CREATED',compiled_body_geom_IDs='UNKNOWN_NOT_CREATED'))
    require(not torch.cuda.is_initialized(),'inspection initialized CUDA')
    return dict(status='CPU_SOURCE_AND_INIT_VERIFIED_RUNTIME_SCENE_BINDING_PENDING',libero_head=LIBERO_PIN,official_task_names=official,benchmark_map_sha256=sha(mapfile),tasks=rows,asset_XML_inventory=xmlrows,asset_XML_fingerprint=digest(xmlrows),new_unique_task_init_identities=len(allnew),old_E2_init_original_hash_count=len(old),new_E2_byte_overlap=0,model_calls=0,simulator_created=False,CUDA_initialized=False,blockers=['Live env.objects_dict/compiled body/geom mapping cannot be verified without separately authorized native scene inspection before protocol freeze.'])
