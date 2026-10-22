# Native always-accept / shadow noninterference

Executor evidence, TASE-001 v1.0. Runtime SHA `16f0249299a11805666f68eb06c09c8f3974efef`; [handoff](runtime_report.md).

All 74 live cases retain equal complete main-state hashes before and after the independent worker. These cover integration time/state, controller/cache/buffer fields, wrapper history/counters, event sustain state and client-process RNG. Independent process IPC serializes copies; CPU tests also verify array isolation.

The worker receives only task/init, horizon, snapshot and saved prefix. It has no policy endpoint/object. The server records 148 read-only RNG queries: each CPU/CUDA fingerprint and model-call count pair is equal and matches the source decision/request index. All 249 model requests reconcile to the six source runs; extra requests attributable to shadow are zero.

Every snapshot has at least three independently restored predictions through the official native wrapper/controller. Each executes at most eight actions with one gripper conversion. Three cases stop after seven actions on official success; the fixed 720-step boundary is also reproduced. Pose/finger/contact/oracle-onset/termination comparisons pass with recorded numeric maximum errors zero.

Two extra direct reference cases cover contact/no-contact always accept. Every main path executes its original prefix after prediction; no rejection exists. M1 dev-policy-007 and M2 dev-m2-013 additionally have exactly equal 141-step native states and converted controls. This single measured pairing does not freeze future B0/G RNG semantics; server seeding remains session-scoped.

The actual installed wrapper is checked in normal/-O CPU mode with a labeled synthetic env: changing unexecuted actions 8–15 leaves consumed actions 0–7 identical; a done condition at step three executes three controls. No real physics/model or budgeted acquisition is hidden in this test.

Completeness is conditional on the pinned Object contract and its inventoried static references. Twenty-four states do not prove arbitrary model/controller reconfiguration or unseen contacts. Executor raw recomputation passes; independent private-content inspection remains pending.
