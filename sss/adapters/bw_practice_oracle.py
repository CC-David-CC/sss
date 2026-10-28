"""Optional fixed practice checker using BW's actual read-only command boundary."""
import hashlib
import json
import ast
import builtins
from pathlib import Path
from sss.practice_oracle import AffineClampFoldCase, MAX_OUTPUT, grade_observation
from sss.records import canonical, digest

# Only rows enter this driver. Expected results remain in the parent S3 process.
DRIVER = '''import json,sys
from pathlib import Path
def pairs(items):
 out={}
 for key,value in items:
  if key in out: raise ValueError('duplicate input key')
  out[key]=value
 return out
def reject(value): raise ValueError('nonfinite input')
rows=json.loads(sys.argv[1],object_pairs_hook=pairs,parse_constant=reject)
space={'__name__':'task'}
exec(compile(Path('task.py').read_bytes(),'task.py','exec'),space)
results=[]
for row in rows:
 results.append(space['solve'](**row))
print(json.dumps(dict(results=results,inputs_after=rows),allow_nan=False,separators=(',',':')))
'''

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_source(source, expected_sha256):
    from sss.adapters.code_check import pure_function, ALLOWED_CALLS
    if type(source) is not bytes or not 0 < len(source) <= 32768:
        raise ValueError('single task.py source must be bounded UTF8 bytes')
    if type(expected_sha256) is not str or hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError('source does not match owner source pin')
    text=source.decode('utf8', errors='strict')
    if not pure_function(text, 'solve'):
        return False
    # The legacy gate is a prerequisite, not a complete authority boundary. Its
    # admitted call spellings must not be rebound to an arbitrary callable.
    tree=ast.parse(text)
    function=tree.body[0]
    args=function.args
    parameters=('values','scale','offset','low','high')
    if (args.posonlyargs or tuple(arg.arg for arg in args.args)!=parameters
            or args.vararg is not None or args.kwarg is not None
            or args.kwonlyargs or args.defaults or args.kw_defaults
            or function.returns is not None or function.type_comment is not None
            or getattr(function,'type_params',())
            or any(arg.annotation is not None or arg.type_comment is not None for arg in args.args)):
        return False
    nodes=list(ast.walk(function))
    if any(isinstance(node,(ast.AnnAssign,ast.Match)) for node in nodes):
        return False
    if any(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node is not function for node in nodes):
        return False
    # Prohibit every builtin binding, not only direct-call spellings. A capture
    # such as [eval for eval in []] is comprehension-local; accepting it as a
    # function-local declaration could otherwise admit global eval as a callback.
    protected=set(vars(builtins))|{'solve'}
    bindings={node.id for node in nodes if isinstance(node,ast.Name) and isinstance(node.ctx,(ast.Store,ast.Del))}
    # ExceptHandler stores its binding as a string, not an ast.Name(Store).
    bindings.update(node.name for node in nodes if isinstance(node,ast.ExceptHandler) and node.name is not None)
    if bindings & protected:
        return False
    names=set(parameters)|bindings|set(ALLOWED_CALLS)|{'solve'}
    return all(node.id in names for node in nodes if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load))

def implementation_pins():
    import sss.practice_oracle as core
    import sss.adapters.code_check as gate
    return dict(checker_implementation_sha256=_sha(core.__file__),
                source_gate_implementation_sha256=_sha(gate.__file__),
                adapter_implementation_sha256=_sha(__file__),
                driver_sha256=hashlib.sha256(DRIVER.encode()).hexdigest())

def observe(case, source, expected_source_sha256, output):
    """Host API, not a model tool. Creates a fresh evidence directory, never overwrites."""
    if type(case) is not AffineClampFoldCase:
        raise ValueError('installed fixed-family case required')
    case.__post_init__()  # Revalidate even a mutated/forged frozen dataclass.
    supported = validate_source(source, expected_source_sha256)
    root = Path(output)
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    result = dict(schema=1, kind='sss.verified-practice-oracle.v1', **case.pins,
                  **implementation_pins(), source_sha256=expected_source_sha256,
                  execution_attempted=False, lesson_approved=False)
    if not supported:
        result.update(status='fail',reason='source contract requires one pure solve function with exact unannotated signature and closed safe names; not executed')
    else:
        # Runtime ownership stays in BW. Importing S3 core does not require BW.
        src=root/'source'; src.mkdir(mode=0o700)
        (src/'task.py').write_bytes(source)
        try:
            from branchwrite.execution import Executor, Grant
            from branchwrite.terminal import NamedCommand, execute_command
            import branchwrite
            command=NamedCommand('practice-oracle',('/usr/bin/python3','-I','-B','-c',DRIVER,case.inputs_json.decode()),5)
            executor=Executor.create(src,root/'world',commands=(command,),project_input=True)
            result.update(execution_attempted=True, operation_id='sss-practice-oracle',
                          command_sha256=digest(command.wire),
                          bw_implementation_sha256=digest({p.name:_sha(p) for p in sorted(Path(branchwrite.__file__).parent.glob('*.py'))}))
            receipt=execute_command(executor,'sss-practice-oracle',Grant((),False,read_paths=('task.py',),command_names=('practice-oracle',)),'practice-oracle')
            raw_out=receipt.stdout.read_bytes(); raw_err=receipt.stderr.read_bytes()
            (root/'stdout.bin').write_bytes(raw_out); (root/'stderr.bin').write_bytes(raw_err)
            result['bw_implementation_after_sha256']=digest({p.name:_sha(p) for p in sorted(Path(branchwrite.__file__).parent.glob('*.py'))})
            unchanged=all(p.read_bytes()==source for p in (src/'task.py',executor.workspace/'task.py'))
            inputs=receipt.details.get('inputs')
            captured=(type(inputs) is list and len(inputs)==1 and type(inputs[0]) is dict
                      and inputs[0].get('path')=='task.py'
                      and type(inputs[0].get('bytes')) is int and inputs[0]['bytes']==len(source)
                      and inputs[0].get('sha256')==expected_source_sha256)
            observation=dict(disposition=receipt.disposition,exit_code=receipt.exit_code,
                stdout=raw_out.decode('utf8',errors='strict'),stderr=raw_err.decode('utf8',errors='replace'),
                stdout_sha256=hashlib.sha256(raw_out).hexdigest(),stderr_sha256=hashlib.sha256(raw_err).hexdigest(),
                output_truncated=receipt.disposition=='output_limit' or max(len(raw_out),len(raw_err))>MAX_OUTPUT,
                captured_execution_source_matches=captured,
                source_unchanged=unchanged,source_before_sha256=expected_source_sha256,
                source_after_sha256=_sha(executor.workspace/'task.py'),original_after_sha256=_sha(src/'task.py'),
                isolation=receipt.details.get('isolation'),details=receipt.details,
                elapsed_seconds=receipt.elapsed_seconds)
            result['observation']=observation
            result.update(grade_observation(case,observation))
            if result['bw_implementation_after_sha256'] != result['bw_implementation_sha256']:
                result.update(status='unavailable',reason='BW implementation changed during observation')
        except (OSError,ValueError,RuntimeError,ImportError) as error:
            result.update(status='unavailable',reason='execution observation unavailable: '+str(error)[:512])
    result['evidence_sha256']=digest(result)
    (root/'result-private.json').write_bytes(canonical(result))
    return result
