"""Real native CPU updates and both CLIs; controlled skill regression injection.

The tiny fixture and controlled evaluator prove orchestration, not model quality.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pcc-root',type=Path,required=True);parser.add_argument('--bw-root',type=Path,required=True);parser.add_argument('--native-executable',type=Path,required=True)
parser.add_argument('--workdir',type=Path,required=True);args=parser.parse_args()
pcc=args.pcc_root.resolve(strict=True);bw=args.bw_root.resolve(strict=True);sys.path[:0]=[str(bw),str(pcc)]
from experimental.native_training.make_cpu_fixture import make_fixture
from tools.pcc_lessons import LessonService,NativeRunner,digest
from sss import SkillTree,SkillGuardRunner
from sss.adapters.pcc_init import initialize
from serve.cow_http import make_server
from sss.adapters.bw_fixtures import task

root=args.workdir.absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
model=make_fixture(root/'tiny.gguf');base_hash=hashlib.sha256(model.read_bytes()).hexdigest();contract=digest(dict(fixture=base_hash))
config=dict(model=str(model),base_sha256=base_hash,executable=str(args.native_executable.resolve(strict=True)),devices=['CPU'],gpu_uuids=[],
            device_budget_bytes={'CPU':1024**3},reserve_bytes=16*1024**2)
service=LessonService(root/'store',contract,lambda text:list(text.encode()),NativeRunner(config),max_tokens=256,max_steps=32)
document=initialize(service,practice_per_skill=16,validation_per_skill=4,blind_per_skill=4);service.close();tree=SkillTree(document)
evaluations=[]
def evaluate(candidate,split,path,fd):
    # Host-controlled regression and recovery, explicitly not native inference.
    failed=set()
    if path.name=='baseline' and candidate is None:failed={'python.arithmetic.ceil'}
    elif path.name=='check-0':failed={'python.arithmetic.floor'}
    elif path.name=='blind-original' and candidate is None:failed={'python.arithmetic.ceil'}
    rows=[dict(id=row['id'],passed=tree.case_skill[row['id']] not in failed) for row in tree.rows(split)]
    evaluations.append(dict(split=split,phase=path.name,failed_skills=sorted(failed)))
    return rows
guard=SkillGuardRunner(NativeRunner(config),tree,evaluate,round_examples=10,max_rounds=3)
service=LessonService(root/'store',contract,lambda text:list(text.encode()),guard,max_tokens=256,max_steps=32)
key='private-cpu-proof-'+os.urandom(16).hex()
server=make_server(object(),api_key=key,training_service=service)
thread=threading.Thread(target=server.serve_forever);thread.start();url='http://127.0.0.1:'+str(server.server_port)
connection=dict(endpoint_url=url,endpoint_pin=digest(dict(url=url)),model_contract_id=contract,execution_profile_id=digest(dict(cpu=1)),eos_tokens=[0])
connection_file=root/'connection.json';connection_file.write_text(json.dumps(connection));connection_file.chmod(0o600)
env=dict(os.environ,PYTHONPATH=str(bw)+os.pathsep+str(pcc),BW_COW_API_KEY=key,COW_API_KEY=key)
def command(argv,name):
    with (root/(name+'.stdout')).open('x') as out,(root/(name+'.stderr')).open('x') as err:
        result=subprocess.run(list(map(str,argv)),stdout=out,stderr=err,env=env,timeout=300)
    if result.returncode:raise AssertionError('Inspect '+name+' stderr; exit '+str(result.returncode))
    return json.loads((root/(name+'.stdout')).read_text())
def bwcli(argv,name):return command([sys.executable,'-m','branchwrite','lesson','--connection',connection_file,'--state-dir',root/'bw-requests',*argv],name)
def cowcli(argv,name):return command([sys.executable,pcc/'tools/cow_cli.py','--url',url,'--state-dir',root/'cow-requests','lesson',*argv],name)
def wait(identity):
    deadline=time.monotonic()+300
    while True:
        value=service.job(identity)
        if value['state'] not in ('running','queued'):
            if value['state']!='complete':raise AssertionError(value)
            return value
        if time.monotonic()>deadline:raise TimeoutError('Retain original job '+identity)
        time.sleep(.1)
try:
    state=task(root/'bw-task',connection,corrected=True,include_failed_check=True)
    create=['create','--corrected-state',state,'--prompt','def double(n): return','--completion',' 2*n','--title','Checked double correction',
        '--skill','python.arithmetic.multiply','--operation-id','skill-example','--train-now','--skill-guard','--batch-size','5','--steps','6','--learning-rate','.01']
    skills=bwcli(['skills'],'bw-skills');assert skills['tree_id']==tree.identity
    assert cowcli(['skills'],'cow-skills')['policy_id']==guard.policy_id
    accepted=bwcli(create,'bw-submit');job=wait(accepted['training']['job_id']);report=job['skill_guard']
    assert report['qualified'] and not job['promoted'] and len(report['rounds'])==2
    assert report['rounds'][1]['focus_skills']==['python.arithmetic.floor']
    assert all(set(row['distribution'])==set(tree.leaves) for row in report['rounds'])
    assert bwcli(create,'bw-reconcile')==accepted
    assert len(list((root/'store/runs/skill-example-train').glob('round-*/launch.json')))==2
    identity=accepted['acceptance']['lesson_id']
    follow=['train',identity,'--operation-id','skill-follow','--skill-guard','--batch-size','5','--steps','6','--learning-rate','.01','--parent-job-id','skill-example-train']
    acceptance=cowcli(follow,'cow-submit');continued=wait(acceptance['job_id'])
    assert continued['skill_guard']['qualified'];assert cowcli(follow,'cow-reconcile')==acceptance
    runs=list((root/'store/runs').glob('*/round-*/launch.json'));assert len(runs)==4
    assert hashlib.sha256(model.read_bytes()).hexdigest()==base_hash
    result=dict(status='PASS',scope='native CPU mixed skill orchestration through BW/COW CLI and authenticated HTTP',
        semantic_evaluator='controlled regression/recovery injection, not language-quality inference',
        spontaneous_model_failure=False,gpu_used=False,promoted=False,base_unchanged=True,
        fixture_sha256=base_hash,tree_id=tree.identity,policy_id=guard.policy_id,native_runs=len(runs),
        first=report,continued=continued['skill_guard'],evaluations=evaluations,
        reconciliation_prevented_duplicate_updates=True,all_declared_skills_replayed=True)
    (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status='PASS',native_runs=len(runs),rounds=len(report['rounds']))))
finally:
    server.shutdown();server.server_close();thread.join();service.close()
