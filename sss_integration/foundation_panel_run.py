"""Run one frozen foundation panel against one model, preserving per-case evidence.

This diagnostic uses llama-server's chat interface, not BW tool use or a COW
branching benchmark. Run models serially with the same arguments and panel.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import time

from sss.adapters.foundation_training import SYSTEM
from sss.foundations import Exercise, check
from sss.records import digest, file_sha256
from sss_integration.admin_model_probe import http, write


def run(a):
    panel = json.loads(a.panel.read_bytes())
    if panel.get('evaluation_id') != digest({k:v for k,v in panel.items() if k != 'evaluation_id'}):
        raise ValueError('Frozen panel identity mismatch')
    if panel.get('split') not in ('development', 'qualification') or not panel.get('cases'):
        raise ValueError('A nonempty protected evaluation panel is required')
    if file_sha256(a.model) != a.model_sha256:
        raise ValueError('Model identity mismatch')
    exercises = [Exercise(**row['exercise']) for row in panel['cases']]
    if any(e.split != panel['split'] for e in exercises):
        raise ValueError('Mixed or incorrect evaluation split')
    if any(e.identity != row['exercise_id'] for e,row in zip(exercises,panel['cases'])):
        raise ValueError('Exercise identity mismatch')
    if not 1 <= a.parallel <= 16 or not 1 <= a.max_tokens <= 4096:
        raise ValueError('Invalid evaluation concurrency or token limit')
    import fcntl
    root = a.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    argv = [str(a.server.resolve(strict=True)), '-m', str(a.model.resolve(strict=True)),
            '-ngl', '99', '-c', str(a.context), '-np', str(a.parallel), '-t', str(a.threads),
            '--host', '127.0.0.1', '--port', str(a.port), '--jinja']
    write(root/'intent.json', dict(schema=1, panel_id=panel['evaluation_id'],
          panel_sha256=file_sha256(a.panel), model_sha256=a.model_sha256,
          server_sha256=file_sha256(a.server), runner_sha256=file_sha256(Path(__file__)),
          argv=argv, temperature=0, max_tokens=a.max_tokens, thinking=False,
          protocol='single-turn direct answer via llama-server; not BW tool evaluation'))
    lock = Path.home()/'.local/state/context-cow'/('gpu-'+str(a.gpu_index)+'.lock')
    lock.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with lock.open('a') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX|fcntl.LOCK_NB)
        rows = subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu',
                                         '--format=csv,noheader,nounits'],text=True).splitlines()
        gpu = [r.split(',') for r in rows if int(r.split(',')[0]) == a.gpu_index]
        if len(gpu)!=1 or int(gpu[0][2])<a.min_free_gib*1024 or int(gpu[0][3])>a.maximum_initial_utilization:
            raise RuntimeError('GPU admission refused')
        env = dict(os.environ, CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES=gpu[0][1].strip())
        with (root/'server.log').open('x') as log:
            child = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env,
                                     pass_fds=(lease.fileno(),), start_new_session=True)
            try:
                for _ in range(180):
                    if child.poll() is not None:
                        raise RuntimeError('Evaluation server exited before readiness')
                    try:
                        http(a.port,'/health'); break
                    except Exception:
                        time.sleep(1)
                else:
                    raise TimeoutError('Evaluation server did not become ready')
                def evaluate(item):
                    i,e = item
                    response = http(a.port,'/v1/chat/completions',dict(
                        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=e.prompt)],
                        temperature=0,max_tokens=a.max_tokens,chat_template_kwargs={'enable_thinking':False}))
                    choice = response['choices'][0]
                    answer = choice['message'].get('content') or ''
                    result = dict(index=i, exercise_id=e.identity, skill_id=e.skill_id, gate=e.gate,
                                  passed=bool(check(e,answer)), finished=choice.get('finish_reason')=='stop',
                                  response=response)
                    write(root/f'{i:04d}-private.json',result)
                    return {k:v for k,v in result.items() if k!='response'}
                with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:
                    results=list(pool.map(evaluate,enumerate(exercises)))
                summary=dict(schema=1,status='COMPLETE',panel_id=panel['evaluation_id'],
                             model_sha256=a.model_sha256, cases=len(results),
                             passed=sum(r['passed'] for r in results), finished=sum(r['finished'] for r in results),
                             results=results, mastery_established=False)
                write(root/'result.json',summary)
                print(json.dumps({k:v for k,v in summary.items() if k!='results'}),flush=True)
            finally:
                if child.poll() is None:
                    child.terminate()
                    try: child.wait(timeout=30)
                    except subprocess.TimeoutExpired: child.kill(); child.wait()
                fcntl.flock(lease,fcntl.LOCK_UN)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('panel','model','server','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--model-sha256',required=True)
    p.add_argument('--gpu-index',type=int,required=True)
    p.add_argument('--min-free-gib',type=int,default=20)
    p.add_argument('--maximum-initial-utilization',type=int,default=10)
    p.add_argument('--context',type=int,default=16384)
    p.add_argument('--parallel',type=int,default=8)
    p.add_argument('--threads',type=int,default=8)
    p.add_argument('--port',type=int,default=18978)
    p.add_argument('--max-tokens',type=int,default=512)
    run(p.parse_args())
