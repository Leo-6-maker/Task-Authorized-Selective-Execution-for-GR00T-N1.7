"""Failure-safe evidence persistence; synthetic tests do not run physics."""
import os
import traceback
from pathlib import Path
from .evidence import append_json, now_sgt, write_json


def persist_trace(folder, states, actions):
    import numpy as np
    path = Path(folder)/'control_trace.npz'
    temporary = path.with_suffix('.pending')
    with temporary.open('wb') as f:
        np.savez_compressed(f, states=np.asarray(states), converted_actions=np.asarray(actions))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def traced_control_step(step, action, state, folder, states, actions, result):
    import numpy as np
    converted = np.array(action, copy=True)
    append_json(Path(folder)/'control_attempts.jsonl', {
        'index': result['inner_steps'], 'action': converted.tolist(), 'at_sgt': now_sgt()})
    try:
        value = step(action)
    except BaseException:
        append_json(Path(folder)/'control_step_errors.jsonl', {
            'index': result['inner_steps'], 'action': converted.tolist(),
            'outcome': 'UNKNOWN_PARTIAL_PHYSICS_STEP', 'traceback': traceback.format_exc()})
        raise
    result['inner_steps'] += 1
    states.append(np.array(state(), copy=True))
    actions.append(converted)
    # Persist before video, wrapper return or any next step. A failed macro-step
    # still retains all successfully returned native control steps.
    persist_trace(folder, states, actions)
    return value


def cleanup_resources(folder, result, resources):
    errors = []
    for name, close in resources:
        if close is None:
            continue
        try:
            close()
        except BaseException as exc:
            errors.append({'resource': name, 'error_type': type(exc).__name__,
                           'traceback': traceback.format_exc()})
    if errors:
        write_json(Path(folder)/'cleanup_errors.json', errors)
        result['cleanup_errors'] = len(errors)
        if result['exit_code'] == 0:
            result.update(status='CLEANUP_ERROR', exit_code=1)
    return errors
