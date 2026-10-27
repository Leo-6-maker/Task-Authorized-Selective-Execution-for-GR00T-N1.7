"""One R015-owned scene-only launch. Immutable native code; no retry path."""
from pathlib import Path
import json,subprocess,os,time,signal,hashlib,sys,shutil
r=Path.home()/'Projects/me6401-e2';op=r/'operator/issue33-r015-scene-02';old=r/'operator/issue33-r014-01';repo=Path(json.loads((op/'source-stage.json').read_text())['repo']);base=Path(json.loads((r/'operator/environment-copy-05/launch.json').read_text())['derived_environments']);py=base/'sim/bin/python';head='9599f2e1b8d8ad4a51cb79cd7274f3daff493d42';review='c0ca90f4827c67e04e4033c6358e410f5ac6aace';key='docs/reviews/R015-E3-SCENE-REENTRY-AUTHORIZED.json'
def require(ok,text):
 if not ok:raise ValueError(text)
def put(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==head,'exact source Head changed')
require(not subprocess.check_output(['git','status','--porcelain'],cwd=repo),'source tree dirty')
with (op/'last-grant-fetch.stdout.private.txt').open('x') as out,(op/'last-grant-fetch.stderr.private.txt').open('x') as err:subprocess.run(['git','fetch','origin','main'],cwd=repo,stdin=subprocess.DEVNULL,stdout=out,stderr=err,check=True)
a=subprocess.check_output(['git','show',review+':'+key],cwd=repo);b=subprocess.check_output(['git','show','origin/main:'+key],cwd=repo);require(a==b,'R015 no longer current');grant=json.loads(a)
require(json.loads(subprocess.check_output(['git','show','origin/main:docs/reviews/R014-E3-SCENE-INSPECTION-AUTHORIZED.json'],cwd=repo))['disposition']=='E3_SCENE_INSPECTION_CONSUMED_FAILED_BOOTSTRAP','R014 consumption changed')
require(hashlib.sha256((old/'scene-probe-01/scene-inspection-result.json').read_bytes()).hexdigest()==grant['prior_R014_original_source_sha256'],'old failure differs')
require(json.loads((old/'scene.exit.json').read_text())['exit_code']==1,'old failure exit differs')
for label in ['CPU-preflight','config-preflight','E2-normal','E2-optimized','config-normal','config-optimized','CPU-full-normal','CPU-full-optimized']:
 require(json.loads((op/(label+'.exit.json')).read_text())['exit_code']==0,label+' preflight not successful')
require(json.loads((op/'E2-equivalence.json').read_text())['full_JSON_equals_final120'] is True,'E2 audit changed')
require(json.loads((op/'E2-originals-recheck.json').read_text())['source_files']==18070,'E2 originals not verified')
require((op/'fixed-environment.private.json').is_file(),'environment/source proof absent')
# Existing original configuration only. Verify ALL five configured paths before imports.
config=r/'runtime/libero-config/config.yaml';raw=config.read_bytes();require(hashlib.sha256(raw).hexdigest()=='5fefd0e212d29140bc34de34b4a30e36fe374207dd160a15076a413aefaad63a','original config differs')
lib=r/'upstream/Isaac-GR00T/external_dependencies/LIBERO';libroot=lib/'libero/libero';mapping={'benchmark_root':libroot,'bddl_files':libroot/'bddl_files','init_states':libroot/'init_files','assets':libroot/'assets','datasets':libroot.parent/'datasets'};cfg=json.loads(raw);require(set(cfg)==set(mapping),'config keys differ')
for k,target in mapping.items():require(Path(cfg[k]).is_dir() and Path(cfg[k]).resolve(strict=True)==target.resolve(strict=True),'config path missing/misdirected: '+k)
require((r/'runtime/home').is_dir(),'existing task HOME missing')
allocation=json.loads((op/'gpu-allocation.R015.private.json').read_text());require(allocation['review_commit']==review and allocation['authorized_head']==head and allocation['gpu_index']==1,'new R015-specific allocation missing')
owner=(op/'owner-resource-approval.private.json').read_bytes();require(hashlib.sha256(owner).hexdigest()==allocation['owner_original_sha256'],'owner scope original differs')
smi=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free','--format=csv,noheader,nounits'],text=True);selected=next(x.split(',') for x in smi.splitlines() if int(x.split(',')[0])==1);require(selected[1].strip()==allocation['gpu_uuid'] and int(selected[2])*1024**2>=grant['minimum_free_gpu_memory_bytes'],'GPU1 identity/free memory failed')
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True);require(apps==allocation['compute_apps_before'],'GPU process set changed')
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  cmd=(p/'cmdline').read_bytes().split(b'\0');tokens=[x.decode(errors='replace') for x in cmd]
  require(not any(x in tokens for x in ['e3.scene_probe','e3.server','e3.native_runner','tase.native_server','tase.shadow_worker']),'active task native process exists')
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
for root in ['E3A_TEST','E3B_TEST']:require(not (r/'runs'/root).exists(),'E3 TEST root appeared')
require(shutil.disk_usage(repo).free>=20*1024**3 and shutil.disk_usage(r/'evidence_exports').free>=20*1024**3,'storage insufficient')
sys.path.insert(0,str(repo));from e3.scene import verify_inventory
verify_inventory(lib,json.loads((repo/'configs/e3_sources.proposed.json').read_text()))
output=op/'scene-probe-02';require(not output.exists(),'fixed R015 output already exists')
# Exclusive persistent reviewer-scoped reservation is global for this single authorized attempt.
ledger=op/'R015-one-shot-reservation.json';put(ledger,dict(status='RESERVED_ONE_ADDITIONAL_SCENE_PROCESS_NO_RETRY',authorized_head=head,review_commit=review,review_path=key,grant_sha256=hashlib.sha256(a).hexdigest(),attempt_id='issue33-r015-scene-02',total_historical_diagnostic_ordinal=2,prior_R014_failure_sha256=grant['prior_R014_original_source_sha256'],fixed_output=str(output),owner_receipt_sha256=hashlib.sha256(owner).hexdigest(),allocation_sha256=hashlib.sha256((op/'gpu-allocation.R015.private.json').read_bytes()).hexdigest(),reserved_unix=time.time(),limits=dict(constructors=9,init_loads=36,models=0,server=0,TEST=0,explicit_controls=0)))
env=dict(os.environ,HOME=str(r/'runtime/home'),LIBERO_CONFIG_PATH=str(config.parent),HF_HOME=str(r/'cache/huggingface'),XDG_CACHE_HOME=str(r/'cache'),CUDA_VISIBLE_DEVICES=allocation['gpu_uuid'],MUJOCO_EGL_DEVICE_ID='1',MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',PYTHONNOUSERSITE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMBA_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',WANDB_MODE='disabled',WANDB_DISABLED='true',DO_NOT_TRACK='1',NO_ALBUMENTATIONS_UPDATE='1',TOKENIZERS_PARALLELISM='false',PYTHONPATH=os.pathsep.join(map(str,[repo,r/'upstream/Isaac-GR00T',lib])))
cmd=[str(py),'-u',str(repo/'scripts/record_process.py'),'--receipt',str(op/'scene.exit.json'),'--',str(py),'-u','-m','e3.scene_probe','--repo',str(repo),'--workspace',str(r),'--allocation-record',str(op/'gpu-allocation.R015.private.json'),'--output',str(output),'--review-commit',review,'--review-path',key]
put(op/'scene-activation.private.json',dict(status='R015_PRECONDITIONS_PASSED_ONE_NEW_DIAGNOSTIC',authorized_head=head,grant_commit=review,config_sha256=hashlib.sha256(raw).hexdigest(),config_paths_verified=list(cfg),explicit_environment={k:env[k] for k in ['HOME','LIBERO_CONFIG_PATH','PYTHONPATH','CUDA_VISIBLE_DEVICES','MUJOCO_EGL_DEVICE_ID','MUJOCO_GL','HF_HUB_OFFLINE','WANDB_MODE']},GPU_index=1,fresh_free_MiB=int(selected[2]),config_stdin='DEVNULL',inventory_verified_immediately_before_constructor=True,one_shot_ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),timeout_seconds=600))
with (op/'scene.stdout.private.txt').open('x') as out,(op/'scene.stderr.private.txt').open('x') as err:
 child=subprocess.Popen(cmd,cwd=repo,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
 put(op/'scene-operator.started.json',dict(wrapper_pid=child.pid,operator_pid=os.getpid(),command=cmd,started_unix=time.time()))
 try:code=child.wait(timeout=600)
 except subprocess.TimeoutExpired:
  child.send_signal(signal.SIGTERM)
  try:code=child.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(child.pid,signal.SIGKILL);code=child.wait()
  put(op/'scene-timeout.json',dict(status='R015_DIAGNOSTIC_TIMEOUT_NO_THIRD_ATTEMPT',actual_returncode=code))
 put(op/'scene-operator.exit.json',dict(actual_exit=code,completed_unix=time.time(),wrapper_pid=child.pid))
result=json.loads((output/'scene-inspection-result.json').read_text()) if (output/'scene-inspection-result.json').is_file() else {}
put(op/'R015-one-shot-terminal.json',dict(status='PROCESS_COMPLETE_NO_REENTRY',actual_exit=code,scene_status=result.get('status','NO_RESULT'),constructors=result.get('constructors'),init_loads=result.get('init_loads'),reservations_consumed=1,additional_diagnostic_processes_remaining=0,model_calls=0,TEST_reservations=0))
print(json.dumps(dict(status='R015_SINGLE_SCENE_PROCESS_FINISHED_NO_RETRY',actual_exit=code,scene_status=result.get('status','NO_RESULT'),constructors=result.get('constructors'),init_loads=result.get('init_loads'),model_calls=0,TEST_reservations=0)))
