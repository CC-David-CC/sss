"""Single-purpose replacement diagnostics; legacy studies remain reproducible.

Boolean truth tables are finite: renaming operands is not additional coverage.
Only direct-answer independent cases are defined here. Reasoning/format scores
must be separate observations, not inferred from these final-answer checks.
"""
from dataclasses import replace
from .curriculum import exercise_for

def cases(skill,split='development',seed=20261028):
    template=exercise_for(skill,split,0,gate='independent',seed=seed)
    rows=[]
    if skill in ('logic.and','logic.or','logic.xor','logic.not'):
        kind=skill.split('.')[-1]
        operands=[(0,),(1,)] if kind=='not' else [(0,0),(0,1),(1,0),(1,1)]
        for values in operands:
            payload={'expression':[kind,*values]}
            prompt=f'Evaluate Boolean {kind.upper()} on '+', '.join(map(str,values))+'. Return 0 or 1.'
            rows.append((payload,prompt))
    elif skill=='math.round':
        # Decimal input tests rounding directly, not fraction conversion.
        for n in (1231,1234,1235,1239,-1231,-1234,-1235,-1239):
            decimal=('-' if n<0 else '')+str(abs(n)//100)+'.'+str(abs(n)%100).zfill(2)
            rows.append((dict(n=n,d=100,places=1),f'Round {decimal} to one decimal place, ties away from zero. Return only the number.'))
    elif skill=='logic.deduction':
        # One purpose: evidence status. No arithmetic or multi-hop proof demand.
        for clauses,query in [([[1]],1),([[1]],-1),([[1]],2),([[1],[-1]],2)]:
            payload=dict(variables=2,clauses=clauses,query=query)
            prompt=('A signed integer denotes a Boolean variable; a negative integer means NOT. '
                    'Each clause must be true. Classify the query as entailed, contradicted, '
                    'undetermined, or inconsistent. Clauses: '+str(clauses)+'. Query: '+str(query)+'. Return only the classification.')
            rows.append((payload,prompt))
    else:raise ValueError('No reviewed primitive replacement for '+skill)
    return tuple(replace(template,payload=p,prompt=t,family_id='primitive-direct-v2:'+skill,
                         trial_id=f'primitive-direct-v2:{split}:{seed}:{skill}:{i}')for i,(p,t)in enumerate(rows))

def expected(case):
    if case.skill_id=='logic.deduction':
        # Closed reference table for the four canonical evidence-status cases.
        return ('entailed','contradicted','undetermined','inconsistent')[int(case.trial_id.rsplit(':',1)[1])]
    from .foundations import reference
    return reference(case)
