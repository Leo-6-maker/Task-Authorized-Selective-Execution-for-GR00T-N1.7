"""CPU-only, source-locked physical GPU routing; no implicit device fallback."""
import json
from pathlib import Path
import subprocess
from .discovery import require
from tase.resource_memory import (require_free_memory, MINIMUM_FREE_BYTES,
                                 MAXIMUM_PROCESS_FRACTION, RESERVED_FREE_BYTES)


def configured_index():
    route = json.loads((Path(__file__).resolve().parents[1]/
                        'configs/e3_gpu_resource.json').read_text())
    index = route.get('physical_gpu_index')
    require(type(index) is int and index in [0, 1], 'explicit physical GPU0 or GPU1 required')
    require(route == dict(schema='E3_GPU_RESOURCE_ROUTE_V1', physical_gpu_index=index,
                         automatic_fallback=False, minimum_free_bytes=MINIMUM_FREE_BYTES,
                         maximum_process_fraction=MAXIMUM_PROCESS_FRACTION,
                         reserved_free_bytes=RESERVED_FREE_BYTES),
            'resource route must retain fixed admission and allocator limits')
    return index


def selected_index(record):
    index = configured_index()
    require(type(record.get('gpu_index')) is int and record['gpu_index'] == index,
            'E3 allocation differs from source-locked GPU route; no fallback')
    return index


def binding(record, env):
    index = selected_index(record)
    require(isinstance(record.get('gpu_uuid'), str) and bool(record['gpu_uuid']),
            'allocated GPU UUID required')
    require(env.get('CUDA_VISIBLE_DEVICES') == record['gpu_uuid'] and
            env.get('MUJOCO_EGL_DEVICE_ID') == str(index) and
            env.get('MUJOCO_GL') == 'egl' and env.get('PYOPENGL_PLATFORM') == 'egl',
            'E3 allocated GPU UUID/EGL environment binding differs')


def live_gpu(record):
    index = selected_index(record)
    inventory = subprocess.check_output([
        'nvidia-smi', '--query-gpu=index,uuid,memory.free',
        '--format=csv,noheader,nounits'], text=True)
    rows = [tuple(v.strip() for v in row.split(','))
            for row in inventory.splitlines() if row.strip()]
    require(all(len(row) == 3 for row in rows), 'invalid GPU inventory')
    selected = [row for row in rows if row[0] == str(index)]
    require(len(selected) == 1, 'exactly one allocated physical GPU required')
    _, uuid, free_mib = selected[0]
    require(uuid == record.get('gpu_uuid'), 'allocated GPU UUID differs')
    free = int(free_mib)*1024**2
    require_free_memory(free)
    return dict(gpu_index=index, gpu_uuid=uuid, egl_device_id=str(index),
                sampled_free_bytes=free)
