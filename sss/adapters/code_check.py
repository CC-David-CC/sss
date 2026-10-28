"""Host-side behavior grading; student exit code cannot forge checker success."""
import ast
import hashlib
import json
from pathlib import Path
from .linux_sandbox import read_owned,inventory
from sss.records import digest

ALLOWED_CALLS={'len','range','enumerate','sum','min','max','abs','sorted','set','list','dict','tuple','int','bool'}
ALLOWED_METHODS={'append','add','get','items','keys','values','count','index','pop'}

def pure_function(source,name):
    try:tree=ast.parse(source)
    except SyntaxError:return False
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!=name:return False
    if tree.body[0].decorator_list:return False
    if len(list(ast.walk(tree)))>2048:return False
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Lambda,ast.Global,ast.Nonlocal,ast.With,ast.AsyncWith,ast.Await,ast.Yield,ast.YieldFrom)):return False
        if isinstance(node,ast.Name) and node.id.startswith('_'):return False
        if isinstance(node,ast.Attribute) and node.attr not in ALLOWED_METHODS:return False
        if isinstance(node,ast.Call):
            if isinstance(node.func,ast.Name):
                if node.func.id not in ALLOWED_CALLS|{name}:return False
            elif isinstance(node.func,ast.Attribute):
                if node.func.attr not in ALLOWED_METHODS:return False
            else:return False
    return True

def run_check(case,boundary):
    work=boundary.workspace;observations=[];passed=False;reason=''
    source_name='app.py' if case.id in ('python.double','python.triple.practice') else 'task.py' if case.language=='python' else 'copy.sh' if case.id=='shell.quoted_filename' else 'check.sh'
    module_name='app' if case.id in ('python.double','python.triple.practice') else 'task'
    source=read_owned(work,source_name).decode()
    if case.language=='python':
        name={'python.sum_empty':'total','python.binary_search':'locate','python.stable_unique':'unique','python.double':'double','python.triple.practice':'triple'}[case.id]
        if not pure_function(source,name):reason='This foundation task requires one pure function; unsupported source was not executed'
        else:
            if case.id=='python.double':
                inputs=[[-1000000],[-7],[-1],[0],[1],[7],[1000000]]
                expected=[2*v[0] for v in inputs]
            elif case.id=='python.triple.practice':
                inputs=[[-1000000],[-11],[-1],[0],[1],[11],[1000000]]
                expected=[3*v[0] for v in inputs]
            elif case.id=='python.sum_empty':inputs=[[v] for v in ([],[0],[-3,4,12],list(range(-30,31)))];expected=[sum(v[0]) for v in inputs]
            elif case.id=='python.binary_search':
                inputs=[[xs,target] for xs in ([],[1],[1,1,2,4,4],list(range(-30,31))) for target in range(-32,33)]
                expected=[xs.index(target) if target in xs else -1 for xs,target in inputs]
            else:
                inputs=[[xs] for xs in ([],[3,1,3,2,1],[0,-1,0,-1,4])]
                expected=[[v for i,v in enumerate(xs) if v not in xs[:i]] for [xs] in inputs]
            # Only inputs enter the student process. Expected results stay here.
            driver='import json,'+module_name+'\ninputs=json.loads('+repr(json.dumps(inputs))+')\nresults=[]\nfor args in inputs:\n results.append('+module_name+'.'+name+'(*args))\nprint(json.dumps(dict(results=results,inputs_after=inputs)))\n'
            observation=boundary.run(['/usr/bin/python3','-c',driver]);observations.append(observation)
            try:
                actual=json.loads(observation['stdout'])
                passed=observation['exit_code']==0 and not observation['timed_out'] and not observation['output_truncated'] and actual==dict(results=expected,inputs_after=inputs)
            except (ValueError,TypeError):passed=False
            reason='' if passed else 'Independent host-side return-value/input-preservation checks failed'
    elif case.id=='shell.quoted_filename':
        passed=True
        for src,dst in [('source one.txt','dest two.txt'),('semi;colon.txt','literal $name.txt')]:
            raw='one\nUnicode: \u03b1\n'.encode();(work/src).write_bytes(raw)
            observation=boundary.run(['/bin/sh','copy.sh',src,dst]);observations.append(observation)
            try:matches=read_owned(work,dst)==raw
            except (ValueError,FileNotFoundError):matches=False
            passed=passed and matches and observation['exit_code']==0
        reason='' if passed else 'Copied file bytes or shell status differ'
    else:
        passed=True
        for text,success in [('READY\n',True),('not ready\n',False)]:
            (work/'input file').write_text(text)
            observation=boundary.run(['/bin/sh','check.sh','input file']);observations.append(observation)
            passed=passed and not observation['timed_out'] and (observation['exit_code']==0)==success
        reason='' if passed else 'Shell exit status does not match observed input'
    allowed=set(case.before)
    if case.id=='shell.quoted_filename':allowed|={'source one.txt','dest two.txt','semi;colon.txt','literal $name.txt'}
    if case.id=='shell.failure_status':allowed.add('input file')
    current=inventory(work)
    if set(current)-allowed:passed=False;reason='Unexpected files outside the declared fixture outputs'
    if any(v['kind']=='symlink' for v in current.values()):passed=False;reason='Symlink cannot substitute for an owned output'
    result=dict(kind='host-verdict',passed=bool(passed),reason=reason,settled=True,checker_id=digest(case.check_program),
                checker_implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                observations=observations,after=current)
    result['evidence_sha256']=digest(result);return result
