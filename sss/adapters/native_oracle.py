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
def oracle_process(binary,model,gpu_uuid,log,adapter=None,*,extra_pass_fds=()):
    rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    selected=[p for line in rows.splitlines() if (p:=[v.strip() for v in line.split(',')])[1]==gpu_uuid]
    if len(selected)!=1:raise RuntimeError('Configured evaluation GPU is unavailable')
    locks=Path.home()/'.local/state/context-cow';locks.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (locks/('gpu-'+selected[0][0]+'.lock')).open('a+') as lease,Path(log).open('wb') as err:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Utilization is a rolling sample and may outlast our retired child.
        # Wait briefly for the SAME idle/free criteria; never relax admission.
        deadline=time.monotonic()+30
        while True:
            rows=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True)
            selected=[p for line in rows.splitlines() if (p:=[v.strip() for v in line.split(',')])[0]==gpu_uuid]
            if len(selected)==1 and int(selected[0][1])>=48*1024 and int(selected[0][2])==0:break
            if time.monotonic()>=deadline:raise RuntimeError('Evaluation GPU lacks the admitted idle headroom after bounded wait')
            time.sleep(1)
        environment=dict(os.environ,CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES=gpu_uuid,
            GGML_CUDA_F32_ACTIVATIONS='1',COW_QWEN35_F32_ATTENTION='1',NVIDIA_TF32_OVERRIDE='0',GGML_NO_BACKTRACE='1')
        argv=[str(binary),str(model),'256','128','8','CUDA0']
        if adapter is not None:argv+=['--lora',str(adapter),'1']
        proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=environment,start_new_session=True,pass_fds=(lease.fileno(),*extra_pass_fds))
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
