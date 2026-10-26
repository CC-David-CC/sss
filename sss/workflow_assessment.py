"""Protected BW workflow observations, separate from artifact-only correctness."""
import hashlib

from sss.records import canonical,digest

SENTINEL=b'Owned input; preserve these bytes.\n'
RECIPE=dict(schema=1,project_files=True,thinking_mode='off',
    instruction_style='compact-finish-request',shell_timeout=10,
    required_order=['read_file','edit-task.py','current-passing-check','finish'],
    oracle='fixed isolated affine-clamp-fold; hidden rows never in prompt')


def workflow_question(case):
    from sss.adapters.bw_verified_practice import TASK
    case.__post_init__()
    return (TASK+'\n\nInspect task.py and save the repair there. Preserve the public interface '
        'and preserve-input.txt exactly. Use the file tools, run a separate terminal check '
        'of your repair, and explicitly finish. Work only inside the prepared project. '
        'Do not put test code or extra functions at module top level in task.py.')


def create_project(case,directory):
    directory.mkdir(mode=0o700)
    for name,raw,mode in [('task.py',case.baseline_source,case.source_mode),
                          ('preserve-input.txt',SENTINEL,0o644)]:
        p=directory/name;p.write_bytes(raw);p.chmod(mode)


def original_project(case,directory):
    expected={'task.py':(case.baseline_source,case.source_mode),
              'preserve-input.txt':(SENTINEL,0o644)}
    if directory.is_symlink() or not directory.is_dir() or {p.name for p in directory.iterdir()}!=set(expected):
        raise ValueError('Original workflow project inventory changed')
    for name,(raw,mode) in expected.items():
        p=directory/name
        if p.is_symlink() or not p.is_file() or p.read_bytes()!=raw or p.stat().st_mode&0o777!=mode:
            raise ValueError('Original workflow project bytes/mode changed')


def make_launch(case,project,connection,limits):
    from branchwrite.coding_cli import build_launch
    launch=build_launch(project,workflow_question(case),connection,
        branch='sss-workflow-'+case.identity,project_files=True,thinking_mode='off',
        instruction_style=RECIPE['instruction_style'],shell_timeout=RECIPE['shell_timeout'])
    launch['config']['profiles']['control'].update(request_tokens=limits['maximum_tokens'],
        max_requests=limits['maximum_requests'],
        max_output_tokens=limits['maximum_tokens']*limits['maximum_requests'])
    return launch


def observe_capture(case,capture,expected_launch):
    """Regrade already archived BW evidence; never execute tools or inference."""
    from branchwrite.lesson_capture import read_capture,_inventory
    from branchwrite.records import RuntimeLog,Artifact,decode
    from branchwrite.kernel import FrameKernel
    checked=read_capture(capture.directory,expected_capture_id=capture.capture_id)
    value=checked.manifest
    if value['kind']!='assessment' or canonical(value['launch'])!=canonical(expected_launch):
        raise ValueError('Original standalone workflow launch/capture changed')
    baseline=[dict(path='task.py',sha256=hashlib.sha256(case.baseline_source).hexdigest(),mode=case.source_mode),
              dict(path='preserve-input.txt',sha256=hashlib.sha256(SENTINEL).hexdigest(),mode=0o644)]
    if value['evidence']['baseline_inventory']!=_inventory(baseline,[]):
        raise ValueError('Workflow baseline differs from frozen task')
    files={row['path']:row for row in value['files']}
    if set(files)!={'task.py','preserve-input.txt'} or value['directories']:
        raise ValueError('Unexpected workflow artifact inventory')
    source=checked.file_bytes('task.py')
    preserved=(checked.file_bytes('preserve-input.txt')==SENTINEL
               and files['preserve-input.txt']['mode']==0o644
               and files['task.py']['mode']==case.source_mode)
    tools=value['evidence']['tools'];events=[]
    with RuntimeLog(checked.directory/'ledger',read_only=True) as log:
        frames={f['id']:f for f in FrameKernel(log).frames()}
        for row in tools:
            frame=frames[row['frame']];plan=decode(log.read_artifact(Artifact(*frame['inputs'])))
            events.append((row['frame'],row['tool'],plan[4]))
    current={c['frame'] for c in value['evidence']['checks'] if c['current'] and c['exit_code']==0}
    read=[i for i,(_,t,a) in enumerate(events) if t=='read_file' and a.get('path')=='task.py']
    edit=[i for i,(_,t,a) in enumerate(events)
          if t in ('replace','replace_text_file') and a.get('path')=='task.py']
    checks=[i for i,(f,_,_) in enumerate(events) if f in current]
    finish=[i for i,(f,_,_) in enumerate(events) if f in value['evidence']['explicit_finish_frames']]
    ordered=any(r<e<c<f for r in read for e in edit for c in checks for f in finish)
    host_verified=value['evidence']['recorded_workflow_verified'] is True
    finished=host_verified and ordered and preserved
    return dict(schema=1,capture_id=checked.capture_id,host_verified=host_verified,
        read_edit_check_finish=ordered,input_preserved=preserved,finished=finished,
        source_sha256=hashlib.sha256(source).hexdigest(),source_mode=files['task.py']['mode'],
        tools=[t for _,t,_ in events],native_receipts=len(value['evidence']['native'])),source
