# R002 evidence-audit hardening (Workstream A)

Author: Codex executor; TASE-001 v1.0; Issue #4 / parent PR #3. Independent decision remains [R002](../../docs/reviews/R002-R1-native-baseline-conditional.md): PR merge CHANGES_REQUIRED; bounded M2 CONDITIONAL_APPROVAL. No signed review was changed.

## Repairs and real verification

R002's four false-PASS paths were valid findings. The stage auditor now requires exact two-image/seven-state observation keys, complete reset stream keys with literal true booleans, complete per-run manifest coverage and unique relative artifact IDs, declared task/language/configuration identities, consistent run/reservation/receipt IDs and exit codes, contiguous reservation and decision indices, all request/action files, trace counts and finite inputs. Server request order, shapes and per-run calls are reconciled. All critical conditions use explicit exceptions and execute under `python -O`.

The immutable delivery manifest can additionally anchor every private runtime byte via `--delivery-manifest`. `verify_delivery.py --require-private` fails when any declared raw item is unavailable; default informational mode still says NOT_VERIFIED and must not be used as the stage gate.

`tests/audit_fixture.py` is a clearly labeled **synthetic CPU fixture**, extended with the newly required metadata and files. Its valid control passes. Nineteen single-corruption variants, resealed where necessary to exercise semantic checks, are rejected: R002's missing wrist, empty observation, empty parity and empty manifest; missing/nonboolean parity; missing/duplicate manifest entry; wrong dtype/shape; modified action; wrong step count; duplicate decision; missing horizon; mismatched source; wrong instruction; wrong process exit; wrong server request index; path escape. The original reviewer fixture/report remain unchanged; rejecting its now-incomplete positive fixture is not counted as a negative-test success.

Normal and optimized Python each pass **13 unittest methods**, including the original eight. Synthetic cleanup/partial-step tests verify that a returned native step is persisted before the next step/video callback, failed native-step attempts are explicitly recorded as UNKNOWN_PARTIAL_PHYSICS_STEP, both cleanup errors are retained, the primary failure remains primary, and cleanup failure after apparent success changes the returned exit status to failure. These are CPU tests, not physics results.

Control trace persistence now uses fsync and atomic replacement after every successful native control step. Client/video/environment cleanup is isolated before the final result/manifest; the main return code follows the final recorded result. An OS kill or storage failure can still leave an incomplete attempt; reservations remain consumed and the auditor rejects unsupported partial records instead of guessing their outcome.

Implementation source SHA for these checks: `a3cd38876df8a8a96b77da47568b0abacc70e57f`. Exact CPU commands and actual exits are in [checks](evidence/audit-hardening-checks.json); results are in [the appended raw re-audit](evidence/audit-hardening-summary.json). No old summary/manifest/result was overwritten.

## Existing raw-data re-audit

The repaired auditor checked the retained private runtime against the historical manifest's runtime records and recomputed all twelve attempts. Normal and `-O` outputs agree with the published ledger, with **no unexplained differences**: four environment passes, two infrastructure errors, five successful policy episodes, one 720-step time limit; 182 requests, 181 successful inferences, 1,438 actual control steps. No new environment or model request was needed.

The historical probe 002 predates object-catalog capture. Its original manifest never claims a catalog; it is checked as an environment probe, not a complete policy episode. All six full episodes and policy attempt 006 have the required catalog. This known version difference is preserved rather than manufacturing a missing artifact. The original server-01 child exit remains NOT_CAPTURED; server-02 exit 1 and server-03 exit 0 remain their recorded values. No startup error or failed attempt was turned into task success.

The reported 6,482,296,832 bytes (6.037109375 GiB) is **PyTorch peak reserved**, not a measured sum of complete process, CUDA context and rendering memory. Policy Torch RNG was seeded once per server session; this repair does not establish paired B0/G randomness.

## Reviewer-accessible private originals

A private sanitized package is prepared for owner-mediated reviewer attachment: `R002-private-sanitized-originals.zip`, 43,397,863 bytes, SHA-256 `d0d317ee83226ce3dd34a654468636b43deb8cae5a959b4fe628fda5ba3eba98`.

It includes 465 original-derived entries: all six complete episodes' numerical observations/actions/control traces/terminal decisions, failed 006, the 182 server request records, process exits, all twelve run metadata records, full episode videos and successful/failed terminal image samples. **453 numerical/media/metadata files retain original bytes**; result JSON uses an explicit allowlist. Package manifest records original IDs/hashes and any transformation. Credentials, host paths, raw machine logs/tracebacks, XML asset paths and weights are excluded. The package stays in authorized private storage and is not committed or uploaded publicly.

This provides inspectable originals rather than another executor PASS summary, but independent raw verification remains **NOT_VERIFIED_BY_REVIEWER** until the reviewer actually receives and opens it. Owner attachment is still needed for a reviewer outside the authorized local/server storage. Codex does not close that item or merge PR #3.

## Budget and continuation

Workstream A consumes **zero new DEV episodes and zero shadow cases**. Original budget remains 12/24. Under R002, the separately branched M2 may use at most six new DEV acquisitions and eighty short shadow cases only after these regression/raw checks and a fresh resource check pass. The other six DEV slots remain reserved. M3/Gate intervention, CALIB, TEST, training and WBC remain unauthorized.
