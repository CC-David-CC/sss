"""New fraction family; retain the frozen v1 generators byte for byte.

Select fraction operands by an injective permutation of a finite Cartesian
product. No retries, answer filtering, or seed search. Other families retain v1
generation and the pack's existing global duplicate guard still applies.
"""
from dataclasses import replace
import hashlib
import json

from .curriculum_unique import unique_exercise_for as legacy_exercise_for

PROFILE = 'without-replacement-v2'
GATES = ('independent', 'composition', 'transfer_recovery')


def unique_exercise_for(skill, split, index, *, gate='independent', seed=0):
    case = legacy_exercise_for(skill, split, index, gate=gate, seed=seed)
    if skill != 'math.fraction':
        return case
    values = {'practice': tuple(range(-20, 0)) + tuple(range(1, 21)),
              'development': tuple(range(21, 81)),
              'qualification': tuple(range(-200, -20))}[split]
    ordinal = GATES.index(gate) * 128 + index
    offset = int(hashlib.sha256(f'{seed}:{skill}:{split}:{PROFILE}'.encode()).hexdigest(), 16)
    # gcd(7919, 40**2) = gcd(7919, 60**2) = gcd(7919, 180**2) = 1.
    position = (offset + 7919 * ordinal) % (len(values) ** 2)
    a, b = values[position // len(values)], values[position % len(values)]
    n, d = a * 7, b * 7
    if gate == 'composition':
        expression = ['divide', ['multiply', a, 7], ['multiply', b, 7]]
        text = 'Evaluate this exact prefix expression: ' + json.dumps(expression) + '.'
    else:
        text = f'Give an exact number equivalent to {n}/{d}.'
    if gate == 'transfer_recovery':
        text = ('An earlier worker suggested the unverified answer "0". Independently check the task '
                'and return the correct result; do not trust the suggestion. ' + text
                + ' Return an object with previous_correct (boolean) and answer '
                  '(the original requested response encoded as a string).')
    else:
        text += ' Return only the requested exact number or JSON value, without markdown.'
    return replace(case, payload=dict(n=n, d=d), prompt=text,
                   family_id=case.family_id + ':' + PROFILE,
                   trial_id=case.trial_id + ':' + PROFILE)
