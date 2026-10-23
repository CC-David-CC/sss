"""CPU-only reference/broken-code proof at a real isolated Linux boundary."""
from pathlib import Path
import argparse,json,tempfile,hashlib
from sss.adapters.linux_sandbox import LinuxSandbox,read_owned,EnvironmentUnavailable
from sss.suites.code_foundations import cases,grade
from sss.adapters.code_check import run_check
from sss.records import digest

def run(root):
    root=Path(root);root.mkdir(mode=0o700,parents=True,exist_ok=False);results=[]
    for case in cases():
        trials={}
        for label,files in [('broken',case.before),('reference',case.reference)]:
            work=root/(case.id+'-'+label);work.mkdir()
            for name,content in files.items():(work/name).write_text(content,encoding='utf-8')
            boundary=LinuxSandbox(work)
            observation=run_check(case,boundary)
            # The check may create its own data fixtures. Source ownership is
            # compared separately to those explicit generated input/output files.
            sources={name:read_owned(work,name) for name in files}
            verdict=grade(case,[observation],sources)
            trials[label]=dict(verdict=verdict,evidence=observation)
            if verdict['status']!=('fail' if label=='broken' else 'pass'):raise AssertionError((case.id,label,verdict))
        results.append(dict(case_id=case.id,trials=trials))
    boundary_root=root/'boundary';boundary_root.mkdir();sandbox=LinuxSandbox(boundary_root)
    boundary=sandbox.run(['/usr/bin/python3','-c','import pathlib,socket; assert not pathlib.Path("/home").exists(); assert not pathlib.Path("/etc/shadow").exists(); print("isolated")'])
    if boundary['exit_code']!=0:raise AssertionError(boundary)
    result=dict(schema=2,status='PASS',scope='real CPU Linux boundary and independent broken/reference checks; no language model inference',model_inference=False,gpu_used=False,results=results,boundary=boundary)
    (root/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    try:result=run(args.output)
    except EnvironmentUnavailable as error:print(json.dumps(dict(status='unavailable',reason=str(error))));return 2
    print(json.dumps(dict(status=result['status'],cases=len(result['results']),model_inference=False)));return 0
if __name__=='__main__':raise SystemExit(main())
