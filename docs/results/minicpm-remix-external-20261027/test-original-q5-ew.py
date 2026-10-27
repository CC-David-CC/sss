"""Add the missing quantization-only control, without repeating existing cases."""
from pathlib import Path
import concurrent.futures,importlib.util,json,subprocess,time,traceback
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior',R/'run-remix-external-eu.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
H=Path.home();out=R/'original-Q5';out.mkdir()
def run():
    original=H/'models/minicpm5-official/MiniCPM5-2B-F16.gguf'
    assert m.sha(original)=='0ffba3682a853295566b98bc38c0ab755d6b2d91b994bc031ed727a08cfcdf25'
    model=out/'model-Q5_K_M.gguf';quant=H/'src/llama.cpp/build/bin/llama-quantize'
    argv=[str(quant),str(original),str(model),'Q5_K_M','8']
    m.write(out/'conversion-intent.json',dict(argv=argv,source_sha256=m.sha(original),quantizer_sha256=m.sha(quant)))
    with (out/'conversion.log').open('x') as f:subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
    m.write(out/'conversion.json',dict(status='CONVERTED',sha256=m.sha(model),bytes=model.stat().st_size))
    port=18973;server=H/'src/llama.cpp/build/bin/llama-server'
    argv=[str(server),'-m',str(model),'-ngl','99','-c','16384','-np','8','-t','8','--host','127.0.0.1','--port',str(port),'--jinja']
    m.write(out/'intent.json',dict(argv=argv,server_sha256=m.sha(server),new_training=False))
    with (out/'server.log').open('x') as log:
        proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
        m.write(out/'process.json',dict(pid=proc.pid))
        try:
            for _ in range(180):
                if proc.poll() is not None:raise RuntimeError('Server exited')
                try:m.http(port,'/health');break
                except Exception:time.sleep(1)
            else:raise TimeoutError('Server health deadline')
            def one(case):
                start=time.monotonic()
                response=m.http(port,'/v1/chat/completions',dict(messages=[{'role':'user','content':case['prompt']}],temperature=0,max_tokens=512,chat_template_kwargs={'enable_thinking':False}))
                text=response['choices'][0]['message'].get('content') or ''
                row=dict(case_id=case['id'],correct=m.score(case,text),response=response,seconds=time.monotonic()-start)
                m.write(out/(case['id'].replace(':','-')+'.json'),row);return row
            rows=[]
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                for row in pool.map(one,m.cases()):
                    rows.append(row);print(json.dumps(dict(completed=len(rows),correct=sum(r['correct'] for r in rows))),flush=True)
            summary=dict(status='COMPLETE',cases=64,correct=sum(r['correct'] for r in rows),groups={k:sum(r['correct'] for r in rows if r['case_id'].startswith(k+':')) for k in ['gsm8k','arc']},finished=sum(r['response']['choices'][0]['finish_reason']=='stop' for r in rows),new_training=False)
            m.write(out/'summary.json',summary)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=30)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':
    try:run()
    except BaseException as e:m.write(out/'failure.json',dict(error=str(e),automatic_retry=False));traceback.print_exc();raise
