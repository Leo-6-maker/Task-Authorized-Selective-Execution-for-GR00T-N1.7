# Issue16 / R008 handoff — STOPPED_FOR_INCIDENT_REVIEW

2026-10-24 (Asia/Singapore) · Codex executor. **This is an incomplete TEST/incident packet, not R3_READY_FOR_REVIEW or an independently approved result.** R008's mandatory stop condition fired at consumed original ID0010; no further TEST or code repair was attempted.

## Exact identities

- Running checkout: **`a1c6424bd348b36c55a20d38750a269e9551a698`**, PR #15 exact Head, independent clean Corelab checkout. Frozen implementation is `a904e2678a3c511e36580a173e77b9c72521e093`; running and report trees contain the same runtime/scientific code. No new code/config, rebase or merge on execution checkout.
- Grant: **`f084723cb1d00cb7675fa7394dc1b03c0ce3dcac`**, `docs/reviews/R008-E2-TEST-AUTHORIZED.json`, blob **`44bb4b617c69c575d9041277ef373f7bd5291f3e`**; [review](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/f084723cb1d00cb7675fa7394dc1b03c0ce3dcac/docs/reviews/R008-TEST-launcher-repair-review.md). R006 stays suspended and was not reused. GPT owns approval; executor did not edit signed grants/reviews.
- Separate report-only branch `codex/16-e2-test-r3`, based on approved PR #15, never substituted for execution identity. Complete new report Head is in its PR and Issue16 checkpoint; embedding a commit's own SHA is self-referential. `git diff a1c6424b..HEAD -- tase scripts tests configs` must remain empty. New `check_safe_review.py` lives under reports and is a CPU artifact reader only, never used for policy/Gate/runtime execution.
- Existing deterministic reviewer selection was rebound to R008 **before first reservation** at report commit `ced2fb4855295ee9d08c63d2ca65f2a65cb0b4e4` (no rule change). [Plan](reviewer_sampling_plan.json) preserves the prior pre-TEST rule and original plan hash.

## Activation completed before launch

[Actual sanitized R008_ACTIVATION_RECEIPT](R008_ACTIVATION_RECEIPT.json), [live preflight audit](live-test-audit.json), [fixed identities](fixed-resource-identities.json), [official initialization contents](task-init-identities.json), [prior incident recheck](incident-recheck.json).

Ordinary authorized SSH was restored, with existing account/host-key controls. Actual node/UID/GID/HOME/mount and task-owned E2 storage alias were checked privately. The live original TEST root was absent; frozen auditor actual exit0 showed120 NOT_STARTED/0 reserved, DEV19/CALIB48/candidates488 unchanged, no reservation lock or project native job. Existing GR00T/LIBERO source and recorded source hashes, dual Python3.12.14 environments (138/159 package versions and ownership markers), Object7/Cosmos10 file byte hashes, six BDDL/init-file hashes and all30 approved initialization-array content hashes matched. Existing task GPU was free/noninterfering (31749MiB free), both backup destinations had space, configured loopback port was available. No access escalation, other-task termination, installation, download or CALIB rerun.

The CPU original archive **164711 bytes/1468 members**, SHA256 **`0115637d34a8c4e4afd0ba9268dcc79733a4323252c207c916093bae18325b47`**, was copied to the previously authorized remote backup location; both original/copy whole SHA256 and every member matched. The historical34-member incident archive **`da962b24213b4472b799f20b6a90a2e7f120ccd3795cb9adf591563033e8ffac`** and all34 corresponding live original source files were rehashed remotely and intact. The prior SSH/backup gaps were genuinely resolved, not filled with snapshot assertions.

One new approved native server session was launched. The native child exclusively created output; staged/published admission SHA matched; actual native loaded.json and launcher ready receipt/liveness/identity passed. A **noninvasive `/proc/net/tcp` listening socket matched to the native PID's socket FD** confirmed127.0.0.1 readiness before first reservation; no endpoint action, inference or RNG probe was used for this check. [Real readiness/start/exit records](review/processes). The old failed R006 session was untouched.

## Execution and mandatory stop

[Incident details](ISSUE16-INCIDENT-002.md). TEST IDs0001–0010 were opened once in fixed catalog order. First two four-cell clusters closed, each frozen structural/pair audit actually exited0, and each complete cluster was backed up in two locations before further cells. No interim threshold, task, seed, condition, sample-size or order adaptation occurred.

At **2026-10-24 14:44:43.686 SGT**, original0010 wrote `CLEANUP_ERROR/exit1` after120 main controls/15 requests with observed `official_success=true`. Original cleanup trace identifies `m2_shadow` close: `RuntimeError: owned shadow worker required termination`; final saved worker exit0. The runner/entry exits are actually1. The operator immediately stopped, retained this consumed ID and shut down its owned server. Native server and launcher actually exit0; outer operator actual exit1. Post-stop live state finds no GPU compute process, no0011 directory and clean approved checkout. A close timing/race explanation is not proven and no fix/restart was attempted.

The failed cell is **not changed to SUCCESS**. It is not an ordinary SEMANTIC_ABORT/TIME_LIMIT, and it is not a pre-TEST infrastructure failure like R006: its reservation is consumed. The operator's raw `remaining_planned=111` means failed0010 plus110 unstarted units, not111 available retries; the actual unused-ID count is110.

## Planned denominator, real exits and limits

[All120 typed rows](review/attempt_ledger_120.json) / [CSV](review/attempt_ledger_120.csv) · [accounting](stopped_ledger_summary.json) · [frozen stopped audit/statistics](review/final_frozen_audit.json).

| Quantity / check | Observed |
|---|---:|
| Fixed planned TEST denominator |120|
| Consumed original reservations / saved result files |10 /10|
| Normal complete outcomes |9 SUCCESS|
| Cleanup failure retained |1 CLEANUP_ERROR (0010)|
| Unstarted planned IDs |110 (0011–0120)|
| Saved main controls |1314|
| Actual server get_action/inference records |168 /168 PASS|
| Frozen post-stop live audit, normal / -O |actual exits0 /0;120/10/9, INCOMPLETE|
| Frozen paired audit |4 PAIRED_PREFIX_EXACT;1 ERROR_PAIR_NOT_EXCLUDED;55 INCOMPLETE_PAIR_NOT_EXCLUDED|
| Native server / launcher actual final exit |0 /0|
| Failed0010 native runner / entry / outer batch operator actual exit |1 /1 /1|
| CPU derivative export actual child exit |0|
| Local public safe-array reader normal / -O |actual child/wrapper exits0 /0|

All168 actual server requests were reconciled by original run order to exact scenario/policy seed/actual instruction (server batching records a singleton language list). All10 full original videos decode to exactly1314 saved controls. No post-stop model action, fresh server or simulator run occurred. Frozen bootstrap2000/seed640500 and all120 rows/bounds remain unchanged, but this is **not a complete TEST estimate**. All observed units belong to alphabet_soup/three init identities; other tasks and most held-out initializations are unrun. Do not claim zero TEST failure, an independent generalization result, complete TSR or UAR=0.

Frozen statistics intentionally mark cleanup0010 `outcome_known=false` and leave110 unstarted units. Its `system_error` mapping recognizes RUNTIME_ERROR, while this raw status is CLEANUP_ERROR; therefore a lower system-error numerator0 is **not** evidence of no cleanup/system failures. The explicit failure inventory reports one. No frozen metric/status code was modified to “fix” the table; this interpretation/coverage limit is preserved for GPT.

## Accessible originals and backups

[Public review entry](README.md) · [source/derivative manifest](review/manifest.json) · [receipt origins](receipt_origins.json) · [full backup proof](backup_verification.json).

129 safe derivative files /5,424,757 bytes, manifest SHA256 **`451a8d14febefb4b76954d63feea6ccc6bc1d82b2ba125ac1c7f5d5ccedb153d`**. All181 source hashes bind to the1130-entry complete stopped raw backup index, with no mismatch. Numeric arrays are finite and `allow_pickle=False`; schema preserves object order/labels/raw16 action streams and whole control/state traces. Two available predeclared actual pairs0001/0002 and0009/0010 include the cleanup error, actual exits, contacts/oracle/guards, selected saved predictions and two-view clips/figures. The two other planned task controls are explicitly unavailable/not started, not replaced. [Selection](review/selection.json) has4 selected scenario identities but only2 with actual data; it is not a claim of4 completed sampled pairs.

[CPU reader](check_safe_review.py) ordinary/-O actual exits0 independently replay selected complete oracle sequences and k3 contact decisions and compare raw actions/native converted controls/paired full-state-RNG digests. Numeric prefix of the failed pair also matches; its cleanup failure remains unchanged. The artifact is executor CPU checking, not GPT independent approval or new model/sim evidence. Two extracted source figures were visually inspected for camera availability; wrist views are partly occluded, with no claim of expert event annotation.

Complete all10 stopped originals, failure trace, snapshots/predictions, physical/observation/action/media, actual processes and activation/shutdown metadata are backed up twice, whole/member verified:

- First cluster0001–0004:73,718,282 bytes, SHA256 `7445ba7f38c29435fe62ecbfb79f8e848fb917315cde8d386ec023ee73da081a`.
- Second0005–0008:72,273,112 bytes, SHA256 `1a75e578ea52293ab9fe42dc7bce8226ffc1d854d9745263d6e6603f74873af3`.
- **Stopped full all10 + metadata:**178,122,020 bytes /1130 members, SHA256 **`6d2697b7b0e226daef18d1a203bb63d19f9d98ca639c19fae0adf67e32b22324`**; standalone complete archive, no dependency on partial-cluster backups.
- CPU export/derivative supplement:4,511,021 bytes /136 members, SHA256 `1acfbd8413b2a57232d13df49c0b8f946152619fc12143cd685de0d8671836c9`.

All old incident/baseline/CALIB/CPU backups remain. Private concrete runtime-map/account/host/paths, raw logs, unsafe pickle/XML, weights and full observation/video stay in authorized private backups. No unsafe pickle was loaded for export/audit. Canonical public file/credential scans and source hashes are in [delivery checks](delivery_checks.json) / [manifest](artifact_manifest.json). A local receipt-export helper initially compared batched language against scalar and exited1; the CPU helper alone was corrected to compare `[actual_language]`, with original records unchanged and no experiment rerun. [Disclosure](cpu/public-helper-failure.json).

## One next action

**GPT incident assessment of consumed0010 cleanup/worker lifecycle and the stopped experiment before further TEST.** No executable repair, timeout change, status relabel, grant edit,0010 replay or new session is authorized by this packet. If future repair/continuation is approved, it must preserve the consumed10 identities and110 unopened original IDs, exact science/frozen statistical plan and fresh scoped approval. Leave PR#11/#13/#15 open/unmerged. Final R3 effects, full120 completion, course slides/code ZIP remain pending.
