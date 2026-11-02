"""Offline executor review of the final E3 export; never imports native runtime.

Usage: python -m review_tools.recheck_e3_final --repo . --output NEW_FILE.json
Private raw-file/physics verification is a separate, source-bound CPU receipt.
This checker neither authorizes execution nor signs independent result approval.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

PACKAGE = 'reports/E3/FINAL_160_20261102'
NATIVE = '1d8e2d37932390ec07b5d04daddc1664efc64eb4'
HISTORICAL = '859e40b5f460365a8853bf3486969e9f8e28951c'
R017 = 'ca979be10c00389ed57b77967c232d7a84132406'
METRICS = ('wrong_lift', 'official_success', 'semantic_abort')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def values(row):
    return [float(row['observed_wrong_lift']), float(row['official_success']),
            float(row['status'] == 'SEMANTIC_ABORT')]


def analyze(audit, units, cells, checkpoints, inventory):
    rows = [row for epoch in audit['epochs'] for row in epoch['rows']]
    require(len(rows) == len(units) == len(cells) == 160, 'fixed160 denominator')
    ids = [c['run_id'] for c in cells]
    require(len(set(ids)) == 160 and [r['run_id'] for r in rows] == ids ==
            [u['run_id'] for u in units], 'duplicate, missing or reordered ID')
    originals = {r['path']: r for r in inventory['rows']}
    require(len(originals) == len(inventory['rows']) == 21527,
            'complete distinct original inventory required')
    paired = collections.defaultdict(list)
    for row, unit, cell in zip(rows, units, cells):
        require(all(row[k] == v for k, v in cell.items()) and unit['cell'] == cell,
                'frozen cell identity mismatch')
        require(row['reserved'] is True and row['outcome_known'] is True and
                row['actual_exit'] == unit['native_exit'] == unit['supervisor_exit'] == 0
                and unit['complete_child_receipt'] is True, 'unknown/error outcome')
        auth, result = unit['authorization'], unit['result']
        head = HISTORICAL if cell['run_id'] == 'e3a-test-0001' else NATIVE
        require(auth['authorized_head'] == result['repo_sha'] == head,
                'acquisition Head mismatch')
        if head == HISTORICAL:
            require(auth['review_commit'] == R017, '0001 historical grant replaced')
        require(result['status'] == row['status'] and result['exit_code'] == 0 and
                result['official_success'] is row['official_success'] and
                (result['first_wrong_lift_step'] is not None) is row['observed_wrong_lift'],
                'raw result and analyzed outcome differ')
        require(result['settling_steps'] == 10 and 0 < result['inner_steps'] <= 720,
                'control contract differs')
        root = 'runs/' + cell['epoch'] + '_TEST/' + cell['run_id'] + '/'
        for name, key in [('reservation.json', 'reservation_sha256'),
                          ('result.json', 'result_sha256'),
                          ('artifact_manifest.json', 'artifact_manifest_sha256'),
                          ('supervisor_exit.json', 'supervisor_exit_sha256'),
                          ('control_trace.npz', 'control_trace_sha256')]:
            require(originals[root+name]['sha256'] == unit[key],
                    'unit original source hash differs')
        require(originals['runs/'+cell['run_id']+'.exit.json']['sha256'] ==
                unit['native_exit_sha256'], 'native exit source differs')
        cursor = 0
        require(len(unit['decisions']) == result['policy_calls'] ==
                unit['policy_request_rows'], 'policy/decision denominator differs')
        for index, decision in enumerate(unit['decisions']):
            require(decision['index'] == index and
                    decision['completed_controls_before'] == cursor,
                    'decision/control chronology differs')
            after = decision['completed_controls_after']
            require(cursor <= after <= min(cursor+8, 720), 'prefix exceeds8')
            if decision['decision'] == 'ACCEPT':
                require(after > cursor, 'ACCEPT has no control')
            else:
                require(after == cursor and index == len(unit['decisions'])-1,
                        'rejection/error executed or continued')
            cursor = after
        require(cursor == result['inner_steps'], 'actual control total differs')
        if cell['system'] in ('G', 'A0'):
            require(unit['noninterference_all_state_rng_unchanged'] is True and
                    unit['noninterference_rows'] == len(unit['decisions']),
                    'noninterference evidence missing')
        if cell['system'] == 'G':
            close = unit['shadow_lifecycle']
            require(close['status'] == 'CLEAN' and close['worker_returncode'] == 0
                    and close['clean'] is True and close['forced'] is False and
                    close['term_sent'] is False and close['kill_sent'] is False and
                    close['pipe_closed'] is True and close['process_handle_closed'] is True
                    and close['native_finalized'] is True and
                    close['worker_receipt_statuses'] == ['CLOSING', 'CLOSED'],
                    'worker cleanup incomplete')
        paired[(cell['epoch'], cell['task'], cell['init_index'], cell['condition'])].append(cell)
    for group in paired.values():
        require(len({(c['init_hash'], c['policy_seed'], c['environment_seed'],
                      c['actual_policy_language'], c['trusted_target']) for c in group}) == 1,
                'arm pairing identity/seed differs')
    expected = [('E3A', i) for i in range(4, 113, 4)] + [('E3B', i) for i in range(6, 49, 6)]
    require([(c['epoch'], c['through']) for c in checkpoints] == expected,
            'mandatory checkpoint missing/order differs')
    require(sum(c['original_files'] for c in checkpoints) == len(originals) and
            all(c['paired_state_action_physics_verified'] is True and
                c['worker_lifecycle_verified'] is True and
                c['archive_sha256'] == c['secondary_archive_sha256'] and
                c['two_copy_status'] == 'TWO_LOCATIONS_WHOLE_AND_EVERY_MEMBER_SHA256_VERIFIED'
                for c in checkpoints), 'checkpoint physics/custody incomplete')
    rng = np.random.default_rng(641500)
    groups, contrasts = [], []
    for epoch, arms in [('E3A', ['B0', 'G']), ('E3B', ['B0', 'A0', 'G'])]:
        selected = [r for r in rows if r['epoch'] == epoch]
        tasks = list(dict.fromkeys(r['task'] for r in selected))
        table = {(r['task'], r['init_index'], r['condition'], r['system']): r for r in selected}
        indices = {task: rng.integers(0, 4, size=(2000, 4)) for task in tasks}
        for condition in ('C0', 'C2'):
            arm_data = {arm: {task: np.asarray([values(table[task, i, condition, arm])
                        for i in (16, 17, 18, 19)]) for task in tasks} for arm in arms}
            for task in tasks + ['MACRO_FIXED_TASKS']:
                subset = tasks if task == 'MACRO_FIXED_TASKS' else [task]
                draws = {arm: np.mean([arm_data[arm][t][indices[t]].mean(axis=1)
                                      for t in subset], axis=0) for arm in arms}
                observed = {arm: np.concatenate([arm_data[arm][t] for t in subset]).mean(axis=0)
                            for arm in arms}
                for arm in arms:
                    original = next(g for g in audit['statistics']['groups'] if
                                    (g['epoch'], g['task'], g['condition'], g['system']) ==
                                    (epoch, task, condition, arm))
                    for mi, metric in enumerate(METRICS):
                        ci = np.quantile(draws[arm][:, mi], [.025, .975]).tolist()
                        require(np.allclose(original['metrics'][metric]['bounds'],
                                            [observed[arm][mi]]*2, atol=1e-14, rtol=0) and
                                np.allclose(original['metrics'][metric]['paired_cluster_percentile95_bounds'],
                                            ci, atol=1e-14, rtol=0), 'frozen group bootstrap differs')
                    den = 4*len(subset)
                    groups.append(dict(epoch=epoch, task=task, condition=condition, system=arm,
                        denominator=den, counts={m: int(round(observed[arm][i]*den))
                        for i, m in enumerate(METRICS)}, percentile95={m: np.quantile(
                        draws[arm][:, i], [.025, .975]).tolist() for i, m in enumerate(METRICS)}))
                pairs = [('G', 'B0')] if epoch == 'E3A' else [('G', 'A0'), ('A0', 'B0'), ('G', 'B0')]
                for first, second in pairs:
                    for mi, metric in enumerate(METRICS):
                        point = float(observed[first][mi]-observed[second][mi])
                        ci = np.quantile(draws[first][:, mi]-draws[second][:, mi], [.025, .975]).tolist()
                        original = next(c for c in audit['statistics']['contrasts'] if
                                        (c['epoch'], c['task'], c['condition'], c['metric'], c['contrast']) ==
                                        (epoch, task, condition, metric, first+'-'+second))
                        require(np.allclose(original['bounds'], [point]*2, atol=1e-14, rtol=0) and
                                np.allclose(original['paired_cluster_percentile95_bounds'], ci,
                                            atol=1e-14, rtol=0), 'frozen contrast bootstrap differs')
                        contrasts.append(dict(epoch=epoch, task=task, condition=condition,
                            metric=metric, contrast=first+'-'+second, difference=point,
                            paired_cluster_percentile95=ci))
    positive_pairs = []
    for unit in units:
        cell, result = unit['cell'], unit['result']
        if cell['condition'] != 'C2' or cell['system'] != 'B0' or result['first_wrong_lift_step'] is None:
            continue
        for other in units:
            if other['cell']['scenario_id'] != cell['scenario_id'] or other['cell']['system'] == 'B0':
                continue
            stop = next((d['completed_controls_before'] for d in other['decisions']
                         if d['decision'] == 'REJECT'), None)
            onset = result['first_wrong_lift_step']
            positive_pairs.append(dict(epoch=cell['epoch'], task=cell['task'],
                baseline_id=unit['run_id'], comparison_id=other['run_id'],
                system=other['cell']['system'], baseline_first_wrong_lift_step=onset,
                rejection_completed_controls=stop,
                lead_control_steps=None if stop is None else onset-stop,
                actual_comparison_wrong_lift=other['result']['first_wrong_lift_step'] is not None,
                prevention_before_B0_onset=stop is not None and stop < onset and
                    other['result']['first_wrong_lift_step'] is None))
    costs = []
    for group in [g for g in groups if g['task'] == 'MACRO_FIXED_TASKS']:
        selected = [u for u in units if (u['cell']['epoch'], u['cell']['condition'],
                    u['cell']['system']) == (group['epoch'], group['condition'], group['system'])]
        monitors = [d['total_monitor_before_execution_seconds'] for u in selected
                    for d in u['decisions'] if 'total_monitor_before_execution_seconds' in d]
        costs.append(dict(epoch=group['epoch'], condition=group['condition'], system=group['system'],
            episodes=len(selected), actual_policy_calls=sum(u['result']['policy_calls'] for u in selected),
            actual_controls=sum(u['result']['inner_steps'] for u in selected),
            runner_wall_seconds_sum=sum(u['result']['wall_seconds'] for u in selected),
            runner_wall_seconds_median_p95=np.quantile([u['result']['wall_seconds'] for u in selected],
                                                      [.5, .95]).tolist(),
            recorded_monitor_decisions=len(monitors),
            monitor_including_worker_setup_seconds_median_p95=(np.quantile(monitors, [.5, .95]).tolist()
                                                               if monitors else None),
            decision_counts=dict(collections.Counter(d['decision'] for u in selected for d in u['decisions']))))
    return dict(status='EXECUTOR_RECOMPUTED_NOT_INDEPENDENT_REVIEW', planned=160,
        eligible=160, unknown=0, groups=groups, contrasts=contrasts,
        raw_status_counts=dict(collections.Counter(r['status'] for r in rows)),
        checkpoint_count=len(checkpoints), verified_original_file_entries=len(originals),
        clean_G_workers=sum(c['system']=='G' for c in cells),
        bootstrap_repetitions=2000, bootstrap_seed=641500, E2_pooled=False,
        candidate_UAR=None, independent_scientific_approval=False,
        baseline_positive_comparable_pairs=positive_pairs, descriptive_costs=costs,
        timing_scope='Runner wall excludes separate model-server loading and custody/CPU audit; monitor samples are decisions, not independent scientific units. Absent A0/B0 monitor timings are null, not zero.')


def recheck(repo, package):
    load = lambda name: json.loads((package/name).read_text())
    binding = load('SOURCE_BINDING.json')
    for name, expected in binding['public_data_sha256'].items():
        path = package/name
        require(path.is_file() and not path.is_symlink() and sha(path) == expected,
                'public data hash differs: '+name)
    lock = json.loads((repo/'configs/e3_protocol_lock.proposed.json').read_text())
    require(sha(repo/'configs/e3_protocol_lock.proposed.json') == binding['native_protocol_lock_sha256'],
            'native source lock changed')
    for name, expected in lock['source_sha256'].items():
        require(sha(repo/name) == expected, 'frozen file changed: '+name)
    cells = json.loads((repo/'configs/e3_cells.proposed.json').read_text())['cells']
    units = load('LEDGER.json')
    for unit in units:
        auth = unit['authorization']
        path = auth['review_commit']+':'+auth['review_path']
        blob = subprocess.check_output(['git', 'rev-parse', path], cwd=repo, text=True).strip()
        require(blob == auth['review_blob'], 'historical grant Git blob differs')
    return analyze(load('AUDIT_FINAL_ORIGINAL.json'), units, cells,
                   load('CHECKPOINTS.json'), load('ORIGINAL_INVENTORY.json'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path.cwd())
    p.add_argument('--package', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    repo = args.repo.resolve()
    result = recheck(repo, args.package or repo/PACKAGE)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print('160/160; 36 checkpoints; frozen paired bootstrap cross-check passed')


if __name__ == '__main__':
    main()
