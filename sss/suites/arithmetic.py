"""Owned practice and disjoint check families for the starter arithmetic tree."""
import argparse
import hashlib
import json
from pathlib import Path
from sss.records import digest
from .legacy_ceiling import check
from sss.guard import SkillTree

KINDS={'add':('Addition','a+b'), 'multiply':('Multiplication','a*b'),
       'abs':('Absolute value','abs(a)'), 'floor':('Signed floor division','a//b'),
       'ceil':('Signed ceiling division','-(-a//b)')}

def generated(kind,split,count):
    descriptions={
        'add':['sum a and b','add a to b','integer addition'],
        'multiply':['multiply a by b','product of a and b','integer multiplication'],
        'abs':['absolute value of a','magnitude of signed a','nonnegative distance of a from zero'],
        'floor':['floor(a/b)','round a/b toward minus infinity','signed floor division'],
        'ceil':['ceil(a/b)','round a/b toward plus infinity','signed ceiling division']}
    statements={
        'add':('Find the sum of the two integers.','Combine both operands by addition.'),
        'multiply':('Compute the integer product of both arguments.','Return the multiplication result for the operands.'),
        'abs':('Give the nonnegative magnitude of the argument.','Find how far the argument is from zero.'),
        'floor':('Return the greatest integer no larger than the exact ratio.','Use the lower integer bound of the quotient.'),
        'ceil':('Return the least integer no smaller than the exact ratio.','Use the upper integer bound of the quotient.')}
    for index in range(count):
        if split=='practice':
            a,b=[('a','b'),('x','y'),('top','bottom'),('value','divisor')][index%4]
            description=descriptions[kind][index%3].replace('a/b',a+'/'+b)
            # Word substitution cannot corrupt other words (e.g. absolute).
            import re
            description=re.sub(r'\ba\b',a,description);description=re.sub(r'\bb\b',b,description)
            function='practice_'+kind+'_'+str(index)
        elif split=='validation':
            a,b=[('numerator','denominator'),('left','right')][index%2]
            description=statements[kind][0]+' Check '+str(index)+'.';function='verify_'+hashlib.sha256(kind.encode()).hexdigest()[:6]+'_'+str(index)
        else:
            a,b=[('first','second'),('u','v')][index%2]
            description=statements[kind][1]+' Trial '+str(index)+'.';function='sealed_'+hashlib.sha256(('blind-'+kind).encode()).hexdigest()[:6]+'_'+str(index)
        parameters=[a] if kind=='abs' else [a,b]
        prompt='# '+description+'\ndef '+function+'('+','.join(parameters)+'):\n    return'
        expression=KINDS[kind][1]
        import re
        expression=re.sub(r'\ba\b',a,expression);expression=re.sub(r'\bb\b',b,expression)
        row=dict(id=hashlib.sha256(prompt.encode()).hexdigest(),prompt=prompt,parameters=parameters,kind=kind)
        completion=' '+expression+'\n'
        if not check(row,completion)['passed']:raise ValueError('Generated teaching target failed independent arithmetic checks')
        yield row,completion
