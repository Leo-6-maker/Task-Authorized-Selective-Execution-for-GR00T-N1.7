# Issue36 — E3 CPU admission repair; scientific freeze still pending

**CPU_REPAIR_READY_FOR_REVIEW / GATE_P_PENDING / E3_TEST_NOT_AUTHORIZED.** No new model, server, native scene, Shadow or TEST was started. Owner explicitly renewed Corelab GPU1 resource consent on2026-10-30; the private owner receipt is preserved. That consent is not an independent scientific/code grant. Current main f10035f only adds the dual-track work package, not a Gate P decision or E3_TEST_AUTHORIZED.

## Concrete error and fix

The E3 server launcher called an undefined `sha256` while building the authorization admission record, although it imports the existing `e3.discovery.sha` helper. With a future valid grant and preflight, this path would raise NameError after resource/socket checks and before handing off to the native server. Existing187 tests did not traverse the allowed launcher branch. This was found on CPU, before any new real E3 acquisition.

A new CPU integration test first reproduced the exact NameError:7 test methods,1 error, actual exit1. Changed one call to the already imported SHA256 helper. The admission record now hashes the exact allocation file bytes and proceeds to the unchanged exclusive native-output helper. No gate/science/resource check is removed, no output directory is pre-created and no native server behavior is changed.

Seven focused tests exercise: exact allocation digest and native exclusive-directory handoff, explicit project HOME/LIBERO config/UUID/EGL/offline bindings, helper nonzero exit propagation, authorization denial before resource effects, stale resource grant, corrupt inventory, insufficient9GiB memory, wrong UUID and occupied port. Positive branches use synthetic authorization/runtime/GPU/socket/native-helper mocks; real temporary allocation bytes and hashing are used. These tests do not prove real model loading or actual TEST execution. Existing R007 native-output lifecycle tests remain unchanged.

CPU code snapshot: **1a032d4fe0cfb6b2e17373c589d51bf61e456f02**, independent branch `codex/36-e3-cpu-admission` stacked on historical scene report PR35@5c959b54c0e7f3c1253b0754c895227341a7f2e0. Only e3/server_launcher.py and the new test change runtime/test code. PR35/PR30 and the old exact9599 checkout remain unchanged; this new code has no native permission.

## Actual verification, including failures

- Before fix: targeted7, actualexit1/NameError; after fix:7/7,actual0.
- Clean CPU snapshot local normal194/194 and -O194/194, actual0/0.
- First Corelab normal194 run: actualexit1, existing `test_receipt_does_not_mean_process_exit` CPU proxy did not become READY within its unchanged8s startup limit. The whole log/exit is permanently retained. This is CPU test infrastructure/startup, not a real Shadow/TEST failure. Exact scheduling cause remains unproven.
- After other E2 read-only checks finished, a bounded recheck used existing runtime thread caps OPENBLAS1/OMP2/MKL2/NUMBA2. Corelab normal194/194 and -O194/194 both actual0. No code, test deadlines or strict lifecycle errors were weakened; initial failure is not erased or attributed definitively to threading.
- E2 frozen full120 audit ordinary/-O actual0/0, full JSON equals original. All18070 originals rehashed unchanged, canonical manifest9e4ce4d233e1d2ff6fc3d2154a099cb1721d4f9140a01463ccb184851277d603. R014 original EOF/exit1 and R015 successful9/36 originals unchanged.
- Additional local CPU numeric helper re-derived all120 statuses,117 complete/3 unknown,60 pairs/57 complete, planned-denominator strata and conservative C2 G−B0 bounds from the fixed public ledger. It does not sign R3 or recompute/bootstrap-certify the original confidence envelopes.

Actual code/exit/log and whole/member backup source hashes are provided alongside this report. No public log includes private host/account/device UUID. Static pyflakes inspection also identified pre-existing unused-import/redefinition warnings; no broad lint cleanup was included.

## Freeze preparation without inventing approval

Scientific configs, all160 cells, splits, seed, k3, TaskSpec, Oracle,16/8/720/10settling, model identities and statistics stay byte-identical to PR35. The protocol lock remains PROPOSED_FOR_INDEPENDENT_FREEZE and formal admission remains closed. FREEZE_PREPARATION.json records one now-stale existing source-lock hash (the repaired launcher) and the new test that must be included when Gate C legitimately refreshes the lock **after** a signed Gate P decision. Leaving this visible is intentional; this CPU candidate is not a frozen runnable TEST release.

Next required decision: independent GPT Gate P on PR35's real9/36 evidence and112+48 proposal, plus same-priority E2 R3 on PR30. Only after Gate P can Codex apply the approved freeze/state/scene bindings, refresh all source hashes including new test, submit a NEW complete runtime Head and obtain a separately signed exact-Head E3_TEST_AUTHORIZED. Fresh GPU1 machine allocation must then bind that new Head/review and live UUID/EGL/memory/weights/storage; the owner's resource consent need not be asked again for the same granted scope unless it changes.

No same-type scene probe is useful or permitted: R014 and R015 are both consumed. No model/TEST/server despite currently available GPU1. First approved native A4/B6 checkpoints and future fixed IDs remain required. Do not self-sign, merge, replay historical errors, change scientific assumptions or submit the course.

E2 R3 and the E2-only15-slide/source fallback remain independent priorities. No new experiments11/06; deadline2026-11-06 23:59SGT. This report does not promise the planned experimental timetable has been achieved; the10/30 activation target is currently unmet because Gate P/C are pending. Any reduced variant requires an explicit pre-first-TEST owner/reviewer decision, not silent truncation.
