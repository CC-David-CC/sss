"""Owned exact foundation exercises, independent effect/equation graders.

Inputs are public task specifications; solutions and graders are host-only.
These bounded families are not claims of general subject mastery.
"""
from dataclasses import dataclass, asdict, replace
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
import hashlib
import json
import math
import random
from .records import digest

from . import extended_math, reasoning
SPLITS=('practice','development','qualification')
OPERATORS=('add','subtract','multiply','divide','remainder','equal','greater','less','minimum','maximum','absolute','power','floor','ceil','and','or','not','xor')
SPECIAL=('place_value','round','fraction','ratio','units','area','volume','linear_equation','quadratic_roots','polynomial_value','polynomial_derivative','definite_integral','dot','matrix_product','linear_system','determinant','eigenvalues','probability','bayes','mean','median','variance','quadratic_minimum','state','deduction','proof')
SPECIAL+=extended_math.KINDS+reasoning.KINDS

@dataclass(frozen=True)
class Exercise:
    skill_id:str
    kind:str
    split:str
    family_id:str
    trial_id:str
    gate:str
    payload:dict
    prompt:str
    @property
    def identity(self):return digest(asdict(self))
    def public(self):return dict(id=self.identity,skill_id=self.skill_id,prompt=self.prompt)

def number(value):
    if type(value) not in (str,int):raise ValueError('Expected an exact integer, decimal or fraction')
    if len(str(value))>1024:raise ValueError('Number too long')
    result=F(value)
    if result.numerator.bit_length()>4096 or result.denominator.bit_length()>4096:raise ValueError('Number too large')
    return result

def rational(value):
    value=F(value)
    return str(value.numerator) if value.denominator==1 else str(value)

def oracle_expression(expr):
    if type(expr) is int:return F(expr)
    if type(expr) is not list or not 2<=len(expr)<=3:raise ValueError('Invalid expression')
    op=expr[0];args=[oracle_expression(v) for v in expr[1:]]
    a=args[0];b=args[-1]
    if op=='add':return a+b
    if op=='subtract':return a-b
    if op=='multiply':return a*b
    if op=='divide':return a/b
    if op=='remainder':return a%b
    if op=='equal':return F(a==b)
    if op=='greater':return F(a>b)
    if op=='less':return F(a<b)
    if op=='minimum':return min(a,b)
    if op=='maximum':return max(a,b)
    if op=='absolute':return abs(a)
    if op=='power':return a**int(b)
    if op=='floor':return F(a.numerator//a.denominator)
    if op=='ceil':return F(-(-a.numerator//a.denominator))
    if op=='and':return F(bool(a) and bool(b))
    if op=='or':return F(bool(a) or bool(b))
    if op=='not':return F(not a)
    if op=='xor':return F(bool(a)!=bool(b))
    raise ValueError('Unknown expression operator')

def reference_expression(expr):
    """Separate Decimal/integer implementation; DIV stays rational for exactness."""
    if type(expr) is int:return F(expr)
    op=expr[0];v=[reference_expression(x) for x in expr[1:]];a=v[0];b=v[-1]
    if op=='add':return F(a.numerator*b.denominator+b.numerator*a.denominator,a.denominator*b.denominator)
    if op=='subtract':return F(a.numerator*b.denominator-b.numerator*a.denominator,a.denominator*b.denominator)
    if op=='multiply':return F(a.numerator*b.numerator,a.denominator*b.denominator)
    if op=='divide':return F(a.numerator*b.denominator,a.denominator*b.numerator)
    if op=='remainder':return a-(a//b)*b
    if op=='power':
        result=F(1)
        for _ in range(abs(int(b))):result*=a
        return result if b>=0 else 1/result
    if op=='floor':return F(math.floor(a))
    if op=='ceil':return F(math.ceil(a))
    if op=='absolute':return a if a>=0 else -a
    if op=='minimum':return a if a<=b else b
    if op=='maximum':return a if a>=b else b
    if op in ('equal','greater','less'):
        difference=a.numerator*b.denominator-b.numerator*a.denominator
        return F({'equal':difference==0,'greater':difference>0,'less':difference<0}[op])
    bits=[int(x!=0) for x in v]
    if op=='and':return F(bits[0]*bits[1])
    if op=='or':return F(min(1,sum(bits)))
    if op=='not':return F(1-bits[0])
    if op=='xor':return F(sum(bits)%2)
    raise ValueError('Unknown reference operator')

def polynomial(coefficients,x):
    result=F(0)
    for value in reversed(coefficients):result=result*x+value
    return result

def _values(text):
    value=json.loads(text,parse_float=str)
    if type(value) is not list or len(value)>32:raise ValueError('Expected a bounded JSON array')
    return [number(v) for v in value]

def _matrix(text):
    value=json.loads(text,parse_float=str)
    if type(value) is not list or not value or len(value)>8:raise ValueError('Invalid matrix')
    if any(type(row) is not list or not row or len(row)!=len(value[0]) or len(row)>8 for row in value):raise ValueError('Invalid matrix rows')
    return [[number(v) for v in row] for row in value]

def _models(p):
    models=[]
    for assignment in range(1<<p['variables']):
        holds=lambda literal: bool(assignment & (1<<abs(literal)-1))==(literal>0)
        if all(any(holds(v) for v in clause) for clause in p['clauses']):models.append(holds(p['query']))
    return models

def check(exercise,completion):
    """Check the requested mathematics/state, not equality to a reference string."""
    if type(completion) is not str or len(completion.encode())>65536:return False
    try:
        p=exercise.payload;k=exercise.kind;t=completion.strip()
        if k in reasoning.KINDS:return reasoning.check(exercise,completion)
        if exercise.gate=='transfer_recovery':
            item=json.loads(t)
            if type(item) is not dict or set(item)!={'previous_correct','answer'} or type(item['previous_correct']) is not bool or type(item['answer']) is not str:return False
            base=replace(exercise,gate='independent')
            return item['previous_correct']==check(base,'0') and check(base,item['answer'])
        if k in extended_math.KINDS:return extended_math.check(k,p,number(t))
        if k in OPERATORS:return number(t)==oracle_expression(p['expression'])
        if k=='place_value':
            if 'expression' in p and oracle_expression(p['expression'])!=p['n']:return False
            return number(t)==abs(p['n'])//10**p['position']%10
        if k=='round':
            scale=10**p['places'];x=F(p['n'],p['d'])*scale
            value=(abs(x).numerator*2+abs(x).denominator)//(2*abs(x).denominator)
            return number(t)==F(value if x>=0 else -value,scale)
        if k=='fraction':return number(t)*p['d']==p['n']
        if k=='ratio':return number(t)*p['a']==p['b']*p['c']
        if k=='units':return number(t)==p['quantity']*F(p['factor_n'],p['factor_d'])
        if k=='area':return number(t)==p['width']*p['height']
        if k=='volume':return number(t)==p['width']*p['height']*p['depth']
        if k=='linear_equation':return p['a']*number(t)+p['b']==p['c']
        if k=='quadratic_roots':
            roots=_values(t)
            return len(roots)==2 and sum(roots)==-p['b'] and roots[0]*roots[1]==p['c']
        if k=='polynomial_value':return number(t)==polynomial(p['coefficients'],F(p['x']))
        if k=='polynomial_derivative':
            candidate=_values(t);source=p['coefficients']
            # Test degree-bound identity by coefficient integration: D(P)=Q iff
            # integrating Q recovers every nonconstant coefficient of P.
            return len(candidate)==len(source)-1 and all(candidate[j]/(j+1)==source[j+1] for j in range(len(candidate)))
        if k=='definite_integral':
            a,b=F(p['a']),F(p['b']);co=p['coefficients']
            # Simpson is exact for the generated degree <=3. Reference uses antiderivatives.
            return number(t)==(b-a)/6*(polynomial(co,a)+4*polynomial(co,(a+b)/2)+polynomial(co,b))
        if k=='dot':
            # Polarization, independent from the reference product loop.
            a,b=p['a'],p['b']
            return 2*number(t)==sum((x+y)**2-x*x-y*y for x,y in zip(a,b))
        if k=='matrix_product':
            answer=_matrix(t);a,b=p['a'],p['b']
            if len(answer)!=2 or any(len(row)!=2 for row in answer):return False
            return all(answer[i][j]==sum(a[i][q]*b[q][j] for q in range(2)) for i in range(2) for j in range(2))
        if k=='linear_system':
            x=_values(t)
            return len(x)==2 and all(sum(a*b for a,b in zip(row,x))==rhs for row,rhs in zip(p['matrix'],p['rhs']))
        if k=='determinant':
            a,b=p['matrix'][0];c,d=p['matrix'][1]
            return number(t)==F(a)*(d-F(c)*b/a)
        if k=='eigenvalues':
            x=_values(t);a,b=p['matrix'][0];c,d=p['matrix'][1]
            return len(x)==2 and sum(x)==a+d and x[0]*x[1]==a*d-b*c
        if k=='probability':return number(t)*p['total']==p['favorable']
        if k=='bayes':return number(t)*(p['true_positive']+p['false_positive'])==p['true_positive']
        if k=='mean':return number(t)*len(p['values'])==sum(p['values'])
        if k=='median':
            x=number(t);v=p['values'];n=len(v)
            return sum(y<x for y in v)<=n//2 and sum(y>x for y in v)<=n//2
        if k=='variance':
            v=p['values'];m=F(sum(v),len(v))
            return number(t)*len(v)==sum((y-m)**2 for y in v)
        if k=='quadratic_minimum':return 2*p['a']*number(t)+p['b']==0 and p['a']>0
        if k=='state':
            state=dict(p['initial'])
            for op in p['operations']:
                previous=dict(state)
                state[op['destination']]=previous[op['source']]+op['offset']
            value=json.loads(t)
            return type(value) is dict and all(type(v) is int for v in value.values()) and value==state
        if k=='deduction':
            models=_models(p)
            wanted='inconsistent' if not models else 'entailed' if all(models) else 'contradicted' if not any(models) else 'undetermined'
            return t==wanted
        if k=='proof':return check_proof(p,json.loads(t))
    except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError):return False
    return False

def check_proof(problem,steps):
    """Tiny modus-ponens kernel. Assumptions are fixed by the exercise."""
    if type(steps) is not list or not 1<=len(steps)<=128:return False
    established=[]
    for step in steps:
        if type(step) is not dict:return False
        if set(step)=={'assumption'}:
            i=step['assumption']
            if type(i) is not int or not 0<=i<len(problem['assumptions']):return False
            established.append(problem['assumptions'][i])
        elif set(step)=={'mp'}:
            refs=step['mp']
            if type(refs) is not list or len(refs)!=2 or any(type(i) is not int or not 0<=i<len(established) for i in refs):return False
            implication,antecedent=(established[i] for i in refs)
            if type(implication) is not list or len(implication)!=3 or implication[0]!='implies' or implication[1]!=antecedent:return False
            established.append(implication[2])
        else:return False
    return established[-1]==problem['conclusion']

def generate(kind,split,index,*,gate='independent',seed=0):
    if kind not in OPERATORS+SPECIAL or split not in SPLITS or type(index) is not int or index<0:raise ValueError('Unknown family/split/index')
    if gate not in ('independent','composition','transfer_recovery'):raise ValueError('Unknown gate')
    if kind in reasoning.KINDS:return reasoning.generate(kind,split,index,gate,seed)
    if kind in extended_math.KINDS:return extended_math.generate(kind,split,index,gate,seed)
    # Separate generator families: new ranges, presentation and composition shapes.
    family=split+'-'+gate+'-'+kind+('-v2' if kind=='place_value' and gate=='composition' else '-v1')
    rng=random.Random(int(hashlib.sha256(f'{seed}:{family}:{index}'.encode()).hexdigest(),16))
    low,high={'practice':(-20,20),'development':(21,80),'qualification':(-200,-21)}[split]
    nz=lambda:rng.choice([v for v in range(low,high+1) if v])
    a,b,c=nz(),nz(),nz();p={}
    if kind in OPERATORS:
        if kind in ('and','or','not','xor'):a,b=rng.randrange(2),rng.randrange(2)
        if kind=='power':b=rng.randrange(0,5)
        expr=[kind,a] if kind in ('absolute','not') else [kind,a,b]
        if kind in ('floor','ceil'):expr=[kind,['divide',a,b]]
        if gate=='composition':expr=['add',['multiply',expr,3],['subtract',7,2]]
        p={'expression':expr};text='Evaluate this exact prefix expression: '+json.dumps(expr)+'. Boolean results are 0 or 1; remainder uses floor division.'
    elif kind=='place_value':
        p=dict(n=abs(a)*10007,position=rng.randrange(5))
        if gate=='composition':
            p['expression']=['add',['multiply',abs(a),10007],['subtract',abs(b)*13,abs(c)]]
            p['n']=int(reference_expression(p['expression']))
            text='First evaluate this exact prefix expression: '+json.dumps(p['expression'])+'. '
            text+=f"Then give the base-10 digit at position {p['position']} in its result; position 0 is units."
        else:text=f"Give the base-10 digit at position {p['position']} in {p['n']}; position 0 is units."
    elif kind=='round':p=dict(n=a*10+5,d=100,places=1);text=f"Round {p['n']}/{p['d']} to {p['places']} decimal places, ties away from zero."
    elif kind=='fraction':p=dict(n=a*7,d=b*7);text=f'Give an exact number equivalent to {a*7}/{b*7}.'
    elif kind=='ratio':p=dict(a=a,b=b,c=c);text=f'If a quantity scales from {a} to {b}, what does {c} scale to by the same factor?'
    elif kind=='units':p=dict(quantity=abs(a),factor_n=1000,factor_d=1);text=f'Convert {abs(a)} kilograms into grams. One kilogram is 1000 grams.'
    elif kind in ('area','volume'):
        p=dict(width=abs(a),height=abs(b));p.update(dict(depth=abs(c)) if kind=='volume' else {})
        text=('Area of a rectangle' if kind=='area' else 'Volume of a rectangular box')+' with dimensions '+json.dumps(p)+' in metres. Return the numeric result in square/cubic metres respectively.'
    elif kind=='linear_equation':p=dict(a=a,b=b,c=c);text=f'Solve {a}*x + ({b}) = {c} for x.'
    elif kind=='quadratic_roots':p=dict(b=-(a+b),c=a*b);text=f"Give both roots, including multiplicity, of x^2 + ({p['b']})*x + ({p['c']}) = 0 as a JSON array."
    elif kind in ('polynomial_value','polynomial_derivative','definite_integral'):
        p=dict(coefficients=[a,b,c,rng.randrange(-9,10)])
        text='Polynomial coefficients, lowest power first: '+json.dumps(p['coefficients'])+'. '
        if kind=='polynomial_value':p['x']=rng.randrange(-3,4);text+=f"Evaluate at x={p['x']}."
        if kind=='polynomial_derivative':text+='Return derivative coefficients lowest power first as a JSON array, retaining trailing zeros.'
        if kind=='definite_integral':p.update(a=0,b=rng.randrange(1,5));text+=f"Give its exact definite integral from 0 to {p['b']}."
    elif kind=='dot':p=dict(a=[a,b,c],b=[c,a,b]);text='Give the dot product of '+json.dumps(p['a'])+' and '+json.dumps(p['b'])+'.'
    elif kind=='matrix_product':p=dict(a=[[a,b],[c,1]],b=[[1,c],[b,a]]);text='Compute A*B as a JSON matrix: '+json.dumps(p)+'.'
    elif kind=='linear_system':
        matrix=[[a,b],[a+1,b]];rhs=[a*c+b*(c+1),(a+1)*c+b*(c+1)]
        p=dict(matrix=matrix,rhs=rhs);text='Solve A*x=b. Return x as a JSON array: '+json.dumps(p)+'.'
    elif kind=='determinant':p=dict(matrix=[[a,b],[c,a]]);text='Give the determinant of '+json.dumps(p['matrix'])+'.'
    elif kind=='eigenvalues':p=dict(matrix=[[a,b],[0,c]]);text='Give both eigenvalues including multiplicity as a JSON array: '+json.dumps(p['matrix'])+'.'
    elif kind=='probability':p=dict(favorable=abs(a),total=abs(a)+abs(b));text=f"A uniform draw has {p['favorable']} favorable outcomes among {p['total']} total outcomes. Give the probability."
    elif kind=='bayes':p=dict(true_positive=abs(a),false_positive=abs(b));text=f'Among positive tests, {abs(a)} are true positives and {abs(b)} are false positives. Give the probability a positive test is a true positive.'
    elif kind in ('mean','median','variance'):
        p=dict(values=[a,b,c,a+b,b-c]);text=f"Give the {'population variance' if kind=='variance' else kind} of {p['values']}."
    elif kind=='quadratic_minimum':p=dict(a=abs(a),b=b,c=c);text=f'Give the minimizer x of {abs(a)}*x^2+({b})*x+({c}).'
    elif kind=='state':
        p=dict(initial=dict(x=a,y=b),operations=[dict(destination=rng.choice(['x','y']),source=rng.choice(['x','y']),offset=nz()) for _ in range(4 if gate=='independent' else 12)])
        text='Execute these assignments in order; each reads the state before that assignment. Return the final register dictionary: '+json.dumps(p)+'.'
    elif kind=='deduction':
        # Clause [-1,2] means NOT P1 OR P2. The query varies across all truth statuses.
        query=rng.choice([1,2,3,4,-1,-3]);p=dict(variables=4,clauses=[[1],[-1,2],[-2,3]],query=query)
        text='Clauses use signed variable numbers; a negative number means NOT. Classify the query as entailed, contradicted, undetermined or inconsistent: '+json.dumps(p)+'.'
    elif kind=='proof':
        length=3 if gate=='independent' else 6;names=[f'P{rng.randrange(1000)}_{i}' for i in range(length)]
        assumptions=[names[0]]+[['implies',names[i],names[i+1]] for i in range(length-1)]
        p=dict(assumptions=assumptions,conclusion=names[-1]);text='Prove the conclusion using a JSON array of steps. A step is {"assumption": i} (zero-based fixed assumption), or {"mp": [implication_step, antecedent_step]} referencing earlier steps. '+json.dumps(p)
    if gate=='transfer_recovery':
        text='An earlier worker suggested the unverified answer "0". Independently check the task and return the correct result; do not trust the suggestion. '+text
    if gate=='transfer_recovery':
        text+=' Return an object with previous_correct (boolean) and answer (the original requested response encoded as a string).'
    elif kind not in ('deduction','proof'):text+=' Return only the requested exact number or JSON value, without markdown.'
    return Exercise('foundation.'+kind,kind,split,family,f'{seed}:{family}:{index}',gate,p,text)

def reference(exercise):
    if exercise.kind in reasoning.KINDS:return reasoning.reference(exercise)
    if exercise.gate=='transfer_recovery':
        answer=reference(replace(exercise,gate='independent'))
        return json.dumps(dict(previous_correct=answer=='0',answer=answer))
    p=exercise.payload;k=exercise.kind
    if k in extended_math.KINDS:return rational(extended_math.reference(k,p))
    if k in OPERATORS:value=reference_expression(p['expression'])
    elif k=='place_value':value=int(str(abs(p['n'])).zfill(p['position']+1)[-1-p['position']])
    elif k=='round':value=F(str((Decimal(p['n'])/Decimal(p['d'])).quantize(Decimal(10)**-p['places'],rounding=ROUND_HALF_UP)))
    elif k=='fraction':value=F(p['n'],p['d'])
    elif k=='ratio':value=F(p['b'],p['a'])*p['c']
    elif k=='units':value=F(p['quantity']*p['factor_n'],p['factor_d'])
    elif k in ('area','volume'):value=math.prod(p.values())
    elif k=='linear_equation':value=F(p['c']-p['b'],p['a'])
    elif k=='quadratic_roots':
        d=math.isqrt(p['b']**2-4*p['c']);return json.dumps([rational(F(-p['b']-d,2)),rational(F(-p['b']+d,2))])
    elif k=='polynomial_value':value=sum(F(c)*p['x']**i for i,c in enumerate(p['coefficients']))
    elif k=='polynomial_derivative':return json.dumps([i*c for i,c in enumerate(p['coefficients']) if i])
    elif k=='definite_integral':value=sum(F(c,i+1)*(p['b']**(i+1)-p['a']**(i+1)) for i,c in enumerate(p['coefficients']))
    elif k=='dot':value=sum(a*b for a,b in zip(p['a'],p['b']))
    elif k=='matrix_product':return json.dumps([[p['a'][i][0]*p['b'][0][j]+p['a'][i][1]*p['b'][1][j] for j in range(2)] for i in range(2)])
    elif k=='linear_system':
        a,b=p['matrix'][0];c,d=p['matrix'][1];u,v=p['rhs'];det=a*d-b*c
        return json.dumps([rational(F(u*d-b*v,det)),rational(F(a*v-u*c,det))])
    elif k=='determinant':a,b=p['matrix'][0];c,d=p['matrix'][1];value=a*d-b*c
    elif k=='eigenvalues':return json.dumps([p['matrix'][0][0],p['matrix'][1][1]])
    elif k=='probability':value=F(p['favorable'],p['total'])
    elif k=='bayes':value=F(p['true_positive'],p['true_positive']+p['false_positive'])
    elif k=='mean':value=F(sum(p['values']),len(p['values']))
    elif k=='median':value=sorted(p['values'])[len(p['values'])//2]
    elif k=='variance':v=p['values'];value=F(sum(x*x for x in v),len(v))-F(sum(v),len(v))**2
    elif k=='quadratic_minimum':value=-F(p['b'],2*p['a'])
    elif k=='state':
        x,y=p['initial']['x'],p['initial']['y']
        for op in p['operations']:
            value=(x if op['source']=='x' else y)+op['offset']
            if op['destination']=='x':x=value
            else:y=value
        return json.dumps(dict(x=x,y=y))
    elif k=='deduction':
        # Forward chaining in this Horn family, independently of truth-table grading.
        known={clause[0] for clause in p['clauses'] if len(clause)==1}
        while True:
            new=known|{b for a,b in (cl for cl in p['clauses'] if len(cl)==2) if -a in known}
            if new==known:break
            known=new
        return 'entailed' if p['query'] in known else 'contradicted' if -p['query'] in known else 'undetermined'
    elif k=='proof':
        steps=[dict(assumption=0)];last=0
        for index in range(1,len(p['assumptions'])):
            implication=len(steps);steps.append(dict(assumption=index));steps.append(dict(mp=[implication,last]));last=len(steps)-1
        return json.dumps(steps)
    else:raise ValueError('No reference for '+k)
    return rational(value)
