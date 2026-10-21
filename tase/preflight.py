"""Read-only, sanitized Linux resource inventory; does not create a GPU context."""
import argparse
import csv
import io
import json
import platform
from pathlib import Path
import shutil
import subprocess
from .evidence import now_sgt, write_json


def inspect(workspace):
    command = ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu,driver_version',
               '--format=csv,noheader,nounits']
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError('nvidia-smi failed; retain private stderr')
    gpus = []
    for row in csv.reader(io.StringIO(result.stdout)):
        index, name, total, used, load, driver = [x.strip() for x in row]
        gpus.append(dict(index=int(index), name=name, total_mib=int(total),
                         used_mib=int(used), free_mib=int(total)-int(used),
                         utilization_percent=int(load), driver=driver))
    disk = shutil.disk_usage(workspace)
    return dict(captured_at_sgt=now_sgt(), os=platform.system(), kernel=platform.release(),
                python=platform.python_version(), gpus=gpus,
                disk_total_bytes=disk.total, disk_free_bytes=disk.free,
                egl_vendors=sorted(p.name for p in Path('/usr/share/glvnd/egl_vendor.d').glob('*.json')),
                gpu_context_created=False, allocation_claim='NOT_ESTABLISHED_BY_PREFLIGHT')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    record = inspect(a.workspace)
    write_json(a.output, record)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
