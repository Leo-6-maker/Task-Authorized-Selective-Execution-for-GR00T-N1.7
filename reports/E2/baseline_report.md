# E2 native baseline — executor runtime evidence

Protocol `TASE-002-v1.0`; scope DEV / C0 / B0. Independent GPT result review: **NOT_PERFORMED**. No Gate effectiveness or TEST result is claimed.

All six predeclared task/init scenarios now have complete native episode evidence: five SUCCESS and one720-control TIME_LIMIT. The original sixth attempt remains an additional infrastructure interruption, so the ledger contains **seven attempts**, not six successes. [Every attempt](baseline.csv), [normal/-O raw-data audits](baseline_audit.json), [diagnostic and overlap proof](baseline_diagnostic.json).

| Task | Init0 | Init1 |
|---|---|---|
| Alphabet soup | SUCCESS,143 controls | SUCCESS,138 controls |
| Cream cheese | SUCCESS,128 controls | SUCCESS,160 controls |
| Ketchup | SUCCESS,143 controls | Original0006 interrupted at537 controls; diagnostic0019 TIME_LIMIT at720 |

Confirmed successful attempts:5/7; complete episode outcomes:5 SUCCESS +1 TIME_LIMIT; interrupted without result:1. All seven reservations have matching process start/exit receipts. The interrupted episode has no invented result.json. Its child exit is143/SIGTERM; complete episodes exit0. The original server exited143 after an incorrect operator shutdown call; the diagnostic uses the fixed native `kill_server()` and exits0.

The six complete episodes contain1,432 policy controls; the retained interruption adds537 observed controls, total1,969, excluding initialization settling. Server logs verify249 model requests across both sessions:180 complete-episode action decisions, one explicit same-reset repeatability request, and68 requests from the interruption. All native input/output shapes match the two uint8 cameras, seven float32 state/action streams,16-step output and at most8 executed controls. Actual language and trusted TaskSpec are separately retained.

First-batch execution SHA: `0b00464eacd8a5e8d6be78de7044584ab9a3ef8b`. Diagnostic execution SHA: `2cb9b437cb8609bc21bb43ede8b9163fe91f16e5`. Runtime lock SHA256: `889b6af83f9afcd19f0c9d7be039bb09175b326adcaa93bda9efce173e99592e`; [actual environments and fixed files](../../configs/runtime_lock_E2.json). Model construction took9.685seconds. Native policy, processor, weights, controller, initialization,20Hz simulation contract and720-control cap were retained.

The operator's360-second wall cap interrupted0006 while writing evidence on NFS. Closed evidence was copied into independently owned node storage; all699 file hashes matched, logical IDs stayed fixed and the NFS tree was retained. Source ACL copying initially failed; that failure and the same-copy verification resume are preserved. Future operational cap900seconds does not change720 physical controls. Diagnostic0019 is one precommitted diagnostic slot, not a replacement. Its initialization/XML/TaskSpec,68 action and observation chunks,537 physical states/controls/frames, scenario RNG and complete snapshot digests exactly match the original overlapping prefix. The full diagnostic finished in34.698seconds. **Wall times across these storage cohorts are not a causal Gate-overhead comparison.**

[Media checks](media_check.json): every frame of all five successful videos decoded and matched the physical-control count. The executor spot-checked first/middle/final dual-view frames; the expected target is visible in the basket at the selected successful endpoints. This is not exhaustive independent annotation. The interrupted original MP4 cannot decode and remains unchanged; separately derived policy-observation frames are labeled as such. The diagnostic video independently decoded720 frames. No complete C0 episode reports a wrong-lift event; this is neither an oracle-accuracy estimate nor a safety guarantee.

Latest synthetic CPU regression: [normal39](cpu/07a8a49a/normal.json), [optimized39](cpu/07a8a49a/optimized.json), exit0. Real JSON/NPZ/byte auditing also agrees in ordinary and optimized modes and never deserializes a pickle. A false audit assumption about `truncated` was fixed against pinned upstream: the native wrapper sets `done=True` at720 and leaves `truncated=False`. The failed checker receipt remains; no model was replayed for that correction and no control/tolerance requirement was relaxed.

The finalized private baseline archive has1,229 members /244,515,238 bytes, SHA256 `a913d913fb69c01aa2c13971d2e10351e7dc11e72e0ef7cd2442934ce77942b3`. Both locations and every member were verified; [receipt](baseline_backup_verification.json). A transport deadline interrupted the first copy near its end; the retained prefix was resumed and the complete original hash matched. Private archive preparation is not independent reviewer access or approval.

Consumption: **DEV7/24; independent short consistency0/96; CALIB0/48 conditional; TEST unauthorized until R2**. Legacy results/budgets remain separate and unverified. P1 machine conditions are satisfied (at least two tasks succeed at both declared initializations), without issuing a GPT approval. Next: six precommitted C2 B0 cases and new shadow windows before real Gate runs.
