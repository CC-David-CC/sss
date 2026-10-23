"""Fine-grained rational, decimal and percentage exercise families."""
from fractions import Fraction as F
import hashlib,json,random
KINDS=('fraction_add','fraction_subtract','fraction_multiply','fraction_divide','fraction_compare','decimal_add','decimal_subtract','decimal_multiply','decimal_divide','percent_of','percent_change','percent_reverse','perimeter','triangle_area')

def generate(kind,split,index,gate,seed):
    from .foundations import Exercise
    if split not in ('practice','development','qualification') or type(index) is not int or index<0 or gate not in ('independent','composition','transfer_recovery'):raise ValueError('Invalid exercise coordinates')
    family=split+'-'+gate+'-'+kind+'-v1';rng=random.Random(int(hashlib.sha256(f'{seed}:{family}:{index}'.encode()).hexdigest(),16))
    low,high={'practice':(1,20),'development':(21,99),'qualification':(100,999)}[split]
    a,b=rng.randint(low,high),rng.randint(low,high);ad,bd=rng.randint(2,12),rng.randint(2,12)
    if kind.startswith('decimal_'):ad,bd=100,100
    p=dict(a=a,b=b,ad=ad,bd=bd)
    op=kind.split('_')[-1]
    if kind.startswith(('fraction_','decimal_')):
        show=lambda n,d:str(F(n,d)) if kind.startswith('fraction') else f'{n//100}.{n%100:02d}'
        text=(f'Is {show(a,ad)} less than {show(b,bd)}? Return 1 for yes or 0 for no.' if op=='compare' else f"Compute {show(a,ad)} {dict(add='+',subtract='-',multiply='*',divide='/')[op]} {show(b,bd)} exactly.")
    elif kind=='percent_of':text=f'What is {a}% of {b}?'
    elif kind=='percent_change':text=f'A value changes from {a} to {b}. Give the signed percentage change as a number, without a percent sign.'
    elif kind=='percent_reverse':text=f'{a}% of an unknown amount is {b}. What is the original amount?'
    elif kind=='perimeter':text=f'A rectangle has sides {a} and {b} metres. Give its perimeter in metres.'
    else:text=f'A triangle has base {a} and perpendicular height {b} metres. Give its area in square metres.'
    if gate=='composition':p['post_scale']=3;p['post_offset']=-2;text+=' Then multiply your result by 3 and subtract 2; return only that final number.'
    if gate=='transfer_recovery':text+=' An earlier answer was 0. Return JSON with previous_correct (boolean) and answer (the exact response as a string).'
    else:text+=' An exact fraction or decimal is acceptable.'
    return Exercise(kind,kind,split,family,family+':'+str(seed)+':'+str(index),gate,p,text)

def reference(kind,p):
    a,b,ad,bd=(p[k] for k in ('a','b','ad','bd'));x,y=F(a,ad),F(b,bd)
    if kind.endswith('_add'):v=x+y
    elif kind.endswith('_subtract'):v=x-y
    elif kind.endswith('_multiply'):v=x*y
    elif kind.endswith('_divide'):v=x/y
    elif kind=='fraction_compare':v=F(x<y)
    elif kind=='percent_of':v=F(a*b,100)
    elif kind=='percent_change':v=F(100*(b-a),a)
    elif kind=='percent_reverse':v=F(100*b,a)
    elif kind=='perimeter':v=F(2*(a+b))
    elif kind=='triangle_area':v=F(a*b,2)
    else:raise ValueError('Unknown extended arithmetic')
    return v*p.get('post_scale',1)+p.get('post_offset',0)

def check(kind,p,value):
    # Grading checks denominator-cleared equations, independent of Fraction
    # arithmetic in the reference solution.
    a,b,ad,bd=(p[k] for k in ('a','b','ad','bd'));x=(value-p.get('post_offset',0))/p.get('post_scale',1)
    if kind.endswith('_add'):return x*ad*bd==a*bd+b*ad
    if kind.endswith('_subtract'):return x*ad*bd==a*bd-b*ad
    if kind.endswith('_multiply'):return x*ad*bd==a*b
    if kind.endswith('_divide'):return x*b*ad==a*bd
    if kind=='fraction_compare':return x==int(a*bd<b*ad)
    if kind=='percent_of':return x*100==a*b
    if kind=='percent_change':return x*a==100*(b-a)
    if kind=='percent_reverse':return x*a==100*b
    if kind=='perimeter':return x/2-a==b
    if kind=='triangle_area':return x*2==a*b
    return False
