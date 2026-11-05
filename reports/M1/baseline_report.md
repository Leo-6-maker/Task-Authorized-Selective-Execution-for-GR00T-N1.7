# M0/M1 baseline handoff

- Author role: Codex executor.
- Protocol: TASE-001 v1.0; branch: `codex/2-native-baseline`; issue: #2.
- Status: **READY_FOR_REVIEW — INCOMPLETE / GATED_BACKBONE_ACCESS_BLOCKED**.
- Starting main: `2edd62f8b3bb06784dac7bf4fa47f5d07d4bff4f`.
- Captured runtime commit: `64ade726bb264b1557c9827273cc1941acd16ee5`; individual run commits are preserved in [dev_runs.csv](dev_runs.csv).
- Runtime lock: [configs/runtime_lock.json](../../configs/runtime_lock.json), SHA-256 `9783e72f673626aba84c2ac63bf40db4247e6cad98ec73e1a21215c0dd80fcb2`.
- Date: 2026-10-21, Asia/Singapore. Final executable reports reference exact run times; PR head is the review object and is stated in the issue/PR handoff.

## Result and denominators

**No model forward or complete policy episode succeeded or was executed.** Object inference files downloaded and verified, but real model construction failed when accessing the gated Cosmos backbone. This is an access/infrastructure blocker, not a policy failure or evidence of unsafe behavior.

Five DEV environment attempts consumed five of the 24 authorized development slots. Four probes passed and one failed. These are real reset/initialization/rendering checks, not five policy episodes and not a policy success rate. TSR is **N/A** (zero eligible complete policy episodes).

| Run | Task / DEV init | Outcome | Exit | Policy calls / steps | Settling steps | Wall seconds |
|---|---|---|---:|---|---:|---:|
| dev-env-001 | alphabet soup / 0 | Restricted initialization-load error | 1 | 0 / 0 | 0 | 7.486 |
| dev-env-002 | alphabet soup / 0 | Environment probe passed | 0 | 0 / 0 | 10 | 9.949 |
| dev-env-003 | alphabet soup / 0 | Repeat environment probe passed | 0 | 0 / 0 | 10 | 6.026 |
| dev-env-004 | cream cheese / 0 | Environment probe passed | 0 | 0 / 0 | 10 | 5.551 |
| dev-env-005 | ketchup / 0 | Environment probe passed | 0 | 0 / 0 | 10 | 5.571 |

All successes, failures and incomplete checks are in [dev_runs.csv](dev_runs.csv), [evidence/checks.json](evidence/checks.json) and [M0 operation receipts](../M0/operations.json). The six initial full-policy DEV cells (three tasks × initialization indices 0/1) remain [NOT_RUN](planned_policy_cells.csv); no failure row was replaced by a successful retry. The failed row remains in the budget.

## Acceptance checks

| R1 evidence requirement | Actual result |
|---|---|
| Isolated source/env/config; reviewed deletion paths | PASS; see M0 |
| Object weight identities and hashes | PASS for download; model construction BLOCKED |
| Real dual cameras and native state/controller | PASS for reset/settling |
| Fixed initialization identity | Tested repeat match for alphabet soup init 0 only |
| Real model/server/client inference | BLOCKED, gated Cosmos HTTP 401 |
| Actual output horizon and exactly-once execution conversion | NOT_VERIFIED; source helper audit is not sufficient |
| Full native policy episode | NOT_RUN |
| Two tasks repeatedly successful on multiple DEV initializations | NOT_RUN / acceptance criterion not met |
| Baseline parity of thin single-environment reset adapter | NOT_VERIFIED |
| All failures and raw artifacts retained | PASS within recorded evidence; first server child exit status was not captured and is explicitly disclosed |

**M1 does not meet the baseline qualification standard.** Do not interpret READY_FOR_REVIEW as READY_FOR_M2 or a GPT approval.

## Actual reproducible operations

Environment invocations below used the configured isolated HOME, LIBERO config, cache, device selection and disabled tracking from [runtime_env.sh](../../scripts/runtime_env.sh). Each command's exact code/config SHA is in its run reservation/result, and its private stdout/stderr and snapshots are manifest-bound.

```bash
# Native environment probe (real simulator; no policy request)
"$SIM_PY" -u -m tase.baseline --workspace "$WORKSPACE" \
  --run-id dev-env-003 --task alphabet_soup --init-index 0 \
  --allocation-record "$WORKSPACE/runs/gpu-authorization.json" --probe-only

# The real server command was attempted; its model load was blocked by HTTP 401.
"$SERVER_PY" -u -m tase.server --model "$WORKSPACE/checkpoints/libero_object" \
  --output "$WORKSPACE/runs/server-01" \
  --allocation-record "$WORKSPACE/runs/gpu-authorization.json"
```

Probe run 001 exited 1; probes 002–005 exited 0. The original background server launcher exited 0 but **does not prove server success**; uncaught gated-access error is retained, and child exit status is NOT_CAPTURED. Future server invocation should be foreground/recorded before any episode. No repeated credential guessing or fallback model was attempted.

## Cost and interpretation

- Server installation: 388.11 s; simulator installation: 685.39 s; model-download operator: 509.42 s. Some operations overlapped, so they must not be added as total elapsed time.
- Successful environment probes: 5.55–9.95 s each including startup and ten settling steps. This is not a policy-episode timing estimate.
- Model inference latency, loaded-model peak VRAM and complete episode cost: **N/A / NOT_MEASURED**.
- No model-forward peak can be inferred from total shared-GPU usage. Other workloads were present; no process was stopped or driver/security setting changed.
- Logical workspace size including retained installer caches: 32,894,533,233 bytes. Public repository contains no model weights, recordings or assets.

## Artifacts and access

[artifact_manifest.json](artifact_manifest.json) binds public evidence plus private raw files by relative ID, bytes and SHA-256. Raw PNGs, native XML/state, installation logs, server traceback, command receipts and exact operator script bytes remain in the task-owned authorized storage and local private evidence copies. No internal absolute path or credential is published.

An independent reviewer without access to private artifacts must mark raw contents NOT_VERIFIED rather than treating a hash alone as proof. The public records support the limited summary but do not substitute for inspecting the retained raw evidence.

## Requested R1 decision

Review this incomplete M0/M1 package and require targeted continuation after owner-side Cosmos model access/authentication. Verify the auxiliary model revision and runtime compatibility, then perform server/client smoke and native baseline qualification within the **19 remaining** DEV slots. Do not reset the ledger. Revisit runner parity and actual action tracing before accepting full episodes.

No request is made here to enter M2–M3, CALIB or TEST. No reviewer decision is authored by Codex and no PR will be merged by this executor.
