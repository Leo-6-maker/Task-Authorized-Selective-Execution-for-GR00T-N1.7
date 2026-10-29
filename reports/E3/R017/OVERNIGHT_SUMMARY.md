# R017 overnight result — NATIVE_STOP_CPU_DIAGNOSED

**One E3-A ID was consumed; 159 remain unstarted.** The sole native run,
`e3a-test-0001` (Salad Dressing/init16/C0/B0), recorded official success after
121 controls and16 policy requests, with actual runner exit0. Its immediate
frozen original audit raised `ValueError: manifest coverage mismatch`. The
operator stopped before0002, closed its server and switched to CPU diagnosis,
preservation, fixed-denominator reporting and independent E2 checks.

This is an evidence-audit failure after an observed successful baseline. It is
not evidence of Gate effectiveness, a Shadow fault or a model failure. The raw
SUCCESS and exit0 are preserved; they do not override the failed frozen audit.
No primary E3 outcome is declared eligible by this executor pending independent
reconciliation. No ID was rerun, replaced or relabeled, and no new TEST resumed
after the error.

## Version, real admission and timeline

- Unique native runtime: `859e40b5f460365a8853bf3486969e9f8e28951c`, clean and
  unchanged before/after the run.
- Current grant: `ca979be10c00389ed57b77967c232d7a84132406`,
  `docs/reviews/R017-E3-TEST-AUTHORIZED.json`, read back against fetched main.
- R017 plan read from main `ffe3941…`; no repeated Gate C or owner request.
- Existing owner GPU1 evidence was hash-verified and bound into a new private
  allocation for this exact Head/grant. Physical UUID/EGL1 were measured; no
  physical GPU0 fallback. Free GPU1 memory at admission was15,899MiB/16,376MiB.
- All139 frozen source bindings, FULL160/R015 provenance,106XML and existing
  LIBERO config/HOME/paths passed. Existing environments and weights were reused;
  no installation, download or shared config change.
- Remote persistent controller started **02:13:53.855872 SGT** with an exclusive
  retained lock and PID/start identity. It did not depend on the SSH connection.
- Model loaded in31.9365s; peak PyTorch reserved6,392,119,296bytes. Loopback socket
  ownership, loaded receipt, exact process identity and post-load9GiB admission
  passed. No extra `get_action` health request was made.
- 0001 ran **02:14:41.097585–02:14:59.113171 SGT**. Reset/10settling, official
  initialization, native16/8 contract, actual control trace and EGL binding are
  recorded. This B0 run made no Shadow predictions or A0 decisions.
- New TEST stopped **02:15:00.494545 SGT** at the first frozen audit exception.
  Controller finished **02:15:03.175489 SGT**, actual exit1. Neither the07:30
  reservation cutoff nor resource waiting caused this early stop.

The verified owned native server was sent SIGINT during shutdown: actual child
returncode−2/mapped exit130, launcher exit1. These are reported literally, not
normalized to0. The launcher records no forced cleanup; post-stop inspection
found no owned native server, episode or worker process and no GPU1 foreign-job
set change. All starts/exits and original errors have source-bound receipts.

## Root cause and CPU candidate

The native runner legitimately seals **all74 pre-close files**, including16
action chunks,16 observations,16 snapshots, physical frames and other evidence.
`e3.audit.original()` passed its15 mandatory file paths to the shared verifier's
**exact-set** argument. The shared verifier correctly rejected74≠15 even though
all15 were present. The59 legitimate extra files were not missing/corrupt data.
The real CPU candidate later verified every recorded file's bytes/hash.

The independent non-runtime CPU candidate adds `e3.audit_manifest`:

1. Require all mandatory native originals.
2. Derive the complete actual runner-time file set and retain strict equality
   against the manifest, checking every size/hash/source-run identity.
3. Reject absent, added/unrecorded, duplicate, mutated, external, symlink or
   non-file entries. Only the manifest itself and the later supervisor exit
   receipt are excluded from the earlier runner manifest. Ledger verification
   still independently requires the actual completed supervisor/child exit.

It does not delete the59 files, weaken the shared verifier or alter Gate, model,
Oracle, TaskSpec, initialization, conditions, seeds, statistics or raw results.
The positive R016 test fixture now loads the actual approved historical source
bytes rather than the unapproved repair checkout. This is a fixture correction,
not a change to authorization or runtime validation.

CPU snapshot: `84ce33cebdbaca74986ccac18928665d15c22a10`.
Local ordinary/`-O` and Corelab ordinary/`-O` each passed **223 tests**, actual
exits **0/0/0/0** (211 existing +12 manifest integration/negative cases).
Read-only candidate audits of the genuine0001 original passed ordinary/`-O`,
actual0/0 with equal JSON. Original frozen ordinary/`-O` audits remain **1/1**.
The candidate's admission with R017 was genuinely tested and rejected before
native execution. It is **CPU-only, not an authorized runtime**. The frozen
source lock is intentionally unchanged; its changed-source drift is disclosed,
not refreshed to manufacture runtime eligibility. No GPU run used this candidate.

Two pre-model external helper errors also remain preserved: a CPU preflight
serialization SyntaxError(exit1), then a metadata variable NameError(exit1).
Both were corrected outside the frozen tree under the allowed finite path;
successful preflight was not repeated for the metadata correction. No policy
request or reservation existed at either failure. No further native retry or
resource-threshold adjustment occurred.

## Full160 accounting and statistical limits

| Epoch | Planned | Reserved | Frozen eligible | Unknown started | Unstarted |
|---|---:|---:|---:|---:|---:|
| E3-A | 112 | 1 | 0 | 1 | 111 |
| E3-B | 48 | 0 | 0 | 0 | 48 |
| Total | 160 | 1 | 0 | 1 | 159 |

`attempt_ledger_160.json/.csv` retains every original cell, raw SUCCESS and
actual exit. The unmodified `e3.statistics.summarize` was run with all160 rows,
2000 task-stratified initialization-cluster bootstrap draws and seed641500.
Because frozen original authentication failed, its conservative primary
diagnostic treats all outcomes as unknown, including unstarted cells; rates
remain0–1 and contrasts−1–1. This output is explicitly a failed-audit diagnostic,
**not a successful frozen CLI audit**. The literal `PROPOSED…` status returned by
the original statistics function is retained, not rewritten.

The successful CPU candidate's separately labeled post-hoc audit can inspect
one authenticated original under that candidate. It does not replace the failed
frozen result or independently approve scientific eligibility. There is no
baseline-positive C2 pair, Gate run, firstA4 checkpoint or E3-B first6 checkpoint.
Conditional prevention is **N/A**. No efficacy, breadth or A0/G comparison is
supported. Full per-task/condition/arm counts, exposure and source media index
are included; unstarted tasks are not safe outcomes or zero-cost observations.

The original771,526-byte video and CPU-decoded controls1/60/121 source frames
are supplied for the single baseline. Selected public JSON/NPZ originals are
byte-identical and source-hashed. Snapshots containing pickle are preserved
privately, never unpickled for this diagnosis or published as safe interchange.

## Custody and independent E2 delivery

The stopped151-artifact package is17,464,247bytes,
SHA256 `4ca80aae9735f0d12f89f727d543d3d02f07fe1b8d954b68fa500b50a6cbb26b`.
The217-artifact final CPU-diagnosis package is18,051,479bytes,
SHA256 `438535a52e83355786ec806a926b62b1863530b8219dcc5eda4b1bff06dc6e6b`.
Each was copied between the two locations and verified as a whole archive and
every member. Their exact0001 original inventories are equal. The private final
runtime map preserves real interpreters, paths, allocation, PID/start identities,
original lock and CPU-candidate location. Final report/Git closure receipts are
published in the final PR handoff without changing the native runtime.

After shutdown, E2's full120 ordinary/`-O` audits again exited0/0 and equaled the
original final audit. All18,070 E2 originals were rehashed unchanged. E2 retains
117 complete results and three permanently censored cleanup errors. Formal
course Head `9efba1994235ee0cb844653a45c6f1b0812442a7` was checked read-only:
real immutable public-ledger recount ordinary/`-O` exited0/0 with equal output;
its five synthetic helper tests passed in both modes. No formal E2 source, result,
deck or submission was changed. E2 R3 still needs its separate independent review.
The E3 appendix candidate is separate and makes no E3 efficacy claim.

## Concrete next step

Independently review the74-file original manifest, preserved0001 observation and
CPU manifest repair, then decide historical eligibility and a precisely versioned
future execution path. Preserve0001 as consumed; next unstarted ID remains0002.
Do not execute the CPU candidate with R017 or resume TEST during this stopped
night. A future authorized runtime would also need legitimate source-lock
refresh and exact-Head authorization. There is no WAIT_GPT/WAIT_OWNER loop here:
all available CPU diagnosis, two-copy preservation, full160 reporting, E2 checks
and delivery work were completed autonomously. No PR merge, Canvas submission,
scientific self-approval, training, WBC or hardware experiment occurred.
