# R018 CPU correction, refreeze and same-ID0001 reconciliation

**READY_FOR_R018_CPU_REFREEZE_REVIEW.** R018 CPU scope completed; no native continuation, replay or new TEST. Source-tested clean snapshot: `6c8e38c1c84083b7664ee0cb7f11fc0cb0d03651`. This branch is stacked on reviewed PR40 `5e3eab34cbde600caa340452996dd470704e55c6`; the final report commit must have zero code/config/test delta from the tested snapshot. The exact full report Head is the PR head / Git commit containing this file; no report can embed its own eventual commit hash.

## B1 fixed and legitimate lock refreshed

Historical fixtures now obtain both filenames and bytes from historical `859e40b5f460365a8853bf3486969e9f8e28951c` and its own139-entry lock. The historical positive remains. A separate positive runs `verify_freeze()` against the actual new worktree and141-entry lock without a mock. Current-tree negative tests reject either new audit module/test missing, mutated, or omitted from the lock, plus an extra unlocked Python source and config/runtime drift. Source inventory is enumerated independently of supplied lock keys; mandatory source coverage was strengthened, never relaxed. Both `e3/audit_manifest.py` and `tests/test_e3_audit_manifest.py` are locked.

New lock SHA-256: `14abb2ace96424b68a5b0bd25fcc3b897d152fa0eb8efb28ae153de38732b3bc`. `SOURCE_AND_FREEZE_IDENTITY.json` records all changed paths and unchanged science/native hashes. The R018-reviewed audit integration/helper bytes remain exact. No Gate/k3/TaskSpec/Oracle/weights/tasks/init/seed/control/reset/statistics change.

## Actual CPU verification

| Clean source snapshot | Ordinary | `python -O` |
| --- | --- | --- |
| Local | 231/231, exit0 | 231/231, exit0 |
| Corelab | 231/231, exit0 | 231/231, exit0 |

`CPU_TEST_RECEIPTS.json` binds raw logs/exit hashes, public logs, timestamps and full source identity.35-case preliminary targeted run also exited0 and is labeled precommit. Source-identical clean independent CPU clone was used after external harness/history recovery errors. Those errors were not silently removed: `OPERATOR_FAILURES_RETAINED.json` preserves initial -O1, Git fetch1, alternate-checkout128 and historical-object-probe128 with raw private source/log bindings. All prior clones and misplaced operator JSON remain in place. These were external CPU operator errors; no native/original file changed.

Actual CPU integration checks exercised authorize, launcher, supervisor, native runner and direct server using both historical R017 and non-execution R018, ordinary/-O: **20 expected denials**, each before allocation/model/native setup; corrected wrapper exits0/0. `STALE_GRANT_DENIALS.json` proves historical identity is accepted for readonly original audit while stale R017 cannot execute new code/0002.

## 0001: three distinct histories retained

- Acquisition: `859e40b5f460365a8853bf3486969e9f8e28951c` / R017 `ca979be10c00389ed57b77967c232d7a84132406`, Salad Dressing/init16/C0/B0. Raw SUCCESS, official success true,121 policy controls +10 settling,16 requests,16 ACCEPT prefixes (15×8 +1), actual native/supervisor0/0. No G/A0/Shadow episode.
- Original frozen ordinary/-O audit: **1/1, manifest coverage failure**, unchanged forever. Old result/manifest/reservation/grant and old report files are untouched. Original controller1 and server SIGINT return−2/mapped130/launcher1 are retained; no all-process-exit0 claim.
- **New R018 versioned readonly reconciliation:** all74 sealed files/15 mandatory paths, full78 original+exit custody, historical source/claim/start/exit, full physical/Oracle/action checks and exact old/new ordinary/-O repaired audit equivalence passed. `RECONCILIATION_0001_v1.json` records authority, immutable sources, hashes and real exits; `RECONCILED_ANALYSIS_v1.json` marks existing0001 eligible SUCCESS under R018's explicit conditional permission. This is executor-attested private verification, not an independent reviewer private-byte rehash or self-signed approval.

Current versioned all160 ledger: **1 consumed/eligible SUCCESS,159 unstarted unknown** (A111+B48). Original failed frozen ledger is preserved separately in R017. Frozen statistics were rerun only as CPU readonly audit on the same originals; all planned denominators, bootstrap2000/seed641500 remain. This incomplete B0-only observation gives **no E3 Gate efficacy conclusion**; conditional prevention=N/A. All missing values stay unknown, never safe zero.

## Custody, E2 and next action

New218-member archive includes original78 and CPU/error evidence; whole SHA-256 `7f17556d09cc34a373284825b90f828dc81c87eb69bfc505153c00b19f6973e5`, 17,591,512bytes, two locations with every member verified. Prior233-member R017 archive was freshly reverified at both locations before reconciliation. Private runtime maps preserve the actual native tree, old/failed CPU clones and new clean CPU tree separately. Post-CPU /proc check found no owned project native process;0002 and E3-B remain absent. Final GitHub metadata/outer archive-exit receipts are sealed in a separate final closure after report push.

E2 is separate: all18,070 originals freshly rehashed unchanged; formal PR38 `9efba1994235ee0cb844653a45c6f1b0812442a7` untouched, no new E2 rollout, no pooling, independent R3 remains pending. Course11/06 priority preserved; no automatic merge or Canvas submission.

**One next action:** independent consolidated review of this complete new Head, new lock and same-ID reconciliation. R018 does not authorize any model/native/TEST action and this night's stop remains latched. Any later exact-version grant must start with untouched0002, never replay0001; first A4 checkpoint must combine historical0001 +0002–0004. Resource consent is not a replacement for the required exact-version grant and fresh resource binding.

## Readonly reproduction

From the final clean report checkout, with the existing CPU dependencies and CUDA hidden:

```sh
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python -m e3.freeze --repo .
```

With private custody mounts available, `REPRODUCE_RECONCILIATION.py --help` lists explicit readonly inputs. Give it a new exclusive output path outside original runs. It never reserves IDs or calls policy/simulator. The exact executed script SHA is bound in the reconciliation record. No public command starts native execution.
