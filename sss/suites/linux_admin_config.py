"""Actual disposable Linux file/configuration checks; no real host services."""
import json
from pathlib import Path
from sss.adapters.linux_sandbox import LinuxSandbox,read_owned

def cases():
    return (
        dict(id='linux.config_port',request='Set the service port to 8080. Preserve workers and protected.txt.',before='[service]\nport=8000\nworkers=2\n',reference='[service]\nport=8080\nworkers=2\n',expected={'port':'8080','workers':'2'}),
        dict(id='linux.config_logging',request='Enable logging by setting enabled=true. Preserve level and protected.txt.',before='[service]\nenabled=false\nlevel=warning\n',reference='[service]\nenabled=true\nlevel=warning\n',expected={'enabled':'true','level':'warning'}),
    )

def prepare(case,work):
    work.mkdir()
    (work/'service.ini').write_text(case['before'])
    (work/'protected.txt').write_bytes(b'protected bytes\n')

def check(case,work):
    script='import configparser,json; p=configparser.ConfigParser(); p.read("service.ini"); print(json.dumps({s:dict(p[s]) for s in p.sections()}))'
    evidence=LinuxSandbox(work).run(['/usr/bin/python3','-c',script])
    try:config=json.loads(evidence['stdout'])
    except ValueError:config=None
    try:protected=read_owned(work,'protected.txt')==b'protected bytes\n'
    except (ValueError,FileNotFoundError):protected=False
    passed=(evidence['exit_code']==0 and not evidence['timed_out'] and not evidence['output_truncated']
            and config=={'service':case['expected']} and protected
            and set(evidence['after'])=={'service.ini','protected.txt'}
            and all(v['kind']=='file' for v in evidence['after'].values()))
    return dict(status='pass' if passed else 'fail',evidence=evidence)

def qualify(root):
    root.mkdir()
    for case in cases():
        for name,source,want in [('broken',case['before'],'fail'),('reference',case['reference'],'pass')]:
            work=root/(case['id']+'-'+name);prepare(case,work);(work/'service.ini').write_text(source)
            if check(case,work)['status']!=want:raise AssertionError((case['id'],name))
        work=root/(case['id']+'-protected');prepare(case,work);(work/'service.ini').write_text(case['reference']);(work/'protected.txt').write_text('changed')
        if check(case,work)['status']!='fail':raise AssertionError('Protected-file change accepted')
    return {'status':'PASS','cases':2,'checks':6,'scope':'isolated configuration files; not host service control'}
