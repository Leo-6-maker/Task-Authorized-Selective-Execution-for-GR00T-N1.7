"""Pure CPU continuation policy. No native imports, reservations or GPU context."""
import datetime as dt
import hashlib
import json
from pathlib import Path

RUNTIME = '126491066226a0d52968d8bcf363d295781c2684'
LOCK = '14abb2ace96424b68a5b0bd25fcc3b897d152fa0eb8efb28ae153de38732b3bc'
HISTORICAL_HEAD = '859e40b5f460365a8853bf3486969e9f8e28951c'
HISTORICAL_GRANT = 'ca979be10c00389ed57b77967c232d7a84132406'
FLOOR_MIB = 9216
HISTORICAL_RESERVED_BYTES = 6392119296
SGT = dt.timezone(dt.timedelta(hours=8))
NORMAL = {'SUCCESS', 'TIME_LIMIT', 'SEMANTIC_ABORT'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def source_digest():
    """Bind every operator/transport module, independent of mutable report files."""
    root = Path(__file__).parent
    rows = {p.name: sha(p) for p in sorted(root.glob('*.py'))}
    return hashlib.sha256(json.dumps(rows, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def aware(value):
    parsed = dt.datetime.fromisoformat(value)
    require(parsed.tzinfo is not None, 'execution window must specify a timezone')
    return parsed


def admission_contract(grant, identity, now, operator_digest):
    """Additional outer constraints; native authorize() is independently mandatory.

    A later independent grant must include this explicit continuation object.
    No default window, legacy R017 reuse or synthesized reviewer decision.
    """
    require(grant.get('disposition') == 'E3_TEST_AUTHORIZED',
            'independent E3 TEST authorization required')
    require(identity['authorized_head'] == grant['authorized_head'] == RUNTIME and
            identity['protocol_lock_sha256'] == grant['protocol_lock_sha256'] == LOCK,
            'exact approved native Head/lock required')
    continuation = grant.get('continuation', {})
    require(continuation.get('release_prior_incident_stop') is True and
            continuation.get('first_new_id') == 'e3a-test-0002' and
            continuation.get('preserve_history_ids') == ['e3a-test-0001'] and
            continuation.get('remaining') == {'E3A': 111, 'E3B': 48} and
            continuation.get('operator_source_sha256') == operator_digest,
            'explicit exact-operator continuation scope required')
    window = continuation.get('execution_window_sgt', {})
    start, cutoff, end = [aware(window[n]) for n in
                          ['start', 'no_new_reservations_after', 'end']]
    require(start < cutoff <= end and cutoff.date() < dt.date(2026, 11, 6),
            'new bounded window required; November6 permits no experiments')
    require(now.tzinfo is not None and start <= now < end,
            'outside independent execution window')
    return dict(start=start, cutoff=cutoff, end=end,
                last_supervisor_start=min(cutoff - dt.timedelta(seconds=1060),
                                          end - dt.timedelta(seconds=1060)))


def capacity(free_mib, total_mib, historical_bytes=HISTORICAL_RESERVED_BYTES):
    require(type(free_mib) is int and type(total_mib) is int and
            0 < total_mib and 0 <= free_mib <= total_mib and historical_bytes >= 0,
            'invalid query-only memory observation')
    historical_mib = historical_bytes / 1024**2
    estimate = free_mib - historical_mib
    return dict(preload_floor_MiB=FLOOR_MIB, postload_floor_MiB=FLOOR_MIB,
                observed_free_MiB=free_mib, observed_total_MiB=total_mib,
                historical_reserved_MiB=historical_mib,
                scheduling_reference_MiB=FLOOR_MIB + historical_mib,
                estimated_postload_free_MiB=estimate,
                status=('LIKELY_POSTLOAD_CAPACITY_BLOCKED'
                        if estimate < FLOOR_MIB else 'SCHEDULING_HINT_ONLY'),
                live_preload_pass=free_mib >= FLOOR_MIB,
                live_postload_pass=None, estimate_is_not_resource_authorization=True,
                estimated_allocator_fraction=min(.55, max(0., (free_mib - 2048) / total_mib)))


def validate_history(cells, audit, original_digest, expected_digest):
    require(original_digest == expected_digest, 'historical0001 original bytes changed')
    expected = ([f'e3a-test-{i:04d}' for i in range(1, 113)] +
                [f'e3b-test-{i:04d}' for i in range(1, 49)])
    require(len(cells) == 160 and [c['run_id'] for c in cells] == expected,
            'original FULL160 sequence required')
    epochs = audit['epochs']
    require(len(epochs) == 2, 'two complete epoch ledgers required')
    rows = [r for e in epochs for r in e['rows']]
    require(len(rows) == 160, 'all planned rows required')
    for row, cell in zip(rows, cells):
        require(all(row.get(k) == v for k, v in cell.items()), 'audit scientific identity differs')
    count = 0
    unstarted_seen = False
    for row in rows:
        if row['reserved']:
            require(not unstarted_seen and row['outcome_known'] is True and
                    row['actual_exit'] == 0 and row['status'] in NORMAL,
                    'unknown/failed/non-prefix consumed ID; stop, never replay')
            count += 1
        else:
            unstarted_seen = True
            require(row['status'] == 'NOT_STARTED' and row['actual_exit'] is None and
                    row['outcome_known'] is False, 'unstarted original is not unknown')
    require(count >= 1 and rows[0]['status'] == 'SUCCESS', 'preserved0001 required; no restart')
    for e in epochs:
        actual = sum(r['reserved'] for r in e['rows'])
        require(e['consumed'] == e['known'] == actual and
                e['planned'] == len(e['rows']) and
                e['unstarted'] == e['unknown'] == len(e['rows']) - actual,
                'ledger aggregates disagree')
    return count


def blocks(cells):
    result = []
    for epoch, size, total in [('E3A', 4, 112), ('E3B', 6, 48)]:
        part = [c for c in cells if c['epoch'] == epoch]
        require(len(part) == total, 'FULL160 budget differs')
        arms = ['B0', 'G'] if epoch == 'E3A' else ['B0', 'A0', 'G']
        for start in range(0, total, size):
            group = part[start:start+size]
            require(len({(c['task'], c['init_index']) for c in group}) == 1 and
                    [(c['condition'], c['system']) for c in group] ==
                    [(c, a) for c in ['C0', 'C2'] for a in arms],
                    'original paired 4/6-cell cluster differs')
            result.append((epoch, start+size, group))
    return result


def drive(backend):
    """One persistent invocation. Never retries a native call after an exception.

    Backend is real in production, explicit synthetic fixtures in CPU tests.
    Checkpoints release through the unchanged native checkpoint.build(), not a
    controller-made PASS. Any failure becomes a latched CPU fallback.
    """
    terminal = 'CPU_ADMISSION_DENIED_NO_NATIVE_EXECUTION'
    error = None
    try:
        backend.admit()
        cells = backend.cells
        require(backend.progress() == 1, 'new controller must start at reconciled0001 only')
        if not backend.capacity_ready():
            terminal = 'CAPACITY_BLOCKED_CPU_WORK'
            return terminal
        terminal = 'NATIVE_STOP_PRESERVE_CPU_DIAGNOSE'
        backend.start_server()
        for epoch, through, group in blocks(cells):
            for cell in group:
                if cell['run_id'] == 'e3a-test-0001':
                    backend.preserve_original()
                    continue
                if not backend.before_cell(cell):
                    terminal = 'PARTIAL_TIMEBOX_CPU_WORK'
                    return terminal
                result = backend.run_cell(cell)
                require(result['status'] in NORMAL and result['exit_code'] == 0,
                        'native or evidence failure; consumed ID retained')
                backend.verify_cell(cell)
            backend.checkpoint(epoch, through, group)
        terminal = 'COMPLETE_160_PENDING_INDEPENDENT_CLAIM_REVIEW'
        return terminal
    except BaseException as exc:
        error = exc
        backend.retain_failure(exc)
        raise
    finally:
        try:
            backend.close_server()
        except BaseException as cleanup:
            terminal = 'NATIVE_STOP_PRESERVE_CPU_DIAGNOSE'
            backend.retain_cleanup_failure(cleanup)
            if error is None:
                raise
        finally:
            backend.finish(terminal)
