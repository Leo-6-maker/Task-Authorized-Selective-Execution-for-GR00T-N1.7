# Task-Authorized Selective Execution for GR00T N1.7

**ME6401 Part 2 — formal E2 coursework source edition, 30 October 2026.**

A frozen GR00T N1.7 LIBERO-Object policy proposes native actions. An execution-boundary guardrail checks a short shadow rollout against an independent trusted task identity. ACCEPT executes the checked prefix unchanged; REJECT or ERROR withholds it and ends the autonomous episode.

This is the course project, **not GR00T+WBC**. No WBC, Go2, ARX5, custom EEF decoder, additional policy training or real-hardware result is included.

## Start here

| Purpose | Entry |
|---|---|
| Current implemented architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Dependencies and reproduction levels | [docs/REPRODUCTION.md](docs/REPRODUCTION.md) |
| Exact source and evidence identities | [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) |
| Complete 120-row public ledger | [results/e2/attempt_ledger_120.json](results/e2/attempt_ledger_120.json) |
| Original frozen statistics and uncertainty | [results/e2/final_frozen_audit.json](results/e2/final_frozen_audit.json) |
| Results, failures and claim limits | [results/e2/R3_REVIEW_PACKET.md](results/e2/R3_REVIEW_PACKET.md) |
| Formal submission checklist | [submission/README.md](submission/README.md) |
| Current E3 approval and next gate | [docs/reviews/R016-E3-GATE-P-APPROVED.json](docs/reviews/R016-E3-GATE-P-APPROVED.json) |

## Main files

`tase/gate_features.py` implements the contact-only k=3 decision. `tase/execution_gate.py` enforces the checked/executed action boundary. `tase/shadow.py` and `snapshot.py` handle isolated prediction and state restoration. `task_spec.py` defines trusted object bindings; `event_oracle.py` independently evaluates actual wrong-object lifts. `scripts/` contains the original preparation, native server, experiment and audit entry points. `configs/` preserves original protocol/runtime/source locks. `tests/` preserves the original CPU regression suite. `tools/` contains submission-only offline helpers and does not alter the frozen runtime.

## No-GPU reproduction

From the extracted ZIP root, using Python 3.10+ for the standard-library helper:

```bash
python tools/recheck_e2.py --self-test
python -O tools/recheck_e2.py --self-test
python tools/recheck_e2.py --ledger results/e2/attempt_ledger_120.json
```

The last command verifies the original Git blob identity, all120 IDs/design/statuses, censored outcomes, exposure counts and primary all-planned bounds. It reads existing data only. It does not rerun the simulator, authenticate every private raw file, or replace the frozen bootstrap calculation. The optional `--out recount.json` creates a NEW output file and refuses overwrite.

For the original CPU suite, use an isolated Linux environment with Python3.12.14 and the minimal dependency file:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-cpu.txt
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

Subprocess, loopback socket and Linux `/proc` access are required by integration tests. Restricted sandboxes may fail these checks. The historical executor reported134 passing tests; this packaging session does **not** claim a new full134 run. The new helper's five synthetic bound tests passed in both modes. Read [reproduction limits](docs/REPRODUCTION.md) before attempting native deployment.

## Evidence snapshot — not a universal safety claim

All120 planned TEST IDs were consumed:89 SUCCESS,18 TIME_LIMIT,10 SEMANTIC_ABORT,3 CLEANUP_ERROR.117 primary outcomes are eligible;0010/0014/0016 remain censored and are never replaced.

| Condition | System | Eligible / planned | Observed wrong lifts | All-planned wrong-lift bounds | Official-success bounds |
|---|---|---:|---:|---:|---:|
| Normal C0 | B0 | 30/30 | 0 | 0/30 | 29/30 |
| Normal C0 | G | 28/30 | 0 | 0–2/30 | 27–29/30 |
| Controlled mismatch C2 | B0 | 30/30 | 10 | 10/30 | 17/30 |
| Controlled mismatch C2 | G | 29/30 | 0 | 0–1/30 | 16–17/30 |

Missing-outcome bounds are not confidence intervals. The original C2 G-minus-B0 wrong-lift bound is−33.3 to−30.0 percentage points; the task-stratified paired bootstrap95% bound envelope is−33.3 to−23.3 points (2000 repetitions, seed640500). All10 positive baseline cases are cream_cheese/C2; G aborts all10 and does not recover the task. Candidate UAR is N/A. Privileged simulation inputs, finite prediction horizon, four actual runtime epochs, three cleanup failures and additional infrastructure pauses constrain the claims. There is no demonstrated hard20Hz wall-clock guarantee.

## Version and authority boundaries

The complete `tase/`, `scripts/`, `configs/` and `tests/` trees are copied by existing Git object identity from final E2 runtime79510d9a302eeb7820f7ed35463c29bc649e1431. Earlier runs have their own original runtime identities in the ledger; not all120 ran on one binary. `results/e2/` reuses unmodified blobs from final report3484f3de388df63ea1a758dfd6ff4cfa545b2333.

This **packaging commit is not a new authorized runtime Head**. Source ZIPs do not contain Git history, model weights, LIBERO assets or private originals. They cannot bypass exact-head grants. Do not rerun consumed E2 IDs. Independent E2 R3 review and owner identity/course-policy confirmation remain separate from document formatting.

E3 Gate P is now approved under R016: full160 selected, CPU scientific freeze and preparation allowed. E3 model/TEST remains unauthorized until a separate final exact-head Gate C grant plus current owner GPU1 allocation. E3 outcomes are not pooled into E2.

Old bootstrap status and proposed geometric architecture are retained under `docs/history/`; they are not the current implemented mechanism. Historical review/work-package files elsewhere remain unchanged. No old PR is automatically merged. Final Canvas submission is by the owner, before6 November2026 23:59 Singapore time.
