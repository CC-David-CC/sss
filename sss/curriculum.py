"""Prerequisite catalog and pure student-day selection, without workflow authority."""
from dataclasses import replace
import random
from .graph import SkillGraph
from .foundations import generate, OPERATORS, SPECIAL

from .catalogue import load_catalog

# The on-disk catalog is authoritative; these views preserve generator APIs.
CATALOG,POLICIES,_GRAPH=load_catalog()
DEFINITIONS=[(k,v['exercise']['family'],v['node']['title'],v['node']['requires'],v['node']['domains']) for k,v in CATALOG.items() if v['exercise']]
PLANNED=[(k,v['node']['title'],v['node']['requires'],v['node']['domains']) for k,v in CATALOG.items() if not v['exercise']]
BY_ID={row[0]:row for row in DEFINITIONS}

def foundation_graph():
    return load_catalog()[2]

def exercise_for(skill,split,index,*,gate='independent',seed=0):
    if skill not in BY_ID:raise ValueError('No implemented generator for '+skill)
    kind=BY_ID[skill][1];case=generate(kind,split,index,gate=gate,seed=seed)
    if skill.startswith(('math.add.','math.subtract.')):
        # Stable subskill shapes; large/signed values are separate from decimal carrying.
        rng=random.Random(case.trial_id+skill)
        digits={'practice':2,'development':3,'qualification':4}[split]
        if skill.endswith('no_carry'):
            aa=[rng.randrange(1,5) for _ in range(digits)];bb=[rng.randrange(0,5) for _ in range(digits)]
        elif skill.endswith('carry'):
            aa=[rng.randrange(6,10) for _ in range(digits)];bb=[rng.randrange(5,10) for _ in range(digits)]
        elif skill.endswith('no_borrow'):
            aa=[rng.randrange(5,10) for _ in range(digits)];bb=[rng.randrange(0,5) for _ in range(digits)]
        elif skill.endswith('borrow'):
            aa=[1]+[rng.randrange(0,4) for _ in range(digits-1)];bb=[0]+[rng.randrange(5,10) for _ in range(digits-1)]
        else:aa=bb=None
        if aa is not None:
            a,b=int(''.join(map(str,aa))),int(''.join(map(str,bb)))
        else:
            a,b=(-rng.randrange(10,10**digits),rng.randrange(10,10**digits))
            if index%4==0:a=0
        expr=[kind,a,b]
        if gate=='composition':expr=['subtract',['add',expr,7],3]
        payload=dict(expression=expr)
        prompt='Evaluate this exact prefix expression: '+__import__('json').dumps(expr)+'. Return the exact number.'
        if gate=='transfer_recovery':prompt+=' An earlier answer was 0. Return JSON with previous_correct (boolean) and answer (the exact response as a string).'
        case=replace(case,payload=payload,prompt=prompt)
    return replace(case,skill_id=skill,family_id=case.family_id+':'+skill,trial_id=case.trial_id+':'+skill)

def student_day(graph,qualified,day,*,weak=(),seed=0):
    if type(day) is not int or day<0:raise ValueError('Invalid day')
    qualified=set(qualified);weak=set(weak)
    if not (qualified|weak)<=set(graph.nodes):raise ValueError('Unknown reported skill')
    ready=[key for key in graph.order if graph.nodes[key]['status']=='implemented' and graph.readiness(key,qualified)['ready']]
    rng=random.Random(f'{seed}:{day}:{graph.identity}');schedule=[]
    rotation=('focus','review','focus','composition','review','focus','review','focus','composition','focus')
    domains=('math','logic','code','linux')
    schedule.append(dict(period='morning',minutes=15,activity='recall',revisit_days=[d for d in (day-1,day-3,day-7) if d>=0]))
    for slot,domain in enumerate(domains):
        purpose=rotation[(day*4+slot)%len(rotation)]
        pool=[k for k in ready if domain in graph.nodes[k]['domains']]
        if not pool:
            schedule.append(dict(period=domain,minutes=60,activity='coverage_unavailable',skill_id=None));continue
        preferred=[k for k in pool if (k in qualified if purpose!='focus' else k in weak or k not in qualified)]
        pool=preferred or pool;key=rng.choice(sorted(pool))
        actual=purpose if purpose=='focus' or key in qualified else 'diagnostic'
        schedule.append(dict(period=domain,minutes=60,activity=actual,skill_id=key,bookmark_after=True))
    schedule.append(dict(period='evening',minutes=30,activity='review_and_questions',archive_required=True))
    return dict(schema=2,graph_id=graph.identity,day=day,schedule=schedule,
                clock='simulated timetable, not wall-clock sleeps',weights_updated=False)
