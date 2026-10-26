"""Lesson-only framing extension over the unchanged legacy profile contract.

Foundation evaluation identities include profiles.py. New lesson representation
support belongs here and must not rewrite historical curriculum identities.
"""
from .profiles import TARGET_POLICIES, target_segments as _legacy_target_segments

FRAMING_PROTOCOL = 'assistant-framing-always-masked-v1'


def target_segments(segments, policy=TARGET_POLICIES[0]):
    rows=list(segments)
    ordinary=[]
    for row in rows:
        if row['kind']=='framing':
            if row['role']!='assistant' or row.get('verified') is not False:
                raise ValueError('Template framing requires assistant role and verified=False')
        else:
            ordinary.append(row)
    # The legacy validator retains authority over every ordinary span, including
    # allowed roles/kinds, optional thinking targets and verified-answer checks.
    selected=iter(_legacy_target_segments(ordinary,policy))
    return [False if row['kind']=='framing' else next(selected) for row in rows]
