# Task-Authorized Selective Execution for GR00T N1.7

## Final ME6401 coursework edition — E2 + E3, 2 November 2026

**RESULTS FROZEN. No new experiment, model, simulator, Shadow, TEST reservation, replacement ID, training or WBC work is authorized.** This repository is the independent ME6401 course project, not GR00T+WBC.

The project implements an execution-boundary guardrail for a frozen GR00T N1.7 policy in native LIBERO/Panda simulation. Independent trusted task identity defines the authorized object. An isolated short rollout checks each candidate prefix before execution; ACCEPT executes the checked prefix unchanged, whereas REJECT or ERROR withholds it and terminates the autonomous episode.

### Start here

| Purpose | File / directory |
|---|---|
| Owner-directed result freeze | `docs/releases/ME6401-E2-E3-RESULTS-FREEZE-20261102.json` |
| Architecture and implemented scope | `docs/ARCHITECTURE.md` |
| Reproduction levels and honest limits | `docs/REPRODUCTION.md` |
| Exact source/result identities | `SOURCE_PROVENANCE.json` |
| E2 immutable public results | `results/e2/` |
| E3 full160 public results and receipts | `reports/E3/FINAL_160_20261102/` |
| E3 independent review scope | `docs/reviews/R020-E3-R3-PUBLIC-RESULT-SCIENTIFIC-REVIEW.json` |
| Final presentation build source | `submission/build_final_deck.py` |
| Submission instructions | `submission/README.md`, `docs/SUBMISSION_CHECKLIST.md` |
| ZIP-friendly offline verifier | `tools/verify_release.py` |

### Main code

`tase/` contains task identity, contact scoring, action boundary, Shadow state isolation and actual-event Oracle. `e3/` contains the reactive comparator, native runner, source/resource admission, ledger, physics audit, 4/6-cell checkpoints and frozen statistics. `operator_engineering/` is the external continuation/custody layer. `scripts/`, `configs/` and `tests/` preserve the executed implementation and its tests. `review_tools/` contains the original E3 export checker; `tools/verify_release.py` is a new submission-only entry point.

The runtime/analysis trees are reused by exact Git object identity from E3 report `36dacd6bcc06dab534330758dcf5708209ffdad8`. No frozen code or scientific configuration is changed by this release. This packaging commit is **not** the native execution Head and carries no permission to execute consumed experiments.

### Frozen results — keep the studies separate

| Study | Planned / consumed | Eligible | Unknown | Status inventory |
|---|---:|---:|---:|---|
| E2 |120|117|3|89 SUCCESS,18 TIME_LIMIT,10 SEMANTIC_ABORT,3 CLEANUP_ERROR|
| E3-A |112|112|0|78 SUCCESS,20 TIME_LIMIT,14 SEMANTIC_ABORT|
| E3-B |48|48|0|36 SUCCESS,4 TIME_LIMIT,8 SEMANTIC_ABORT|

Under controlled instruction mismatch C2, E2 B0 has10/30 wrong lifts; G has0 observed among29 complete outcomes, with all-planned bound0–1/30. E3-A has B0 14/28 versus G0/28; E3-B has B0 4/8, A0 3/8 and G0/8. E3-A risk-positive cases span4/7 additional tasks. In E3-B, predictive G stops before baseline onset in4/4 positive pairs, whereas this specific current-streak A0 does so in1/4.

The results support bounded interruption of unauthorized manipulation, not task recovery or universal safety. E3 C2 official success is unchanged across arms (A11/28; B4/8). In E3 C0, all arms succeed with no observed wrong lifts or rejects, but zero observed events are not zero population risk. E3 paired bootstrap uses2000 task-stratified init-cluster resamples/seed641500 and only four inits per fixed task; degenerate intervals are not certainty. E2 uses its own frozen seed640500 and censoring. No pooled E2/E3 rate, natural OOD, unseen-pretraining task, hardware safety or hard20Hz claim is made.

### Offline use after extracting the source ZIP

Python3.10+ standard library is sufficient for the basic public-result recount; the reference native environment was Linux/Python3.12.14.

```bash
python tools/verify_release.py --self-test
python -O tools/verify_release.py --self-test
python tools/verify_release.py --repo .
```

For the existing E3 export/paired-bootstrap checks without Git history:

```bash
python -m pip install -r requirements-offline.txt
python tools/verify_release.py --repo . --full-e3 --output new-offline-check.json
```

The output path must be new; outputs are not written over originals. These commands read public exports and never execute a model or simulator. They do not authenticate private raw trajectories or reconstruct historical runtime permissions. The original `python -m review_tools.recheck_e3_final ...` additionally requires historical Git objects and should be run from the full repository, not assumed to work in a history-free ZIP.

### Rebuild the editable presentation

```bash
python -m pip install -r submission/requirements-docs.txt
python submission/build_final_deck.py --output ME6401_TASE_Final_E2E3.pptx
```

The deck contains one cover,15 content slides and one reference slide. Delivered PPTX/PDF binaries are conversation attachments; this source edition contains the exact builder and artifact checksums, not an asserted binary attachment. Fill the student name/ID in the PPTX and re-export the PDF before Canvas. The owner must confirm applicable AI-assistance policy. The two course deliverables are a PPTX/PDF and the source ZIP; the document bundle alone is not the source ZIP.

### Verification and authority boundaries

E3 R020 is a qualified independent **public-evidence** review. Private raw-file/member validation remains executor-attested. E2 independent R3 remains separately pending; this packaging change does not close it. Historical E3 0001 remains859e40/R017/GPU1 with old audit failures1/1 and a separate accepted reconciliation. The other159 used source-locked GPU0 under recorded Owner-direct permission, not independent GPT runtime approval. All historical failures and source identities are retained.

The new helper's five synthetic cases passed normal and optimized Python during packaging. All17 final presentation pages were rendered and visually checked. The entire new ZIP and full original runtime/physics suites were **not** executed locally in this packaging session; no such receipt is fabricated. See `submission/ARTIFACTS.json` and `submission/QA.json`.

E2-only PR38 remains an unchanged fallback. Final integration PRs are not automatically merged. Deadline:6 November2026,23:59Singapore time. No Canvas upload has been performed.
