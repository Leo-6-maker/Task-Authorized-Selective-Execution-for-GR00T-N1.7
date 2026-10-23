# R2_DELTA_HANDOFF — READY_FOR_R2_DELTA_REVIEW

2026-10-24 (Asia/Singapore) · Issue #10 · Codex executor. **TEST NOT_AUTHORIZED; no independent GPT approval is claimed.**

## Exact lineage and review boundary

- Live PR #9 base at takeover: `main / 069d5ce2972747f6ca01d6c7b0e2585660954d45`; head `codex/8-e2-gate / fc38e816ff3e75e87c29da3aa18009dcc0542f02`. This delta's independent `codex/10-test-freeze` branch starts from that exact head and targets `codex/8-e2-gate`, not a rewritten main implementation. Parent PR remains draft/open and unmerged.
- Main review read at `e00f40cea298ce67159007d619dbf5e2747cb178`: [R005](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/e00f40cea298ce67159007d619dbf5e2747cb178/docs/reviews/R005-R2-E2-conditional-freeze.md), blob `ec2f8f3ad1518daddfc75ffb1a46b61dfdab3cb6`; [independent_checks](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/e00f40cea298ce67159007d619dbf5e2747cb178/reports/reviewer/R005/independent_checks.json), blob `31c48910567e58576a1004fbfccfceeaf4646cf9`. Disposition remains `CONDITIONAL_SCIENTIFIC_FREEZE__TEST_NOT_AUTHORIZED`, bound to parent head only.
- **New executable/code head and final CPU source: `94c1f1acdf0370039a39ed780ebed1295f34a757`.** Later delivery commits contain evidence/docs/manifests, not new runtime code. The enclosing delivery head's full SHA is recorded in the PR and Issue #10 executor checkpoint; embedding a commit's own SHA in its own bytes would be self-referential. Compare `git diff 94c1f1a..HEAD -- tase scripts tests configs` to verify no later implementation/config changes.
- CALIB CPU export/preflight code: `cb4e10a8e240c9fd80e0cf1176fcf47e18a7b83a`; the exporter/auditor/runtime-preflight sources remain unchanged at the executable head. Sampling plan was committed before export at `9611114d70f26bd123a51fb5c5f36ab10dbf4c17`. Actual CALIB-G execution remains historical `03653db11bfb0f570b5e3e6ab78b1a37ef2c9b57`, with no rerun.

## Code delta (IMPLEMENTED + CPU_TESTED; not TEST runtime-validated)

[TEST entry contract](../../docs/work_packages/E2-TEST-ENTRY.md) specifies the independent main-committed GPT grant. Admission binds exact clean code head, runtime/config/split/selection/catalog SHA256 and exact120 ordered IDs. Missing/stale/conditional/local-file permissions fail before model/GPU operations. No grant is included and the existing proposal's false authorization fields stay false.

`test_authorization`, `test_ledger`, `test_execution`, `test_context` and `test_runtime` add separate TEST admission, append-only counting, stop lifecycle, prediction-envelope validation and CPU pinned-resource verification. `e2_test_server.py` is a future grant-guarded offline server launcher; `e2_run_test.py` admits one next frozen cell and reserves before native imports/requests. It records the actual native child through existing `record_process`, forwards owned-child signals, retains startup/timeout/error failures and never retries an ID. Empty/partial reservations still consume a planned cell and block silent continuation. Operator reconciliation closes an interrupted original ID without replacing it or inventing an exit.

The existing epoch runner shares its unchanged native control loop; only the TEST branch/admission/envelope/lifecycle/timing instrumentation is added. DEV/CALIB setup retains its prior behavior. `gate_features.py`, `event_oracle.py`, `task_spec.py`, `e2_context.py`, native source/model/processor identities, k3 selection, C0/C2, split, exact120 cells/scenario/seeds and protocol lock remain byte-identical to parent. The native raw16 / prefix<=8 /720-cap /10-settling contract remains fixed. REJECT/ERROR return without new main execution; after stop, no next prediction/control is admitted. Oracle/fault labels do not enter the contact Gate.

`e2_audit_test.py` reuses the CPU JSON/NPZ/byte auditor, reconciles all120 planned units and checks actual cell/init/task/instruction/grant/process identities and paired actions/state/RNG/controller prefixes. It reports task×condition×system wrong lift, official/compliant success, semantic abort, monitor/system errors, timeout, coverage and measured inference/monitor costs. Missing/censored units remain in planned denominators with bounds; arm and paired-difference percentile95% intervals use task-stratified init-cluster bootstrap2000/seed640500 with both conditions/arms retained together. No TEST outcomes were used to choose these rules. Candidate UAR remains N/A without audited first-event candidate coverage, never fabricated from zero events or early abort.

## Existing-original CPU export (DELIVERED; independent reviewer read still pending)

[Safe package entry](R2_delta/README.md) · [488 CSV rows](R2_delta/calib/candidate_decisions.csv) · [typed JSON](R2_delta/calib/candidate_decisions.json) · [origin/derivative manifest](R2_delta/calib/manifest.json) · [predeclared sample](R2_delta/calib/sampling_plan.json).

All488 candidate rows include first actual major onset/window, k1/2/3 decisions, source/candidate code and artifact/snapshot/action hashes and prediction counts. The frozen rule recomputes4 first-event positives,286 C0 local negatives,0 first-event accepts and0 C0 local rejects for each k, then selects k3 by the existing tie rule. No new model request or shadow prediction was made.

Eight fixed B0/G pairs (16 full episodes) include all four positive B0 IDs0010/0012/0014/0016 and C0 controls0001/0005/0009/0017. Export includes complete actual frames/contacts/unchanged oracle labels, raw16 actions, complete finite controller/state NPZ, all G predictions,187 selected-source candidate numeric inputs, TaskSpec vs actual language, guards/snapshot digests and actual child/worker exits. The C0 timeout and all four positive B0 timeouts remain visible. Four G runs abort at56 with zero rejected-candidate main execution; B0 onsets62/148/61/61 match the exact previously published five-frame snippets.

Public derivative:1441 files /41,461,644 bytes plus manifest. Manifest SHA256 `6c21c57a3196d08f1f7872736399c2b85e4f4499ddfb291cc0937d750354bdc8`; archive7,271,801 bytes SHA256 `4defac23a1f828b359c660d142a6d63def3b5099fec1f139d7dd1ee82f0e95c4`. All4944 source hashes match the12675-entry existing raw backup source index. Unsafe pickle bytes are only hashed; no pickle deserialization or publishing, weights, XML, full videos or private operator logs. Public files are actually in this PR, not local-path promises.

## Actual CPU commands / exits (including failures)

[All22 recorded CPU invocations and logs](R2_delta/cpu/test_receipts.json) retain development passes and failures. Final exact-source commands used existing Python3.12.14/NumPy1.26.4 with `CUDA_VISIBLE_DEVICES=-1`, `PYTHONNOUSERSITE=1`, `OPENBLAS_NUM_THREADS=1`:

| Command (private interpreter/output paths replaced) | Source SHA | Actual exit |
|---|---|---|
| `<CPU_PYTHON> -m unittest discover -s tests -v` | `94c1f1acdf0370039a39ed780ebed1295f34a757` | **0,71/71 synthetic** |
| `<CPU_PYTHON> -O -m unittest discover -s tests -v` | same | **0,71/71 synthetic** |
| `<CPU_PYTHON> scripts/e2_audit_calib_delta.py --package reports/E2/R2_delta/calib --repo . --output <NEW_JSON>` | same | **0** |
| same public package audit with `-O` | same | **0** |
| CPU original export via `record_process`, `e2_export_calib_delta.py --workspace <WORKSPACE> --repo <EXPORT_REPO> --output <NEW_PACKAGE>` | `cb4e10a8e240c9fd80e0cf1176fcf47e18a7b83a` | **0 actual child/controller** |
| CPU `test_runtime.verify` (source/environment/model byte checks only) | same | **0 actual child** |
| CPU `e2_audit_test.py --workspace <WORKSPACE> --repo <TEST_REPO> --output <NEW_JSON>` | `94c1f1acdf0370039a39ed780ebed1295f34a757` | **0 actual child; ledger unopened** |

[Actual remote start/exit receipts](R2_delta/remote_cpu_receipts.json) bind redacted command templates and original receipt SHA256. [Ordinary public numeric audit](R2_delta/normal-public-calib-audit.json) and [-O](R2_delta/optimized-public-calib-audit.json) independently load this small public package, replay all selected actual oracle sequences and verify paired actions/states/snapshot digests, Gate scores, original snippet equality and real exits. This is executor CPU verification, not independent GPT review or a physics rerun.

Retained development failure: `e9de31eb8128bf072b77c03f34b2dbdd4a626083` normal and `-O` each exit1, because the new synthetic signal-forwarding case exposed a missing operator-log parent directory. One-line `mkdir(parents=True)` fix at94c1f1a; final71/71 both0. Original private failure logs and their hashes remain, public copies are redacted **before publication**. First exploratory14-test invocation showed OK and shell0 but did not separately capture unittest child status; it is explicitly nonfinal, not assigned a fabricated child exit. A metadata capture initially raced an unfinished zero-audit receipt (helper shell1), then succeeded after the actual child exit; no experiment was launched/replaced.

## Runtime / ledger / backup / privacy

[Zero TEST state](R2_delta/zero_runtime_state.json) and [full unopened TEST audit](R2_delta/zero_test_audit.json): **TEST0 reservations,0 outcomes,0 new TEST model calls; TEST directory absent**. DEV19, CALIB48, candidates488 are unchanged, and no owned native/model/download process remains. The original Corelab course checkout is still clean at parentfc38; CPU export and final audit used separate new worktrees. Other research checkouts, locks, old records and oldM1/M2 budgets were not modified or reconstructed.

[Existing-resource CPU preflight](R2_delta/pinned_runtime_cpu_preflight.json) verifies the fixed native source, Python3.12.14 dual environments (server138/sim159 required package versions) and all17 existing Object/Cosmos file byte hashes. **0 model loads,0 CUDA initialization,0 simulation,0 downloads or installs.** This is identity verification, not new rollout acceptance.

[Backup verification](R2_delta/backup_verification.json): derivative archive and every exported member verified at remote/local locations;4944 original source hashes match the already verified raw chain ending `calib-final-09` SHA256 `69b1403787d2fe74b6c2891bc7d8dc11a70606248d77aa0a26d3d0667ff352f3`. Additional private metadata archive retains original CPU logs (including failed tests), actual receipts and private runtime map at two locations with member hashes. No old backup/result was overwritten. Private concrete runtime paths/UID/GID/node remain outside Git.

[Delta canonical public manifest](R2_delta/artifact_manifest.json) covers changed public code/config/docs and evidence with Git blob and SHA256; [privacy/unchanged-freeze check](R2_delta/delivery_checks.json) records current-byte checks. The old parent public manifest remains historical, not falsely presented as covering this delta. Earlier noncredential paths in parent Git history remain disclosed in the parent packet; no history rewrite/force push was performed.

## Remaining unverified and one next step

TEST software is CPU-tested, **not native TEST runtime-validated**; actual TEST server/120 cells were never started. Full private raw/pickle/video bytes, independent physics replay and all24 CALIB raw pairs are still not claimed independently reviewed by GPT. The public sample supplies8 complete pairs and187 full candidate numeric inputs; the488-row table covers the fixed whole library but does not publish every excluded original. C2 remains a controlled instruction mismatch, positives are from one task, CALIB selects/evaluates on the same data, and no20Hz wall-time guarantee or general safety claim is made. Legacy M1/M2 remains NOT_INDEPENDENTLY_VERIFIED.

**Only next action: independent GPT delta-review of this exact published head, TEST entry/ledger/audit/CPU negatives and accessible CALIB subset.** GPT must issue a separate exact-head `TEST_AUTHORIZED` decision and scoped grant before any120 TEST execution. Codex supplies no grant, does not flip the lock, merge PRs, tune/test, train, attach WBC or operate hardware.
