# GPU1 shared deployment — complete CPU resource-entry delta

**READY_FOR_INDEPENDENT_GPU1_RESOURCE_DELTA_REVIEW / NO_NEW_TEST_GRANT.** Owner explicitly selected GPU1 and allowed parallel deployment. This is a CPU-only candidate stacked on preserved PR26 report Head9178913a10bd32fab9e2701a6a74e86c77d210fb. CPU-tested source commit is `d9e445cc693c4fc7284cfa54a83924e340f04360`. Actual last acquired execution stays `908bef373eedf8d008ad8d9a91478e3f719eecfb` under R012; candidate acquired zero IDs and started no model/simulator.

## Concrete failure and resulting behavior

GPU1 reports16376MiB total and10121MiB free. Both the TEST launcher and native model process previously demanded16GiB free,so even an idle16376MiB device could not pass. The original exact CPU guard rejection/actual exit1 is preserved in the parent report. Merely recording parallel permission could not change either hard-coded predicate.

The pinned actual R012 server's saved1823 inference records show peak allocated6386141184bytes and peak reserved6482296832bytes (about6.04GiB). Its source loaded/inference hashes appear in `observations/memory-evidence.json`. These are allocator telemetry,not TEST efficacy/Oracle/Gate outcomes. They do not prove a GPU1 startup or every future memory demand.

The proposed single fixed admission floor is **9GiB free**,checked by a shared pure CPU helper in both launcher and native process. The existing allocator rule stays exactly `min(0.55,(free-2GiB)/total)`. At the9GiB floor this provides at most7GiB to the allocator,about0.96GiB above the observed peak while retaining the2GiB arithmetic reserve. At the recorded GPU1 inventory the budget is8073MiB. Existing inputs with>=16GiB free compute the identical original fraction. No CLI/environment/resource-receipt override can relax the new floor,55% cap or2GiB reserve.

The native process rechecks live CUDA memory after the launcher,so a fall below9GiB is rejected before model construction. Inventory types/ranges fail closed. Validation now uses ValueError; native startup remains nonzero on failure and no TEST ID is reserved by server startup. GPU allocation/UUID/EGL binding,strict exact-head review admission,loopback readiness,exclusive native output creation and post-episode lifecycle remain unchanged. New loaded metadata records actual total memory and resource policy. No model dtype,weights,offload,quantization,policy input or inference operation changes.

The reserve is a sampled allocator-budget margin,not an exclusive device reservation. Fragmentation,non-allocator CUDA costs and other jobs' later growth can still cause failure. Such a real startup/runtime failure must remain an error with actual receipts; the candidate provides no retry,error suppression or override. GPU1 native capacity validation is **NOT_EXECUTED**.

## Exact implementation boundary

Only four executable/test paths differ from actual908 and parent917:

- `tase/resource_memory.py`: fixed9GiB floor,existing2GiB reserve/55% cap,strict inventory validation.
- `scripts/e2_test_server.py`: use that floor after unchanged grant/allocation/environment verification and before spawning.
- `tase/server.py`: use the same fresh-memory rule before allocation/model creation;record resource metadata.
- `tests/test_resource_memory.py`:11 CPU cases,including genuine CPU subprocesses with explicit fake torch/GR00T modules. Exit17 proves pre-model rejection;exit23 proves reaching only the stubbed constructor boundary. No fixture creates a model or MODEL_LOADED receipt.

All configs remain byte-identical,including config SHA256 `69df8bae0fa52314c62815771802b129159419a95411325cf413b09d2d03fb17` and all14 frozen source hashes. No hash-only config edit is needed because neither entry file belongs to that14-file map;the new exact Git Head still requires independent authorization. The entire post-load policy request/reset/seed/instrumentation AST is identical. Gate,k3,TaskSpec,wrong-object-lift oracle,C0/C2,models,initializations/seeds,16/8/720,120 IDs,statistics and cleanup are unchanged. `scientific_configuration_check.json` records this boundary and rejection of the old R012 grant on the CPU candidate.

## Actual CPU and original-data validation

Local ordinary134/134 actual0 and optimized134/134 actual0. Corelab ordinary134/134 actual0 and optimized134/134 actual0,using the existing environments. New cases cover one-byte-below/exact-floor boundaries,invalid/malformed inventory,55% cap/2GiB margin,old-formula equivalence,GPU1 routing/no-spawn on low memory,native recheck,and the16376MiB device. The baseline startup/lifecycle/history suite and its expected negative-process exits remain included.

On real Corelab originals,new-source ordinary and optimized historical audits each actual0. **Both entire JSON outputs equal the prior frozen908 audit**,including all120 rows,pairs,statistics,timing and code epochs. Original16 source members remain byte-identical;all old runtime checkouts stay clean at their exact Heads.52 recorded CPU child receipts were checked absent after exit. None is a native TEST process.

Actual ledger remains84 consumed=61SUCCESS+10TIME_LIMIT+10SEMANTIC_ABORT+3 original CLEANUP_ERROR0010/0014/0016,81 known outcomes,36NOT_STARTED,next0085 absent. Saved official-success observations never promote old cleanup failures. No old ID was replayed and no scientific parameter was selected from TEST outcomes.

Original84 full archive and parent review proof remain preserved. New Corelab CPU/source/permission/audit archive393916bytes/840members,SHA256 `141b71b0a242c7da95e838a70916914856e7917a270b104059c6cdcd2bc496ea`;new local CPU/source archive144587bytes/761members,SHA256 `99d5bfe221e05a9162c7a94e10f365163115acdbe166c9a89f678163575289fa`. Both whole+every-member hashes verified in two owner-authorized locations. Public receipts distinguish original and redacted hashes;raw proxy failures/logs/maps remain private. GPT has not independently rehashed private originals.

## One independent control point before deployment

Review the complete final PR Head and this resource-only policy. If accepted,independently register the old R012 acquisition as closed through84 using preserved report917 and original84 archive,then suspend its future acquisition and sign a **new exact-complete-Head TEST grant**. `HISTORICAL_R012_EPOCH_PROPOSAL.json` contains unfilled independent review fields and is not a grant. Current R012 cannot admit the candidate;no signed reviewer files were modified.

Only after that grant: new COMPLETE84-prefix live preflight on owner-assigned sharedGPU1,exact candidate source/config/upstreams/environments/17 model files/30 fixed inits/old hashes/ledger/two backups/storage/port/actual GPU1 UUID/free memory,no residual own worker;use the newly reviewed memory policy rather than the obsolete private20GiB/GPU0-only preflight. Create a new unique native server,verify genuine load/listener without an inference probe,and execute original0085/0086 once. Require full native lifecycle/paired control/prediction/RNG/original84/two-copy checkpoint after0086 before0087;then unchanged original order and four-cell audits through0120. No extra model diagnostic,baseline or TEST ID is requested. Any new real error stops permanently on its consumed ID.

Actual acquisitions currently have three code epochs;this would become a fourth only if independently authorized and actually used. Final R3 must retain every acquisition's source/grant/device and the three historical cleanup censored outcomes. Final36 acquisitions,R3 conclusions and owner course submission remain incomplete. No WBC,training,hardware,automatic merge or self-issued approval.
