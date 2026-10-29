# Reproduction and verification levels

## Level 1 — understand/recount the public results (no GPU)

Use root README commands for `tools/recheck_e2.py`. Python standard library only. The ledger is reused as the exact original Git blob; the helper rejects edited bytes, incomplete IDs, altered outcomes and design/count mismatches. The output is descriptive recounting of the public ledger, not private-raw verification. The original full statistical output is `results/e2/final_frozen_audit.json`; this helper does not replace its task-stratified paired bootstrap.

The helper's five synthetic bound cases passed locally in ordinary and optimized Python3.13.5. The entire real120 ledger was not newly executed through this helper during packaging; a result of that command must not be fabricated. Full report/table values are source-derived. Original implementation and report evidence remain inspectable.

## Level 2 — CPU implementation tests

Original reference environment: Linux/Python3.12.14; minimal NumPy1.26.4. Use `requirements-cpu.txt` and root README commands. Existing tests include real CPU subprocess fixtures, Git identity, signals, sockets and `/proc` process checks. They are not model or physics tests. A restricted container can block valid integration checks; retain actual failures. Historical134/134 executor receipts are not a new reviewer rerun.

R016 independently tested exact ReactiveGate/contact-scoring source with explicit TaskSpec/discovery test doubles:10 cases ordinary and10 optimized, actual exits0. This is a narrower rule-level test, not the E3 full187 suite or native equivalence proof.

## Level 3 — native model and simulator (not a turnkey offline ZIP)

The actual experiment used separately pinned model/server and simulator environments, fixed upstream GR00T/LIBERO sources, Object/Cosmos weights and official assets. The controlling inventory is `configs/runtime_lock_E2.json`; `configs/sim_constraints.txt` lists compatibility repairs, NOT a complete model installation recipe. Read `scripts/prepare_runtime.py` and historical execution documentation before any installation. Do not blindly execute upstream setup scripts in a shared environment.

For an authorized operator with the original Git repository, `git checkout --detach 79510d9a302eeb7820f7ed35463c29bc649e1431` recovers the final E2 runtime source, NOT permission to repeat its consumed experiments. Native server/test entry points require matching current-main exact-head grants, real allocation records and an appropriate initialized workspace. The submission ZIP deliberately includes no machine grant override, credentials, weights, assets or private snapshots. Preserve fail-closed checks; do not change them to make the ZIP run.

All original120 E2 IDs are consumed. Any new replication study needs its own approved protocol and IDs; do not replay, renumber or overwrite original data. This formal source tree is for assessment and offline inspection, not a new runtime authorization.

## What this edition actually verifies

Exact original module-tree/evidence-blob reuse; source inspection; narrow synthetic rule tests; five new bound-helper tests; editable17-page deck, PDF conversion and rendered layout. No new model/MuJoCo/TEST, no full private-original rehash, no current GPU measurement, no completed R3 result approval and no Canvas submission are asserted.
