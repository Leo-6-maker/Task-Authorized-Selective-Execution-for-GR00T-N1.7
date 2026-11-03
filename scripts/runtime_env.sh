#!/usr/bin/env bash
# Source this file after setting the task-owned workspace and allocated device.
set -euo pipefail
: "${TASE_WORKSPACE:?set the isolated absolute workspace}"
: "${TASE_GPU_UUID:?set the authorized physical GPU UUID}"
: "${TASE_EGL_DEVICE_ID:?set and verify the EGL physical-device index}"
test -d "$TASE_WORKSPACE/runtime/home"
TASE_REPO="$TASE_WORKSPACE/course-repo"
TASE_UPSTREAM="$TASE_WORKSPACE/upstream/Isaac-GR00T"
export HOME="$TASE_WORKSPACE/runtime/home"
export LIBERO_CONFIG_PATH="$TASE_WORKSPACE/runtime/libero-config"
export XDG_CACHE_HOME="$TASE_WORKSPACE/cache"
export HF_HOME="$TASE_WORKSPACE/cache/huggingface"
export UV_CACHE_DIR="$TASE_WORKSPACE/cache/uv"
export PYTHONPATH="$TASE_REPO:$TASE_UPSTREAM"
export PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES="$TASE_GPU_UUID"
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export MUJOCO_EGL_DEVICE_ID="$TASE_EGL_DEVICE_ID"
export WANDB_MODE=disabled
export WANDB_DISABLED=true
export HF_HUB_DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
export NO_ALBUMENTATIONS_UPDATE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=2
export NUMBA_NUM_THREADS=2
