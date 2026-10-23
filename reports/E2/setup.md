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
| Cosmos revision | `9ce19a195e423419c349abfc86fd07178b230561`; 10/10 existing cached files verified and independently copied, 4,888,970,298 bytes; real copy child exit0 |
| CPU synthetic tests | Latest 33 normal and 33 optimized, exit0; [export-boundary receipt](cpu/review_export.json); earlier source-bound full logs retained |
| New independent environments | Python3.12.14; server138 / sim159 packages pass dependency check; native imports exit0 with CUDA uninitialized |
| Real E2 baseline | NOT_RUN; no success or governance claim |
| Independent GPT review of new code/results | NOT_PERFORMED |

## Environment continuation

The new server and simulation environments are separate. No other research checkout, system Python, driver, old record or weight was changed. Installation is CPU only, with telemetry disabled and isolated HOME/cache/config paths.

All observed failures remain in private operator evidence: missing system pip, an incomplete uv transfer invocation, a first sim installer targeting externally managed Python (refused), a cache lock timeout, and the full server lock timing out at 1,200 seconds. One interrupted sim resume has a start record and missing child exit; it is not counted as success and no exit code is invented.

The bounded network continuation exported the unchanged upstream lock with TensorRT/DeepSpeed omitted, and applied final sim constraints together. These operations were deliberately stopped once the existing project cache was located; UV child exits -15 and installer exits1 are retained. A subsequent offline cache-index resolution failed immediately (exit1); cache metadata is not treated as an installed environment.

The final environments are independent copies of the existing pinned native environments, using the new E2 Python3.12.14 base. Original environments were not changed. Only the copies' interpreter/editable source references were redirected to the new fixed checkout, with before/after hashes retained. They retain the full original dependency sets, including optional server packages; the earlier proposed omissions did not become the final recipe. Server138 and sim159 packages pass `uv pip check`; native imports pass with CUDA uninitialized and no model/environment constructed. Both source-binding checks point into the new fixed GR00T/LIBERO sources and match their file hashes. Server Torch2.9.0+cu128, sim Torch2.9.0, both CUDA12.8; Transformers4.57.3/NumPy1.26.4; sim robosuite1.4.0/MuJoCo3.3.1/Gymnasium0.29.1.

Every continuation uses a new operation ID, start/exit receipts and captured logs; no old result is overwritten. Private interpreter paths and copy provenance are in the verified-environment runtime map. The first installation-progress backup has two verified locations and all78 archived members match; [receipt](setup_backup_verification.json). This is not yet a finalized experiment backup.

## Model-cache finding

A fresh unauthenticated Cosmos small-file request returned HTTP401. That was insufficient evidence of a missing model: following the owner's request, a bounded model-cache check located the earlier project's runtime-resolution link and all ten expected Cosmos files. All ten files have now been streamed into an independent E2 copy and verified against fixed bytes and SHA256, with real child exit0. The source was left untouched. There is no remaining Cosmos credential requirement for these verified local files. Hostnames, internal paths and private cache provenance remain outside Git. No token has been printed or committed.

## Execution and evidence boundaries

New DEV reservations: 0/24 at the last direct inventory. Independent consistency: 0/96; CALIB: 0/48; TEST not authorized. Environment installation/download attempts are recorded separately and are not physical episode successes. The six committed C0 B0 cells must run only after model identities, environment imports/dependency checks, isolated LIBERO config and current GPU availability are verified. Any physical attempt, including failure, reserves before imports/reset; no silent replacement run IDs.

The Gate and audit code are implemented with synthetic CPU evidence. Real shadow consistency, physical acceptance/rejection, event/media checks, CALIB and R2 remain unfinished. Legacy results are excluded from all new effect denominators. Private runtime map, manifests and two-copy backup verification are part of this work package and will be recorded before a larger experiment batch.
