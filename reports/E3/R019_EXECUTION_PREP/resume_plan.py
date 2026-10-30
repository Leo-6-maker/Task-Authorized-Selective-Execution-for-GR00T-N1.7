"""Read-only E3 resume planning. Cannot start a process, reserve an ID or grant TEST.

The caller supplies a current full original audit, never just the successful rows.
Runtime/source identity is checked by the CLI against the separate approved tree.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

APPROVED_HEAD = '126491066226a0d52968d8bcf363d295781c2684'
CPU_SNAPSHOT = '6c8e38c1c84083b7664ee0cb7f11fc0cb0d03651'
OLD_HEAD = '859e40b5f460365a8853bf3486969e9f8e28951c'
OLD_GRANT = 'ca979be10c00389ed57b77967c232d7a84132406'
R019_COMMIT = '266ce04507a6a430fade03f1dac4ce0f568aca22'
R019_PATH = 'docs/reviews/R019-E3-CPU-REFREEZE-APPROVED.json'
LOCK_SHA = '14abb2ace96424b68a5b0bd25fcc3b897d152fa0eb8efb28ae153de38732b3bc'
FULL = {'SUCCESS', 'TIME_LIMIT', 'SEMANTIC_ABORT'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def build(cells, audit, review, reconciliation):
    """Prepare exactly the R019 one-consumed history; fail closed on any drift.

    This deliberately does not infer a native grant or a new execution window.
    A later operator must re-audit originals, call the unchanged authorization
    path, and run existing checkpoint.build() with real paired/backup evidence.
    """
    require(review['review_id'] == 'R019' and review['disposition'] ==
            'APPROVED_CPU_REFREEZE_AND_0001_RECONCILIATION_NO_TEST' and
            review['B1_status'] == 'CLOSED', 'wrong independent CPU review')
    require(review['reviewed_complete_head'] == APPROVED_HEAD and
            review['source_lock']['sha256'] == LOCK_SHA,
            'reviewed exact Head/lock differs')
    boundary = review['authorization_boundary']
    require(boundary['runtime_execution_authorized'] is False and
            boundary['new_TEST_authorized'] is False and
            boundary['previous_night_stop_latched'] is True,
            'R019 planning cannot become an execution grant')
    require(len(cells) == 160 and len({c['run_id'] for c in cells}) == 160,
            'all160 unique original cells required')
    expected_ids = ([f'e3a-test-{i:04d}' for i in range(1, 113)] +
                    [f'e3b-test-{i:04d}' for i in range(1, 49)])
    require([c['run_id'] for c in cells] == expected_ids,
            'original fixed A112/B48 ID order differs')
    rec = reconciliation
    require(rec['reconciliation_id'] == 'R018-0001-v1' and
            rec['disposition'] == 'ELIGIBLE_SUCCESS_IN_NEW_R018_RECONCILED_ANALYSIS' and
            rec['current_CPU_head'] == CPU_SNAPSHOT and
            rec['protocol_lock_sha256'] == LOCK_SHA,
            'reviewed same-ID reconciliation identity differs')
    acquisition = rec['acquisition']
    require(acquisition['run_id'] == 'e3a-test-0001' and
            acquisition['execution_head'] == OLD_HEAD and
            acquisition['review_commit'] == OLD_GRANT and
            acquisition['cell'] == cells[0], 'historical0001 acquisition rewritten')
    require(rec['original_result']['sha256'] ==
            'c78ff39766f533f5fa6cb512404c2cc2ac95b266539cef4573709901300c9dcc' and
            rec['original_manifest']['sha256'] ==
            'd28191ccd311d56903a3bdd9c1fb93c868fdc76516855b4c2fd66bb38c32062a',
            'original result/manifest identity differs')
    original_files = rec['original_files']
    require(len(original_files) == len({r['path'] for r in original_files}) == 78,
            'full unique78-file custody required')
    require(rec['eligibility']['new_analysis_outcome_known'] is True and
            rec['eligibility']['new_analysis_status'] == 'SUCCESS' and
            rec['eligibility']['original_bytes_rewritten'] is False and
            rec['eligibility']['old_frozen_audit_PASS'] is False and
            [x['actual_exit'] for x in rec['old_frozen_audit_failures']] == [1, 1],
            'reconciliation cannot rewrite old frozen failure or raw bytes')
    for key in ['complete_historical_original_audit',
                'actual_physics_oracle_action_checks',
                'claim_and_native_supervisor_exit_chain',
                'source_identity_preserved',
                'ordinary_optimized_and_old_new_readonly_audits_equal']:
        require(rec['checks'][key] is True, 'incomplete reconciliation: ' + key)
    require(review['planned_160_status']['consumed'] ==
            review['planned_160_status']['eligible'] == 1 and
            review['planned_160_status']['unstarted'] == 159,
            'reviewed history not one-consumed/159-unstarted')

    epochs = audit['epochs']
    require(len(epochs) == 2, 'both full epoch audits required')
    rows = [r for epoch in epochs for r in epoch['rows']]
    require(len(rows) == 160, 'full audit denominator required')
    for row, cell in zip(rows, cells):
        require(all(row.get(k) == v for k, v in cell.items()),
                'audit/cell identity drift: ' + cell['run_id'])
    require(rows[0]['reserved'] is True and rows[0]['outcome_known'] is True and
            rows[0]['status'] == 'SUCCESS' and rows[0]['actual_exit'] == 0,
            '0001 must remain consumed, known and preserved; no replay')
    for row in rows[1:]:
        require(row['reserved'] is False and row['outcome_known'] is False and
                row['status'] == 'NOT_STARTED' and row['actual_exit'] is None,
                'unexpected reservation/partial/error; preserve and re-audit')
    for epoch, size, consumed in zip(epochs, [112, 48], [1, 0]):
        require(epoch['planned'] == len(epoch['rows']) == size and
                epoch['consumed'] == epoch['known'] == consumed and
                epoch['unstarted'] == epoch['unknown'] == size - consumed,
                'full ledger aggregate contradicts original rows')

    checkpoints = []
    remaining = []
    for epoch, size in [('E3A', 4), ('E3B', 6)]:
        part = [c for c in cells if c['epoch'] == epoch]
        require(len(part) == (112 if epoch == 'E3A' else 48),
                'cross-epoch original cell identity differs')
        for offset in range(0, len(part), size):
            block = part[offset:offset + size]
            arms = ['B0', 'G'] if epoch == 'E3A' else ['B0', 'A0', 'G']
            require(len({(c['task'], c['init_index']) for c in block}) == 1 and
                    [(c['condition'], c['system']) for c in block] ==
                    [(condition, arm) for condition in ['C0', 'C2'] for arm in arms],
                    'checkpoint must preserve full original 4/6-cell cluster')
            preserved = [c['run_id'] for c in block if c['run_id'] == 'e3a-test-0001']
            pending = [c['run_id'] for c in block if c['run_id'] not in preserved]
            remaining.extend(pending)
            checkpoints.append(dict(epoch=epoch, through=offset + size,
                                    all_original_ids=[c['run_id'] for c in block],
                                    historical_reuse_only=preserved,
                                    once_only_future_ids=pending,
                                    mandatory_before_next_block=True,
                                    actual_checkpoint_status='NOT_EXECUTED'))
    require(len(remaining) == len(set(remaining)) == 159 and
            remaining == expected_ids[1:], 'resume must start0002 and never repeat0001')
    return dict(status='READ_ONLY_RESUME_PLAN_NOT_EXECUTION_AUTHORIZATION',
                reviewed_runtime_head=APPROVED_HEAD, source_lock_sha256=LOCK_SHA,
                R019_commit=R019_COMMIT, all_cells_sha256=digest(cells),
                all_audited_rows_sha256=digest(rows), reserved=1, eligible=1,
                unstarted_unknown=159, next_untouched_id=remaining[0],
                remaining_once_only_ids=remaining, checkpoints=checkpoints,
                preserved_acquisition=copy.deepcopy(acquisition),
                old_frozen_audit_exits=[1, 1],
                normal_scientific_terminal_statuses=sorted(FULL),
                normal_negative_outcomes_continue_after_real_checks=True,
                real_execution_or_evidence_error='STOP_NEW_TEST_KEEP_ID_SWITCH_TO_CPU',
                native_grant='NOT_ISSUED_BY_R019', new_execution_window='NOT_AUTHORIZED',
                fresh_resource_binding='REQUIRED_AT_LATER_NATIVE_ADMISSION',
                native_execution_authorized=False, previous_night_stop_latched=True,
                new_GPU_model_sim_Shadow_calls=0, new_TEST_reservations=0,
                G_A0_Shadow_experiment_evidence='NONE', conditional_prevention='N/A')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['repo', 'workspace', 'audit', 'review', 'reconciliation', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    git = lambda *a: subprocess.check_output(['git', *a], cwd=repo)
    require(git('rev-parse', 'HEAD').decode().strip() == APPROVED_HEAD and
            not git('status', '--porcelain'), 'separate clean approved runtime tree required')
    review_bytes = args.review.read_bytes()
    require(review_bytes == git('show', R019_COMMIT + ':' + R019_PATH) ==
            git('show', 'refs/remotes/origin/main:' + R019_PATH),
            'R019 must match immutable review and current fetched main')
    rec_path = repo/'reports/E3/R018/RECONCILIATION_0001_v1.json'
    require(args.reconciliation.read_bytes() == rec_path.read_bytes(),
            'reconciliation must match reviewed exact report bytes')
    output = args.output.resolve()
    require(not output.is_relative_to(repo) and
            not output.is_relative_to(args.workspace.resolve()/'runs') and
            not output.exists(), 'exclusive output outside approved tree/original runs required')
    # Freeze validation imports only CPU source, never LIBERO/MuJoCo/model.
    sys.path.insert(0, str(repo))
    from e3.freeze import verify_freeze
    verify_freeze(repo)
    cells = json.loads((repo/'configs/e3_cells.proposed.json').read_text())['cells']
    value = build(cells, json.loads(args.audit.read_text()),
                  json.loads(review_bytes), json.loads(args.reconciliation.read_text()))
    value['input_sha256'] = {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
                             for name in ['audit', 'review', 'reconciliation']}
    with args.output.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=value['status'], next_id=value['next_untouched_id'],
                         remaining=len(value['remaining_once_only_ids']),
                         checkpoints=len(value['checkpoints']), new_TEST_reservations=0)))


if __name__ == '__main__':
    main()
