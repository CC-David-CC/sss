"""Explicit division operand permutation for new frozen packs.

Older profiles and nondivision families retain their existing questions. No
retries, answer-dependent filtering or seed search are used.
"""
from dataclasses import replace
import hashlib
import json

from .curriculum_unique_v2 import unique_exercise_for as previous_exercise_for

PROFILE = 'without-replacement-v3'
GATES = ('independent', 'composition', 'transfer_recovery')


def unique_exercise_for(skill, split, index, *, gate='independent', seed=0):
    case = previous_exercise_for(skill, split, index, gate=gate, seed=seed)
    if skill != 'math.divide':
        return case
    values = {'practice': tuple(range(-20, 0)) + tuple(range(1, 21)),
              'development': tuple(range(21, 81)),
              'qualification': tuple(range(-200, -20))}[split]
    ordinal = GATES.index(gate) * 128 + index
    offset = int(hashlib.sha256(f'{seed}:{skill}:{split}:{PROFILE}'.encode()).hexdigest(), 16)
    # 7919 is coprime to 40^2, 60^2 and 180^2; all 384 ordinals are distinct.
    position = (offset + 7919 * ordinal) % (len(values) ** 2)
    a, b = values[position // len(values)], values[position % len(values)]
    expression = ['divide', a, b]
    if gate == 'composition':
        expression = ['add', ['multiply', expression, 3], ['subtract', 7, 2]]
    original = json.dumps(case.payload['expression'])
    if case.prompt.count(original) != 1:
        raise ValueError('Original division question no longer has its expected expression')
    return replace(case, payload=dict(expression=expression),
                   prompt=case.prompt.replace(original, json.dumps(expression), 1),
                   family_id=case.family_id + ':' + PROFILE,
                   trial_id=case.trial_id + ':' + PROFILE)
