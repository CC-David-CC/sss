from pathlib import Path
from contextlib import contextmanager
import fcntl,json,os,select,signal,struct,subprocess,time

def receive(proc,count,timeout=120):
    result=bytearray();deadline=time.monotonic()+timeout
    while len(result)<count:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Owned native oracle timed out')
        ready,_,_=select.select([proc.stdout],[],[],remaining)
        if not ready:raise TimeoutError('Owned native oracle output timed out')
        part=os.read(proc.stdout.fileno(),count-len(result))
        if not part:raise RuntimeError('Native oracle exited; inspect its private log')
        result.extend(part)
    return bytes(result)

@contextmanager
def oracle_process(binary,model,gpu_uuid,log,adapter=None,*,extra_pass_fds=(),context_tokens=256,batch_tokens=128,minimum_free_mib=48*1024,maximum_initial_utilization=0,admission_wait_seconds=30,all_logits=None):
    if not (type(context_tokens) is int and 128<=context_tokens<=1048576 and type(batch_tokens) is int and 1<=batch_tokens<=context_tokens and type(minimum_free_mib) is int and minimum_free_mib>=1 and type(maximum_initial_utilization) is int and 0<=maximum_initial_utilization<=100 and type(admission_wait_seconds) is int and 0<=admission_wait_seconds<=300 and (all_logits is None or type(all_logits) is bool)):
        raise ValueError('Explicit bounded context and owner admission settings required')
    rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    selected=[p for line in rows.splitlines() if (p:=[v.strip() for v in line.split(',')])[1]==gpu_uuid]
    if len(selected)!=1:raise RuntimeError('Configured evaluation GPU is unavailable')
    locks=Path.home()/'.local/state/context-cow';locks.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (locks/('gpu-'+selected[0][0]+'.lock')).open('a+') as lease,Path(log).open('wb') as err:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Utilization is a rolling sample and may outlast our retired child.
        # Wait briefly for the SAME configured criteria; never relax admission.
        deadline=time.monotonic()+admission_wait_seconds
        while True:
            rows=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True)
            selected=[p for line in rows.splitlines() if (p:=[v.strip() for v in line.split(',')])[0]==gpu_uuid]
            if len(selected)==1 and int(selected[0][1])>=minimum_free_mib and int(selected[0][2])<=maximum_initial_utilization:break
            if time.monotonic()>=deadline:raise RuntimeError('Evaluation GPU lacks the admitted idle headroom after bounded wait')
            time.sleep(1)
        environment=dict(os.environ,CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES=gpu_uuid,
            GGML_CUDA_F32_ACTIVATIONS='1',COW_QWEN35_F32_ATTENTION='1',NVIDIA_TF32_OVERRIDE='0',GGML_NO_BACKTRACE='1')
        if all_logits is not None:environment['PCC_ORACLE_ALL_LOGITS']=str(int(all_logits))
        argv=[str(binary),str(model),str(context_tokens),str(batch_tokens),'8','CUDA0']
        if adapter is not None:argv+=['--lora',str(adapter),'1']
        proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=environment,start_new_session=True,pass_fds=(lease.fileno(),*extra_pass_fds))
        proc.pcc_admission=dict(gpu_uuid=gpu_uuid,free_mib=int(selected[0][1]),utilization=int(selected[0][2]),context_tokens=context_tokens,batch_tokens=batch_tokens,minimum_free_mib=minimum_free_mib,maximum_initial_utilization=maximum_initial_utilization)
        try:yield proc
        finally:
            if proc.poll() is None:
                proc.stdin.close()
                try:proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=15)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()

def completion(proc,tok,prompt,maximum=24):
    import numpy as np  # Binary-output decoding only, never the training runtime.
    prefix=tok.encode(prompt);generated=[]
    for _ in range(maximum):
        tokens=prefix+generated
        packet=dict(schema=1,spans=[dict(kind='text',tokens=tokens)],chunks=[[0,len(tokens)]],embedding_paths={})
        proc.stdin.write(('M '+json.dumps(packet)+'\n').encode());proc.stdin.flush()
        vocab,work,position=struct.unpack('<iQi',receive(proc,16))
        if work!=len(tokens) or position!=len(tokens)-1:raise ValueError('Oracle did not prove fresh full-prefill work')
        raw=receive(proc,vocab*4);logits=np.frombuffer(raw,dtype='<f4')
        if not np.isfinite(logits).all():raise ValueError('Nonfinite independent oracle logits')
        generated.append(int(logits.argmax()))
        text=tok.decode(generated)
        if '\n' in text:return text.split('\n',1)[0]
        if '<|im_end|>' in text or '<|endoftext|>' in text:return text
    return tok.decode(generated)


def token_completion(proc,tok,prefix,*,maximum,context_tokens,batch_tokens,stop_token_ids,protocol='tokens-v1'):
    """Greedy full-prefill completion from exact rendered IDs, with token stopping.

    Unlike the legacy line-answer helper, this preserves multiline JSON and
    strips only an actual sampled stop token. NumPy is an optional adapter need.
    """
    import numpy as np
    if (protocol not in ('tokens-v1','spans-v1') or type(prefix) is not list or not prefix
            or type(maximum) is not int or not 1<=maximum<=4096
            or type(context_tokens) is not int or not 128<=context_tokens<=1048576
            or type(batch_tokens) is not int or not 1<=batch_tokens<=context_tokens
            or len(prefix)+maximum>context_tokens):
        raise ValueError('Bounded explicit prefix, protocol, context and generation required')
    vocab_expected=len(tok.tokens)
    if any(type(t) is not int or not 0<=t<vocab_expected for t in prefix):
        raise ValueError('Prefix token outside the pinned vocabulary')
    if type(stop_token_ids) not in (list,tuple) or not stop_token_ids or any(type(t) is not int or not 0<=t<vocab_expected for t in stop_token_ids):
        raise ValueError('Explicit valid stop token IDs required')
    generated=[];work_total=0
    for _ in range(maximum):
        tokens=prefix+generated
        if protocol=='tokens-v1':
            request='F '+str(batch_tokens)+' '+str(len(tokens))+' '+' '.join(map(str,tokens))+'\n'
        else:
            packet=dict(schema=1,spans=[dict(kind='text',tokens=tokens)],chunks=[[0,len(tokens)]],embedding_paths={})
            request='M '+json.dumps(packet)+'\n'
        proc.stdin.write(request.encode());proc.stdin.flush()
        vocab,work,position=struct.unpack('<iQi',receive(proc,16))
        if vocab!=vocab_expected or work!=len(tokens) or position!=len(tokens)-1:
            raise ValueError('Oracle vocabulary or fresh full-prefill receipt differs')
        logits=np.frombuffer(receive(proc,vocab*4),dtype='<f4')
        if not np.isfinite(logits).all():raise ValueError('Nonfinite independent oracle logits')
        token=int(logits.argmax());generated.append(token);work_total+=work
        if token in stop_token_ids:
            return dict(text=tok.decode(generated[:-1]),sampled_token_ids=generated,
                        stop_reason='eos',stop_token_id=token,prefill_tokens=work_total,model_calls=len(generated))
    return dict(text=tok.decode(generated),sampled_token_ids=generated,
                stop_reason='length',stop_token_id=None,prefill_tokens=work_total,model_calls=len(generated))
