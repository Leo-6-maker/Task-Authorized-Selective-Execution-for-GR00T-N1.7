# M2 native snapshot contract — implementation before runtime

Protocol TASE-001 v1.0; authority R002 / Issue #4. Parent PR #3 head `3e214c0b761d0639bf73948356a92a03bf2ddedc`. This initial contract is IMPLEMENTED/CPU_TESTED, not a physics PASS. Runtime evidence will be appended separately.

| State group | Actual capture/restore method |
|---|---|
| Physical integration | MuJoCo `mj_getState/mj_setState` with `mjSTATE_INTEGRATION`; complete size from the installed library, including time, generalized state, warm-start/control/applied-force/mocap/user/plugin integration fields represented by that spec |
| Derived physics | `mj_forward` on clone only, then reapply integration state before restoring caches; stepwise trajectory/contacts must validate equivalence |
| Model identity | Exact native compiled XML SHA-256; clone must match before restore |
| Controller | All actual controller dictionary fields except its simulator reference, including goals, gains, Jacobian/mass/state caches, update flag, transforms and interpolator state when present; unknown opaque field fails |
| Robot | Native numerical/scalar fields and DeltaBuffer/RingBuffer contents; robot-model, gripper/controller objects and controller-construction config remain independently constructed references |
| Gripper | Native `current_action` plus robot finger state and full physics actuator state |
| Environment | Numerical/scalar fields, time/timestep/done, observation cache and per-observable sample/delay/current-value state; per-field inventory is retained |
| Task state | Per-object/site state fields; references to each clone's own environment and object-model query dictionary remain native |
| Wrapper | Deep-copied observation history, rewards, done history, info deques and maximum lengths; pre-action prefix progress is zero, source control count explicit |
| Oracle | Stable initial heights, prior relative poses, grasp/lift counters, last global control step and sticky first violation |
| RNG | Main NumPy/Python/Torch CPU state in snapshot; independent worker process gets restored copies; server Torch CPU/CUDA RNG is queried by a read-only fingerprint endpoint and must be unchanged across shadow |

Static construction references are explicitly listed in `tase/snapshot.py` and each captured field inventory. XML/asset graphs, renderer objects, initialization placement samplers, robot/model objects and native sensor callback functions are not serialized into another simulator. They are reconstructed from the same fixed source/scene. This assumes no model/asset/controller reconfiguration during the declared native Object episode; failure to cover a live mutable field is a validation failure, not a reason to loosen tolerances. Unsupported fields fail rather than being silently omitted.

The shadow worker has no policy object or network endpoint. It creates one independent native environment, performs one explicit reset and ten settling steps, then restores snapshots without historical action replay. Each construction/reset/settling operation is recorded with the first shadow case. Physics predictions consume only the same native maximum-eight-step prefix and honor native success and wrapper limits. Two independent source/clone copies must not share mutable arrays.

Predeclared `configs/m2_validation.json` sets position 1e-5 m, SO(3) 1e-4 rad and finger 1e-6 m tolerances, exact actions/step counts/contact/event/termination outcomes, three restores per snapshot, maximum 24 selected snapshots and 80 total shadow attempts. C0 decision indices are 0/3/6/9/12/15; C2 indices 6/9/89 (global cap applies in acquisition order). At most one extra direct always-accept reference is added in each contact/no-contact category. Boundary evidence includes pre-time-limit states and prefixes ending early on official success. Missing strata must be reported.

`configs/m2_dev_cells.json` predeclares three native C0 and three controlled instruction-mismatch C2 acquisitions, all initialization 0, at most six total. C2 changes only policy text; actual TaskSpec/BDDL/authorized target stay original. Main execution always accepts; no Gate rejection, threshold search or formal TEST is implemented.
