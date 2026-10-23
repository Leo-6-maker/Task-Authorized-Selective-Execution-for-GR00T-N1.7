# E2 setup and execution status

Executor: Codex. Protocol: `TASE-002-v1.0`. Epoch: `E2`.
Authority: Issue #8 and [R004](../../docs/reviews/R004-fresh-epoch-progress-decision.md).
This is an execution progress record, not a GPT result review.

## Version and scope

The branch starts at PR #7 `bb9b4346037441b220d03c26737002748856dc23`, inheriting PR #5 `7e73108fd87a711b4cdc339d93749cc4add3628f` and M1 base `3e214c0b761d0639bf73948356a92a03bf2ddedc`. Main was merged normally. Live PR heads/base were checked again; the stale PR #5 body was not used to reset code. Existing dirty work and historical evidence remain preserved.

| Component | Fixed identity / current evidence |
|---|---|
| GR00T source | `dac54b313160c201c450f97df0fd74ebd379c892` in new checkout |
| LIBERO source | `8f1084e3132a39270c3a13ebe37270a43ece2a01` in new submodule |
| Object revision | `2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21`; 7/7 files rehashed, 6,914,936,710 bytes, match |
| Cosmos revision | `9ce19a195e423419c349abfc86fd07178b230561`; existing project cache located, independent copy/verification in progress |
| CPU synthetic tests | 31 normal and 31 optimized, exit0; [receipts](cpu/normal.json), [optimized](cpu/optimized.json) |
| Real E2 baseline | NOT_RUN; no success or governance claim |
| Independent GPT review of new code/results | NOT_PERFORMED |

## Environment continuation

The new server and simulation environments are separate. No other research checkout, system Python, driver, old record or weight was changed. Installation is CPU only, with telemetry disabled and isolated HOME/cache/config paths.

All observed failures remain in private operator evidence: missing system pip, an incomplete uv transfer invocation, a first sim installer targeting externally managed Python (refused), a cache lock timeout, and the full server lock timing out at 1,200 seconds. One interrupted sim resume has a start record and missing child exit; it is not counted as success and no exit code is invented.

The bounded continuation exports the unchanged upstream lock and omits TensorRT/DeepSpeed distributions for the native PyTorch inference environment. It does not change policy/model/controller source. Simulation applies the upstream script's final Torch, physics and supporting constraints in one resolution, avoiding temporary latest-package downloads. Every continuation uses a new operation ID, start/exit receipts and captured logs; no old result is overwritten. Actual installed versions and dependency checks are still pending.

## Model-cache finding

A fresh unauthenticated Cosmos small-file request returned HTTP401. That was insufficient evidence of a missing model: following the owner's request, a bounded model-cache check located the earlier project's runtime-resolution link and all ten expected Cosmos files. The link points to the fixed revision. Reuse is permitted only after complete byte/hash verification; it creates a separate E2 copy and leaves the source untouched. Hostnames, internal paths and private cache provenance remain outside Git. No token has been printed or committed.

## Execution and evidence boundaries

New DEV reservations: 0/24 at the last direct inventory. Independent consistency: 0/96; CALIB: 0/48; TEST not authorized. Environment installation/download attempts are recorded separately and are not physical episode successes. The six committed C0 B0 cells must run only after model identities, environment imports/dependency checks, isolated LIBERO config and current GPU availability are verified. Any physical attempt, including failure, reserves before imports/reset; no silent replacement run IDs.

The Gate and audit code are implemented with synthetic CPU evidence. Real shadow consistency, physical acceptance/rejection, event/media checks, CALIB and R2 remain unfinished. Legacy results are excluded from all new effect denominators. Private runtime map, manifests and two-copy backup verification are part of this work package and will be recorded before a larger experiment batch.
