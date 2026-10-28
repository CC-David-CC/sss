"""Observe a check through BW's actual interpreter, grants and OS boundary.

The host supplies the program variant and exact check. No language model runs.
The existing S3 code checker grades a separate copy of the saved program.
"""
from pathlib import Path
import hashlib, json
from ..records import digest
from .linux_sandbox import EnvironmentUnavailable, LinuxSandbox, read_owned
from .code_check import run_check


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def observe(case, files, command, output):
    # Optional dependency: the S3 core remains importable without BW or NumPy.
    import branchwrite
    from branchwrite.execution import Executor, Grant
    from branchwrite.terminal import ShellConfig
    from branchwrite.tool_registry import ToolRegistry
    from branchwrite.records import RuntimeLog, encode
    from branchwrite.kernel import FrameKernel
    from branchwrite.interpreter import Interpreter, Value
    if (type(files) is not dict or set(files)!=set(case.before)
            or any(type(text) is not str for text in files.values())
            or type(command) is not str or not 0<len(command.encode())<=16384):
        raise ValueError('Exact owned program files and a bounded check command required')
    root=Path(output)
    root.mkdir(mode=0o700,parents=True,exist_ok=False)
    source=root/'source';source.mkdir(mode=0o700)
    for name,text in files.items():
        path=Path(name)
        if path.is_absolute() or not path.parts or any(part in ('..','.') for part in path.parts):
            raise ValueError('Owned project-relative source paths required')
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf8') as stream:stream.write(text)
    before={name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()}
    executor=Executor.create(source,root/'world',shell=ShellConfig(timeout=5),project_input=True)
    registry=ToolRegistry(executor,Grant((),False,allow_shell=True,project_files=True))
    program=('FLOW sensitivity\n'
        'PLAN freeze from=check against=world -> plan\n'
        'ACT execute plan=plan -> checked\n'
        'PLAN final from=finish against=world -> finish-plan\n'
        'ACT close plan=finish-plan -> outcome\n'
        'VERIFY verify contract=project-checks-and-finish input=outcome -> verified\nEND\n')
    with RuntimeLog(root/'ledger') as log:
        runtime=Interpreter(FrameKernel(log),registry,verification=dict(schema=1,selected_checks=True))
        runtime.start(program,dict(
            check=Value('ToolProposal',json.dumps(dict(tool='run_check',arguments=dict(name='behavior',command=command)))),
            finish=Value('ToolProposal',json.dumps(dict(tool='finish',arguments=dict(answer='Host-controlled check-quality probe; not a model answer'))))))
        result=runtime.run()
        if result.status!='complete':raise ValueError('BW probe did not reach its recorded workflow boundary')
        outcome=result.value['bindings']['checked'][1]
        identity=runtime.identity
        outcome_sha=hashlib.sha256(encode(outcome)).hexdigest()
    captured={name:read_owned(executor.workspace,name) for name in files}
    unchanged=all(hashlib.sha256(captured[name]).hexdigest()==before[name] and _sha(source/name)==before[name] for name in files)
    truth_dir=root/'independent';truth_dir.mkdir(mode=0o700)
    for name,raw in captured.items():
        path=truth_dir/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    truth=run_check(case,LinuxSandbox(truth_dir))
    with (root/'independent-private.json').open('x') as stream:json.dump(truth,stream,indent=2)
    if (truth.get('settled') is not True or any(row.get('settled') is not True or row.get('timed_out') is not False or row.get('output_truncated') is not False for row in truth.get('observations',[]))):
        raise EnvironmentUnavailable('Independent oracle did not complete a bounded observation')
    isolation=outcome['details'].get('isolation',{})
    bw_root=Path(branchwrite.__file__).resolve().parent
    implementation=digest({str(p.relative_to(bw_root)):_sha(p) for p in sorted(bw_root.glob('*.py'))})
    value=dict(schema=1,kind='sss.bw-check-observation.v1',case_id=case.id,
        program_sha256=digest(before),command_sha256=hashlib.sha256(command.encode()).hexdigest(),
        checker_id=truth['checker_id'],checker_implementation_sha256=truth['checker_implementation_sha256'],
        oracle_passed=truth['passed'],oracle_evidence_sha256=truth['evidence_sha256'],
        tool_disposition=outcome['disposition'],tool_exit_code=outcome['exit_code'],
        namespace_retired=isolation.get('worker_exited') is True and isolation.get('namespace_members_after')==[],
        source_unchanged=unchanged,bw_ledger_sha256=_sha(root/'ledger/events.bwl'),
        bw_outcome_sha256=outcome_sha,bw_interpreter_id=identity,bw_implementation_sha256=implementation)
    with (root/'observation.json').open('x') as stream:json.dump(value,stream,indent=2)
    return value
