"""Original file-tool scenarios inspired by tool-eval-bench's category design.

This grades host-validated observations. It neither executes model proposals
nor grants tools. BW or another adapter supplies its canonical completed trace.
These evaluation cases are not a training export.
"""
from dataclasses import dataclass
import re
from sss.records import digest

@dataclass(frozen=True)
class Scenario:
    id:str
    skill_id:str
    request:str
    before:dict
    expected:dict
    required_read:tuple=()
    required_check:str|None=None
    answer_contains:str|None=None
    maximum_writes:int|None=None
    read_before_write:bool=False

def scenarios():
    return [
        Scenario('files.read','tools.files.read','Read service.conf and tell me its port.',
                 {'service.conf':'port=8127\n'}, {'service.conf':'port=8127\n'}, ('service.conf',),answer_contains='8127',maximum_writes=0),
        Scenario('files.write','tools.files.write','Create status.txt containing exactly ready followed by a newline.',
                 {},{'status.txt':'ready\n'},maximum_writes=1),
        Scenario('files.edit','tools.files.edit','Change only the port in service.conf from 8127 to 9136.',
                 {'service.conf':'name=demo\nport=8127\nkeep=yes\n'},{'service.conf':'name=demo\nport=9136\nkeep=yes\n'},('service.conf',),maximum_writes=1),
        Scenario('tasks.finish','tools.tasks.finish','Create status.txt as ready plus newline, check it with verify-status, then finish.',
                 {},{'status.txt':'ready\n'},required_check='verify-status',maximum_writes=1),
        Scenario('tasks.recover','tools.errors.recover','Change the port in service.conf from 0 to 9136, retry verify-port after a failed check, and finish only after it passes.',
                 {'service.conf':'port=0\n'},{'service.conf':'port=9136\n'},('service.conf',),required_check='verify-port'),
        Scenario('files.scope','tools.boundaries.scope','Create status.txt as ready plus newline. Leave credentials.txt unchanged.',
                 {'credentials.txt':'fixture-placeholder\n'},{'credentials.txt':'fixture-placeholder\n','status.txt':'ready\n'},maximum_writes=1),
        Scenario('files.noisy_read','tools.outputs','Read inspection.json and report the service port, ignoring the metadata port.',
                 {'inspection.json':'{"metadata":{"port":65500},"service":{"port":8127}}\n'},
                 {'inspection.json':'{"metadata":{"port":65500},"service":{"port":8127}}\n'},('inspection.json',),answer_contains='8127',maximum_writes=0),
        Scenario('tasks.chain','tools.chains','Read job.json first, then create report.txt with its job name followed by a newline.',
                 {'job.json':'{"job":"nightly-echo","attempt":17}\n'},
                 {'job.json':'{"job":"nightly-echo","attempt":17}\n','report.txt':'nightly-echo\n'},('job.json',),maximum_writes=1,read_before_write=True),
        Scenario('files.exact_path','tools.arguments','Read configs/service local.conf and report its port without changing it.',
                 {'configs/service local.conf':'port=8127\n'},{'configs/service local.conf':'port=8127\n'},
                 ('configs/service local.conf',),answer_contains='8127',maximum_writes=0),
    ]

def describe():
    return [dict(id=v.id,skill_id=v.skill_id,request=v.request,split='evaluation',training_eligible=False) for v in scenarios()]

def grade(scenario,events,after_files):
    """Grade actual completed host events; a model's claimed result is insufficient.

    An adapter must authenticate/validate its own operation receipts before
    calling this function. Dictionaries here do not independently prove that a
    command ran. Unknown effects/infrastructure retirement remain unavailable.
    """
    def result(status,*reasons):return dict(schema=1,scenario_id=scenario.id,skill_id=scenario.skill_id,status=status,
        reasons=list(reasons),evidence_sha256=digest(dict(events=events,after_files=after_files)))
    if not events:return result('fail','No completed task trace')
    ids=[v.get('operation_id') for v in events]
    if any(type(v) is not str or not v for v in ids) or len(ids)!=len(set(ids)):
        return result('unavailable','Missing or duplicated host operation identity')
    if any(v.get('settled') is not True or v.get('disposition') in ('timeout','spawn_error','indeterminate') for v in events):
        return result('unavailable','Tool effects or infrastructure have not settled')
    if events[-1].get('tool')!='finish' or sum(v.get('tool')=='finish' for v in events)!=1:
        return result('fail','Exactly one final finish action is required')
    if after_files!=scenario.expected:return result('fail','Actual final files differ from the requested change')
    read=set();mutated=set();writes=0;last_write=-1;matching_checks=[]
    for index,event in enumerate(events):
        tool=event.get('tool');arguments=event.get('arguments',{})
        successful=(event.get('exit_code')==0 and event.get('disposition') in ('read','created','applied','replaced','mode_changed','exited'))
        if tool=='run_check' and arguments.get('name')==scenario.required_check:matching_checks.append((index,successful))
        if not successful and tool!='finish':
            continue
        if tool=='read_file':read.add(arguments.get('path'))
        if tool in ('create_file','create_text_file','replace','replace_text_file','set_mode'):
            path=arguments.get('path');writes+=1;last_write=index;mutated.add(path)
            if path in scenario.required_read and path not in read:return result('fail','Edit preceded the required file observation')
            if scenario.read_before_write and not set(scenario.required_read)<=read:return result('fail','Dependent action preceded its required input')
    if not set(scenario.required_read)<=read:return result('fail','Required file was not read successfully')
    changed={key for key in set(scenario.before)|set(scenario.expected) if scenario.before.get(key)!=scenario.expected.get(key)}
    if not changed<=mutated:return result('fail','Requested file change has no completed mutation receipt')
    if scenario.maximum_writes is not None and writes>scenario.maximum_writes:return result('fail','Extra mutation beyond the scenario budget')
    if scenario.required_check and (not matching_checks or matching_checks[-1][0]<=last_write or matching_checks[-1][1] is not True):
        return result('fail','A completed passing check after the last change is required')
    if scenario.id=='tasks.recover' and not any(not passed for _,passed in matching_checks):return result('fail','Recovery scenario did not exercise its failed check')
    if scenario.answer_contains and not re.search(r'(?<!\w)'+re.escape(scenario.answer_contains)+r'(?!\w)',str(events[-1].get('arguments',{}).get('answer',''))):
        return result('fail','Final answer omitted the observed requested value')
    return result('pass')
