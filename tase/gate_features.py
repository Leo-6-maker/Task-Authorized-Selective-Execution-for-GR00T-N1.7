"""Contact-only precursor view. No oracle, condition or instruction input."""
def contact_view(frame, names):
    if type(frame) is not dict:
        raise ValueError('contact frame must be a mapping')
    view = {'step': frame['step']}
    if type(view['step']) is not int or view['step'] < 1:
        raise ValueError('positive integer contact step required')
    for key in ['left_contacts', 'right_contacts']:
        values = frame[key]
        if type(values) is not dict or set(values) != set(names):
            raise ValueError('complete contact object set required')
        if any(type(value) is not bool for value in values.values()):
            raise ValueError('boolean contacts required')
        view[key] = dict(values)
    return view


def score_contacts(predicted_views, names, target, history, last_step, k=2):
    if type(k) is not int or k not in [1, 2, 3]:
        raise ValueError('undeclared gate candidate')
    if not predicted_views or len(predicted_views) > 8:
        raise ValueError('must inspect one nonempty executed prefix')
    if target not in names or set(history) != set(names):
        raise ValueError('gate TaskSpec/history mismatch')
    if any(type(n) is not int or n < 0 for n in history.values()):
        raise ValueError('invalid contact history')
    counts = dict(history); risk = 0; triggers = []
    for offset, view in enumerate(predicted_views, 1):
        if set(view) != {'step', 'left_contacts', 'right_contacts'}:
            raise ValueError('gate scorer accepts contact-only view')
        view = contact_view(view, names)
        if view['step'] != last_step + offset:
            raise ValueError('predicted contacts must follow actual history')
        for name in names:
            bilateral = view['left_contacts'][name] and view['right_contacts'][name]
            counts[name] = counts[name] + 1 if bilateral else 0
            if name != target and bilateral:
                risk = max(risk, counts[name])
                if counts[name] >= k:
                    triggers.append({'object': name, 'predicted_step': view['step'],
                                     'bilateral_count': counts[name]})
    return {'decision': 'REJECT' if triggers else 'ACCEPT', 'risk': risk,
            'k': k, 'triggers': triggers, 'checked_controls': len(predicted_views)}
