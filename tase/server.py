"""Instrument the pinned native GR00T policy; bind only to localhost."""
import argparse
import json
import time
import hashlib
import os
from pathlib import Path
from .evidence import append_json, now_sgt, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=5558)
    p.add_argument('--policy-seed', type=int, default=640100)
    p.add_argument('--allocation-record', type=Path, required=True)
    p.add_argument('--audit-rng', action='store_true', help='M2 read-only policy RNG fingerprint endpoint')
    p.add_argument('--epoch', choices=['E2'], help='Enable scenario-scoped E2 reset/seed receipts')
    a = p.parse_args()
    permission = json.loads(a.allocation_record.read_text())
    if not permission.get('shared_gpu_inference_authorized'):
        raise ValueError('GPU inference allocation is not authorized')
    a.output.mkdir(parents=True, exist_ok=False)
    if a.epoch and os.environ.get('GROOT_SKIP_HF_MODEL_WEIGHTS','').strip().lower() not in ['', '0','false','no','off']:
        raise ValueError('E2 requires real weights; upstream test-only weight skipping is forbidden')
    import torch
    from gr00t.policy.gr00t_policy import Gr00tPolicy, Gr00tSimPolicyWrapper
    from gr00t.policy.server_client import PolicyServer
    torch.manual_seed(a.policy_seed)
    torch.cuda.manual_seed_all(a.policy_seed)
    free, total = torch.cuda.mem_get_info()
    if free < 16 * 1024**3:
        raise RuntimeError('less than 16 GiB free VRAM; do not share this device now')
    # Leave >=2 GiB of currently free memory and cap this process at 55% total.
    fraction = min(0.55, (free - 2*1024**3) / total)
    torch.cuda.set_per_process_memory_fraction(fraction)
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
        'torch': torch.__version__, 'torch_cuda': torch.version.cuda,
        'free_vram_before_load_bytes': free, 'allocator_fraction_cap': fraction,
        'mode': 'eval/no_training', 'host': '127.0.0.1', 'port': a.port})
    original = policy.get_action
    calls = 0
    scenario = None

    def measured(observation, options=None):
        nonlocal calls
        calls += 1
        if a.epoch:
            if scenario is None:
                raise ValueError('E2 requires reset_and_seed before inference')
            language = observation.get('annotation.human.action.task_description')
            append_json(a.output / 'actual_requests.jsonl', {
                'request': calls, 'epoch': a.epoch, 'scenario': scenario,
                'actual_policy_language': language})
        torch.cuda.synchronize()
        start = time.perf_counter()
        try:
            result = original(observation, options)
        except Exception as exc:
            append_json(a.output / 'inference.jsonl', {
                'request': calls, 'status': 'ERROR', 'error_type': type(exc).__name__,
                'elapsed_ms': (time.perf_counter()-start)*1000,
                'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                'peak_reserved_bytes': torch.cuda.max_memory_reserved()})
            raise
        torch.cuda.synchronize()
        append_json(a.output / 'inference.jsonl', {
            'request': calls, 'status': 'PASS',
            'input_shapes': {k: list(v.shape) for k, v in observation.items()
                             if hasattr(v, 'shape')},
            'inference_ms': (time.perf_counter()-start)*1000,
            'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
            'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
            'output_shapes': {k: list(v.shape) for k, v in result[0].items()}})
        return result

    policy.get_action = measured
    with PolicyServer(policy, host='127.0.0.1', port=a.port) as server:
        if a.epoch:
            import random
            import numpy as np

            def reset_and_seed(scenario_id, seed):
                nonlocal scenario
                # Native PolicyServer dispatches input data as keyword arguments.
                payload = {'scenario_id': scenario_id, 'seed': seed}
                if type(seed) is not int or not 0 <= seed < 2**32:
                    raise ValueError('invalid scenario seed')
                if not isinstance(payload['scenario_id'], str) or not payload['scenario_id']:
                    raise ValueError('invalid scenario identity')
                policy.reset()
                random.seed(seed); np.random.seed(seed)
                torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
                scenario = dict(payload)
                ack = {'epoch': a.epoch, **scenario, 'policy_calls_before': calls,
                    'cpu_rng_sha256': hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
                    'cuda_rng_sha256': [hashlib.sha256(s.numpy().tobytes()).hexdigest()
                                       for s in torch.cuda.get_rng_state_all()]}
                append_json(a.output/'scenario_resets.jsonl', ack)
                return ack

            server.register_endpoint('reset_and_seed', reset_and_seed, requires_input=True)
        if a.audit_rng:
            def rng_digest():
                result={'policy_calls':calls,
                    'cpu_rng_sha256':hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
                    'cuda_rng_sha256':[hashlib.sha256(s.numpy().tobytes()).hexdigest()
                                       for s in torch.cuda.get_rng_state_all()]}
                if a.epoch:
                    result.update(python_rng_sha256=hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
                                  numpy_rng_sha256=hashlib.sha256(repr(np.random.get_state()).encode()).hexdigest())
                append_json(a.output/'rng_checks.jsonl', result)
                return result
            server.register_endpoint('rng_digest', rng_digest, requires_input=False)
        server.run()


if __name__ == '__main__':
    main()
