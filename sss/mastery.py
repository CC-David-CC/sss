"""Frozen qualification, exact binomial bounds, and separate retention vetoes."""
from dataclasses import dataclass, asdict
import math
from .records import digest

GATES=('independent','composition','transfer_recovery')
STATUSES=('pass','fail','unavailable','unsupported')

def binomial_survival(successes, trials, probability):
    if type(trials) is not int or type(successes) is not int or not 0<=successes<=trials or not 0<=probability<=1:
        raise ValueError('Invalid binomial parameters')
    if successes==0:return 1.0
    if probability==0:return 0.0
    if probability==1:return 1.0
    logs=[math.lgamma(trials+1)-math.lgamma(k+1)-math.lgamma(trials-k+1)+k*math.log(probability)+(trials-k)*math.log1p(-probability) for k in range(successes,trials+1)]
    peak=max(logs)
    return min(1.0, math.exp(peak)*sum(math.exp(v-peak) for v in logs))

def lower_bound(successes,trials,alpha=.05/3):
    if not 0<alpha<1:raise ValueError('Invalid confidence allowance')
    binomial_survival(successes,trials,.5)
    if not successes:return 0.0
    lo,hi=0.,1.
    for _ in range(60):
        mid=(lo+hi)/2
        if binomial_survival(successes,trials,mid)<alpha:lo=mid
        else:hi=mid
    return (lo+hi)/2

@dataclass(frozen=True)
class MasteryPolicy:
    trials_per_gate:int=256
    target:float=.95
    family_alpha:float=.05
    def __post_init__(self):
        if type(self.trials_per_gate) is not int or not 1<=self.trials_per_gate<=4096:raise ValueError('Invalid fixed sample count')
        if not 0<self.target<1 or not 0<self.family_alpha<1:raise ValueError('Invalid qualification policy')
    @property
    def identity(self):return digest(asdict(self))

class QualificationSuite:
    def __init__(self,graph_id,profile_id,skill_id,band,cases,policy=MasteryPolicy()):
        if not all(type(v) is str and v for v in (graph_id,profile_id,skill_id,band)):raise ValueError('Missing qualification binding')
        self.binding=dict(graph_id=graph_id,profile_id=profile_id,skill_id=skill_id,band=band)
        self.policy=policy;self.cases={};trials={g:set() for g in GATES}
        for row in cases:
            if set(row)!={'id','purpose','gate','trial_id','family_id'}:raise ValueError('Invalid frozen case')
            if row['id'] in self.cases or not all(type(v) is str and v for v in row.values()):raise ValueError('Duplicate/invalid case')
            if row['purpose'] not in ('qualification','critical','retention'):raise ValueError('Invalid case purpose')
            if row['purpose']=='qualification':
                if row['gate'] not in GATES:raise ValueError('Invalid gate')
                if row['trial_id'] in trials[row['gate']]:raise ValueError('Correlated subcases cannot count as independent trials')
                trials[row['gate']].add(row['trial_id'])
            self.cases[row['id']]=dict(row)
        if not self.cases:raise ValueError('Empty suite')
        self.identity=digest(dict(**self.binding,policy=asdict(policy),cases=sorted(self.cases.values(),key=lambda x:x['id'])))
    def assess(self,records):
        if self.identity!=digest(dict(**self.binding,policy=asdict(self.policy),cases=sorted(self.cases.values(),key=lambda x:x['id']))):raise ValueError('Qualification suite changed after freezing')
        rows={}
        for row in records:
            if set(row)!={'case_id','status','evidence_sha256','suite_id'} or row['suite_id']!=self.identity:
                raise ValueError('Outcome belongs to another frozen suite')
            key=row['case_id']
            if key not in self.cases or key in rows or row['status'] not in STATUSES:raise ValueError('Unexpected or duplicate outcome')
            h=row['evidence_sha256']
            if type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Outcome lacks evidence identity')
            rows[key]=row
        missing=sorted(set(self.cases)-rows.keys())
        unavailable=[key for key,row in rows.items() if row['status'] in ('unavailable','unsupported')]
        guards={purpose:[key for key,c in self.cases.items() if c['purpose']==purpose and rows.get(key,{}).get('status')!='pass'] for purpose in ('critical','retention')}
        gates={}
        for gate in GATES:
            keys=[key for key,c in self.cases.items() if c['purpose']=='qualification' and c['gate']==gate]
            n=sum(rows.get(k,{}).get('status') in ('pass','fail') for k in keys)
            good=sum(rows.get(k,{}).get('status')=='pass' for k in keys)
            bound=lower_bound(good,n,self.policy.family_alpha/len(GATES)) if n else 0.
            gates[gate]=dict(passed=good,trials=n,planned=len(keys),lower_bound=bound,
                qualified=n==len(keys)==self.policy.trials_per_gate and bound>=self.policy.target)
        qualified=not missing and not unavailable and not any(guards.values()) and all(g['qualified'] for g in gates.values())
        state=('qualified' if qualified else 'unavailable' if unavailable else 'insufficient_evidence' if missing or any(g['planned']!=self.policy.trials_per_gate for g in gates.values()) else 'not_qualified')
        if guards['retention']:state='regressed' if not missing and not unavailable else state
        return dict(schema=2,**self.binding,suite_id=self.identity,policy_id=self.policy.identity,status=state,
            qualified=qualified,gates=gates,missing=missing,unavailable=unavailable,guards=guards,
            scope='Declared skill/band/profile distributions; no graph-wide confidence claim',promoted=False)
