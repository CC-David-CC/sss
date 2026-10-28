"""Bounded diagnostic model connection, not a BW/harness leaderboard runner."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,urllib.request
from sss.suites.admin_tool_fixtures import cases,execute_reference,grade
from sss.suites.code_foundations import cases as code_cases,grade as code_grade
from sss.adapters.linux_sandbox import LinuxSandbox,read_owned
from sss.adapters.code_check import run_check
from sss.suites.linux_admin_config import cases as config_cases,prepare as prepare_config,check as check_config

def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def http(port,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=data,headers={'Content-Type':'application/json'}),timeout=180) as r:return json.load(r)
def ask(port,messages):
    return http(port,'/v1/chat/completions',dict(messages=messages,temperature=0,max_tokens=1024,chat_template_kwargs={'enable_thinking':False},response_format={'type':'json_object'}))
def text(response):return response['choices'][0]['message'].get('content') or ''
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(model,expected,server,root,config_only=False):
    root.mkdir(parents=True,exist_ok=False)
    if sha(model)!=expected:raise ValueError('Model SHA mismatch')
    port=18976;argv=[str(server),'-m',str(model),'-ngl','99','-c','8192','-np','1','-t','8','--host','127.0.0.1','--port',str(port),'--jinja']
    write(root/'intent.json',dict(model_sha256=expected,server_sha256=sha(server),runner_sha256=sha(Path(__file__)),argv=argv,temperature=0,max_tokens=1024,thinking=False,scope='custom diagnostic JSON action protocol plus single-turn code generation; not BW or native function-calling score',training=False))
    results=[]
    with (root/'server.log').open('x') as log:
        child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(180):
                if child.poll() is not None:raise RuntimeError('Server exited')
                try:http(port,'/health');break
                except Exception:time.sleep(1)
            else:raise TimeoutError('Server startup')
            for case in (() if config_only else cases()):
                folder=root/case.id;folder.mkdir();calls=[];responses=[]
                messages=[{'role':'system','content':'Operate a disposable simulated filesystem. Return exactly one JSON object per turn: {"tool":"read_file","arguments":{"path":"..."}}, {"tool":"list_files","arguments":{}}, {"tool":"write_file","arguments":{"path":"...","content":"..."}}, or {"tool":"finish","arguments":{"answer":"..."}}. Read observations before acting. Paths are relative. The finish answer must be a string.'}, {'role':'user','content':case.request}]
                for turn in range(8):
                    response=ask(port,messages);responses.append(response)
                    try:call=json.loads(text(response))
                    except ValueError:call={}
                    previous=execute_reference(case,calls)
                    calls.append(call);observation=execute_reference(case,calls)
                    messages.append({'role':'assistant','content':text(response)})
                    fresh=observation['outputs'][len(previous['outputs']):]
                    messages.append({'role':'user','content':'Host observation: '+json.dumps(fresh if fresh else {'error':'invalid or denied tool call'})})
                    if type(call) is dict and call.get('tool')=='finish':break
                verdict=grade(case,execute_reference(case,calls));write(folder/'attempt.json',dict(responses=responses,calls=calls,verdict=verdict,observation=execute_reference(case,calls)))
                results.append(dict(id=case.id,domain='simulated_tools_admin',**verdict))
            if config_only:
                for case in config_cases():
                    folder=root/case['id'];folder.mkdir();work=folder/'work';prepare_config(case,work)
                    response=ask(port,[{'role':'system','content':'Return exactly a JSON object with one key service.ini whose value is the complete corrected configuration file as a string.'},{'role':'user','content':case['request']+'\nservice.ini:\n'+case['before']}])
                    write(folder/'response.json',response)
                    try:files=json.loads(text(response))
                    except ValueError:files=None
                    if type(files) is dict and set(files)=={'service.ini'} and type(files['service.ini']) is str:
                        (work/'service.ini').write_text(files['service.ini']);verdict=check_config(case,work);write(folder/'check.json',verdict)
                        verdict={'status':verdict['status']}
                    else:verdict={'status':'fail','reason':'Invalid file mapping'}
                    results.append(dict(id=case['id'],domain='isolated_linux_config',**verdict))
            selected_code_ids={'python.sum_empty','python.binary_search','python.stable_unique','shell.quoted_filename','shell.failure_status'}
            for case in (() if config_only else [c for c in code_cases() if c.id in selected_code_ids]):
                folder=root/case.id;folder.mkdir();work=folder/'work';work.mkdir()
                for name,value in case.before.items():(work/name).write_text(value)
                response=ask(port,[{'role':'system','content':'Return a JSON object mapping each supplied filename to its full replacement source as a string. No extra files. Work in the stated language.'},{'role':'user','content':case.request+'\nStarting files:\n'+json.dumps(case.before)}])
                write(folder/'response.json',response)
                try:files=json.loads(text(response))
                except ValueError:files=None
                if type(files) is dict and set(files)==set(case.before) and all(type(x) is str for x in files.values()):
                    for name,value in files.items():(work/name).write_text(value)
                    evidence=run_check(case,LinuxSandbox(work));verdict=code_grade(case,[evidence],{n:read_owned(work,n) for n in case.before});write(folder/'check.json',evidence)
                else:verdict=dict(status='fail',reasons=['Invalid replacement file mapping'])
                results.append(dict(id=case.id,domain='isolated_linux_code',**verdict))
            write(root/'result.json',dict(status='COMPLETE',results=results,passed=sum(x['status']=='pass' for x in results),cases=len(results),training=False))
        finally:
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=30)
                except subprocess.TimeoutExpired:child.kill();child.wait()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('model','server','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--sha256',required=True);p.add_argument('--config-only',action='store_true');a=p.parse_args();run(a.model,a.sha256,a.server,a.output,a.config_only)
