# Issue20 consolidated runtime delta handoff

**READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW. Not TEST_AUTHORIZED.** Codex execution evidence,not GPT approval. R010 `8e43b0c528e6dd7b2ef2ee609bdd317ea68487fd` authorizes standing CPU engineering and explicitly requires a new exact-head machine grant before model/GPU/MuJoCo/TEST. User has not been asked to approve intermediate CPU failures.

## Identities and unchanged acquisition

Base report PR19 `29f50b36af25a8b76583308cf0e5fbbe22365f27`,untouched/unmerged. Original actual runtime `a1c6424bd348b36c55a20d38750a269e9551a698`;its code checkout remains clean. Original grant `f084723cb1d00cb7675fa7394dc1b03c0ce3dcac`,blob `44bb4b617c69c575d9041277ef373f7bd5291f3e`,is suspended on fetched main. Original grant/code Git objects remain preserved;R009 clearance is superseded.

CPU-tested engineering source/config/tests commit **`4d46e7550596263df35fa8cc1a5419b492e8a067`**,identical on local and isolated Corelab CPU checkout. Final report-only commits add evidence/status/docs;the final complete PR Head in issue/PR metadata is the requested review/signing identity. Verify no executable/config/test delta from the tested commit before signing. No executor-signed new grant or authorization JSON exists.

**120 planned =14 consumed (12 SUCCESS,0010/0014 CLEANUP_ERROR) +106 NOT_STARTED,next0015.**1882 original main controls/240 actual requests remain unchanged. No model/GPU context/MuJoCo/real TEST,CALIB rerun,training,WBC,weight download,environment reinstall,failed-ID replay,status rewrite,ledger reset or merge in this package. GPU inventory queries are read-only.

## Engineering implementation

1. `tase/shadow.py`:cooperative CLOSING/CLOSED token/PID protocol,actual native finalizer and process-exit evidence,bounded nonblocking shutdown JSON framing,explicit finalizer/process deadlines and owned TERM/KILL fallback. Missing/partial/backpressured/failing/forced/nonzero/unknown cleanup stays error;repeat close is idempotent and parent resources close. Startup exceptions preserve the original exception and append actual close evidence. Predict/receive and the worker prediction try block are unchanged. Default finalizer10s,separate exit2s,TERM2s,KILL2s;no huge timeout extension or ignored error. See [design](LIFECYCLE_DESIGN.md) and [old incident chronology](INCIDENT_TIMELINE.md).
2. `tase/e2_context.py`:post-episode writes shadow_close.json and legacy-compatible worker exit fields from the actual cached close receipt,after releasing process handles. No Gate/prediction/frame/oracle path change.
3. Historical reader `tase/test_history.py` plus `e2_audit_test.py`/`audit_epoch.py`:authenticate each stored run against immutable historical grant/code/config/source identities. Revoked R008 additionally binds the independently reviewed closed14 prefix and every original manifest/result/reservation/start/exit/supervisor hash. Old grants cannot expand into0015,hide lost consumed IDs,or authorize new code. Current admission/runner/ledger guards remain unchanged. Future full G outcomes require both genuine exit0 and strict complete lifecycle proof. See [historical audit](HISTORICAL_AUDIT.md).
4. Necessary `e2_test_server.py` shutdown wrapper fix:Corelab CPU regression exposed an existing forwarded INT immediately overwritten by finally TERM. A bounded forwarded-signal exit window now precedes existing TERM/KILL fallback. A delayed real CPU INT proxy makes the counterexample deterministic. Native exclusive mkdir/admission/startup/serve code remains AST-identical;this changes only shutdown behavior. Actual original CPU failure retained.
5. `configs/e2_test.json`:only two existing frozen_sha256 entries for changed shadow.py/e2_context.py updated. All semantic fields and other12 frozen digests unchanged. The server helper is bound by the full executable Head. Config SHA256 **`7468d82722143124dcf730e2ac2af0634124ce8347d073087726e0cba7d08004`**. All other grant-binding hashes in [review_bindings.json](review_bindings.json) remain original. This file is NOT a grant.

[Static proof](local/final_scientific_checks.json) verifies18 functions/blocks and15 whole files:Gate/TaskSpec/oracle/native controller/epoch runner/snapshot/admission/ledger/reset/seeds/model lock/catalog/statistical methods unchanged. Bounds/statistics/paired-prefix functions remain AST-identical. No claim that distinct whole code versions are the same binary.

## Actual CPU and historical-data checks

| Source/platform | Ordinary | python -O | Scope |
| --- | --- | --- | --- |
|Local fixed CPU Python|118/118,actual child+wrapper0|118/118,actual child+wrapper0|All original89 plus29 new cases |
|Corelab existing isolated sim Python|118/118,actual child+wrapper0|118/118,actual child+wrapper0|Same exact source4d46…;real CPU proxies only |
|Original14 local read-only copy|actual0|actual0|All raw manifests,labels,prefixes,process/grant/config identities |
|Original14 LIVE Corelab originals|actual0|actual0|All primary rows,pairs,stats,costs/intervals exactly equal to old audit |
|Exported candidate ZIP unpacked|118/118,actual0|Not repeated|Self-contained CPU package check,not historical Git object availability |

New cases include actual spawn workers,slow finalization,real elapsed>10s clean finalizer/exit boundary,EOF,partial framed JSON,request backpressure,invalid/missing completion,nonzero exit,native finalizer error,TERM/KILL,repeat close,startup failure,clock/token/PID tampering and jitter. **64 actual Corelab CPU worker receipts** prove reaping,no survivor PIDs. Fixture abnormal exits are retained;they are not native model experiments. New tests consist of19 shadow,9 historical-Git and1 deterministic server-signal case. All89 prior tests remain covered.

[History equivalence](history_equivalence.json):new normal/-O output agrees exactly with original14 primary output,including120 rows,pair states,metrics,bounds,2000/seed640500 bootstrap intervals and timing aggregates. Only code_epochs metadata is added. [Versioned120 ledger](versioned_ledger_120.csv) assigns real acquisition identity only to old14;106 unexecuted IDs have no fabricated code/grant. Two cleanup errors remain unknown/censored,with an explicit operational failure inventory. Frozen system_error lower0 must not be called zero observed system failure.

[Negative original-copy probes](local/final-negative-originals.json) all9 reject:changed frame bytes,missing video,forged config/manifest/grant,missing child exit,lost consumed prefix,unknown duplicate ID,and old grant new-code admission. Temporary synthetic Git fixtures additionally cover revoked/reformatted grants,mixed old/new identities and false backup/reference claims. Original archive/real bytes were not modified. The original clean a1c checkout also refuses R008 with reason `TEST grant changed on main` before process/reservation.

CPU iteration failures are retained in [failure inventory](retained_cpu_failures.json):exclusive-writer synthetic fixture error,incorrect main-code ancestry assumption,and genuine Corelab CPU INT/TERM cleanup race. Routine document builder/policy failures and raw logs remain in private proof;no real failure was relabeled or dropped. No GPU debugging/reproduction followed them.

## Originals,source hashes and backups

- Old all14 archive254951092bytes/1611 members,SHA256 `cfe5f8357d2b48b473e95015f46dad933b1a17afbe830f6d83e1a2a30e85a76f`:both copies whole/member reverified;remote every live original source also matches. Old startup/cleanup archives and original reviewed reports remain intact.
- New actual Corelab CPU source/suite/worker/signal/history-audit/failure archive **392054bytes/758 members**,SHA256 `df40f1497c9f10bdf1b7d85bee6879e1fd0f972ab3e56e53ef06f6313d143ead`:two locations whole/every member verified.
- New local actualCPU/failure/course metadata archive **4233318bytes/1065 members**,SHA256 `51f36905b6e4920dd9527592c26dcd34241fea74e8a1b4deb8e7cb4a4cc3dda7`:two locations whole/every member verified. Duplicate raw-copy/ZIP extraction bytes are already covered by their original archives.

[Backup proof](backup_verification.json) · [360 source-bound redacted receipts](receipt_origins.json) · [real CPU summary](remote_summary.json). Original and public-derived hashes are separate. Actual private UID/HOME/node/mount/source/runtime map and code_epoch_ledger.json are owner-only and backed up. Unsafe pickle,weights,full original videos,observations,private paths and course PDF are not republished. No claim that GPT has independently read every private archive.

## Other completed work and genuine remaining gate

An independent docs worktree/branch `codex/20-course-draft` contains an editable preliminary15-slide deck (cover+13content+references),CPU-checked source ZIP,README,reproduction contract and claim/limitation notes. All slide pages retain partial14/120/R3-pending status;structure/font/layout/import checks and individual visual review passed. Source ZIP118 CPU tests pass. It contains no weights/private originals/grant. These are course drafts,not final R3-approved conclusions or a submitted assignment.

**One next control point:independent GPT review of the complete final PR Head and a NEW TEST_AUTHORIZED grant.** Requested continuation remains0015(C2/B0/init9),0016(C2/G/init9),mandatory full checkpoint0016 with historical14 unchanged,then0017–0120 in frozen order with automatic four-cell structure/worker/two-copy checkpoints. Ordinary outputs need no further permission. Any real runtime/monitor/state/RNG/resource/evidence error stops real execution and permits further CPU engineering;changed code needs a new exact-head grant again. New native GPU/GL behavior is still NOT_EXECUTED. R3 final data/statistics/claims and owner course submission remain pending. No automatic merge.
