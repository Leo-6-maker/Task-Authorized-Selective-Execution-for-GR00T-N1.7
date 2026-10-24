# ISSUE12-INCIDENT-001 — STOPPED_BEFORE_MODEL_LOAD / TEST0

R006 authorizes exact code `3e2cb7ff0b98ac82564e0b7a60523a29cb4c8964` and requires a stop for a genuine program/system failure. The first approved server launch failed before model loading. **No TEST reservation was created; all120 planned cells remain unrun. No model request, simulator episode or CUDA initialization occurred.** This is a server-startup failure, not a failed TEST episode, a Gate semantic abort or evidence of TEST performance.

## Observed trigger and exact source

The frozen `scripts/e2_test_server.py` creates `runs/<server-session>` and writes `test_admission.json` there **before** launching `tase.server --output` with that same path. The unchanged native server starts with `a.output.mkdir(parents=True, exist_ok=False)` and therefore raises `FileExistsError`. This happens at line24 before `import torch` at line27. A fresh session name cannot solve the contract conflict because the launcher precreates every supplied session directory. [Exact source blobs/excerpts](incident-001/source_identity.json) bind the diagnosis.

Actual native child exit **1**; server launcher child exit **1**; the private operator records a failure and0 closed TEST units with120 remaining planned. Its outer OS process exit was not separately captured, so it is not assigned a fabricated actual exit code. The legal GPU check, fixed dual environments/packages,17 existing Object/Cosmos hashes, machine grant, six BDDL/init file hashes and30 selected official initialization array hashes passed first. The presence of `test_admission.json` proves preflight/admission completed; `loaded.json` is absent. Retain admission as a failed startup receipt, not as successful loading.

## Retention and accounting

The operator stopped and did not relaunch under a new session, change scientific/execution files, alter the grant, create a TEST ID, clean/delete the failed server directory, delete locks, redo CALIB, install or download. The separate report worktree is the only committed delta. Execution checkout remains clean at the exact R006 Head. The full frozen CPU TEST auditor was run after stop:120 planned units,0 reservations/outcomes, all120 unknown/unstarted, and no owned GPU compute task. Event-rate bounds are uninformative0–1; no TSR/UAR/effect estimate is claimed.

Original private stderr/start/exit/admission/allocation/operator records and the runtime map are backed up at two locations with archive/member hashes. Public copies remove concrete node, account and operator paths while retaining original SHA256, actual exit and stack location. Existing DEV19/CALIB48 and legacy raw remain untouched.

A separate **CPU synthetic** reproduction invokes the exact frozen `tase.server` against an already created output directory and a dummy permitted allocation, with no model present and CUDA hidden. Both normal and `-O` children actually exit1 with the same `FileExistsError` before the first torch import. These are expected-failure reproductions, not passing native TEST runs and not a replacement for the prior71-unit-test suite.

## Minimal repair proposal — not applied or executed

Preserve the native server's exclusive output-directory creation. Change only the TEST launcher's bookkeeping so it does not precreate that output directory: write the independent admission receipt to its new operator-session directory, launch the owned server with an absent output path, then publish the admission receipt exclusively to the output directory after that exact owned child creates it, with a bounded wait/child-exit check and symlink/ownership checks. The per-cell entry must continue requiring the same admission/grant before reservation and must not start until both admission and actual `loaded.json` exist. Preserve all startup failures and forbid reuse of an old output directory.

Add a meaningful CPU launcher→server output-ownership integration check (normal/`-O`) proving an initially absent output is created once by the server, the valid admission is published only for its owned child, missing/stale/foreign output/admission fails closed, and the existing71 tests continue to pass. Use fakes for model initialization, clearly labeled CPU; do not load another model or consume a TEST ID for this repair. Do not globally set `exist_ok=True`, delete the old directory, bypass the frozen launcher, pre-create fake `loaded.json`, reuse another server, or edit R006 grant to make a new Head appear authorized.

This changes executable code, so **R006 cannot authorize the repaired Head automatically**. Required next step: GPT incident assessment permits the bounded launcher/CPU repair; after its new exact Head is independently reviewed and explicitly authorized, resume with unopened `e2-test-0001` under the unchanged120-cell protocol. All original startup-failure receipts stay in the handoff. Until then, no further model/server/TEST launch.
