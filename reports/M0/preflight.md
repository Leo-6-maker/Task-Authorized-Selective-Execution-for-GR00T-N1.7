# M0 execution report

- Author role: Codex executor; protocol: TASE-001 v1.0; issue: #2.
- Handoff status: **READY_FOR_REVIEW**, with a gated-backbone access blocker. This is not GPT approval.
- Starting main: `2edd62f8b3bb06784dac7bf4fa47f5d07d4bff4f`.
- Provisioning implementation subsequently committed as `bc5c1279ecf15267e33a207ced74388212d166a1`; exact operator script bytes are retained privately. Provisioning began before that commit and is labelled exploratory bootstrap, not a clean-commit scientific experiment.
- Captured runtime identity commit: `64ade726bb264b1557c9827273cc1941acd16ee5`.
- Runtime lock: [configs/runtime_lock.json](../../configs/runtime_lock.json), SHA-256 `9783e72f673626aba84c2ac63bf40db4247e6cad98ec73e1a21215c0dd80fcb2`.
- Execution date: 2026-10-21, Asia/Singapore; machine receipts cover approximately 18:13–18:39 SGT.
- Resource authorization: direct owner instruction permits shared inference when VRAM is sufficient. Later owner instruction requests submission with the access blocker and no further GPU attempts.

## Scope and resource evidence

Only M0–M1 native LIBERO work was attempted. No WBC, training, shadow, Gate, CALIB, TEST or physical robot execution occurred.

Three reachable GPU resources were inspected. The selected resource reported a 32760 MiB GPU with approximately 21 GiB free, alongside active existing workloads; other inspected 16 GB GPUs had less free VRAM, and one resource had insufficient disk capacity. No existing process was stopped. Public preflight captures are [initial selected-resource state](../M1/evidence/preflight-shared-authorized.json) and [final state](../M1/evidence/preflight-final.json). These read-only inventories do not constitute an exclusive reservation.

An independent task-owned directory contains upstream source, two virtual environments, isolated HOME/LIBERO configuration, caches, checkpoints and raw runs. Internal paths and resource identifiers are intentionally absent from this repository. The final private inventory found no remaining task server/downloader/installer process. Final workspace logical size, including installer cache, was 32,894,533,233 bytes; this is not a physical disk-space or quota claim.

## Source and installation identity

| Component | Actual identity / result |
|---|---|
| GR00T | `dac54b313160c201c450f97df0fd74ebd379c892` |
| LIBERO submodule | `8f1084e3132a39270c3a13ebe37270a43ece2a01` |
| Object model | `nvidia/GR00T-N1.7-LIBERO@2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21`, suite `libero_object` |
| Model files | Seven explicit inference files; both LFS weight hashes match the upstream metadata; all file sizes and local SHA-256 recorded |
| Server | Python 3.12.14; torch 2.9.0+cu128; torchvision 0.24.0+cu128; transformers 4.57.3 |
| Simulator | Python 3.12.14; torch 2.9.0; robosuite 1.4.0; MuJoCo 3.3.1; numpy 1.26.4; gymnasium 0.29.1 |
| Dependency checks after repair | Server: 138 packages compatible; simulator: 159 packages compatible |

The full dependency inventory and relevant source hashes are in the runtime lock. Object inference files total 6,914,934,198 bytes. No optimizer state or training dataset was downloaded.

The audited upstream setup deletes its simulator environment and `$HOME/.libero`. [prepare_runtime.py](../../scripts/prepare_runtime.py) requires task-contained paths, replaces environment deletion with a fresh-directory assertion, and omits user-configuration deletion plus final EGL smoke. The generated setup SHA-256 is `c5dfcb308e86d4c4c336b8189264d1a25cbc9682299b80588612361307bd1c94`; the exact diff is a private artifact. LIBERO configuration was generated separately in the isolated configuration directory. Tracking was disabled for the project processes; no external telemetry service was invoked.

## Actual commands and exit status

Paths below are redacted placeholders for the private task workspace, upstream checkout and user-level installer. Full private command bytes, stdout and stderr are retained and hashed in the manifest. [Operation receipts](operations.json) preserve launcher status and elapsed time.

| Command / operation | Exit status and result |
|---|---|
| Pinned sparse upstream checkout and LIBERO submodule initialization | 0 |
| `python scripts/prepare_runtime.py --root "$WORKSPACE" --uv "$UV" --stage server` | 0; upstream `uv sync --frozen --no-dev`, 388.11 s |
| Corresponding `--stage sim` | 0; dependency setup 685.39 s; later dependency check found three conflicts |
| `uv run --no-project --with huggingface-hub python scripts/download_model.py --destination "$WORKSPACE/checkpoints"` | 0; operator duration 509.42 s, including isolated tool bootstrap |
| Initial source helper audit plus server CLI help | Helper audit passed, but combined operation exited 2 because the help path used the wrong working directory; corrected help later exited 0 |
| Official server `--help` using absolute upstream path | 0 |
| `python -m tase.server ...` | **Model loading failed with HTTP 401**; original background launcher exited 0, but did not capture child exit code. Child exit status is explicitly NOT_CAPTURED, not inferred from launcher success |
| Initial simulator `uv pip check` | Three conflicts reported; wrapper suppressed its exit code, so exact initial check status is NOT_CAPTURED |
| `uv pip install --python "$SIM_PY" -c configs/sim_constraints.txt opencv-python-headless==4.10.0.84 tifffile==2024.8.30 pettingzoo==1.24.3` | 0 |
| Both post-repair `uv pip check` commands | 0 |
| `python -m unittest discover -s tests -v` | 8 passed locally and 8 passed on the remote resource, exit 0; CPU integrity/scope tests only |

## Retained failures and repairs

1. The first environment probe failed because the pinned LIBERO helper calls `torch.load` without adapting to PyTorch's restricted-loading default. The runner now uses `weights_only=True` with a scoped allowlist of the NumPy array/dtype types used by the official initialization files. It does not globally disable restricted loading. The original failed attempt remains `dev-env-001`.
2. Upstream setup initially resolved incompatible headless OpenCV, tifffile and PettingZoo versions. [sim_constraints.txt](../../configs/sim_constraints.txt) records the targeted compatibility repair; both final environment checks passed.
3. An unquoted upstream Python heredoc contains backticks around `imp` in a comment, causing a nonfatal `imp: command not found` shell diagnostic. The original installer stderr is retained. It did not prevent setup from returning 0; the diagnostic is not silently removed from evidence.
4. One local operator command had a quoting failure before remote execution. A source lookup initially used the wrong wrapper directory and returned 404. These operator failures are included separately from the episode ledger.
5. Native model construction attempts to fetch gated `nvidia/Cosmos-Reason2-2B/config.json`; the request returned 401. Standard credential locations had no token; only presence was checked, with no credential values printed. There was no fallback model, borrowed research checkpoint or bypass of access controls.

## Remaining blocker and requested review

Object weights being public does **not** make this complete runtime anonymously usable: this source/model combination also loads the gated VLM backbone. Owner-side access and isolated authentication are required before another genuine model-load attempt. Auxiliary model revision and its loaded files remain unverified.

Request GPT R1 review of the delivered evidence and a targeted M0/M1 continuation after access is provided. Do not approve M2–M3 based on environment probes alone. A future server launch must capture the actual child exit status; this delivery explicitly retains the first launcher's observability limitation.
