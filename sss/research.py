"""Controlled computing-lab research fixtures and independently checked findings.

The host creates environments. These functions measure actual algorithmic
comparison counts, not fabricated wall-clock performance or general research ability.
"""
import bisect,hashlib,json,random
from .records import digest

def experiment(seed,size,queries):
    if any(type(v) is not int for v in (seed,size,queries)) or not 2<=size<=4096 or not 1<=queries<=1024:raise ValueError('Bounded owned experiment required')
    rng=random.Random(seed);data=rng.sample(range(size*8),size);targets=[rng.randrange(size*8) for _ in range(queries)];comparisons=0
    def merge_sort(xs):
        nonlocal comparisons
        if len(xs)<2:return xs[:]
        a=merge_sort(xs[:len(xs)//2]);b=merge_sort(xs[len(xs)//2:]);out=[];i=j=0
        while i<len(a) and j<len(b):
            comparisons+=1
            if a[i]<=b[j]:out.append(a[i]);i+=1
            else:out.append(b[j]);j+=1
        return out+a[i:]+b[j:]
    ordered=merge_sort(data);sort_cost=comparisons;linear_cost=binary_cost=0;linear=[];binary=[]
    for target in targets:
        hit=False
        for value in data:
            linear_cost+=1
            if value==target:hit=True;break
        linear.append(hit);lo=0;hi=len(ordered)
        while lo<hi:
            mid=(lo+hi)//2;binary_cost+=1
            if ordered[mid]<target:lo=mid+1
            else:hi=mid
        binary_cost+=1;binary.append(lo<len(ordered) and ordered[lo]==target)
    # Independent membership oracle, including absent queries.
    expected=[target in set(data) for target in targets]
    if linear!=expected or binary!=expected or ordered!=sorted(data):raise AssertionError('Experiment implementation failed its control')
    row=dict(schema=1,seed=seed,size=size,queries=queries,input_sha256=digest(dict(data=data,targets=targets)),metric='key_comparisons_including_sort',sort_cost=sort_cost,linear_cost=linear_cost,binary_query_cost=binary_cost,indexed_total=sort_cost+binary_cost,outputs_agree=True)
    row['id']=digest(row);return row

def finding(rows):
    if not rows:raise ValueError('Measurements required')
    for row in rows:
        if row!=experiment(row['seed'],row['size'],row['queries']):raise ValueError('Measurement cannot be reproduced')
    wins=[r['id'] for r in rows if r['indexed_total']<r['linear_cost']]
    losses=[r['id'] for r in rows if r['indexed_total']>=r['linear_cost']]
    return dict(question='Does sorting plus binary search always use fewer comparisons than repeated linear search?',universal_claim_refuted=bool(losses),indexed_wins=wins,other_cases=losses,established='Reproduced comparison counts for declared inputs only',not_established=['wall-clock speed','all input distributions','autonomous scientific capability'],measurement_ids=[r['id'] for r in rows])

def check_finding(rows,answer):
    try:
        value=json.loads(answer);expected=finding(rows)
        return type(value) is dict and value==expected
    except (ValueError,KeyError,TypeError):return False
