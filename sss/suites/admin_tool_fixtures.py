"""Small, simulated admin and tool-use fixtures with host-side state checks.

These are fixture specifications, not a model runner or real service manager.
The operator supplies observations from an isolated task environment.
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Fixture:
    id: str
    request: str
    files: dict
    reference: tuple
    required: tuple
    writable: tuple = ()

def cases():
    return (
        Fixture('tools.read_config', 'Read service.conf and report the configured port as a number.',
                {'service.conf': 'port=8080\n'},
                ({'tool':'read_file','arguments':{'path':'service.conf'}}, {'tool':'finish','arguments':{'answer':'8080'}}),
                ('read:service.conf', 'finish:8080')),
        Fixture('tools.recover_missing', 'Read service.conf; if missing, inspect the directory and read service.conf.example. Report its port.',
                {'service.conf.example':'port=9000\n'},
                ({'tool':'read_file','arguments':{'path':'service.conf'}}, {'tool':'list_files','arguments':{}}, {'tool':'read_file','arguments':{'path':'service.conf.example'}}, {'tool':'finish','arguments':{'answer':'9000'}}),
                ('missing:service.conf', 'list', 'read:service.conf.example', 'finish:9000')),
        Fixture('admin.repair_port', 'The application expects port 8080. Correct service.conf and preserve the other settings and protected.txt.',
                {'service.conf':'port=8000\nworkers=2\n', 'protected.txt':'preserve exactly\n'},
                ({'tool':'read_file','arguments':{'path':'service.conf'}}, {'tool':'write_file','arguments':{'path':'service.conf','content':'port=8080\nworkers=2\n'}}, {'tool':'finish','arguments':{'answer':'done'}}),
                ('read:service.conf', 'write:service.conf', 'finish:done'), ('service.conf',)),
        Fixture('admin.diagnose_log', 'Inspect service.log and report the error code, preserving the log.',
                {'service.log':'startup ok\nERROR E42: permission denied\n'},
                ({'tool':'read_file','arguments':{'path':'service.log'}}, {'tool':'finish','arguments':{'answer':'E42'}}),
                ('read:service.log', 'finish:E42')),
    )

def execute_reference(fixture, calls):
    """Run explicit calls on an in-memory disposable filesystem; return observations.

    Intended as a deterministic reference environment; not a Linux host executor.
    """
    files=dict(fixture.files); events=[]; outputs=[]; finished=False
    for call in calls:
        if finished:
            events.append('invalid');continue
        if type(call) is not dict or set(call)!={'tool','arguments'}:
            events.append('invalid');continue
        tool=call.get('tool'); args=call.get('arguments')
        if type(args) is not dict: events.append('invalid'); continue
        if tool=='read_file' and set(args)=={'path'} and type(args['path']) is str:
            path=args['path']; events.append(('read:' if path in files else 'missing:')+path)
            outputs.append({'tool':tool,'path':path,'content':files.get(path),'error':None if path in files else 'not_found'})
        elif tool=='list_files' and not args:
            events.append('list');outputs.append({'tool':tool,'paths':sorted(files)})
        elif tool=='write_file' and set(args)=={'path','content'} and all(type(args[k]) is str for k in args):
            path=args['path']
            if path not in fixture.writable: events.append('denied:'+path)
            else:
                files[path]=args['content'];events.append('write:'+path)
                outputs.append({'tool':tool,'path':path,'written':True})
        elif tool=='finish' and set(args)=={'answer'} and type(args['answer']) is str:
            events.append('finish:'+args['answer']);finished=True
        else: events.append('invalid')
    return {'events':events,'files':files,'outputs':outputs}

def grade(fixture, observation):
    if type(observation) is not dict:return {'status':'unavailable'}
    events=observation.get('events');files=observation.get('files')
    if (type(events) is not list or any(type(e) is not str for e in events)
            or type(files) is not dict):return {'status':'unavailable'}
    expected=dict(fixture.files)
    if fixture.id=='admin.repair_port':expected['service.conf']='port=8080\nworkers=2\n'
    position=0
    for event in events:
        normalized=event
        if event.startswith('finish:'):
            answer=event[len('finish:'):]
            if fixture.id=='admin.repair_port' and answer.strip():normalized='finish:done'
            if fixture.id=='admin.diagnose_log' and re.findall(r'\bE\d+\b',answer)==['E42']:normalized='finish:E42'
        if position<len(fixture.required) and normalized==fixture.required[position]:position+=1
    passed=(position==len(fixture.required) and files==expected and 'invalid' not in events
            and not any(e.startswith('denied:') for e in events))
    return {'status':'pass' if passed else 'fail', 'required_events_observed':position,
            'required_events_total':len(fixture.required), 'final_state_correct':files==expected}
