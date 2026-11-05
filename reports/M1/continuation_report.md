# M0–M1 native baseline continuation

Author: Codex executor; 2026-10-21 Asia/Singapore; TASE-001 v1.0; Issue #2 / PR #3.
Status: **READY_FOR_REVIEW — native baseline evidence delivered; independent R1 pending.**

## Result and complete denominator

Six predeclared native C0 DEV cells ran to official success or the fixed 720-step limit: **5 successes / 6 complete episodes (83.3%, descriptive DEV result)**. Alphabet soup and cream cheese each succeeded at both predeclared initialization indices 0 and 1. Ketchup initialization 1 failed at the time limit and is retained. No seeds/tasks were changed and no retry was used to replace this failure.

| Attempt | Task | DEV init | Result | Official success | Calls | Control steps | Wall seconds | Exit |
|---|---|---:|---|---|---:|---:|---:|---:|
| 006 | alphabet soup | 0 | State dtype validation error | N/A | 0 | 0 | 6.479 | 1 |
| 007 | alphabet soup | 0 | SUCCESS | true | 18 | 141 | 10.453 | 0 |
| 008 | alphabet soup | 1 | SUCCESS | true | 18 | 144 | 9.219 | 0 |
| 009 | cream cheese | 0 | SUCCESS | true | 16 | 127 | 8.420 | 0 |
| 010 | cream cheese | 1 | SUCCESS | true | 21 | 162 | 9.705 | 0 |
| 011 | ketchup | 0 | SUCCESS | true | 18 | 144 | 9.047 | 0 |
| 012 | ketchup | 1 | TIME_LIMIT | false | 90 | 720 | 21.953 | 0 |

Attempts 001–005 remain exactly as previously reported: one restricted-init loading error and four successful environment probes, all with zero policy calls. [All 12 rows](dev_runs_resume.csv) include both infrastructure errors, four environment probes and all six complete episodes. Budget **12/24 used, 12 remaining**. Seven policy attempts include the dtype error; success per policy attempt is 5/7, distinct from the 5/6 complete-episode descriptive rate. Probes are not task successes. Server-only startup failures are retained separately, without creating/resetting an environment or consuming another episode reservation.

## Authorization and resolved blockers

The independent [R001](../../docs/reviews/R001-M0-M1-access-blocked.md) reviewed the old head `24ad57fd0dad73327f00851529c32ba762e42569` as BLOCKED_RESOURCE. It is unchanged. The owner subsequently instructed continuation under the original M0–M1 scope and existing shared-GPU permission, conditional on sufficient VRAM. No M2, shadow, oracle, Gate, CALIB, TEST, training or WBC was run.

The original HF 401 was a credential-path issue: the isolated HOME/HF_HOME did not locate the owner's existing active token. A process-level external `HF_TOKEN_PATH` resolved authentication; whoami and Cosmos config access passed without token output. The owner's CLI token-index error did not invalidate the existing active token. Credentials were neither copied into the workspace/cache nor archived.

Cosmos is frozen at `9ce19a195e423419c349abfc86fd07178b230561`; ten inference files (including the 4,877,470,304-byte backbone tensor file) were hashed and checked against pinned upstream sizes and LFS SHA-256. See [backbone evidence](evidence/backbone-verified-03.json). Object remains `nvidia/GR00T-N1.7-LIBERO@2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21/libero_object`; its seven original files and hashes are unchanged.

Server 02 then failed with exit 1: Transformers 4.57.3 tokenizer Mistral detection called remote model metadata despite offline mode. Server 03 resolved the native Cosmos identifier through a working-directory relative symlink to the fixed local snapshot and ran offline. No checkpoint, upstream policy or tokenizer source was modified. Server 03 loaded the actual Object policy and shut down through the official loopback endpoint with **child exit 0**. The old server-01 child exit remains NOT_CAPTURED; it has not been retrospectively invented. [All server sessions](evidence/server-sessions.json).

Attempt 006 reached the strict policy interface with float64 state, before any model forward. The thin runner had omitted Gymnasium SyncVectorEnv's declared-space dtype conversion. The repair uses the same installed `gymnasium.vector.utils.concatenate/create_empty_array` batching functions, preserving native float32 state and uint8 images. Attempt 006 remains a failed budget row; attempts 007–012 use the committed repair.

## Runtime identity and recomputation

- Successful runner SHA: `46b3461a0f24d0575141b4e35e430ee1e3280e2c`; failed 006 SHA: `5c8d8136b6e52a50ebcaf243f713a4c1a16bbda1`. Both worktrees were clean at reservation.
- Server 03 started at `5c8d8136b6e52a50ebcaf243f713a4c1a16bbda1`. Its instrumented server code is unchanged by the subsequent runner-only batching fix; source hash and request-to-run map are in the new lock.
- GR00T source: `dac54b313160c201c450f97df0fd74ebd379c892`; LIBERO: `8f1084e3132a39270c3a13ebe37270a43ece2a01`; tracked upstream diff is empty.
- DEV config hash: `543653dcdecdf4227c9814713041dc58635bef0da4379b6dafd844274ebab389`.
- [Continuation runtime lock](../../configs/runtime_lock_resume.json), SHA-256 `5666660bfb7ba215912b774bf546fbddc1c7b34d1c07f52689f5ab8c5d9ce29d`.
- Torch policy seed 640100 is set **once per server session**, not once per episode. Client reset does not reseed the stochastic action sampler. Ordered requests 1–182 are explicitly mapped to runs; environment seed 640101 is set per environment. No deterministic policy replay claim is made.

The CPU [audit](evidence/resume-summary.json), regenerated by `scripts/summarize_baseline.py`, verified every per-run artifact hash, all **181 successful model calls**, request image/state dtypes/shapes, all **1,438 actual control inputs** against saved raw model prefixes with exactly one native gripper transformation, control-state counts, official success/terminal decisions, process receipts, fixed reset/history parity and the unchanged budget denominator. One additional request was rejected before forward. The six episode videos and raw NPZ/state files are retained privately. The executor inspected successful and failed terminal video frames; this is not an event oracle or governance result.

Actual observation contract: two uint8 `[1,1,256,256,3]` images, six float32 scalar state streams `[1,1,1]`, two-finger state `[1,1,2]`, native language. Actual actions: seven float32 `[1,16,1]` streams; official horizon resolver returns observation offsets `[0]`, action horizon 16, execution prefix 8. Architecture config horizon 40 is not the emitted LIBERO modality horizon. Details: [continuation contract](runtime_contract_resume.md).

## Measured resource cost and limits

Inference ran on the authorized shared 32-GiB-reported RTX 4080 SUPER device with about 20.6 GiB free before loading and a 55% process allocator cap; other workloads remained running. Object load took 10.020 s. Maximum allocated/reserved bytes were 6,386,141,184 / 6,482,296,832 (about 5.95 / 6.04 GiB). After clean shutdown, free memory returned to the pre-load level observed in the shared inventory. Sharing can affect latency; these observations do not establish zero performance impact on other workloads.

Across 181 forwards, GPU-synchronized server latency: median **88.0 ms**, mean 99.7 ms, minimum 62.7 ms, maximum/first cold call **950.3 ms**. Complete-episode wall time including process startup/reset/settling: median **9.462 s**, mean **11.466 s**, range 8.420–21.953 s. These are six DEV samples under shared load. A naive 90-baseline-episode extrapolation is about 17.2 minutes; governed episode cost is unmeasured and requires its own budget. Native 20 Hz is simulation control frequency; the cold call exceeds the 400 ms eight-step interval, so these data do not establish real-time deadline compliance.

CPU evidence/installer tests: 8 passed locally and remotely. Manual process-receipt fault injection returned and recorded child exit 7. The full raw-evidence audit passed with exit 0. Earlier failed local invocation/transport and source-discovery operations are retained in [operation receipts](../M0/operations_resume.json); they are not GPU/episode attempts.

## Artifact access and requested R1

[Continuation manifest](artifact_manifest_resume.json) binds the current public snapshot and private raw records by relative ID, bytes and SHA-256. Original reports, runtime lock, manifest and failed evidence remain available; their old manifest refers to its recorded historical public snapshot, not today's changed README/status files. The private 43,066,832-byte runtime archive was transferred with matching local/remote SHA-256 `87e1cfa17f00413a7ae7cac0fc518bf6914170dcea188f6a3543ef9add56edc7`. Exact executed operator scripts and command/exit receipts are also archived privately. Neither weights nor credentials are in these evidence archives or the public repository.

Independent raw-content review remains **NOT_VERIFIED** until the reviewer accesses the authorized private files. Hash verification by the executor does not substitute for that review. The remaining policy failure, small sample and session-scoped stochastic RNG are explicit limits.

Request: independent R1 review of the new PR head, including native reset/batching/action parity, all failures, resource cost and raw evidence availability; decide whether M2–M3 may begin and under what budget. Codex does not approve the stage or merge this PR. No further GPU attempts are running.
