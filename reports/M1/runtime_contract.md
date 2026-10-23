# M1 runtime contract — partial evidence

Author: Codex executor. Protocol: TASE-001 v1.0. Status: **READY_FOR_REVIEW / POLICY_RUNTIME_NOT_VALIDATED**. Runtime lock and its SHA-256 are linked in the [M0 report](../M0/preflight.md). No GPT stage approval is asserted.

## Provenance and validation levels

Environment probes ran from commits `3e5bfeb379239fa9c372d0b6ccd236a8025c5afd`, `577d05b181449f9fc1581982cf7dca0dc6590a76` and `871dbb37274a3cb29dc2951a2d5608ab2000ae1d`; each attempt records its exact code/config identity. The initial probe failed and is retained. Successful probes reset the real native LIBERO/Panda simulator, load a declared official DEV initialization and execute ten explicit raw initialization steps. They do not execute model actions.

| Contract element | Evidence | Validation level |
|---|---|---|
| Front/wrist images | `video.image`, `video.wrist_image`; actual `(256,256,3)`, uint8; real PNGs visually inspected | RUNTIME_VALIDATED for reset/settling |
| Image direction | Native wrapper flips both spatial axes with `[::-1, ::-1]`; previews preserved privately | SOURCE_VERIFIED plus visual inspection |
| State | Six scalar pose streams plus two finger positions: seven streams, **8 continuous values** | RUNTIME_VALIDATED for reset/settling |
| Pose rotation | Fields named roll/pitch/yaw contain quaternion-to-axis-angle output, not ordinary Euler angles | SOURCE_VERIFIED |
| Language | Official task language, unchanged; no object ground truth added to policy input | Native reset metadata recorded; policy input NOT_RUN |
| Controller | OSC_POSE, delta mode; six control coordinates, kp=150, input [-1,1], translation scaling ±0.05, rotation scaling ±0.5 | Actual controller attributes recorded |
| Control frequency | 20 Hz | Actual native environment attribute |
| Renderer/device | NVIDIA renderer; own EGL process observed on selected physical GPU index 0 in probes 003–005 | RUNTIME_VALIDATED |
| Model architecture horizon | Checkpoint config contains 40 | SOURCE/FILE_VERIFIED only |
| LIBERO modality offsets | Processor has offsets 0–15, seven action streams | SOURCE/FILE_VERIFIED only |
| Actual policy output horizon/shape | No successful model load or request | **NOT_VERIFIED** |
| Execution prefix | Candidate H_e=8; resolver uses official PolicyHorizonSpec | IMPLEMENTED, policy execution NOT_RUN |
| Native gripper mapping | Official helpers produce policy 0→raw +1, 0.5→raw 0, 1→raw -1; source helpers actually executed on CPU | SOURCE_HELPERS_EXECUTED; full model-to-controller trace NOT_RUN |
| Complete policy episode / parity | No successful model forward | **NOT_RUN** |

Measured schemas and controller attributes are in [evidence](evidence/). The state values' physical interpretation follows the pinned wrapper/controller; raw action.x must not be interpreted directly as metres without the controller scaling. Gripper opening/closing direction is source-backed; successful model control of it has not been demonstrated.

## Initialization contract

The three declared tasks use their own native BDDL and official `pruned_init` file, not a shared synthetic scene. Only DEV initialization index 0 was executed in this delivery; index 1 policy cells remain NOT_RUN. Native files are read with the restricted loader compatibility adapter. No seed was selected for policy success.

Native reset is followed by explicit fixed-state loading and ten settling steps with raw `[0,0,0,0,0,0,-1]` (open gripper). These are initialization actions, not a HOLD/REPLAN policy or a governance intervention. Forty such settling steps occurred across four successful probes, separately from zero policy execution steps.

The single-environment adapter supplies the already-settled observation to official MultiStepWrapper reset/history initialization, then would use the official native wrapper and controller unchanged. This adapter's reset behavior differs from the upstream vector runner. Its action/history parity remains **NOT_VERIFIED** because the gated model could not be loaded. It must be validated before treating policy episodes as qualified baseline evidence.

Alphabet-soup probes 002 and 003 independently produced identical:

- initialization array SHA-256: `34350cbaada02949b397a75286eb1f8b4034bee665ed29e4fc3ba1229b4455f2`;
- scene XML SHA-256: `67343e48219418a95042ae9d55d1c9ca23ec784815c811c8202eac86889628f9`;
- settled state SHA-256: `fb092b3673f4a74898a2019f082017066d53b5ab56ff696264cedec4c4b67bb1`.

This supports repeatable reset/settling for that tested initialization. It does not prove complete shadow snapshots, hidden-controller restoration, deterministic policy actions, all tasks/initializations, or test-split independence.

## Native object inventory

Actual object catalogs are recorded per task. `objects_of_interest` contains the target and basket; it is **not** the complete list of scene objects. For alphabet soup the full catalog also contains salad dressing, cream cheese, milk, tomato sauce and butter. The other task catalogs are independently captured. No common distractor list or Gate TaskSpec was invented in M1.

## Stop and continuation boundary

The owner requested submission with the gated-backbone blocker. Budget consumed: 5/24, including the failed initialization probe; 19 remain under the original cap. No further GPU attempts will be made as part of this handoff. Future continuation must verify access, the exact auxiliary model revision, complete policy shapes, action conversion exactly once, actual execution counts, full episodes and repeat success on at least two tasks and more than one DEV initialization. Shadow/oracle/Gate work remains outside this delivery.
