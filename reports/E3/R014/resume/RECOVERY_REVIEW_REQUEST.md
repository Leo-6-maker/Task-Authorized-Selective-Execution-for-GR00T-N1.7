# R014 failed bootstrap — scoped re-entry review requested

Status: **READY_FOR_INDEPENDENT_R014_REENTRY_REVIEW**. This is an execution/custody report, not scene success, protocol freeze or TEST authorization. Current machine permit's one diagnostic process was attempted and failed; no automatic retry is performed even though no constructor was reached.

## Actual attempt

At clean exact `9599f2e1b8d8ad4a51cb79cd7274f3daff493d42`, current-main grant matched signed `eac3d8edeb3de7a33727d462ea652d7719e03629`. Fresh CPU verification passed all106 XML,9 BDDL/init sources and36 official initialization identities, no E2 byte overlap, no initialized CUDA. All7 pinned upstream source hashes and dual Python3.12.14 package inventories matched (server138/sim159). Owner's existing same-scope GPU1 permission was bound to a measured UUID/EGL physical1; free15899MiB exceeded9216MiB. No competing compute-process set change was observed; owner jobs were untouched.

The once-only `e3.scene_probe` child, original record_process wrapper and external operator returned **1**. The saved result is **SCENE_INSPECTION_ERROR / EOFError**, constructors0/init_loads0/bindings0/model_calls0/TEST_reservations0. Failure occurred while importing the upstream `libero.libero` configuration bootstrap, before `LiberoEnv` import completed and before any `LiberoEnv(...)` call. No native scene worker started. Both child/wrapper PIDs were absent in /proc after actual exit; no E3 TEST roots were created. Import may have created the real user's empty default `.libero` directory; it is retained; whether it preexisted was not captured, and no config file was generated.

## Root cause and prepared correction

This executor's external diagnostic launcher supplied CUDA/EGL/PYTHONPATH/offline bindings but omitted **LIBERO_CONFIG_PATH** and the task runtime HOME. The pinned LIBERO initializer consequently looked for the login HOME's default config, prompted for dataset setup, then received closed/exhausted stdin and raised EOFError. The correct task-owned `runtime/libero-config/config.yaml` already existed and was not modified. Existing E2 launchers, e3.supervisor and e3.server_launcher already set this binding. No package, asset, model or science change is needed. This was a deployment omission in this attempt; the signed probe source and science remain unchanged.

Prepared next invocation must explicitly set:

- `LIBERO_CONFIG_PATH = workspace/runtime/libero-config` and `HOME = workspace/runtime/home`.
- The same pinned repo/upstream/LIBERO PYTHONPATH, approved GPU1 UUID/EGL1, offline/telemetry-disabled settings and noninteractive stdin.
- Before importing anything native, require the existing config and verify benchmark_root, assets, BDDL and init paths resolve to the actual pinned LIBERO source; missing/misdirected config fails closed without generating or modifying config.
- All fresh R014 source/current-grant/exact clean Head/resource/backup checks must be repeated. Never answer the bootstrap prompt, generate a replacement config, reinstall, download, loosen resource guard, switch GPU or edit signed source.

`CPU_CONFIG_REGRESSION.py` executes **only** pinned LIBERO's os/yaml configuration initializer by runpy in real child processes, with closed stdin and CUDA disabled. Four tests cover: actual original EOF, valid existing config/no prompt/no rewrite, missing explicit config/no side effect, wrong source mapping/early failure. No simulator/benchmark/GR00T/native scene import occurs. Normal and -O results plus full187 normal/-O regression and frozen E2 audit receipts are supplied in this directory's machine proofs.

## Preserved originals and scientific boundary

Full E2 normal/-O read-only audit equals the original120 final audit, including117 full outcomes and3 permanent CLEANUP_ERROR. All18070 original files were rehashed before this attempt and again after the failure with canonical manifest identity unchanged. No original result, reservation, source, grant, k3, TaskSpec, oracle, control contract, seed, split or course fallback changed.

This failed R014 **diagnostic process** is permanently retained and is not a TEST attempt. E3 still has0/160 reservations,0 native constructors and0 init loads. No scientific variant is selected on outcomes. Original EOF, staging bundle failure and successful CPU recovery receipts all remain in the private whole/member-hashed archive; independent GPT has not examined private bytes merely because executor checked them.

## One requested next decision

Independent GPT should review this failed bootstrap, CPU-only deployment correction, exact execution identity and custody, then explicitly authorize **one additional same-scope 9-environment/36-init scene-only diagnostic** if acceptable. Either publish a new named exact9599 machine permit with unchanged science scope, or explicitly specify how the failed one-process limit is superseded; the executor does not self-extend R014. Source9599 remains unchanged, and this report Head is not a new approved runnable version.

No E3 protocol freeze or formal TEST grant is requested by this failure report alone. Successful future scene identity would still not establish native reset/settling/Shadow/policy fidelity. E2 independent R3 and Nov6 E2-only course delivery remain separate priorities. No auto merge or course submission.
