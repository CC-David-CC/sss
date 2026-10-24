"""Explicit without-replacement families for larger arithmetic assessments.

Legacy questions retain their original generator. These two finite families use
an injective ordinal permutation, not retries or changed question labels.
"""
from dataclasses import replace
import copy
import hashlib
import json
from .curriculum import exercise_for
from .foundations import reference_expression

PROFILE = 'without-replacement-v1'
GATES = ('independent', 'composition', 'transfer_recovery')

def unique_exercise_for(skill, split, index, *, gate='independent', seed=0):
    if type(index) is not int or not 0 <= index < 128:
        raise ValueError('Unique generator ordinal must be 0..127')
    case = exercise_for(skill, split, index, gate=gate, seed=seed)
    if skill not in ('math.place_value', 'math.multiply'):
        return case
    offset = int(hashlib.sha256(f'{seed}:{skill}:{split}:{PROFILE}'.encode()).hexdigest(), 16)
    ordinal = GATES.index(gate) * 128 + index
    payload = copy.deepcopy(case.payload)
    text = case.prompt
    if skill == 'math.multiply':
        values = {'practice': tuple(range(-20, 0)) + tuple(range(1, 21)),
                  'development': tuple(range(21, 81)),
                  'qualification': tuple(range(-200, -20))}[split]
        position = (offset + 7919 * ordinal) % (len(values) ** 2)
        a, b = values[position // len(values)], values[position % len(values)]
        expression = ['multiply', a, b]
        if gate == 'composition':
            expression = ['add', ['multiply', expression, 3], ['subtract', 7, 2]]
        old = json.dumps(payload['expression'])
        assert text.count(old) == 1
        text = text.replace(old, json.dumps(expression), 1)
        payload['expression'] = expression
    else:
        # Split magnitudes are disjoint. Qualification extends beyond development.
        first, count = {'practice': (1, 20), 'development': (21, 60),
                        'qualification': (81, 120)}[split]
        if index >= count * 5:
            raise ValueError('Unique place-value family exhausted; no automatic redraw')
        position = (offset + 7919 * index) % (count * 5)
        factor, digit = first + position // 5, position % 5
        old_digit = payload['position']
        if gate == 'composition':
            old = json.dumps(payload['expression'])
            expression = copy.deepcopy(payload['expression'])
            expression[1][1] = factor
            payload['expression'] = expression
            payload['n'] = int(reference_expression(expression))
            assert text.count(old) == 1
            text = text.replace(old, json.dumps(expression), 1)
        else:
            old = str(payload['n']); payload['n'] = factor * 10007
            assert text.count(old) == 1
            text = text.replace(old, str(payload['n']), 1)
        text = text.replace(f'position {old_digit}', f'position {digit}', 1)
        payload['position'] = digit
    return replace(case, payload=payload, prompt=text,
                   family_id=case.family_id + ':' + PROFILE,
                   trial_id=case.trial_id + ':' + PROFILE)
