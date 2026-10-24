# R007_FIX_HANDOFF — READY_FOR_R007_FIX_REVIEW

2026-10-24 (Asia/Singapore) · Issue #14 · Codex executor. **TEST_EXECUTION_SUSPENDED; no R008 grant, GPU/model/simulation/TEST launch or independent GPT approval is claimed.**

## Exact source and authority

- Parent is PR #13's live head `61e1b976924ee9b162a9a933d9b9a755934cce8f`, retaining the original R006 startup incident and prior120-unit planned ledger. New independent branch: `codex/14-r007-startup-fix`, stacked on `codex/12-e2-test-r3`. PR #11 and #13 are not rewritten or merged.
- R007/main read at `b24db4982790e862fe8d8ec71fbd3ebaec5a4e4c`: [signed incident/CPU repair decision](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/b24db4982790e862fe8d8ec71fbd3ebaec5a4e4c/docs/reviews/R007-TEST-server-startup-incident.md). No signed review file or grant was edited by the executor.
- **Final executable and CPU-tested code SHA: `a904e2678a3c511e36580a173e77b9c72521e093`.** The subsequent delivery commit contains only documentation/evidence. Full delivery SHA is recorded in PR/Issue #14; a commit cannot contain its own final SHA. Verify no implementation/config delta after the tested SHA using `git diff a904e267..HEAD -- scripts tase tests configs`.
- Current main R006 disposition is `TEST_SUSPENDED_AFTER_INCIDENT`. The historical grant at `6c5d6c69e9abecf66999eab318b6d8c8a1b676a6` remains intact in Git, but a CPU negative probe on the clean original exact execution Head, after fetching main, raises `TEST grant changed on main`. [Actual negative probe](checks/R006-negative-probe.json). This probe did not launch a server or query a GPU.

## Bounded implementation

Only two implementation/test paths differ from PR #11 science: `scripts/e2_test_server.py` and new `tests/test_e2_server_startup.py`. **All `tase/` files (including native server), all configs, original71 tests, policy/processor/model identities, TaskSpec, contact Gate, oracle, k3, C0/C2, split,120 cells, seeds and native16/8/720 remain byte-identical.** Existing `record_process.py` is unchanged. No other research checkout, environment, model cache, old lock/result or old session was modified.

1. The launcher stages the original admission exclusively in its new owner-controlled `operator/<session>/`. It checks native output and old start/exit/session records are absent, refuses symlinks/foreign ownership, verifies the E2 runs alias where present, and leaves `runs/<session>` absent at `Popen`. The **unchanged native child alone** performs its original `mkdir(parents=True, exist_ok=False)`.
2. The same `record_process` wrapper records the exact native command, PID and actual exit. Before publication, the launcher verifies its direct wrapper PID, the recorded native PID/command/output argument, and real Linux `/proc` owner/parent/argv/start ticks/liveness. It waits boundedly (180s default) for actual output creation. No global `exist_ok=True`, directory deletion, old-session reuse, fake loaded record or alternate launch path was introduced.
3. Publication copies exact staged bytes to an exclusive retained source file inside the verified child output and atomically hard-links that file to `test_admission.json` without overwrite. This works when operator and runs are different filesystems; both link endpoints are inside the output directory. An owned non-symlink directory FD, device/inode equality and staged SHA256 bind publication. Existing admission and changed output/staging/process identity fail closed. The retained publish-source is evidence; no cleanup removes it.
4. The launcher records publication separately from readiness, rechecks liveness/output identity/admission integrity, and waits for the real owned `loaded.json` with correct loopback/port before writing operator `server_ready.json`. Admission **does not mean** model loaded. Partial buffered JSON writes are never accepted, and waiting remains bounded. After a future R008, the operator must wait for readiness **and** real loaded/liveness; the unchanged per-cell entry continues to validate grant/admission/loaded before reservation.
5. Startup failure or TERM/INT returns nonzero and closes only the owned new session/process group, boundedly even for signal-ignoring children. Original child/launcher receipts, forced cleanup and missing child exits are retained honestly. A forced kill may prevent `record_process` from recording a native child exit; this remains **missing/unknown**, not a fabricated code. Original failed `test-server-r006-01` is never removed or reused.

Process/path checks enforce this project's owner/account workflow, not cryptographic protection against arbitrary hostile code running as the same UID. Linux `/proc`, directory no-follow and hard-link semantics are explicit implementation dependencies. Real shared filesystem/native-model startup has **not** been exercised under this repair; only CPU proxy tests are authorized here.

## Actual CPU tests and exits

[All suite receipts](cpu_receipts.json) · [public CPU origin hashes](cpu_origin_manifest.json) · [final ordinary log](cpu/a904e267/normal/stderr.redacted.txt) · [final optimized log](cpu/a904e267/optimized/stderr.redacted.txt).

Existing Python3.12.14/NumPy1.26.4 environment; no install. Commands use `CUDA_VISIBLE_DEVICES=-1`, `PYTHONNOUSERSITE=1`, `OPENBLAS_NUM_THREADS=1`. `TASE_CPU_STARTUP_EVIDENCE=<PRIVATE_CASE_ROOT>` preserves CPU proxy files instead of discarding temporary fixtures. Suites are wrapped in the unchanged `record_process`, retaining actual start/PID/exit.

| Actual command at final exact code SHA | Observed count | Actual suite child / wrapper exit |
|---|---:|---:|
| `<CPU_PYTHON> -m unittest discover -s tests -v` | **89/89** | **0 / 0** |
| `<CPU_PYTHON> -O -m unittest discover -s tests -v` | **89/89** | **0 / 0** |

The prior71 tests are unchanged, plus18 new startup integration methods. New tests spawn actual **CPU proxy** processes and native-style exclusive mkdir/receipts; no model, torch, CUDA, MuJoCo, policy inference or native TEST is run. Their synthetic `loaded.json` is labeled `SYNTHETIC_CPU_PROXY_NOT_MODEL`, confined to private CPU fixture roots; it is never placed in the real E2 workspace or used as a runtime approval.

Coverage includes absent→child exclusive mkdir→atomic identical admission; child exits7 before mkdir; child mkdir then exits8 before load; preexisting/broken-symlink/foreign owner; live PID/parent/command/output mismatch; output replacement; staged-byte change; duplicate admission and duplicate session retention; partial/bad native loaded receipt; different filesystems; no-mkdir/no-loaded timeout; actual TERM/INT forwarding; and signal-ignoring owned-child cleanup. Foreign UID is injected in the CPU stat check, with no actual `chown` or elevated access.

Final preserved case directories:24 per mode, including preflight rejections and subcases. Actual child receipts **where present** record0,7,8,143(TERM),130(INT); these expected negative outcomes remain visible. Ignored-signal cleanup has wrapper returncode−9 and no child-exit receipt; one ordinary command-mismatch cleanup also lacked a final child receipt, recorded as missing. No missing case is silently assigned a success/exit. See `case_records` and corresponding `supervisor_exit.json` / `*.exit*.json` in the public CPU tree.

Earlier fixed-source whole-suite passes at `08c6e8dd00e2b597c152ab03aa922323c40d8a6d` (86 each) and `47f58b054f488284b7fb16c9744c15e70e2fa6ba` (88 each) are retained as nonfinal evidence. Initial uncommitted13-method development pass is labeled exploratory. All actual suite exits were0; negative proxy process exits are expected test inputs, not hidden suite failures. A report-export helper encountered intentionally corrupt negative-fixture JSON (shell1), then an already-created report folder (shell1); both are disclosed in [helper receipt](checks/export-development-failure.json). Only the report helper was corrected to retain invalid source text/hash and resume generated derivatives; runtime/test source remained unchanged.

## Zero TEST and incident preservation — freshness limits

**This task made0 real GPU/server/model/simulator/TEST launches and consumed0 TEST units.** CPU proxy roots assert the dedicated TEST root remains absent. Existing synthetic budget tests in the prior71 operate only on temporary fixtures and do not consume real reservations. No R006 restart or new grant was used.

The latest independently inspectable **retained remote state** remains the prior incident's TEST0/120, all120 NOT_STARTED, DEV19/CALIB48/candidates488. Its original frozen read-only auditor exited0. [Preserved prior state](../TEST/execution_state.json), [120 planned ledger](../TEST/planned_120_ledger.csv), and [prior archive recheck](checks/prior-incident-recheck.json) are unchanged.

**Current Corelab SSH is unavailable.** A fresh read-only fetch/audit request never reached the remote because the configured SSH connection timed out; subsequent bounded connectivity checks also exited255. No model/GPU/runtime operation was requested in those checks. [Connectivity receipts](checks/ssh-attempt-02.json), [third check](checks/ssh-attempt-03.json). Therefore the new live remote ledger, process state and remote old-file hashes are **NOT_VERIFIED_THIS_ROUND**, not asserted current from old receipts. Restore ordinary authorized connectivity and re-run the original read-only audit before any future runtime. No credential, network-security or host-key setting was changed.

To keep a reproducible CPU check despite that outage, the unchanged TEST auditor was run normal/`-O` against an explicitly reconstructed read-only view of the verified retained TEST0 snapshot: both actual children/wrappers exit0, planned120/reserved0/outcomes0/UNOPENED. [Snapshot binding](readonly-snapshot/source-binding.json), [ordinary audit summary](readonly-snapshot/normal-audit.summary.json), [optimized](readonly-snapshot/optimized-audit.summary.json). This **is not a fresh remote audit** and does not invent current remote absence. No meaningful TEST TSR/UAR/effect estimate follows from0 outcomes.

## Backups / privacy / unverified scope

[Backup verification](backup_verification.json): existing original incident archive SHA256 `da962b24213b4472b799f20b6a90a2e7f120ccd3795cb9adf591563033e8ffac`,34 members, had two authorized verified locations previously; all34 member hashes were rechecked locally in this task. Historical failure receipt/dir identities are retained unchanged. Fresh remote byte verification is pending SSH access.

New private CPU original archive is fully hashed and every member locally verified; its exact bytes/member count/SHA are in the same receipt. It retains raw suite/proxy logs, process receipts and exploratory versions. **The new private archive remote copy was not performed because SSH is unavailable; two-copy completion is not claimed.** Current public redacted evidence is delivered in Git with separate original/public SHA256; no private runtime path, full environment, credentials, models, unsafe pickle or original operator implementation is committed.

[Scientific diff/privacy checks](delivery_checks.json) enumerate unchanged native/scientific sources and known-marker scan. [Canonical artifact manifest](artifact_manifest.json) binds the public delta bytes. Old signed reviews/records are never overwritten; earlier disclosed noncredential local paths in parent Git history are not rewritten. This is executor CPU evidence, not independently reviewed native runtime validation.

## One next action

**GPT reviews this exact new delivery Head and bounded launcher/CPU diff (`READY_FOR_R007_FIX_REVIEW`).** No future grant is pre-signed; R006 remains suspended. A new exact-head R008 is required before a fresh server or TEST session. Ordinary SSH access, current read-only TEST0/old-record checks and missing backup verification must be restored before runtime admission. Do not use the old grant, bypass launcher checks, alter the120-cell/k3/TaskSpec/oracle/split/seed/native contract, train, attach WBC, use hardware or auto-merge.
