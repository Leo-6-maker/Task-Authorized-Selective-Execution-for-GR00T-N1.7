# ISSUE18-INCIDENT-003 — repeated cleanup failure at consumed0014

2026-10-24 (Asia/Singapore). **STOPPED_FOR_REPEATED_CLEANUP_INCIDENT_REVIEW**. Exact running code remains `a1c6424bd348b36c55a20d38750a269e9551a698`; R008 machine grant and R009 reviewer clearance are unchanged. No retry, status rewrite, runtime repair, new session or additional TEST after the failure.

R009 fresh live activation genuinely passed. A new unique native session loaded and served0011/0012; both SUCCESS,136 controls/17 requests, actual child0, G worker0. The mandatory checkpoint after0012 passed frozen raw/paired/controller/state/RNG/Gate checks and true two-copy backup before0013. Its442-artifact cluster archive SHA256 is `522b47cdfcf09cf6b3a64c3c59941aeb577ec34c1243237d9139e16114b57bf5`. Original0010 remains CLEANUP_ERROR,actual exit1,worker0,outcome_known=false.

## Recurrence and actual stop

0013 (alphabet_soup/init9/C0/B0) succeeded after148 controls/19 requests,exit0. Paired0014 (same task/init/condition,G) saved official_success=true after148 controls/19 calls,19 ACCEPT k3 decisions and19/19 full-state/policy-RNG guards passing. Last ACCEPT executed controls144→148; no first wrong-lift observed. During resource `m2_shadow` cleanup, the same `Shadow.close` branch raised `RuntimeError: owned shadow worker required termination`. **Original0014 final status CLEANUP_ERROR / native child1 / entry1 / complete_child_receipt=true / worker final0**. Completed result timestamp2026-10-24T16:10:09.146320+08:00. The task-success observation never replaces cleanup/error/missing eligibility.

Frozen source is unchanged: send close,join10,if still alive terminate/join5,raise; E2Context records eventual worker exit in finally. The recurrence makes the R009 repeat-failure stop mandatory. Both final worker0 and the error are retained. Source and receipts locate the post-action cleanup branch; they do **not establish exact close/liveness/native finalizer/termination ordering**. No wall-clock lifecycle instrumentation exists in these originals. No GPU reproduction, timeout change, benign-error reclassification or code repair was attempted.

The operator stopped immediately on0014's entry1. Native server and launcher exited0; outer operator exited1 at16:10:13.591874+08:00. Exact native start/exit receipts are retained separately. Fresh live post-stop checks show old/new server PIDs and0014 episode/worker PIDs absent, allocated GPU compute0, code clean,0015 absent. Original0010 hashed failure receipts are unchanged.

## Accounting and preserved evidence

**120 planned =14 consumed (12 SUCCESS +2 CLEANUP_ERROR) +106 NOT_STARTED.** New resumption consumed exactly0011–0014; no budget reset.0015 is unopened. The private operator's `remaining_planned=107` counts three newly normal-closed units and includes failed0014; it is **not**107 unused slots. Authoritative raw inventory shows106 unused. Original operator record is not edited.

All14 saved units have1882 actual main controls/240 requests; new session has72 requests (17+17+19+19). Frozen live normal/-O audits each exit0 with identical120-row/statistical output:12 full outcomes,2 retained error pairs,5 exact normal pairs,53 incomplete/unstarted pairs. Frozen experiment_status stays INCOMPLETE. Full nominal120 denominator, task-stratified2000 bootstrap/seed640500 and missing bounds stay unchanged. Both cleanup errors are observed operational failures even though frozen system_error maps only RUNTIME_ERROR; lower0 must not be described as zero operational errors.

All evidence remains source-bound: all14 original results/reservations/controls/snapshots/predictions/video/worker/error/process files; both native sessions and actual outer exits; live activation and CPU helper failures. See [backup proofs](backup_verification.json), [stopped ledger](stopped_ledger_summary.json), [numeric review](review/manifest.json), [0014 result](review/episodes/e2-test-0014/result.json), [cleanup trace](review/episodes/e2-test-0014/cleanup_errors.json) and [mandatory checkpoint](checkpoint_after_0012.json). Private originals remain at two authorized locations; public finite NPZ/JSON/short dual-view media retain separate source/derivative hashes. Old incident archives and PR17 fixed Head are preserved.

All observed TEST units remain alphabet_soup,init6–9; other tasks and most120 cells are unstarted. No full TEST effect, safety certification, no-failure claim or R3 approval.

## One required next action

**GPT review of the repeated cleanup incident and authorization of a bounded CPU lifecycle repair package**, followed by review of a new exact code Head and new machine grant before any further TEST. Preserve0010 and0014 forever as consumed CLEANUP_ERROR and resume only unopened0015 if later explicitly authorized. No automatic continuation under the old R008/R009 pair, no retry, new IDs, scientific tuning, download/CALIB/training/WBC/hardware or merge.
