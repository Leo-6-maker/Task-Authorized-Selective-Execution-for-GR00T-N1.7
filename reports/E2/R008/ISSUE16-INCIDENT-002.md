# ISSUE16-INCIDENT-002 — STOPPED_AFTER_CONSUMED_e2-test-0010

2026-10-24 (Asia/Singapore). Execution Head `a1c6424bd348b36c55a20d38750a269e9551a698`, R008 grant commit `f084723cb1d00cb7675fa7394dc1b03c0ce3dcac`. This is a new runtime cleanup incident **after TEST started**, distinct from the prior pre-model server-directory incident. No fix, retry, replacement ID or ledger reset was performed.

## Actual trigger

`e2-test-0010` is the frozen alphabet_soup / init8 / C0 / G cell. Its original `result.json` records **CLEANUP_ERROR, exit1**, `official_success=true`,15 policy calls,120 actual main controls, no observed first wrong lift. All15 Gate decisions are ACCEPT with the expected k3 checked prefix; the final accepted prefix reaches120 controls. This observed task-success flag is not permission to overwrite the operational failure or exclude the cell.

Original `cleanup_errors.json` identifies resource `m2_shadow` and `RuntimeError: owned shadow worker required termination`, from `tase/shadow.py::Shadow.close`. The original cleanup function retains this error and changes a zero-exit outcome to `status=CLEANUP_ERROR, exit_code=1`. The native runner and entry actually exit1; supervisor records failure, with an actual complete child-exit receipt. [Original-derived failure files](review/episodes/e2-test-0010/result.json), [cleanup trace](review/episodes/e2-test-0010/cleanup_errors.json), [worker exit](review/episodes/e2-test-0010/shadow_worker_exit.json), [actual native exit](receipts/runs-e2-test-0010.exit.json).

The saved worker exit is **0**, despite the close path having raised the required-termination error. These two records are retained together. Source shows `join(10)` followed by an `is_alive()` branch that requests termination, joins again and raises, while `E2Context.close` writes the eventual exitcode in `finally`. They support identifying the shutdown branch that triggered the failure; they **do not independently establish** the worker's wall-clock lifecycle, whether a liveness/exit race occurred, or whether all finalizers completed before termination. No physical/model reproduction or timeout increase was attempted.

## Stop and accounting

The R008 operator stopped immediately at entry exit1, never created `e2-test-0011`, and closed its owned server. Native server actual exit0; launcher exit0; outer batch operator actual exit1. No GPU compute process remained at the post-stop live check. The execution checkout remains clean at the exact approved Head; all code/scientific/config identities are unchanged.

**120 planned =10 reserved/result files (9 normal SUCCESS +1 CLEANUP_ERROR) +110 NOT_STARTED.** Failed0010 consumes its original slot permanently. The original operator field `remaining_planned=111` means111 units not normally closed (failed0010 plus110 unopened), not111 unused IDs. No file was changed to hide that naming limitation. Frozen normal and `-O` **live** post-stop audits each actually exit0 and return120 planned /10 reserved /9 full outcomes /INCOMPLETE. Four complete normal pairs are exact; the fifth pair is retained as ERROR_PAIR_NOT_EXCLUDED;55 pairs are incomplete/unstarted, not omitted.

Saved observed totals across these ten consumed units are1314 main controls and168 actual model requests. Independent CPU reconciliation matches all168 server get_action records/inference records to the per-run exact actual language singleton-list, scenario and policy seed. All10 source videos decode to their exact main-control counts. These are partial-run accounting facts, not final120-TEST performance or a general safety result.

## Evidence and statistical limits

Complete raw originals for all10 attempts, including cleanup error, process starts/exits, snapshots/predictions, physical/contact/control/observations, videos, shutdown and activation records, are in the stopped full archive at two authorized locations. [Backup receipts](backup_verification.json) bind whole and every member hash. The first8 had also passed two frozen structural audits and two independent raw-cluster backups before the next cluster was released. No archive, failed result, old incident or lock was removed.

[Public safe subset](review/manifest.json) contains complete numeric sequences/actions/contacts/unchanged oracle labels for two available predeclared pairs: normal0001/0002 and failed0009/0010. It includes actual source-bound dual-view video clips and decoded control-frame figures. Two planned C0/init6 controls belong to tasks never started and are explicitly unavailable, with no replacement. All120 ledger rows and all10 video checks remain public. No unsafe pickle or full private log/weight is published.

The ordinary/`-O` public CPU reader replays selected actual wrong-lift labels, verifies raw16/native controls, k3 contact decisions, source/exit bindings and paired state/RNG/action prefixes. The failed pair's observed numeric prefix is exact too; that does not turn its cleanup outcome into SUCCESS. These are executor checks, not independent GPT approval or a new simulation.

Frozen statistics retain0010 as `outcome_known=false` and110 unstarted units, with missing/censored bounds. Its legacy `system_error` numerator directly recognizes RUNTIME_ERROR, while CLEANUP_ERROR remains a distinct raw status/unknown outcome; **do not quote its lower numerator0 as proof of zero system errors.** The explicit failure inventory contains one observed cleanup error. No statistical code, denominator or label was patched. All observed runs are from alphabet_soup and only three initialization identities (two complete four-cell clusters plus the C0 pair at init8); cream_cheese/ketchup and most holdout cells are unrun. No complete R3 effect/TSR/UAR claim is made.

## Required next action

**GPT incident review of0010's shutdown/cleanup lifecycle and preserved evidence before any further TEST.** If an executable repair is needed, permit a bounded CPU diagnosis/repair and independently authorize its exact new Head, preserving all scientific hashes and the same already-consumed IDs. Any later permitted continuation begins at still-unopened0011; it must not replay0010 or replenish120 budget. This handoff implements no repair and assumes no permission to resume. The current packet is STOPPED_FOR_INCIDENT_REVIEW, not R3_READY_FOR_REVIEW or a completed120-cell experiment.
