"""Read-only Gate P/R015 provenance and FULL160 freeze verification (CPU only).

Scientific freeze never grants execution. authorize() independently requires a
current, exact-Head E3_TEST_AUTHORIZED decision before calling this verifier.
"""
import argparse
import csv
import io
import json
import subprocess
from pathlib import Path
from tase.task_spec import TaskSpec
from .discovery import require, sha
from .manifest import verify
from .scene import validate

P_COMMIT = '5dafcec4dc390f69dad6f08ebff1eec4577caf2f'
P_PATH = 'docs/reviews/R016-E3-GATE-P-APPROVED.json'
R015_HEAD = '5c959b54c0e7f3c1253b0754c895227341a7f2e0'
SCENE_PATH = 'reports/E3/R015/SCENE_RESULT.json'
CSV_PATH = 'reports/E3/R015/COMPILED_SCENE_BINDINGS_36.csv'


def source_inventory(repo):
    """Active code/test/config paths, independent of the supplied lock's keys."""
    repo = Path(repo)
    paths = set()
    for directory in ['e3', 'tase', 'scripts', 'tests']:
        for p in (repo/directory).rglob('*'):
            if p.is_file() and p.suffix in ['.py', '.sh']:
                require(not p.is_symlink(), 'source inventory contains a symlink')
                paths.add(str(p.relative_to(repo)))
    for p in (repo/'configs').rglob('*'):
        if p.is_file() and p.suffix in ['.json', '.txt'] and p.name != 'e3_protocol_lock.proposed.json':
            require(not p.is_symlink(), 'config inventory contains a symlink')
            paths.add(str(p.relative_to(repo)))
    return paths


def historical(repo, revision, path):
    return subprocess.check_output(['git', 'show', revision+':'+path], cwd=repo)


def verify_freeze(repo):
    repo = Path(repo)
    lock = json.loads((repo/'configs/e3_protocol_lock.proposed.json').read_text())
    require(lock['status'] == 'FROZEN_BY_INDEPENDENT_REVIEW' and
            lock['runtime_scene_binding_verified'] is True and
            lock['variant'] == 'FULL160', 'Gate P FULL160 freeze required')
    require(lock['authorized_real_TEST'] is False,
            'scientific lock cannot self-authorize real TEST')
    require(source_inventory(repo) <= set(lock['source_sha256']),
            'E3 source lock missing active files')
    approval = historical(repo, P_COMMIT, P_PATH)
    require((repo/P_PATH).read_bytes() == approval, 'R016 historical approval differs')
    gate_p = json.loads(approval)
    require(gate_p['disposition'] == 'GATE_P_APPROVED_CPU_FREEZE_AUTHORIZED' and
            gate_p['selected_variant'] == 'FULL160' and
            gate_p['runtime_execution_authorized'] is False, 'wrong Gate P decision')
    require(lock['gate_P'] == dict(commit=P_COMMIT, path=P_PATH,
                                  reviewed_report_head=R015_HEAD), 'Gate P identity differs')
    proposal = 'docs/protocols/E3-001-v1.0-PROPOSED.md'
    require((repo/proposal).read_bytes() == historical(repo, R015_HEAD, proposal),
            'reviewed scientific proposal differs')
    baseline_lock = json.loads(historical(repo, R015_HEAD, 'configs/e3_protocol_lock.proposed.json'))
    for name, digest in baseline_lock['source_sha256'].items():
        if name.startswith(('tase/', 'scripts/', 'configs/')) or name == 'e3/reactive_gate.py':
            require(sha(repo/name) == digest, 'reviewed E2/scientific/A0 source differs: '+name)
    for field, name in [('cells_file_sha256', 'e3_cells.proposed.json'),
                        ('source_inventory_sha256', 'e3_sources.proposed.json'),
                        ('runtime_lock_sha256', 'runtime_lock_E2.json')]:
        require(sha(repo/'configs'/name) == gate_p[field], 'R016 science identity differs: '+name)
    for key, value in dict(budgets={'E3A':112, 'E3B':48}, gate_k=3, raw_chunk=16,
                           execution_prefix=8, episode_control_cap=720,
                           settling_controls=10, bootstrap_repetitions=2000,
                           bootstrap_seed=641500).items():
        require(lock[key] == value, 'frozen scientific constant differs: '+key)
    source = json.loads((repo/'configs/e3_sources.proposed.json').read_text())
    cells = json.loads((repo/'configs/e3_cells.proposed.json').read_text())['cells']
    verify(cells, source)
    scene_bytes = historical(repo, R015_HEAD, SCENE_PATH)
    csv_bytes = historical(repo, R015_HEAD, CSV_PATH)
    require((repo/SCENE_PATH).read_bytes() == scene_bytes and
            (repo/CSV_PATH).read_bytes() == csv_bytes, 'published R015 evidence differs')
    scene_binding = lock['scene_identity']
    require(scene_binding['source_head'] == R015_HEAD and
            scene_binding['source_path'] == SCENE_PATH and
            scene_binding['csv_path'] == CSV_PATH and
            scene_binding['scope'] == 'SCENE_IDENTITY_ONLY', 'scene provenance/scope differs')
    frozen = repo/scene_binding['frozen_path']
    require(frozen.read_bytes() == scene_bytes and sha(frozen) == scene_binding['sha256'],
            'frozen scene evidence differs')
    scene = json.loads(scene_bytes)
    require(scene['authorized_head'] == gate_p['reviewed_executable_head'] and
            scene['grant_commit'] == 'c0ca90f4827c67e04e4033c6358e410f5ac6aace' and
            scene['status'] == 'SCENE_IDENTITY_INSPECTED_NOT_TEST_AUTHORIZATION' and
            scene['constructors'] == 9 and scene['init_loads'] == 36 and
            scene['actual_exit'] == 0 and scene['model_calls'] == 0 and
            scene['TEST_reservations'] == 0, 'R015 result/count/authority differs')
    bindings = {(b['task'], b['init_index']): b for b in scene['bindings']}
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode())))
    indexed = {(r['task'], int(r['init_index'])): r for r in rows}
    required = {(c['task'], c['init_index']) for c in cells}
    require(len(scene['bindings']) == len(rows) == len(bindings) == len(indexed) == 36
            and set(bindings) == set(indexed) == required, 'R015/FULL160 cluster coverage differs')
    tasks = {s['task']: s for s in source['tasks']}
    for cell in cells:
        key = cell['task'], cell['init_index']
        b, row = bindings[key], indexed[key]
        spec = validate(TaskSpec(**b['TaskSpec']), cell, tasks[cell['task']])
        require(b['init_hash'] == row['init_sha256'] == cell['init_hash'] and
                b['compiled_scene_sha256'] == row['compiled_scene_sha256'],
                'R015 initialization/scene hash differs')
        distractor = tasks[cell['task']]['c2_target']+'_1'
        for name, obj in [('target', spec.target), ('distractor', distractor), ('basket', spec.basket)]:
            require(row[name] == obj and int(row[name+'_body_id']) == spec.objects[obj]['body_id']
                    and json.loads(row[name+'_geom_ids']) == spec.objects[obj]['geoms'],
                    'R015 CSV/TaskSpec object identity differs')
        require(json.loads(row['left_finger_geom_ids']) == spec.left_geoms and
                json.loads(row['right_finger_geom_ids']) == spec.right_geoms,
                'R015 finger identity differs')
    for name, digest in lock['source_sha256'].items():
        require(sha(repo/name) == digest, 'E3 source lock differs: '+name)
    return dict(status='SCIENTIFIC_FREEZE_VERIFIED_GATE_C_REQUIRED', variant='FULL160',
                budgets=lock['budgets'], clusters=36, native_scene_tasks=9,
                scene_scope='SCENE_IDENTITY_ONLY', gate_P_commit=P_COMMIT,
                protocol_lock_sha256=sha(repo/'configs/e3_protocol_lock.proposed.json'),
                cells_file_sha256=gate_p['cells_file_sha256'],
                runtime_lock_sha256=gate_p['runtime_lock_sha256'],
                scene_identity_sha256=scene_binding['sha256'],
                authorized_real_TEST=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    print(json.dumps(verify_freeze(p.parse_args().repo), indent=2))
