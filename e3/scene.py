"""Runtime TaskSpec checks against real source object set, not policy language."""
from tase.task_spec import TaskSpec
from .discovery import require,sha

def validate(spec,cell,source):
    spec.validate();require(spec.target==cell['trusted_target'] and spec.basket==cell['basket'],'wrong trusted TaskSpec')
    require(set(spec.objects)==set(source['objects']) and cell['policy_target']+'_1' in spec.objects,'ambiguous/missing/extra live scene objects')
    return spec

def verify_files(libero,cell,source):
    require(sha(libero/source['bddl_path'])==cell['bddl_sha256'] and sha(libero/source['init_file_path'])==cell['init_file_sha256'],'pinned BDDL or official init source differs')

def verify_inventory(libero,source):
    """CPU rehash of active task+init and complete local XML inventory."""
    require(sorted(str(f.relative_to(libero)) for f in (libero/'libero/libero/assets').rglob('*.xml'))==sorted(x['path'] for x in source['asset_XML_inventory']),'active scene asset XML set changed')
    for item in source['asset_XML_inventory']:require(sha(libero/item['path'])==item['sha256'],'active scene asset XML bytes changed')
    for row in source['tasks']:verify_files(libero,row,row)
