"""Versioned logic variations for the 66-skill mixed curriculum.

Boolean truth tables are finite. Different split wordings may share the same
truth-table input; they are not independent semantic samples. Composition uses
Boolean operations only. Existing historical generator profiles remain intact.
"""
from dataclasses import replace
import json

from .curriculum_unique import unique_exercise_for

PROFILE='mixed66-v1'
_BOOLEAN={'logic.and','logic.or','logic.not','logic.xor'}
_INTRO={'practice':'Compute the value of this prefix expression: ',
        'development':'Evaluate this prefix expression: ',
        'qualification':'Determine the value of this prefix expression: '}
_QUERIES=(1,-1,2,-2,3,-3,4,-4)


def exercise_for(skill,split,index,*,gate='independent',seed=0):
    case=unique_exercise_for(skill,split,index,gate=gate,seed=seed)
    if skill in _BOOLEAN:
        op=skill.split('.')[-1]
        operands=((0,),(1,)) if op=='not' else ((0,0),(0,1),(1,0),(1,1))
        if split!='practice' and index>=len(operands):
            raise ValueError('Finite Boolean truth table exhausted for this gate')
        values=operands[index%len(operands)]
        expr=[op,*values]
        if gate=='composition':expr=['not',['not',expr]]
        text=_INTRO[split]+json.dumps(expr)+'. Boolean results are 0 or 1.'
        if gate=='transfer_recovery':
            text=('An earlier worker suggested the unverified answer "0". Independently check the task and return the correct result; do not trust the suggestion. '+text
                  +' Return an object with previous_correct (boolean) and answer (the original requested response encoded as a string).')
        else:text+=' Return only the requested exact number, without markdown.'
        return replace(case,payload={'expression':expr},prompt=text,
                       family_id=case.family_id+':'+PROFILE,trial_id=case.trial_id+':'+PROFILE)
    if skill=='logic.deduction':
        if split!='practice' and index>=len(_QUERIES):
            raise ValueError('Deduction query family exhausted for this gate')
        clauses={'practice':[[1],[-1,2]],
                 'development':[[1,2],[-1,3],[-2,3]],
                 'qualification':[[1],[2],[-1,-2,3]]}[split]
        clauses=[list(row) for row in clauses]
        if gate=='composition':clauses.append([-3,4])
        payload=dict(variables=4,clauses=clauses,query=_QUERIES[index%len(_QUERIES)])
        text=('Clauses use signed variable numbers; a negative number means NOT. '
              'Classify the query as entailed, contradicted, undetermined or inconsistent: '+json.dumps(payload)+'.')
        if gate=='transfer_recovery':
            text=('An earlier worker suggested the unverified answer "0". Independently check the task and return the correct result; do not trust the suggestion. '+text
                  +' Return an object with previous_correct (boolean) and answer (the original requested response encoded as a string).')
        return replace(case,payload=payload,prompt=text,
                       family_id=case.family_id+':'+PROFILE,trial_id=case.trial_id+':'+PROFILE)
    return case
