"""Real CPU weight updates through both CLIs; generated model, controlled tasks."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,threading,time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pcc-root',type=Path,required=True);parser.add_argument('--bw-root',type=Path,required=True)
parser.add_argument('--native-executable',type=Path,required=True)
parser.add_argument('--workdir',type=Path,required=True,help='New private output directory; existing directories are refused.')
args=parser.parse_args()
pcc=args.pcc_root.resolve(strict=True);bw=args.bw_root.resolve(strict=True)
sys.path[:0]=[str(bw),str(pcc)]
from serve.cow_http import make_server
from tools.pcc_lessons import LessonService,NativeRunner
from sss.adapters.bw_fixtures import task
from sss.curriculum import exercise_for
from sss.learning_lessons import build_scalar_pcc_lesson
from branchwrite.lesson_cli import digest

root=args.workdir.absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
from experimental.native_training.make_cpu_fixture import make_fixture
model=make_fixture(root/'tiny-byte-fixture.gguf',context_length=1024);binary=args.native_executable.resolve(strict=True)
base_hash=hashlib.sha256(model.read_bytes()).hexdigest();contract=hashlib.sha256(b'pcc-byte-fixture-v1'+model.read_bytes()).hexdigest()
service=None;server=None;thread=None
def phase(name,**extra):
 value=dict(phase=name,time=time.time(),**extra);temp=root/'phase.tmp';temp.write_text(json.dumps(value)+'\n');temp.replace(root/'phase.json');print(json.dumps(value),flush=True)
def command(argv,name,env):
 with (root/(name+'.stdout')).open('w') as out,(root/(name+'.stderr')).open('w') as err:
  p=subprocess.run(list(map(str,argv)),stdout=out,stderr=err,env=env,timeout=240)
 (root/(name+'.exit')).write_text(str(p.returncode)+'\n');assert p.returncode==0,'Inspect '+name+'.stderr'
 return json.loads((root/(name+'.stdout')).read_text())
try:
 phase('native-cpu-service')
 runner=NativeRunner(dict(model=str(model),base_sha256=base_hash,executable=str(binary),devices=['CPU'],gpu_uuids=[],
   device_budget_bytes={'CPU':1024**3},reserve_bytes=16*1024**2))
 service=LessonService(root/'service',contract,lambda text:list(text.encode()),runner,max_tokens=512,max_steps=16)
 key='cpu-proof-'+os.urandom(16).hex()
 server=make_server(object(),api_key=key,training_service=service,connection_info=dict(model_contract_id=contract,execution_profile_id=digest({'cpu':'fixture'}),eos_tokens=[0]))
 thread=threading.Thread(target=server.serve_forever);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 connection=dict(endpoint_url=url,endpoint_pin=digest({'url':url}),model_contract_id=contract,execution_profile_id=digest({'cpu':'fixture'}),eos_tokens=[0])
 connection_file=root/'connection.json';connection_file.write_text(json.dumps(connection));connection_file.chmod(0o600)
 env=dict(os.environ,PYTHONPATH=str(bw)+os.pathsep+str(pcc),BW_COW_API_KEY=key,COW_API_KEY=key)
 def bwcli(args,name):return command([sys.executable,'-m','branchwrite','lesson','--connection',connection_file,'--state-dir',root/'bw-requests',*args],name,env)
 def cowcli(args,name):return command([sys.executable,pcc/'tools/cow_cli.py','--url',url,'--state-dir',root/'cow-requests','lesson',*args],name,env)
 def wait(identity):
  deadline=time.monotonic()+180
  while True:
   value=service.job(identity)
   if value['state'] not in ('queued','running'):
    assert value['state']=='complete',value
    assert value['promoted'] is False
    return value
   if time.monotonic()>deadline:raise TimeoutError('Native CPU job '+identity)
   time.sleep(.05)
 phase('real-bw-failed-check-help-and-passing-check')
 states={}
 for name,factor in [('double',2),('triple',3),('quadruple',4),('quintuple',5)]:
  states[name]=task(root/name,connection,corrected=True,factor=factor,name=name,include_failed_check=True)
 def author(name,factor,*extra):
  return ['create','--corrected-state',states[name],'--prompt','Python '+name+'(n):','--completion',' '+str(factor)+'*n',
      '--title','Controlled '+name+' correction','--operation-id',name+'-lesson',*extra]
 phase('bw-one-command-single-example-update')
 first=bwcli(author('double',2,'--train-now','--learning-rate','.01'),'single-submit');single=wait(first['training']['job_id'])
 assert len(single['steps'])==1 and single['steps'][0]['examples']==1
 phase('queue-lessons-through-both-clis')
 second=bwcli(author('triple',3,'--queue'),'queue-triple')
 draft=bwcli(author('quadruple',4),'draft-quadruple')
 third=cowcli(['submit',draft['lesson_file'],'--operation-id','quadruple-lesson'],'queue-quadruple')
 fourth=bwcli(author('quintuple',5,'--queue'),'queue-quintuple')
 listing=bwcli(['list'],'pending-list');assert sum(row['pending'] for row in listing['lessons'])==3
 batch_args=['train','--pending','--operation-id','cpu-batch','--batch-size','2','--learning-rate','.01','--parent-job-id',single['job_id']]
 phase('bw-batch-default-covers-all-three-with-final-partial-batch')
 accepted=bwcli(batch_args,'batch-submit');batch=wait(accepted['job_id'])
 assert [step['examples'] for step in batch['steps']]==[2,1]
 assert all(step['after']<step['before'] for step in batch['steps'])
 phase('retry-frozen-selection-after-pending-queue-is-empty')
 assert bwcli(batch_args,'batch-retry')==accepted
 assert not any(row['pending'] for row in cowcli(['list'],'empty-pending')['lessons'])
 assert len(list((root/'service/runs').iterdir()))==2
 phase('cow-cli-direct-full-weight-update-and-continuation')
 identity=first['acceptance']['lesson_id']
 full_accept=cowcli(['train',identity,'--operation-id','cpu-full','--mode','full','--batch-size','1'],'full-submit')
 full=wait(full_accept['job_id'])
 continued_accept=cowcli(['train',identity,'--operation-id','cpu-full-next','--mode','full','--batch-size','1','--parent-job-id','cpu-full'],'full-next-submit')
 continued=wait(continued_accept['job_id'])
 phase('verify-native-candidate-reload')
 def evaluate(name,job,lesson_id,mode):
  record=json.loads((root/'service/operations'/(job+'.json')).read_text());candidate=record['candidate']
  example=service.lesson(lesson_id)['example']
  request=dict(model=str(model),base_sha256=base_hash,devices=['CPU'],mode='lora',rank=4,backprop_mode='standard',evaluate_only=True,
      examples=[example],learning_rate=.0001,device_budget_bytes={'CPU':1024**3},reserve_bytes=16*1024**2)
  if mode=='lora':request['initial_adapter']=candidate['candidate_path']
  else:request.update(model=candidate['candidate_path'],base_sha256=candidate['candidate_sha256'])
  path=root/(name+'-private.json');path.write_text(json.dumps(request)+'\n')
  result=command([binary,'--train',path],name,env)
  assert abs(result['losses'][0]-candidate['receipt']['steps'][-1]['after'])<=1e-6
  return dict(candidate_sha256=candidate['candidate_sha256'],loss=result['losses'][0])
 batch_record=json.loads((root/'service/operations/cpu-batch.json').read_text())
 reload_lora=evaluate('reload-lora','cpu-batch',batch_record['request']['lesson_ids'][-1],'lora')
 reload_full=evaluate('reload-full','cpu-full',identity,'full')
 continuation_record=json.loads((root/'service/operations/cpu-full-next.json').read_text())
 assert continuation_record['candidate']['base_sha256']==reload_full['candidate_sha256']
 assert hashlib.sha256(model.read_bytes()).hexdigest()==base_hash
 assert len(list((root/'service/runs').iterdir()))==4
 phase('multi-turn-v2-thinking-target-policy-through-both-clis')
 from sss.adapters.episode_lessons import pcc_lesson
 v2ids=[];v2single=None
 for index,policy in enumerate(('verified_thinking_actions_answer','actions_answer','verified_thinking_actions_answer')):
  number=index+2;answer=str(number+number)
  rows=[dict(role=role,kind=kind,rendered=text,verified=verified,scope='practice') for role,kind,text,verified in [
   ('user','question',str(number)+'+'+str(number)+'?',False),('assistant','thinking','sum='+answer+';',True),('assistant','action','read;',True),('tool','observation',answer+';',False),('user','question','ok?',False),('assistant','answer',answer+'!',True)]]
  evidence=digest(dict(inputs=[number,number],checked=sum([number,number]),expected=int(answer)))
  lesson=pcc_lesson('Owned multi-turn '+str(index),contract,rows,archive_sha256=digest(rows),verification_sha256=evidence,renderer_sha256=digest('byte-fixture-spans-v1'),tokenizer_sha256=digest('utf8-byte-v1'),target_policy=policy)
  path=root/('v2-lesson-'+str(index)+'.json');path.write_text(json.dumps(lesson))
  queued=bwcli(['submit',path,'--operation-id','v2-lesson-'+str(index)],'v2-queue-'+str(index));v2ids.append(queued['lesson_id'])
  if index==0:
   accepted=bwcli(['train',queued['lesson_id'],'--operation-id','v2-single','--learning-rate','.001'],'v2-single-submit');v2single=wait(accepted['job_id'])
 accepted=cowcli(['train',*v2ids[1:],'--operation-id','v2-batch','--batch-size','2','--mode','full','--learning-rate','.001'],'v2-batch-submit');v2batch=wait(accepted['job_id'])
 assert v2single['steps'][0]['examples']==1 and v2batch['steps'][0]['examples']==2
 assert sum(service.lesson(v2ids[0])['example']['loss_mask'])>sum(service.lesson(v2ids[1])['example']['loss_mask'])
 assert hashlib.sha256(model.read_bytes()).hexdigest()==base_hash
 phase('s3-response-level-and-reasoning-lessons-through-real-bw-pcc-native-path')
 def render_scalar(rows):
  return [dict(role=row['role'],kind=row['kind'],
      rendered=('U:' if row['role']=='user' else 'A:')+row['content'],
      verified=row['verified'],scope=row['scope']) for row in rows]
 exercise=exercise_for('math.add.no_carry','practice',41,gate='independent',seed=20261028)
 response_cases=[('answer','direct','answer_only'),
     ('answer','reasoning','reasoning_and_answer'),
     ('format','direct','format_only'),
     ('composed','direct','answer_and_format'),
     ('composed','reasoning','reasoning_answer_and_format')]
 response_results=[]
 for index,(level,answer_mode,policy) in enumerate(response_cases):
  key=level+'-'+answer_mode
  prepared=build_scalar_pcc_lesson(exercise,level,render_scalar,
      archive_path=root/('s3-archive-'+key),model_contract_id=contract,
      renderer_sha256=digest('cpu-s3-renderer-v1'),tokenizer_sha256=digest('utf8-byte-v1'),
      tokenize=lambda text:list(text.encode()),maximum=8192,answer_mode=answer_mode)
  assert prepared['lesson']['target_policy']==policy
  lesson_file=root/('s3-lesson-'+key+'.json')
  lesson_file.write_text(json.dumps(prepared['lesson'])+'\n')
  accepted=bwcli(['submit',lesson_file,'--operation-id','s3-'+key],'s3-submit-'+key)
  saved=service.lesson(accepted['lesson_id'])
  expected=prepared['expected_example'];actual=saved['example']
  assert actual['tokens']==expected['tokens'] and actual['targets']==expected['targets']
  assert actual['loss_mask']==expected['loss_mask']
  assert sum(actual['loss_mask'])>0
  operation='s3-train-'+key
  trained=bwcli(['train',accepted['lesson_id'],'--operation-id',operation,
      '--mode','full','--batch-size','1','--steps','1','--learning-rate','.001'],
      's3-train-submit-'+key)
  completed=wait(trained['job_id'])
  request=json.loads((root/'service/runs'/operation/'request-private.json').read_text())
  assert request['examples'][0]['loss_mask']==expected['loss_mask']
  assert completed['promoted'] is False and len(completed['steps'])==1
  response_results.append(dict(level=level,answer_mode=answer_mode,target_policy=policy,
      supervised_tokens=sum(expected['loss_mask']),job_id=operation,
      loss_before=completed['steps'][0]['before'],loss_after=completed['steps'][0]['after'],
      native_mask_equal=True))
 assert hashlib.sha256(model.read_bytes()).hexdigest()==base_hash
 result=dict(status='PASS',scope='real native CPU single/batch/update/reload wiring through both CLIs and real BW tool boundaries',
    fixture='generated tiny hybrid GGUF with byte vocabulary; not a language-quality test',spontaneous_model_failure=False,
    gpu_used=False,promoted=False,base_unchanged=True,model_sha256=base_hash,executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    single=single,batch=batch,full=full,full_continued=continued,lora_reload=reload_lora,full_reload=reload_full,
    multi_turn_v2=dict(single=v2single,batch=v2batch,thinking_targets_optional=True,context_gradients_preserved=True),
    s3_response_level_native_updates=response_results,
    duplicate_update_prevented=True,selected_batch_frozen=True,partial_final_batch=True,same_task_failure_and_repair=True)
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');phase('complete',status='PASS');(root/'command.exit').write_text('0\n')
except BaseException as error:
 phase('failed',error=type(error).__name__+': '+str(error));(root/'command.exit').write_text('1\n');raise
finally:
 if server is not None:server.shutdown();server.server_close()
 if thread is not None:thread.join()
 if service is not None:service.close()
