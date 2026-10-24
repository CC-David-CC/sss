"""One owner-configured native optimizer pilot step; no model promotion or retries.

This integration command owns its explicit resource window. PCC owns the native
update/candidate, S3 binds the checked practice selection and records the result.
"""
from pathlib import Path
import argparse,json,sys,os,time,subprocess,fcntl,hashlib,shutil,signal

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def write(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def run(a):
 if not (1<=a.steps<=1000 and a.batch_size>=1 and 1<=a.timeout_seconds<=3600 and a.gpu_index>=0 and a.device_budget_gib>a.reserve_gib>=1 and a.host_reserve_gib>=1 and a.disk_reserve_gib>=1 and 0<=a.maximum_initial_utilization<=100 and __import__('math').isfinite(a.learning_rate) and a.learning_rate>0):raise ValueError('Explicit bounded owner resources and update settings required')
 pcc=a.pcc_root.resolve(strict=True);sys.path.insert(0,str(pcc))
 from tools.pcc_native_training import execute_native,read_optimizer_state,validate_examples
 from tools.gguf_reader import GGUFFile
 selection=json.loads(a.selection.read_text())
 if selection.get('pilot_id')!=digest({k:v for k,v in selection.items() if k!='pilot_id'}):raise ValueError('Checked practice selection identity differs')
 if selection.get('protected_cases_exported') is not False or selection.get('target_policy')!='actions_answer':raise ValueError('Unexpected pilot split/target policy')
 examples=validate_examples(selection['examples'],sequence_profile='dense-llama-short-v1')
 if [x['id'] for x in examples]!=[x['lesson_id'] for x in selection['selection']]:raise ValueError('Selected token examples differ from admitted lessons')
 probe=json.loads(a.gradient_evidence.read_text())
 if probe.get('status')!='PASS' or probe.get('pilot_id')!=selection['pilot_id'] or probe.get('finite_gradient_tensors')!=381:raise ValueError('Actual-model gradient gate is not established for this selection')
 root=a.output.resolve();root.mkdir(mode=0o700,parents=True,exist_ok=False)
 original=a.model.resolve(strict=True)
 if sha(original)!=selection['model_sha256']:raise ValueError('Original MiniCPM weights differ')
 settings=json.loads(a.optimizer_settings.read_text()) if a.optimizer_settings else dict(schema=1,**({'aux_learning_rate':.000001} if a.optimizer=='muon' else {}))
 request=dict(model=str(original),base_sha256=selection['model_sha256'],mode='full',devices=['CUDA0'],sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',device_budget_bytes={'CUDA0':a.device_budget_gib<<30},reserve_bytes=a.reserve_gib<<30,host_reserve_bytes=a.host_reserve_gib<<30,examples=examples,optimizer=a.optimizer,optimizer_settings=settings,optimizer_state_mode='fresh',learning_rate=a.learning_rate,batch_size=a.batch_size,steps=a.steps,deadline_seconds=a.timeout_seconds)
 parent=None
 if a.parent_result:
  parent=json.loads(a.parent_result.read_text())
  if parent.get('result_id')!=digest({k:v for k,v in parent.items() if k!='result_id'}) or parent.get('pilot_id')!=selection['pilot_id'] or parent.get('status')!='MECHANICS_COMPLETE':raise ValueError('Parent result is not this completed pilot')
  candidate=parent['candidate'];checkpoint=candidate['receipt']['optimizer_checkpoint']
  request.update(model=candidate['candidate_path'],base_sha256=candidate['candidate_sha256'],optimizer_state_mode='resume',initial_optimizer_state=checkpoint['path'],initial_optimizer_state_sha256=checkpoint['sha256'],example_cursor=candidate['receipt']['example_cursor'])
 info=GGUFFile(original);weights=sum(t.elements*4 for t in info.tensors);hidden=sum(t.elements*4 for t in info.tensors if t.name.startswith('blk.') and t.name.split('.',2)[2] in {'attn_q.weight','attn_k.weight','attn_v.weight','attn_output.weight','ffn_up.weight','ffn_gate.weight','ffn_down.weight'})
 states=2*weights if a.optimizer=='adamw' else hidden+2*(weights-hidden)
 if shutil.disk_usage(root).free<weights+states+(a.disk_reserve_gib<<30)+(64<<20):raise RuntimeError('Candidate/state/disk reserve admission refused')
 write(root/'intent.json',dict(schema=1,pilot_id=selection['pilot_id'],selection_sha256=sha(a.selection),gradient_evidence_sha256=sha(a.gradient_evidence),request=request,executable_sha256=sha(a.native_executable),source_sha256=sha(__file__),parent_result_id=None if parent is None else parent['result_id'],quality_acceptance=False))
 lock=Path.home()/'.local/state/context-cow'/('gpu-'+str(a.gpu_index)+'.lock');lock.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 start=time.monotonic();status='FAILED';candidate=None
 with lock.open('a') as lease:
  fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True)
  selected=[l.split(',') for l in raw.splitlines() if int(l.split(',')[0])==a.gpu_index]
  if len(selected)!=1 or int(selected[0][2])<a.device_budget_gib*1024 or int(selected[0][3])>a.maximum_initial_utilization:raise RuntimeError('GPU headroom/utilization admission refused')
  physical=selected[0];env=dict(os.environ,CUDA_VISIBLE_DEVICES=physical[1].strip(),CUDA_DEVICE_ORDER='PCI_BUS_ID',GGML_CUDA_F32_ACTIVATIONS='1',NVIDIA_TF32_OVERRIDE='0')
  write(root/'admission.json',dict(physical_gpu=a.gpu_index,gpu_uuid=physical[1].strip(),free_mib=int(physical[2]),utilization=int(physical[3]),lease=str(lock)))
  try:
   candidate=execute_native(a.native_executable,request,root/'update',timeout=a.timeout_seconds+20,environment=env,pass_fds=(lease.fileno(),))
   receipt=candidate['receipt'];last=receipt['steps'][-1];count=last['examples'];cursor=last['example_cursor'];batch=examples[(cursor-count)%len(examples):(cursor-count)%len(examples)+count]
   evaluate={k:v for k,v in request.items() if k not in ['optimizer','optimizer_settings','optimizer_state_mode','initial_optimizer_state','initial_optimizer_state_sha256','steps','example_cursor']}
   evaluate.update(model=candidate['candidate_path'],base_sha256=candidate['candidate_sha256'],evaluate_only=True,examples=batch,candidate=str(root/'never-written.gguf'))
   path=root/'reload-request-private.json';write(path,evaluate)
   with (root/'reload-stdout-private.json').open('x') as out,(root/'reload-stderr-private.log').open('x') as err:
    child=subprocess.Popen([str(a.native_executable),'--train',str(path)],env=env,stdout=out,stderr=err,start_new_session=True,pass_fds=(lease.fileno(),))
    write(root/'reload-process.json',dict(pid=child.pid,start_ticks=Path('/proc',str(child.pid),'stat').read_text().split()[21]))
    try:code=child.wait(timeout=a.timeout_seconds+20)
    except subprocess.TimeoutExpired:child.kill();child.wait();raise
    if code:raise RuntimeError('Candidate reload failed; preserve original result')
   losses=json.loads((root/'reload-stdout-private.json').read_text())['losses'];error=abs(sum(losses)/len(losses)-last['after'])
   if error>2e-4:raise ValueError('Actual-model candidate reload loss mismatch')
   checkpoint=receipt['optimizer_checkpoint'];state=read_optimizer_state(checkpoint['path'],checkpoint['sha256'])
   result=dict(schema=1,status='MECHANICS_COMPLETE',scope='Actual-model native update/reload; not learning acceptance',pilot_id=selection['pilot_id'],candidate=candidate,reload_loss_error=error,optimizer_completed_steps=state['completed_steps'],example_cursor=state['example_cursor'],gradient_tensors=[len(s['gradients']) for s in receipt['steps']],nonzero_gradient_tensors=[sum(g['l2']>0 for g in s['gradients']) for s in receipt['steps']],parent_result_id=None if parent is None else parent['result_id'],promoted=False)
   result['result_id']=digest(result);write(root/'result-private.json',result);status='MECHANICS_COMPLETE'
   print(json.dumps({k:result[k] for k in ['status','pilot_id','reload_loss_error','optimizer_completed_steps','example_cursor','gradient_tensors','nonzero_gradient_tensors','promoted']}),flush=True)
  finally:
   write(root/'settlement.json',dict(status=status,allocated_seconds=time.monotonic()-start,physical_gpus=1,quality_acceptance=False))
   fcntl.flock(lease,fcntl.LOCK_UN)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pcc-root',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--gradient-evidence',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--native-executable',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--optimizer',choices=['muon','adamw'],required=True);p.add_argument('--optimizer-settings',type=Path);p.add_argument('--parent-result',type=Path);p.add_argument('--learning-rate',type=float,required=True);p.add_argument('--batch-size',type=int,default=2);p.add_argument('--steps',type=int,default=1);p.add_argument('--gpu-index',type=int,required=True);p.add_argument('--device-budget-gib',type=int,required=True);p.add_argument('--reserve-gib',type=int,default=4);p.add_argument('--host-reserve-gib',type=int,default=4);p.add_argument('--disk-reserve-gib',type=int,default=16);p.add_argument('--timeout-seconds',type=int,default=300);p.add_argument('--maximum-initial-utilization',type=int,default=50);run(p.parse_args())
