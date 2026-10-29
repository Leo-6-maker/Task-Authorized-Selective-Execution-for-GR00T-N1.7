"""CPU-only physical GPU1 routing checks; never creates a CUDA context."""
import subprocess
from .discovery import require
from tase.resource_memory import require_free_memory


def binding(record, env):
    require(type(record.get('gpu_index')) is int and record['gpu_index'] == 1,
            'E3 requires physical GPU1; no GPU0 fallback')
    require(isinstance(record.get('gpu_uuid'), str) and bool(record['gpu_uuid']),
            'GPU1 UUID required')
    require(env.get('CUDA_VISIBLE_DEVICES') == record['gpu_uuid'] and
            env.get('MUJOCO_EGL_DEVICE_ID') == '1' and
            env.get('MUJOCO_GL') == 'egl' and env.get('PYOPENGL_PLATFORM') == 'egl',
            'E3 GPU1 UUID/EGL environment binding differs')


def live_gpu1(record):
    require(type(record.get('gpu_index')) is int and record['gpu_index'] == 1,
            'E3 requires physical GPU1; no GPU0 fallback')
    inventory = subprocess.check_output([
        'nvidia-smi', '--query-gpu=index,uuid,memory.free',
        '--format=csv,noheader,nounits'], text=True)
    rows = [tuple(v.strip() for v in row.split(','))
            for row in inventory.splitlines() if row.strip()]
    require(all(len(row) == 3 for row in rows), 'invalid GPU inventory')
    selected = [row for row in rows if row[0] == '1']
    require(len(selected) == 1, 'exactly one physical GPU1 required')
    _, uuid, free_mib = selected[0]
    require(uuid == record.get('gpu_uuid'), 'allocated GPU UUID differs')
    free = int(free_mib)*1024**2
    require_free_memory(free)
    return dict(gpu_index=1, gpu_uuid=uuid, egl_device_id='1',
                sampled_free_bytes=free)
