"""Independent-skill HTTP diagnostic; no practice, training or mastery promotion."""
from pathlib import Path
from dataclasses import asdict
import concurrent.futures,json,subprocess,time
from sss.curriculum import BY_ID,exercise_for
from sss.foundations import reference,check
from sss_integration.admin_model_probe import sha,write,http

OLD={'math.add.carry','math.add.no_carry','math.add.signed','math.divide','math.fraction','math.fraction.add','math.multiply','math.place_value','state.registers'}
def run(root):
    root.mkdir(exist_ok=False)
    skills=sorted(set(BY_ID)-OLD)
    if len(skills)!=57:raise ValueError('Expected 57 other implemented foundations')
    tasks=[];unavailable=[]
    for skill in skills:
        try:
            rows=[exercise_for(skill,'development',i,gate='independent',seed=20261028) for i in range(8)]
            if any(not check(e,reference(e)) for e in rows):raise ValueError('Reference failed independent checker')
            if len({e.prompt for e in rows})!=8:raise ValueError('Duplicate prompts in preliminary screen')
            tasks+=rows
        except Exception as exc:unavailable.append(dict(skill_id=skill,error=repr(exc)))
    write(root/'cases-private.json',[asdict(e) for e in tasks])
    write(root/'preparation.json',dict(status='PREPARED',seed=20261028,skills=skills,gate='independent',requested_cases_per_skill=8,available_cases=len(tasks),unavailable=unavailable,scope='preliminary coverage screen; not mastery or training; new development set, not sealed qualification'))
    h=Path.home();server=h/'src/llama.cpp/build/bin/llama-server'
    models=[('original',h/'minicpm-curve-inputs-20261024-a/original-F32.gguf','2323c47d8bf14fb2906e1275688aa784768cf39a364729bc52bf6ba5c0742764'),('remix2',h/'minicpm-rank32-quant-external-20261027-fn/update-042-F32/model-F32.gguf','7254cd2904ff5114d50ee5b5f961482789388dae3d609723ae67b759100288be')]
    for name,model,expected in models:
        out=root/name;out.mkdir()
        if sha(model)!=expected:raise ValueError('Model identity mismatch')
        argv=[str(server),'-m',str(model),'-ngl','99','-c','16384','-np','8','-t','8','--host','127.0.0.1','--port','18977','--jinja']
        write(out/'intent.json',dict(argv=argv,model_sha256=expected,server_sha256=sha(server),source_sha256=sha(Path(__file__)),cases_sha256=sha(root/'cases-private.json'),temperature=0,max_tokens=512,thinking=False))
        with(out/'server.log').open('x')as log:
            child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
            try:
                for _ in range(180):
                    if child.poll() is not None:raise RuntimeError('Server exited')
                    try:http(18977,'/health');break
                    except Exception:time.sleep(1)
                else:raise TimeoutError('Startup')
                def one(item):
                    i,e=item
                    response=http(18977,'/v1/chat/completions',dict(messages=[{'role':'system','content':'Follow the requested answer format exactly. This is a direct-answer assessment; no tools are available.'},{'role':'user','content':e.prompt}],temperature=0,max_tokens=512,chat_template_kwargs={'enable_thinking':False}))
                    c=response['choices'][0];row=dict(index=i,skill_id=e.skill_id,passed=check(e,c['message'].get('content')or''),finished=c['finish_reason']=='stop',response=response)
                    write(out/f'{i:04d}.json',row);return row
                with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:rows=list(pool.map(one,enumerate(tasks)))
                groups=[dict(skill_id=s,cases=sum(x['skill_id']==s for x in rows),passed=sum(x['passed'] for x in rows if x['skill_id']==s),finished=sum(x['finished'] for x in rows if x['skill_id']==s))for s in skills]
                write(out/'result.json',dict(status='COMPLETE',cases=len(rows),groups=groups,unavailable=unavailable,training=False,mastery_established=False))
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:child.wait(timeout=30)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
    write(root/'result.json',dict(status='COMPLETE',training=False))

if __name__=='__main__':
    import argparse,traceback
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:run(a.output)
    except BaseException as exc:
        if a.output.exists():write(a.output/'failure.json',dict(error=repr(exc),automatic_retry=False))
        traceback.print_exc();raise
