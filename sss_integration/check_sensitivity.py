"""Exercise check quality through actual BW and independent S3 Linux checks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse, hashlib, json, os, subprocess, sys, time


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bw-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check-file',type=Path,help='Owned JSON with exactly name and command from a proposed check')
    args=parser.parse_args(argv)
    bw=args.bw_root.resolve(strict=True)
    if not (bw/'branchwrite/interpreter.py').is_file():raise ValueError('Actual inspected BW checkout required')
    sys.path.insert(0,str(bw))
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from sss.adapters.bw_check_probe import observe
    from sss.studies.check_sensitivity import assess
    from sss.suites.code_foundations import cases
    from sss.records import digest
    proposed='sh -n copy.sh'
    proposed_origin='Operator-authored syntax-only weak control; no model inference'
    if args.check_file is not None:
        data=json.loads(args.check_file.read_text())
        if type(data) is not dict or set(data)!={'name','command'} or type(data['command']) is not str:
            raise ValueError('Exact proposed check arguments required')
        proposed=data['command']
        proposed_origin='Existing proposed command supplied by operator; this recipe makes no model calls'
    control="""python3 - <<'PY'
import pathlib, subprocess, tempfile
with tempfile.TemporaryDirectory() as directory:
    source=pathlib.Path(directory)/'input one;value.txt'
    target=pathlib.Path(directory)/'output $two.txt'
    raw=bytes(range(256))+b'\\n'
    source.write_bytes(raw)
    subprocess.run(['/bin/sh','copy.sh',str(source),str(target)],check=True)
    assert target.read_bytes()==raw
PY"""
    case=next(value for value in cases() if value.id=='shell.quoted_filename')
    programs=dict(reference=case.reference,unquoted_source=case.before,
                  empty_output={'copy.sh':'#!/bin/sh\n: > "$2"\n'})
    commands=dict(proposed=proposed,assertive_control=control)
    root=args.output.absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    plan=dict(schema=1,case_id=case.id,programs={name:digest(files) for name,files in programs.items()},
        commands={name:hashlib.sha256(command.encode()).hexdigest() for name,command in commands.items()},
        proposed_origin=proposed_origin,control_origin='Operator-authored control with difficult paths and byte assertions',
        bw_commit=subprocess.check_output(['git','-C',str(bw),'rev-parse','HEAD'],text=True).strip(),
        model_inference=False,gpu_used=False,training_approved=False)
    (root/'plan-private.json').write_text(json.dumps(plan,indent=2)+'\n')
    started=time.monotonic();observed={};errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(observe,case,files,command,root/(check+'-'+variant)):(check,variant)
                 for check,command in commands.items() for variant,files in programs.items()}
        for future in as_completed(futures):
            check,variant=futures[future]
            try:observed[check,variant]=future.result()
            except Exception as exc:errors.append(dict(check=check,variant=variant,type=type(exc).__name__,detail=str(exc)))
    assessments={}
    for check in commands:
        if all((check,variant) in observed for variant in programs):
            assessments[check]=assess(observed[check,'reference'],[observed[check,key] for key in programs if key!='reference'])
    value=dict(schema=1,status='COMPLETE' if len(observed)==6 and not errors else 'PARTIAL',
        scope='Host-controlled check sensitivity on three independently graded program variants; no model skill or training result',
        assessments=assessments,observations=[dict(check=check,variant=variant,observation=value)
            for (check,variant),value in sorted(observed.items())],errors=errors,
        elapsed_seconds=time.monotonic()-started,model_inference=False,gpu_used=False,
        training_approved=False,promoted=False)
    (root/'result.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(status=value['status'],assessments={k:v['status'] for k,v in assessments.items()},
        model_inference=False,gpu_used=False)))
    return 0 if value['status']=='COMPLETE' else 2


if __name__=='__main__':
    raise SystemExit(main())
