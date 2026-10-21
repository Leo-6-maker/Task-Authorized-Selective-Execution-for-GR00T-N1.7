# M1 native runtime contract — continuation evidence

Author: Codex executor. TASE-001 v1.0. READY_FOR_REVIEW; independent R1 pending. See [report](continuation_report.md), [lock](../../configs/runtime_lock_resume.json) and [CPU raw-data audit](evidence/resume-summary.json).

| Contract | Actual evidence / limit |
|---|---|
| Object policy | Official Object-adapted weights, processor, statistics and LIBERO_PANDA; exact hashes in lock; native Gr00tPolicy + Gr00tSimPolicyWrapper, eval BF16 |
| Auxiliary model | Fixed Cosmos snapshot, local identifier resolution, offline loading; original files, no patched backbone |
| Images | Front + wrist, uint8 `[1,1,256,256,3]`; official two-axis image flip retained |
| State | Six scalar pose streams plus two finger positions, float32; seven streams / eight values; rotation fields carry native axis-angle, not Euler |
| Batching | Installed native Gymnasium declared-space concatenate/create_empty_array, as used by SyncVectorEnv; failed float64 request 006 is retained |
| Language | Native task instruction; no privileged object state added to policy inputs |
| Output | Seven float32 `[1,16,1]` streams; all 181 forwards checked finite |
| Horizon/history | Native PolicyHorizonSpec: action 16, executed prefix up to 8, video/state offsets `[0]`; architecture horizon 40 is a different layer |
| Action path | Official MultiStepWrapper → LiberoEnv → native OSC_POSE; exactly one binarize/invert gripper mapping `-sign(2*g-1)`; all 1,438 control inputs recomputed from saved raw policy chunks |
| Control | Native delta OSC_POSE, 20 simulation Hz, translation output ±0.05, rotation ±0.5, kp 150; no WBC or custom action decoding |
| Termination | Official success (may end within an eight-action chunk), otherwise 720 policy steps. Official wrapper marks time cap through done=true while truncated=false; the runner classifies the unsuccessful fixed-limit episode as TIME_LIMIT |
| Fixed DEV initialization | Each task's pinned BDDL/pruned_init index 0 or 1, seed 640101, ten raw open-gripper settling steps; arrays, scene XML, settled state hashed |
| Reset parity | Six complete runs: supplying settled observation to native wrapper reset leaves simulator state unchanged and all latest native image/state/language streams equal; official history logic retained |
| Repeat initialization | Alphabet soup 006/007 matches prior 002/003 init/scene/settled-state hashes; cream cheese 009 and ketchup 011 match their prior init-0 probes. This is fixed-reset evidence, not shadow/snapshot round-trip evidence |
| RNG | Server Torch seed 640100 once at startup; requests ordered and bound to run IDs; client reset does not reseed; no identical-action replay claim |
| Success scope | Alphabet soup 2/2, cream cheese 2/2, ketchup 1/2; six predeclared DEV cells. No TEST, governance or safety effectiveness claim |

Private records include native object catalogs (objects_of_interest is not the whole scene), raw observations and full 16-step model chunks, converted controller inputs, native states, dual-view videos, terminal decisions and process exit receipts. The executor audit checks hashes and arrays; independent private-content review remains NOT_VERIFIED without access.
