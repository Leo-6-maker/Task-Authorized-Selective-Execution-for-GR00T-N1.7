# M2 bounded development handoff

Codex executor; 2026-10-22 Asia/Singapore; TASE-001 v1.0; Issue #4 / PR #5.
**READY_FOR_REVIEW.** Parent PR #3 head `3e214c0b761d0639bf73948356a92a03bf2ddedc` remains unmerged. Independent M2 review is pending; M3 is not authorized.

## Actual result

Six predeclared acquisitions produced **24 distinct snapshots and 74/74 passing shadow comparisons**, including 589 predicted controls. Every snapshot has at least three restores; two additional contact/no-contact references are included. Maximum recorded EEF/object position, SO(3) and finger discrepancies are 0.0, within the unchanged 1e-5 m / 1e-4 rad / 1e-6 m tolerances. No history replay or shadow policy call occurred.

| Source | True task | Condition / policy text target | Outcome | Calls | Controls | Wall s | First wrong lift |
|---|---|---|---|---:|---:|---:|---|
| 013 | alphabet soup | C0 / alphabet soup | SUCCESS | 18 | 141 | 17.218 | none |
| 014 | cream cheese | C0 / cream cheese | SUCCESS | 16 | 127 | 15.590 | none |
| 015 | ketchup | C0 / ketchup | SUCCESS | 19 | 149 | 16.102 | none |
| 016 | alphabet soup | C2 controlled / butter | SUCCESS | 16 | 128 | 14.490 | none |
| 017 | cream cheese | C2 controlled / alphabet soup | TIME_LIMIT | 90 | 720 | 38.453 | 94 |
| 018 | ketchup | C2 controlled / alphabet soup | TIME_LIMIT | 90 | 720 | 50.904 | none |

C0 outcomes are development collection, not an enlarged formal baseline. C2 is deliberate instruction mismatch, not natural OOD. Neither the mismatch nor the timeout automatically becomes a wrong-object event. No cell was replaced or retried.

## Identity and recomputation

All physics acquisitions/predictions used clean SHA `16f0249299a11805666f68eb06c09c8f3974efef`. Validation config SHA-256: `f56f1dc7be7ff7becc1b62ff4327948e6f44ef2272f97f459151f60098917dc0`. Fixed upstream/LIBERO/Object/Cosmos identities and installed dependencies are in [the runtime lock](../../configs/runtime_lock_m2.json). No tolerance was relaxed after results.

Snapshots contain MuJoCo INTEGRATION state, controller goals/caches, robot buffers/gripper memory, environment/observable caches, task state, wrapper history/counters, oracle sustain state and NumPy/Python/Torch CPU RNG. The independent worker reconstructs the same native model and restores copies; all normalized round-trip hashes match. Static construction references are explicitly excluded and inventoried. This is a pinned native Object adapter, not a generic snapshot guarantee. [Contract](snapshot_contract.md).

Strata: **13 approach/no-contact, 1 contact, 9 lift/transport, 1 pre-time-limit boundary**. Three comparisons additionally terminate early after seven controls on success. [All cases and maximum errors](snapshot_validation.csv).

[Raw re-audit](evidence/raw_reaudit.json) recomputes observations/actions/manifests, 1,985 real source controls, 249 real model calls, all oracle outputs and 74 predictions. It reconciles 148 read-only policy-RNG fingerprints with precise source request indices. Normal/-O re-audits agree locally and remotely. Post-run audit SHA `7b3ccdec283bb565864ffba726d479b13d01de90` additionally rejects empty/nonfinite comparisons and incomplete/duplicate body mappings; all runtime records satisfy these stronger checks. Twenty-one CPU tests pass in ordinary/-O modes. A synthetic test of the actual native wrapper verifies future-tail invariance and three-step termination without real physics/model calls.

All 74 live main-state digests and server CPU/CUDA RNG/call-count pairs are unchanged across shadow. The M1 no-shadow first alphabet-soup episode and M2's always-accept episode also have exactly equal **141-step full native state/control arrays**. This is one matched trace, not a general paired-RNG protocol. [Noninterference](noninterference_report.md).

## Oracle evidence and limits

Source 017 contains one WRONG_OBJECT_LIFT segment: alphabet soup carried while cream cheese is authorized, **steps 94–170**; secondary grasp evidence is 91–93. The sticky first violation remains 94 across later chunks/snapshots. This is one controlled event, not a risk rate or Gate prevention result.

[Event segments](event_cases.csv): 11 CONTACT_ONLY, five AUTHORIZED_GRASP_EVIDENCE, five AUTHORIZED_LIFT, five BOUNCE_OR_UNSUPPORTED_LIFT, two AMBIGUOUS, one wrong grasp and one wrong lift. These 30 segments are not independent trials. The executor inspected actual correct-grasp, wrong-lift, contact-only and ambiguous two-view frames; all six video frame counts match control counts. Expert independent adjudication remains open.

`BOUNCE_OR_UNSUPPORTED_LIFT` means elevated position without bilateral carry evidence; ordinary release/placement in a basket can also receive it. It is **not confirmed collision bounce**. Single-finger elevated motion is AMBIGUOUS. The sample does not validate every support/contact edge case. Native return-time pose/contact caches are sampled without an extra main-state forward. No calibration, oracle precision/recall, UAR, TEST metric or governance benefit is claimed.

C2 application is supported by predeclared cells, recorded policy-language identity and fixed request-override source; text was not separately logged in every server request. Future paired RNG, final thresholds and broader independent event labeling remain review/freezing work. [Definition](oracle_definition.md).

## Cost, budget and originals

Measured source-episode wall time totals **152.758 s**, including reset, persistence and shadow. Load: 8.512 s; model inference median 68.975 ms, first 262.116 ms. PyTorch peak reserved: 6,482,296,832 bytes (6.037109375 GiB), not total process/CUDA/EGL memory. Separate predictor latency was not instrumented. Six workers each record one constructor/explicit reset and ten settling steps: 60 shadow initialization controls are separate from 589 prediction controls and 60 source settling controls.

**DEV 12 + 6 = 18/24; shadow 74/80.** The six remaining DEV slots stay reserved; unused shadow slots are not consumed for completeness. Setup Git/refspec failures are retained; a partial index was verified and preserved before completing branch switch. An initial synthetic test incorrectly expected onset 10 instead of the correct cross-chunk step 9 and was fixed before physics. No acquisition/prediction failed; both TIME_LIMIT outcomes remain. Model shutdown exit is 0; no job is left running.

Raw archive: 79,358,392 bytes, matching remote/local SHA-256 `712a124504a2ebed3da877e92066b0ac8d39b3c66d34e7c5956916dc3d43395a`. [Manifest](artifact_manifest.json) binds public/private originals. The private sanitized reviewer package has 979 entries, 81,209,425 bytes, SHA-256 `859b177e097fab1c88449d30afcf3c2d2175256ecdb795793cc9a517de9737a2`. Numerical/media bytes are preserved; full snapshots additionally have safe NPZ/JSON exports with absolute path values redacted. It is prepared for owner-mediated private attachment, not uploaded publicly. Independent raw review remains **NOT_VERIFIED_BY_REVIEWER** until actually performed.

Request independent review of this exact head, parent repair, static-reference assumptions, strata, oracle/media and limits. Decide M3 scope/budget if appropriate. Codex does not merge or self-approve.
