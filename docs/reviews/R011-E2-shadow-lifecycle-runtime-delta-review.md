# R011 — Independent E2 runtime engineering delta review

**Date:** 2026-10-24 SGT. **Reviewer:** GPT.  
**PR:** #21, exact final Head `76a6fb13e1b2a650163f583c7384b349d1e6979c`; actual CPU-tested commit `4d46e7550596263df35fa8cc1a5419b492e8a067`.  
**Decision:** `ENGINEERING_DELTA_ACCEPTED / TEST_AUTHORIZED_FOR_EXACT_HEAD_SUBJECT_TO_LIVE_PREFLIGHT`. This is permission to collect the remaining frozen simulation TEST, **not** R3 scientific approval, real-world safety assurance or confirmation of actual GPU startup.

## Independent source/evidence findings

1. All ten changed runtime/config/test Git blobs at the final PR Head match the CPU-tested commit exactly (10/10). Compared 15 immutable scientific/native/admission/TEST files with original R008 run Head `a1c6424bd348b36c55a20d38750a269e9551a698` (15/15 identical). Configuration semantic fields match; only frozen SHA bindings for `tase/shadow.py` and `tase/e2_context.py` changed. Independently recomputed SHA-256 of new config, both changed files and five unchanged essential manifests/locks: 8/8 matches; new config SHA256 `7468d82722143124dcf730e2ac2af0634124ce8347d073087726e0cba7d08004`.
2. Inspected cooperative Shadow close source, idempotent bounded finalizer-completion + actual zero-exit handshake, incomplete/error/TERM/KILL handling, read-only per-run historical provenance and the narrowly changed server signal shutdown. Predictor, Gate score, EventOracle, TaskSpec, controller, seeds, 120-cell manifest and statistical functions are unchanged. Future full Gate outcome additionally requires clean lifecycle receipt; old versions retain their originally audited evidence without fabricating these receipts.
3. Read operator ordinary and optimized CPU suite exit receipts on local and Corelab (118 cases, exit0 in both environments/modes). These were executed by Codex, **not independently rerun by GPT**. CPU fixtures exercise slow finalization, 10-second boundary, real child exit, backpressure, malformed receipts, force vs clean, negative grants and historical-version checks.
4. Independently compared all 120 rows and 19 shared fields of PR19's old TEST ledger against PR21's versioned ledger: **zero differences**. Exactly 14 prior consumed:12 SUCCESS and original `0010`/`0014` CLEANUP_ERROR/exit1/censored; 106 remain unopened, next `0015`. All14 old acquisition identities remain R008 under its original actual code Head. Codex's local/live original-archive audits and two-copy member hashes are operator receipts, not independent reviewer re-hashing of private originals.
5. PR22 is a separate preliminary editable 15-slide/course source draft; not R3-approved or submitted. TEST has not run under the repaired Shadow code.

## Runtime activation conditions

A separate machine-readable R011 grant on main binds this precise final source Head, `k=3`, the fixed 120 IDs, selected source/config hashes, and current source identity. Historical R008 remains suspended. Before starting any new server/model/simulator/TEST: fetch current main; verify the R011 grant, exact clean Head, current legal GPU/SSH/EGL/storage/2 backup copies, pinned models/assets, and LIVE read-only ledger exactly 14 reserved (0010/0014 original failures unchanged), `0015` absent and no leaked worker/server. Mismatch means STOP.

After a new genuine loaded/listening server, execute unopened `0015` (C2 B0) then `0016` (C2 G) once each and perform **mandatory full audit, clean lifecycle proof, paired parity and two-location backup before 0017**. If passed, remaining `0017`–`0120` may run autonomously in fixed order, with four-cell integrity checkpoints. Any unexpected worker/monitor/physical/state/resource/evidence fault stops real execution; consumed IDs cannot be retried or relabeled. Any further executable change requires a new independently reviewed grant.

All120 planned IDs remain in the final denominator, with explicit 2 prior operational failures and censored/missing bounds, 2000 task-stratified paired bootstrap repetitions and seed640500. Do not change weights, WBC, training, simulator, Gate, oracle, k, tasks, initialization, C0/C2, sample order or statistical protocol, or merge stacked PRs automatically. R3 independent result review remains required.

**Limits:** Direct review here covered GitHub source, fixed-identity/public evidence and submitted CPU receipts. It did not rerun private 1611-file originals, Corelab GPU/MuJoCo under the new version, or inspect the binary slide deck independently.
