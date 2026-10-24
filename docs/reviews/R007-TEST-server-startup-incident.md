# R007 — TEST Server Startup Incident Review / Scoped Repair Authorization

- **Date:** 2026-10-24 (Asia/Singapore)
- **Reviewer:** GPT
- **Incident PR:** [#13](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/13)
- **Reviewed incident HEAD:** `61e1b976924ee9b162a9a933d9b9a755934cce8f`
- **Original R006 TEST execution HEAD:** `3e2cb7ff0b98ac82564e0b7a60523a29cb4c8964`
- **R006 grant commit:** `6c5d6c69e9abecf66999eab318b6d8c8a1b676a6`
- **Incident:** `ISSUE12-INCIDENT-001`
- **Decision:** **`INCIDENT_CONFIRMED / SCOPED_CPU_REPAIR_AUTHORIZED / TEST_EXECUTION_SUSPENDED`**.
- **Next:** Codex submits tested minimal launcher fix under *new* exact code SHA. GPT separately reviews and, only upon passing, issues new explicit TEST grant bound to that SHA. **NO model/server/simulator/TEST launch is authorized by R007.**

## 1. Reviewer scope and independently supported facts

Read PR #13 metadata/changed-file list, incident report and R3 handoff, exact frozen `scripts/e2_test_server.py`, `tase/server.py`, `scripts/record_process.py`, `tase/evidence.py`, `scripts/e2_run_test.py`, native/server/launcher exit receipts, actual redacted stderr, CPU reproduction metadata, post-stop TEST ledger/audit and two-location backup receipt.

1. **Deterministic root cause:** the TEST launcher calls `folder=workspace/'runs'/session; folder.mkdir()` and writes `folder/test_admission.json`, then invokes the unmodified native `tase.server --output <same folder>`. That server performs `a.output.mkdir(parents=True, exist_ok=False)` **before** importing `torch`. Thus the same launcher always precreates the directory the child requires absent. Changing the session name or repeating the old Head cannot resolve this contract conflict.
2. **Actual failure receipts:** native child recorded exit1; launcher wrapper recorded exit1. Redacted original stderr shows `FileExistsError: [Errno 17] File exists` in the exclusive native mkdir at server line24. No `loaded.json`. The operator's outer OS exit was **not separately captured**; do not infer it.
3. **TEST accounting:** independent parsing of PR #13's published planned CSV gives exactly120 planned rows (plus header), first `e2-test-0001`, last `e2-test-0120`, each `reserved=False`, `outcome_known=False`, `NOT_STARTED`, zero physical controls/model calls. Published CPU read-only audit returns `UNOPENED`, `reserved=0`, `full_outcomes=0`; no TEST reservation directory exists per executor state receipt. Zero observed outcomes means no TEST effect estimate/TSR/UAR. This is a **startup infrastructure incident**, not the first failed TEST cell.
4. **Scope preservation:** compare fixed `3e2cb7ff...` → incident PR head yields two report-only commits,48 changed paths, **zero modifications** under `tase/`, `scripts/`, `configs/`, `tests/`. No k/TaskSpec/oracle/model/test-catalog change; DEV19, CALIB48, candidates488 unchanged in submitted evidence.
5. **Reproduction & retention:** Codex recorded expected CPU normal/-O reproductions each exit1 before torch, without GPU/model; reviewer corroborated deterministic failure by source, **not** by independently rerunning those remote children. Operator reports current source/model/resource checks and two-location 34-file archive with SHA256, but full private archive bytes were **not** read by reviewer.

**Conclusion:** R006 required the executor to stop on an unexpected system/program error; the decision to stop and retain the failed session was correct. Model download/retraining/CALIB redo would not address this error. 120 TEST cells are all still eligible *after a new safe launcher and a newly bound GPT grant*.

## 2. Machine-enforced R006 suspension

R006's published grant is still committed as a historical record at its original SHA. **Its then-current authorized code is not permitted to restart following the known deterministic failure.** To enforce this in the existing code's `authorize()` rather than trusting prose, GPT changes the *current main version* of `docs/reviews/R006-E2-TEST-AUTHORIZED.json` to a suspension record, while preserving the old authorized JSON unchanged at its original commit.

Existing `authorize()` requires the grant at `review_commit:path` to exactly match the same file at fetched `refs/remotes/origin/main:path`. A changed current-main suspension file **invalidates an attempt to reuse the old R006 commit**, and using the new suspended version fails `disposition=='TEST_AUTHORIZED'`. A stale `origin/main` can still be stale; operators must explicitly fetch main and follow R007 instructions, and this workflow is not a cryptographic proof of independent roles.

## 3. Authorized fix, with narrow technical contract

**Permit CPU-only changes** to the TEST launcher/output-directory ownership handshake, plus its synthetic tests and supporting documentation. *Do not change the native model server's exclusive output mkdir, GR00T, upstream source, test policy, event oracle, contact Gate, action conversion, frozen 120-cell catalog, k3, C0/C2, split/seeds, 16/8/720, R006/R005 science, or historical receipts.*

Acceptance design:
1. Stage the launcher-owned `test_admission.json` (with exact grant/port/GPU UUID/allocation hash) exclusively under the already owner-controlled `workspace/operator/<new-session>/` before child startup. Native `runs/<new-session>` output directory must **not exist** at `Popen`. Refuse preexisting/foreign/symlink output; never remove or reuse the original failed session.
2. Start only the launcher-owned `record_process` wrapper and native server with the same absent output path. The native child retains sole authority for `mkdir(...,exist_ok=False)`.
3. Use a **bounded** wait for the exact owned child to create that directory; check it is a real directory, no symlink, belongs to expected project owner, and that the matching original process start receipt is present (PID/command/output-path identity); fail closed on early exit/timeout, without fabricating model load or requests.
4. Publish an immutable/exclusive (`write_json` / mode `x`) identical `test_admission.json` into the now child-created output directory **without overwriting an existing file**. Check child liveness/identity around publication; record in operator receipts precisely when publication succeeded. An admission by itself **does not mean model loaded**; per-cell entry continues to require the exact grant, a real `loaded.json`, a live owned server/no server exit receipt, correct loopback/port and resource identity.
5. Preserve original `server-session` start/exit plus native child and launcher exits, including early failures, unexpected signals and malformed output. Maintain nonzero failure exit, no auto retry, no deletion, no stub `loaded.json`; stage anything for debugging under a **new unique session** only after a newly signed grant.
6. Add regression cases in both ordinary and `python -O` CPU mode demonstrating (a) normal output creation exactly once by a child proxy and admission publication afterward, (b) child exits before directory exists, (c) preexisting/symlink/foreign/mismatched output refused, (d) child dies before load, (e) duplicate admission refused and original records retained, (f) signal forwarding/cleanup and no TEST reservations/model operations. A CPU child proxy must be honestly labeled as such, not a genuine GPU model start.
7. Re-run all existing TEST/whole-suite CPU tests (at least previous71) in both modes and retain start/exit/log receipts; preserve all failures, including this incident and any development test failures.
8. Report latest source HEAD, changed paths, source hash/provenance, no science changes, no TEST/model/CALIB run, new private+public evidence receipts and backup hashes. New PR tagged `READY_FOR_R007_FIX_REVIEW`.

**Important:** a fix like `exist_ok=True` in native server, blindly deleting/replacing directories, staging fake `loaded.json`, writing grant JSON into a local file to trick runtime, or restarting the old R006 code/grant **is not approved**. The identity/ownership checks and append-only semantics are necessary.

## 4. After Codex submits the tested fix

GPT will inspect the exact new Head (primarily launcher diff, tests and true CPU receipts); run/reproduce focused source-level cases where possible; confirm no changes to frozen scientific files; verify R006 suspension and new grant mechanism and that TEST is still0/120; then **separately publish R008 `TEST_AUTHORIZED`** (if passed) with new exact Head and frozen hashes on main. No future grant is pre-signed by this decision.

Only after that grant is confirmed on fetched main and existing legal GPU allocation and saved evidence checks remain valid may Codex start a **new server session** and the still-unopened `e2-test-0001` through `e2-test-0120`. The failed prior server startup remains an infra incident and is **not** a TEST attempt. Any new defect/failed model start triggers the same stop and evidence workflow.

## Review limitations

This is a source, published receipts and protocol review; GPT did not log into Corelab, access private originals or run a GPU/MuJoCo process, and did not independently regenerate the entire frozen grant/remote archive. It authorizes a bounded repair, not a successful native startup, model readiness or final TEST statistical finding.
