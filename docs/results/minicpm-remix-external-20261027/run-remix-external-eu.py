"""Inference-only, paired external spot check. No training or model promotion."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,re,subprocess,time,urllib.request,traceback
ROOT=Path(__file__).resolve().parent
HOME=Path.home()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def http(port,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)
def cases():
    result=[]
    for kind,file in [('gsm8k','remix-gsm8k32-eu.json'),('arc','remix-arc32-eu.json')]:
        rows=json.loads((ROOT/file).read_bytes())['rows'];assert len(rows)==32
        for r in rows:
            v=r['row'];i=r['row_idx']
            if kind=='gsm8k':
                prompt=v['question']+'\nGive your final numerical answer after ####.'
                answer=v['answer'].split('####')[-1].strip().replace(',','')
            else:
                prompt=v['question']+'\n'+'\n'.join(k+': '+s for k,s in zip(v['choices']['label'],v['choices']['text']))+'\nReply with only the correct option label.'
                answer=v['answerKey']
            result.append(dict(id=f'{kind}:{i}',kind=kind,prompt=prompt,expected=answer))
    return result
def score(case,text):
    # Explicit, reproducible extraction; not an official benchmark score.
    if case['kind']=='gsm8k':
        match=re.search(r'####\s*([-+]?\d[\d,]*(?:\.\d+)?)',text)
        return bool(match and match.group(1).replace(',','')==case['expected'])
    return text.strip()==case['expected']
def run():
    rows=cases();write(ROOT/'cases-private.json',rows)
    candidate=ROOT/'MiniCPM5-2B-SSS-Muon-Full-U068-Q5_K_M.gguf'
    partial=Path(str(candidate)+'.partial')
    expected='5d3f60288c576c8122c4b950343611051365b2a1e7e2be3536e0175d825da439'
    if not candidate.exists():
        assert partial.stat().st_size==1808061504 and sha(partial)==expected
        partial.rename(candidate)
    assert sha(candidate)==expected
    original=HOME/'models/minicpm5-official/MiniCPM5-2B-F16.gguf'
    assert sha(original)=='0ffba3682a853295566b98bc38c0ab755d6b2d91b994bc031ed727a08cfcdf25'
    server=HOME/'src/llama.cpp/build/bin/llama-server'
    write(ROOT/'plan.json',dict(status='FROZEN',cases=64,per_domain=32,new_training=False,
        models={'trained-Q5':expected,'original-F16':sha(original)},server_sha256=sha(server),
        source_sha256=sha(__file__),dataset_payload_sha256={n:sha(ROOT/n) for n in ['remix-gsm8k32-eu.json','remix-arc32-eu.json']},
        sampling=dict(temperature=0,max_tokens=512,enable_thinking=False),
        limitations=['First 32 test rows per dataset, not a random representative sample','Public data may have appeared in base pretraining','Strict answer extraction; not an official leaderboard protocol','Compares different training and storage precision together'],weights_updated=False))
    summaries=[]
    for name,model,port in [('original-F16',original,18971),('trained-Q5',candidate,18972)]:
        folder=ROOT/name;folder.mkdir()
        argv=[str(server),'-m',str(model),'-ngl','99','-c','16384','-np','8','-t','8','--host','127.0.0.1','--port',str(port),'--jinja']
        write(folder/'intent.json',dict(argv=argv,model_sha256=sha(model)))
        with (folder/'server.log').open('x') as log:
            proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
            write(folder/'process.json',dict(pid=proc.pid,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
            try:
                for _ in range(180):
                    if proc.poll() is not None:raise RuntimeError('Server exited during initialization')
                    try:http(port,'/health');break
                    except Exception:time.sleep(1)
                else:raise TimeoutError('Server health deadline')
                def one(case):
                    start=time.monotonic()
                    response=http(port,'/v1/chat/completions',dict(messages=[{'role':'user','content':case['prompt']}],temperature=0,max_tokens=512,chat_template_kwargs={'enable_thinking':False}))
                    choice=response['choices'][0];text=choice['message'].get('content') or ''
                    record=dict(case_id=case['id'],correct=score(case,text),response=response,seconds=time.monotonic()-start)
                    write(folder/(case['id'].replace(':','-')+'.json'),record)
                    return record
                records=[]
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                    for record in pool.map(one,rows):
                        records.append(record)
                        print(json.dumps(dict(model=name,completed=len(records),correct=sum(r['correct'] for r in records))),flush=True)
                summary=dict(model=name,cases=64,correct=sum(r['correct'] for r in records),groups={k:sum(r['correct'] for r in records if r['case_id'].startswith(k+':')) for k in ['gsm8k','arc']})
                write(folder/'summary.json',summary);summaries.append(summary)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=30)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
        
    write(ROOT/'result.json',dict(status='COMPLETE',summaries=summaries,new_training=False))
if __name__=='__main__':
    try:run()
    except BaseException as e:
        write(ROOT/'failure.json',dict(status='NEEDS_REVIEW',error=str(e),automatic_retry=False));traceback.print_exc();raise
