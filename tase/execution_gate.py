"""One immutable checked candidate; no main execution on reject/error."""
import copy
import numpy as np


KEYS = ['action.'+name for name in ['x','y','z','roll','pitch','yaw','gripper']]


def candidate(actions, horizon=16):
    if set(actions) != set(KEYS):
        raise ValueError('action stream contract')
    result = {}
    for key in KEYS:
        arr = np.asarray(actions[key])
        if arr.shape != (1,horizon,1) or arr.dtype != np.float32 or not np.isfinite(arr).all():
            raise ValueError('action shape/dtype/finite contract')
        result[key] = np.array(arr[0], copy=True)
    return result


def execute_checked(prefix, predict_and_decide, execute):
    """Predict on an isolated copy; require exact candidate immutability."""
    reference = {key: np.array(value, copy=True) for key,value in prefix.items()}
    try:
        inspected = copy.deepcopy(reference)
        decision = predict_and_decide(inspected)
        if set(inspected) != set(reference) or any(not np.array_equal(inspected[k], reference[k]) for k in reference):
            raise ValueError('inspected candidate mutated')
        if set(prefix) != set(reference) or any(not np.array_equal(prefix[k], reference[k]) for k in reference):
            raise ValueError('candidate mutated while checking')
        if decision.get('decision') not in ['ACCEPT', 'REJECT', 'ERROR']:
            raise ValueError('invalid gate decision')
    except Exception as exc:
        return {'decision':'ERROR','error_type':type(exc).__name__}, None
    if decision['decision'] != 'ACCEPT':
        return decision, None
    return decision, execute({key:np.array(value,copy=True) for key,value in reference.items()})
