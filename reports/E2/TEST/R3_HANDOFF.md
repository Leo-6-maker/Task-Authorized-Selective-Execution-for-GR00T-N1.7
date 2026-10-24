# Issue12 handoff — READY_FOR_INCIDENT_REVIEW / STOPPED_BEFORE_MODEL_LOAD

2026-10-24 (Asia/Singapore). Codex executor, **not an R3 result approval**. The user invoked the newly authorized Issue #12 via the pasted R006 handoff. Work stopped under R006's explicit program/system-failure condition, before any TEST unit was admitted.

## Exact identities and preserved checkout

- Execution: `3e2cb7ff0b98ac82564e0b7a60523a29cb4c8964`; fresh independent Corelab checkout, clean. Original course checkout and previous evidence remain untouched. No running-source edit/rebase/merge/new code SHA.
- Grant on fetched main: `6c5d6c69e9abecf66999eab318b6d8c8a1b676a6`, `docs/reviews/R006-E2-TEST-AUTHORIZED.json`, blob `49c04284f1e61198ee323868180b0707800d0c54`; `authorize()` passed with all120 exact ordered IDs and frozen hash bindings. [Reference/admission](r006_reference.json). PR #11's live Head/base remained `3e2cb7ff0b98ac82564e0b7a60523a29cb4c8964` / `fc38e816ff3e75e87c29da3aa18009dcc0542f02`, draft/open/unmerged.
- Separate report-only branch `codex/12-e2-test-r3` starts at that execution Head. No differences under `tase/`, `scripts/`, `tests/`, or `configs/`. Report-only commits cannot be substituted for R006's authorized execution SHA.
- Before any outcome, deterministic reviewer sampling was committed at `6991e7b0d271bd34ced365608e38da20b310547f`: [plan](reviewer_sampling_plan.json). No TEST sample was selected/exported because no TEST exists.

## Preflight and observed stop

Existing legal E2 account and same project GPU were rechecked: correct owner UID/GID/mount/alias; no active compute process; current free GPU memory31749 MiB on the allocated device; runs disk287,920,779,264 bytes free, remote backup disk1,517,776,011,264 bytes free, and local second destination387,946,434,560 bytes available at preflight. No exclusive-resource claim, access elevation, other-task termination, installation or download. The allocation record cites the user's Issue12/R006 instruction and records current UUID/index and time privately; no credential is printed or published.

Frozen launcher CPU preflight validated official GR00T/LIBERO source, both Python3.12.14 package inventories (138 server,159 sim), ownership markers and all17 existing Object/Cosmos file byte hashes. Six BDDL/initialization-file hashes match prior CALIB, and restricted CPU loading confirms all30 official TEST init-array contents equal the frozen split hashes. No model or simulator was used for these identity checks. The launcher created its successful admission receipt, then failed as described below.

At approximately **2026-10-24 11:43:53 SGT**, the first model-server child exited1: TEST launcher creates the server output directory and admission record, but native server line24 also calls exclusive `mkdir(... exist_ok=False)` on the same path. `FileExistsError` occurs before line27 `import torch`. No `loaded.json` exists. Native child and launcher exits are actual `record_process` receipts; they are not relabeled semantic abort or TEST timeout.

[INCIDENT-001](INCIDENT-001.md) contains source-bound diagnosis and one minimal repair proposal. Every old directory/receipt remains; no alternate server name, ad hoc server invocation, precreated fake success, global `exist_ok=True` patch, grant modification or automatic retry was used. The operator recorded STOPPED and closed its server lifecycle. No owned GPU compute task remains.

## Actual receipts and planned denominator

[Execution state](execution_state.json) · [120 planned ledger rows](planned_120_ledger.csv) · [full frozen CPU audit](unopened_test_audit.json) · [safe actual starts/exits and source hashes](incident-001/origin_manifest.json).

| Operation | Actual observed status |
|---|---|
| Exact-head grant admission | exit0; valid120 IDs and hash bindings |
| Restricted CPU official-init content check | exit0;30/30 match |
| Frozen native model-server child | **exit1**, `FileExistsError`, before model load |
| Frozen TEST server launcher child | **exit1**, actual outer `record_process` receipt |
| Private bounded operator | failure recorded,0 closed units; its outer OS exit not separately captured, not fabricated |
| Post-stop frozen `e2_audit_test.py` | **exit0** actual child,120 planned /0 reserved /0 outcomes |
| CPU synthetic exact-source reproduction, normal | **actual child/wrapper exit1**, expected same pre-model directory error |
| CPU synthetic exact-source reproduction, `-O` | **actual child/wrapper exit1**, expected same pre-model directory error |

CPU reproductions deliberately use no model, a synthetic existing output and CUDA hidden. Both match the actual startup exception before torch import. They are not native TEST execution or a rerun/extension of the71-item prior CPU suite. No TEST model call, physical control, prediction, oracle event or video exists. All120 planned rows remain NOT_STARTED with unknown outcomes; no effect rate, TSR, UAR or meaningful interval is claimed. Frozen audit's missing-data bounds0–1 reflect absence of evidence, not safety. DEV19/CALIB48 and488 candidates remain historical E2 data, not TEST denominators.

One read-only process-status probe raced completion of git checkout and returned shell1 because its target PID had ended. One local report-export helper initially returned1 from a private `operator.py`/stdlib import-name collision; rerunning the **CPU export helper only** under isolated `-I` invocation succeeded. Neither consumed a TEST ID, modified frozen source, launched a model, or caused the native server failure. These bookkeeping failures are explicitly separate from the original recorded server error; original helper/source metadata remains private.

## Evidence, backups and exclusions

[Backup verification](backup_verification.json):34 original startup/preflight/audit/operator/runtime files archived at both authorized remote and owner-local private locations; whole archive and every member SHA256 verified. Archive17,082 bytes, SHA256 `da962b24213b4472b799f20b6a90a2e7f120ccd3795cb9adf591563033e8ffac`. The pre-existing full E2 backup chain is preserved unchanged.

[Supplemental private CPU metadata backup](cpu_metadata_backup_verification.json) retains CPU reproduction actual starts/exits/stderr, operator source/hash and the private runtime map at two locations, again with archive/member checks. The concrete node/account/HOME/mount/interpreter/source paths remain in the private map outside Git. Public derivatives retain original SHA256 separately from redacted public bytes. No weights, private operator implementation, unsafe pickle, XML, raw environment variables or credentials are published.

[Public artifact manifest](artifact_manifest.json) covers this report-only delta; [delivery checks](delivery_checks.json) show no frozen-code/config changes and no known private-path/credential markers in current public files. No nonexistent TEST media/numeric sample is substituted with CALIB or synthetic data. Full independent raw/media verification remains a reviewer task; Codex does not sign GPT approval or merge PRs.

## One next step

**GPT incident assessment and scoped repair authorization for the TEST launcher/output-directory contract, then independent approval of the resulting new exact execution Head before resuming at unopened `e2-test-0001`.** The proposed repair and CPU integration acceptance cases are concrete in INCIDENT-001. R006 does not cover any new executable/config SHA; no fix has been applied to the running/frozen code and no new launch will be made under a mismatched grant. The120-cell protocol, k3, TaskSpec, oracle, C0/C2, split/seeds, native16/8/720 and statistics remain fixed.
