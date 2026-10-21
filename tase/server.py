"""Instrument the pinned native GR00T policy; bind only to localhost."""
import argparse
import json
import time
from pathlib import Path
from .evidence import append_json, now_sgt, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=5558)
    p.add_argument('--policy-seed', type=int, default=640100)
    p.add_argument('--allocation-record', type=Path, required=True)
    a = p.parse_args()
    permission = json.loads(a.allocation_record.read_text())
    if not permission.get('shared_gpu_inference_authorized'):
        raise ValueError('GPU inference allocation is not authorized')
    a.output.mkdir(parents=True, exist_ok=False)
    import torch
    from gr00t.policy.gr00t_policy import Gr00tPolicy, Gr00tSimPolicyWrapper
    from gr00t.policy.server_client import PolicyServer
    torch.manual_seed(a.policy_seed)
    torch.cuda.manual_seed_all(a.policy_seed)
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    policy = Gr00tSimPolicyWrapper(Gr00tPolicy(
        embodiment_tag='LIBERO_PANDA', model_path=str(a.model), device='cuda:0'))
    torch.cuda.synchronize()
    write_json(a.output / 'loaded.json', {
        'status': 'MODEL_LOADED', 'started_at_sgt': now_sgt(),
        'load_seconds': time.perf_counter()-start, 'policy_seed': a.policy_seed,
        'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
        'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
        'device_name': torch.cuda.get_device_name(0), 'dtype': 'bfloat16',
        'mode': 'eval/no_training', 'host': '127.0.0.1', 'port': a.port})
    original = policy.get_action
    calls = 0

    def measured(observation, options=None):
        nonlocal calls
        calls += 1
        torch.cuda.synchronize()
        start = time.perf_counter()
        result = original(observation, options)
        torch.cuda.synchronize()
        append_json(a.output / 'inference.jsonl', {
            'request': calls, 'inference_ms': (time.perf_counter()-start)*1000,
            'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
            'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
            'output_shapes': {k: list(v.shape) for k, v in result[0].items()}})
        return result

    policy.get_action = measured
    with PolicyServer(policy, host='127.0.0.1', port=a.port) as server:
        server.run()


if __name__ == '__main__':
    main()
