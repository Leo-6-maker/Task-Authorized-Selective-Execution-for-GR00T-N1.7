"""Reproduce R002 audit-completeness gaps using ONLY SYNTHETIC fixtures.

Run against the reviewed PR checkout with numpy installed:
  python reproduce_audit_gap.py --repo-root /path/to/reviewed-checkout

No GPU, simulator, model, real observations or credentials are used. The output
is validator behavior, not robot performance. On a repaired checkout the invalid
cases should be REJECTED while valid_control remains ACCEPTED.
"""
import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    args = parser.parse_args()
    rootcode = args.repo_root.resolve()
    sys.path.insert(0, str(rootcode))
    from tase.evidence import manifest
    spec = importlib.util.spec_from_file_location('reviewed_auditor',
                                                  rootcode/'scripts/summarize_baseline.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def write(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj)+'\n')

    results = []
    for mutation in ['valid_control', 'missing_wrist', 'empty_observation',
                     'empty_reset_keys', 'empty_manifest']:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/'runs/episodes/synthetic-dev'
            folder.mkdir(parents=True)
            record = dict(run_id='synthetic-dev', task='alphabet_soup', init_index=0,
                          status='SUCCESS', official_success=True, exit_code=0,
                          policy_calls=1, policy_requests_attempted=1, inner_steps=1,
                          settling_steps=10, wall_seconds=1.0, repo_sha='SYNTHETIC',
                          config_hash='SYNTHETIC', split='DEV')
            write(folder/'result.json', record)
            write(folder/'reservation.json', dict(split='DEV', repo_sha='SYNTHETIC', probe_only=False))
            write(root/'runs/synthetic-dev.exit.json', dict(exit_code=0))
            write(folder/'horizon.json', dict(n_action_steps=8, action_horizon=16,
                                              video_delta_indices=[0], state_delta_indices=[0]))
            keys = ['action.'+x for x in ['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'gripper']]
            actions = {key: np.zeros((1, 16, 1), dtype=np.float32) for key in keys}
            np.savez(folder/'action-000.npz', **actions)
            expected = np.zeros((1, 7), dtype=np.float32)
            expected[0, -1] = 1.0
            np.savez(folder/'control_trace.npz', states=np.zeros((1, 2)), converted_actions=expected)
            write(folder/'decisions.jsonl', dict(index=0, inner_steps=1, official_success=True,
                                                 terminated=True, truncated=False))
            obs = {key: np.zeros((1, 1, 256, 256, 3), dtype=np.uint8)
                   for key in ['video.image', 'video.wrist_image']}
            obs.update({key: np.zeros((1, 1, 2 if key == 'state.gripper' else 1), dtype=np.float32)
                        for key in ['state.x', 'state.y', 'state.z', 'state.roll', 'state.pitch',
                                    'state.yaw', 'state.gripper']})
            parity = {key: True for key in obs}
            parity['annotation.human.action.task_description'] = True
            if mutation == 'missing_wrist':
                del obs['video.wrist_image']
            if mutation == 'empty_observation':
                obs = {}
            if mutation == 'empty_reset_keys':
                parity = {}
            np.savez(folder/'observation-000.npz', **obs)
            write(folder/'reset_parity.json', dict(state_unchanged=True,
                                                   latest_native_observation_equal=parity))
            entries = manifest(root, list(folder.glob('*')), 'synthetic-dev')
            if mutation == 'empty_manifest':
                entries = []
            write(folder/'artifact_manifest.json', entries)
            write(root/'runs/server-03/inference.jsonl', dict(request=1, status='PASS',
                  inference_ms=1.0, peak_allocated_bytes=1, peak_reserved_bytes=2))
            write(root/'runs/server-03.exit.json', dict(exit_code=0))
            try:
                output = module.audit(root)
                outcome, flags = 'ACCEPTED', output['audit'][0]
            except Exception as exc:
                outcome, flags = 'REJECTED:'+type(exc).__name__, {}
            results.append(dict(fixture='SYNTHETIC_REVIEW_ONLY', mutation=mutation,
                                outcome=outcome, flags=flags))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
