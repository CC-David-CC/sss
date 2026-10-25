"""Durable learning rounds using real tiny native classification, not injected scores.

The fixture learns a constant-token rule on training prefixes that differ from
the evaluation prefixes. It is an orchestration check, not language capability.
"""
from pathlib import Path
import argparse,json,os,subprocess,sys,threading,time,hashlib


def run(pcc_root,bw_root,executable,output):
    pcc=Path(pcc_root).resolve(strict=True);bw=Path(bw_root).resolve(strict=True)
    sys.path[:0]=[str(bw),str(pcc),str(pcc/'experimental/branching_context/src')]
    import numpy as np
    from experimental.native_training.make_llama_fixture import make_fixture
    from tools.pcc_lessons import LessonService,NativeRunner
    from tools.pcc_native_training import sha256
    from tools.pcc_optimizer_profiles import identity
    from serve.cow_http import make_server
    from sss.records import digest
    from sss.adapters.learning_policy import LearningPolicy
    root=Path(output).absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    model=make_fixture(root/'base.gguf',dtype='f32',layers=1);base=sha256(model)
    cases=[dict(id=digest(dict(prefix=p,target='constant-six')),prefix=p,target=6,
        skill_id='fixture.constant-six',gate=gate) for p,gate in [([1,2],'independent'),([2,3],'composition'),
        ([3,4],'transfer_recovery'),([4,5],'transfer_recovery')]]

    class Evaluator:
        def binding(self):return dict(source=sha256(__file__),native=sha256(executable),cases=cases,scope='tiny constant-token classification')
        def verify(self):
            if sha256(model)!=base:raise ValueError('Original fixture changed')
        def validate_lessons(self,lessons,report):
            for record in lessons:
                lesson=record['lesson']
                if lesson.get('skill_id')!='fixture.constant-six' or lesson['completion']!='6':raise ValueError('Wrong checked practice rule')
                prefix=list(map(int,lesson['prompt']))
                if prefix in [v['prefix'] for v in cases]:raise ValueError('Evaluation prefix reached practice')
        def validate(self,value,candidate):
            expected=base if candidate is None else candidate['candidate_sha256']
            if (value['evaluation_id']!=digest(cases) or value['runtime_id']!=digest(self.binding())
                    or value['model_sha256']!=expected or {v['id'] for v in value['outcomes']}!={v['id'] for v in cases}):
                raise ValueError('Wrong actual evaluation identity/coverage')
        def __call__(self,candidate,directory,worker_fd):
            actual=model if candidate is None else Path(candidate['candidate_path'])
            actual_sha=sha256(actual);rows=[]
            for index,case in enumerate(cases):
                prefix=case['prefix'];example=dict(id=case['id'],tokens=prefix,
                    targets=prefix[1:]+[case['target']],loss_mask=[False]*(len(prefix)-1)+[True],
                    verified=True,provenance_sha256=digest(dict(rule='constant-six',prefix=prefix)))
                request=dict(model=str(actual),base_sha256=actual_sha,mode='full',rank=2,
                    devices=['CPU'],device_budget_bytes={'CPU':4<<30},reserve_bytes=128<<20,host_reserve_bytes=128<<20,
                    sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',examples=[example],
                    optimizer='sgd',learning_rate=.001,batch_size=1,steps=1,evaluate_only=True,
                    backprop_mode='standard',logits_output=str(directory/('logits-'+str(index)+'.bin')))
                config=directory/('case-'+str(index)+'.json');config.write_text(json.dumps(request))
                with (directory/('case-'+str(index)+'.stdout')).open('x') as stdout,(directory/('case-'+str(index)+'.stderr')).open('x') as stderr:
                    done=subprocess.run([str(executable),'--train',str(config)],stdout=stdout,stderr=stderr,
                        pass_fds=(worker_fd,),timeout=30)
                if done.returncode:raise RuntimeError('Original native fixture evaluation failed')
                logits=np.fromfile(request['logits_output'],dtype='<f4').reshape(len(prefix),7)
                if not np.isfinite(logits).all():raise ValueError('Nonfinite fixture logits')
                prediction=int(logits[-1].argmax())
                rows.append(dict(id=case['id'],skill_id=case['skill_id'],gate=case['gate'],
                    passed=prediction==case['target'],finished=True))
                (directory/('observed-'+str(index)+'.json')).write_text(json.dumps(dict(prediction=prediction,target=case['target'])))
            return dict(schema=1,status='COMPLETE',evaluation_id=digest(cases),runtime_id=digest(self.binding()),
                model_sha256=actual_sha,cases=len(rows),passed=sum(v['passed'] for v in rows),finished=len(rows),
                outcomes=rows,weights_updated=False,promoted=False,scope='Actual tiny native argmax classification; finished means one bounded classification, not LLM EOS')

    config=dict(model=str(model),base_sha256=base,executable=str(executable),devices=['CPU'],gpu_uuids=[],
        device_budget_bytes={'CPU':4<<30},reserve_bytes=128<<20,host_reserve_bytes=128<<20,
        sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',timeout_seconds=60)
    fresh=dict(schema=2,title='Tiny full AdamW learning-round fixture',mode='full',rank=None,optimizer='adamw',
        learning_rate=.01,optimizer_settings=dict(schema=1),state_policy='fresh',training_budget_seconds=None)
    config['optimizer_profiles']={identity(fresh):fresh}
    training=dict(mode='full',rank=2,batch_size=1,steps=16,learning_rate=.01,optimizer_profile_id=identity(fresh))
    policy=LearningPolicy(Evaluator(),training,title='Actual tiny native round integration',max_rounds=3,assessment_purpose='machinery')
    policy_id=digest(policy.describe())
    def service_new(policies=None):return LessonService(root/'service','a'*64,lambda text:list(map(int,text)),NativeRunner(config),
        max_tokens=512,max_steps=32,sequence_profile='dense-llama-short-v1',learning_policies={policy_id:policy} if policies is None else policies)
    service=service_new();server=make_server(object(),api_key='private-cpu-round-key',training_service=service)
    thread=threading.Thread(target=server.serve_forever);thread.start()
    port=server.server_port;url='http://127.0.0.1:'+str(port)
    connection=root/'connection-private.json';connection.write_text(json.dumps(dict(endpoint_url=url,endpoint_pin=digest(dict(url=url)),model_contract_id='a'*64,execution_profile_id='b'*64,eos_tokens=[0])))
    environment=dict(os.environ,PYTHONPATH=os.pathsep.join([str(bw),str(pcc),str(pcc/'experimental/branching_context/src'),str(Path(__file__).resolve().parents[1])]),BW_COW_API_KEY='private-cpu-round-key',COW_API_KEY='private-cpu-round-key')
    def cli(client,arguments,name):
        prefix=([sys.executable,'-m','branchwrite','learning','--connection',str(connection),'--state-dir',str(root/'bw-journal')] if client=='bw' else [sys.executable,'-m','tools.pcc_learning_loop','--url',url,'--state-dir',str(root/'cow-journal')])
        done=subprocess.run([*prefix,*arguments],env=environment,capture_output=True,text=True,timeout=30)
        (root/(name+'.stdout')).write_text(done.stdout);(root/(name+'.stderr')).write_text(done.stderr)
        assert done.returncode==0,(name,done.returncode,done.stdout,done.stderr)
        return json.loads(done.stdout)
    from urllib.request import Request,urlopen
    from urllib.error import HTTPError
    def call(path,data=None):
        with urlopen(Request('http://127.0.0.1:'+str(server.server_port)+path,
            data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer private-cpu-round-key',
            'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
    def status():return call('/cow/training/learning-runs/learning-fixture')
    def settle():
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            value=status()
            if not value['phase'].endswith('_running'):return value
            time.sleep(.02)
        raise TimeoutError('Original phase still owned; do not dispatch again')
    serial=0;faults=dict(creation=False,dispatch_gap=False,after_submit=False,baseline_commit=False)
    def reopen(policies=None):
        nonlocal service,server,thread
        server.shutdown();server.server_close();thread.join();service.close()
        service=service_new(policies);server=make_server(object(),port=port,api_key='private-cpu-round-key',training_service=service)
        thread=threading.Thread(target=server.serve_forever);thread.start()
    def step(action='advance',**extra):
        nonlocal serial
        current=status();assert action in {row['action'] for row in current['available_actions']},current
        serial+=1;request=dict(operation_id='step-'+str(serial),run_id='learning-fixture',
            expected_revision=current['revision'],action=action,**extra)
        client='bw' if serial%2 else 'cow'
        arguments=[action,'learning-fixture',*extra.get('lesson_ids',[]),'--operation-id',request['operation_id']]
        if action=='preserve':
            notes=root/'preservation-notes.txt';notes.write_text(extra['notes']);arguments+=['--name',extra['name'],'--notes-file',str(notes)]
        fault_kind=('before' if not faults['dispatch_gap'] else 'after' if not faults['after_submit'] else None)
        if action=='advance' and extra.get('lesson_ids') and fault_kind is not None:
            from branchwrite.cow_client import CowClient,OperationJournal
            def interrupted_dispatch(kind,identity,operation,work):
                if fault_kind=='after':service.submit('/cow/training/jobs',work)
                raise SystemExit('Injected exit at original native dispatch boundary: '+fault_kind)
            service.learning._dispatch=interrupted_dispatch
            owner=CowClient.http(url,api_key='private-cpu-round-key',endpoint_pin=digest(dict(url=url)),journal=OperationJournal(root/'lost-acceptance-journal'))
            class CountTransport:
                name='actual-http-with-discarded-response';posts=0
                def __init__(self,transport):self.transport=transport
                def request(self,method,*args,**kwargs):
                    if method=='POST':self.posts+=1
                    return self.transport.request(method,*args,**kwargs)
            transport=CountTransport(owner.transport);owner.transport=transport
            payload={k:v for k,v in request.items() if k!='operation_id'}
            ack=owner.training_submit('learning-steps',payload,request['operation_id'])
            assert owner.training_submit('learning-steps',payload,request['operation_id'])==ack and transport.posts==1
            value=status();assert value['phase']=='training_pending'
            assert (service.root/'operations'/(value['training_job_id']+'.json')).exists()==(fault_kind=='after')
            reopen();faults['dispatch_gap' if fault_kind=='before' else 'after_submit']=True
            assert status()['phase']=='training_pending'
        else:
            ack=cli(client,arguments,'step-'+str(serial))
            assert cli(client,arguments,'repeat-step-'+str(serial))==ack
        assert call('/cow/training/learning-steps',request)==ack
        return settle()
    try:
        assert call('/cow/training/learning-policies')['policies'][0]['id']==policy_id
        create=dict(operation_id='learning-fixture',policy_id=policy_id,parent_job_id=None,expected_parent_sha256=None)
        start=['start','--operation-id','learning-fixture','--policy-id',policy_id]
        creation_written=threading.Event();initial_save=service.learning._save
        def interrupt_creation(value):
            if value['phase']=='baseline_pending' and value['revision']==0:
                creation_written.set();raise SystemExit('Injected exit between creation intent and run record')
            return initial_save(value)
        service.learning._save=interrupt_creation
        ack=cli('bw',start,'start');assert creation_written.wait(10)
        assert not (service.root/'learning/learning-fixture/run.json').exists()
        reopen();assert status()['phase']=='baseline_pending'
        assert not list((service.root/'runs').iterdir())
        faults['creation']=True
        assert call('/cow/training/learning-runs',create)==ack
        assert cli('bw',start,'repeat-start')==ack
        # Actual native evaluation completes, then the durable phase commit is interrupted.
        baseline_written=threading.Event();original_save=service.learning._save
        def interrupt_baseline_commit(value):
            if value['phase']=='choosing_lessons' and 'baseline_evaluation' in value:
                baseline_written.set();raise SystemExit('Injected exit after evaluation file, before phase commit')
            return original_save(value)
        service.learning._save=interrupt_baseline_commit
        serial+=1
        cli('bw',['advance','learning-fixture','--operation-id','step-'+str(serial)],'interrupted-baseline')
        assert baseline_written.wait(10)
        baseline_path=service.root/'learning/learning-fixture/baseline-evaluation.json'
        original_baseline_sha=sha256(baseline_path)
        original_evaluation_files=len(list((service.root/'learning/learning-fixture/baseline-backend').glob('observed-*.json')))
        reopen();value=step('reconcile');assert value['phase']=='choosing_lessons',value
        assert sha256(baseline_path)==original_baseline_sha
        assert len(list((service.root/'learning/learning-fixture/baseline-backend').glob('observed-*.json')))==original_evaluation_files==4
        faults['baseline_commit']=True
        reports=[];native_jobs=[]
        for index,prompt in enumerate(('01','02','03')):
            # Independent constant-rule teacher; exact evaluation prefixes are not admitted.
            truth=dict(rule='constant-six',training_prefix=list(map(int,prompt)),target=6,passed=True)
            lesson=dict(schema=1,title='Owned constant-rule mechanics '+str(index),model_contract_id='a'*64,
                prompt=prompt,completion='6',rationale='Synthetic native classification fixture, not language capability',
                scope='owned-training',skill_id='fixture.constant-six',evidence=dict(method='host-verified-correction-v1',
                failed_result_sha256=digest(dict(actual_baseline=service.learning._evaluation(service.learning._run('learning-fixture'),'baseline_evaluation'))),
                corrected_result_sha256=digest(truth),verification_sha256=digest(truth)))
            accepted=call('/cow/training/lessons',dict(operation_id='lesson-'+str(index),lesson=lesson))
            value=step(lesson_ids=[accepted['lesson_id']]);assert value['phase'] in ('training_pending','training','candidate_pending'),value
            if value['phase']=='training_pending':value=step('reconcile')
            deadline=time.monotonic()+60
            while status()['training_job']['state'] in ('queued','running'):
                if time.monotonic()>deadline:raise TimeoutError('Original native job still active')
                time.sleep(.02)
            value=step('reconcile') if status()['phase'] in ('training_pending','training') else status();assert value['phase']=='candidate_pending',value
            native_jobs.append(value['training_job_id'])
            launch=json.loads((service.root/'runs'/value['training_job_id']/'launch.json').read_text())
            assert launch['process_identity']['start_ticks']>0 and launch['process_identity']['boot_id']
            value=step();assert value['phase']=='report_pending',value
            value=step();assert value['phase']=='round_complete',value;reports.append(value['last_report'])
            if index==0:
                # Close/reopen the actual service store between completed rounds.
                reopen()
                assert status()['last_report']==reports[-1]
                value=step();assert value['phase']=='choosing_lessons'
            elif index==1:
                value=step();assert value['phase']=='choosing_lessons'
        assert reports[-1]['working_decision']=='RETAIN_PARENT'
        assert cli('bw',['round','learning-fixture','1'],'read-old-round-bw')['report']==reports[0]
        assert cli('cow',['round','learning-fixture','2'],'read-old-round-cow')['report']==reports[1]
        old_record=service.root/'learning/learning-fixture/round-000001.json';original_bytes=old_record.read_bytes()
        changed=json.loads(original_bytes);changed['report']['parent_answer_delta']=999
        try:
            old_record.write_text(json.dumps(changed))
            try:call('/cow/training/learning-runs/learning-fixture/rounds/1')
            except HTTPError as error:assert error.code==400;error.close()
            else:raise AssertionError('Changed historical report accepted')
        finally:old_record.write_bytes(original_bytes)
        # A late completion from an older round cannot rewind the current run.
        run_before=service.learning._run('learning-fixture')
        first_round=service.learning._read(service.root/'learning/learning-fixture/round-000001.json')
        old_request=first_round['training_request']
        old_operation=next(p.stem for p in (service.root/'operations').glob('*.json')
            if (lambda v:v['path']=='/cow/training/learning-steps' and v['request'].get('lesson_ids')==old_request['lesson_ids'])(service._read(p)))
        service.learning._dispatch('train','learning-fixture',old_operation,old_request)
        assert service.learning._run('learning-fixture')==run_before
        value=status();assert value['last_assessment']['purpose']=='machinery' and not value['last_assessment']['requires_assessment_expansion']

        if value['working_parent_job_id'] is not None:
            value=step('preserve',name='Tiny-Learning-Working',notes='Native mechanics fixture, not a useful language model')
            assert value['preserved_export']['weights_published'] is False
        # Scores and stale revisions cannot be smuggled through the client boundary.
        for extra in [dict(scores={'passed':864}),dict(expected_revision=0)]:
            request=dict(operation_id='refused-'+str(len(extra))+str('scores' in extra),run_id='learning-fixture',
                expected_revision=status()['revision'],action='advance');request.update(extra)
            try:call('/cow/training/learning-steps',request)
            except HTTPError as error:assert error.code==400;error.close()
            else:raise AssertionError('Untrusted/stale learning transition admitted')
        before_restart=service.learning._run('learning-fixture')
        assert call('/cow/training/learning-runs',create)==ack
        assert service.learning._run('learning-fixture')==before_restart
        reopen(policies={});assert not status()['policy_available'] and status()['available_actions']==[]
        assert cli('bw',['round','learning-fixture','1'],'retired-policy-round-bw')['report']==reports[0]
        assert cli('cow',['round','learning-fixture','2'],'retired-policy-round-cow')['report']==reports[1]
        assert len(list((service.root/'runs').iterdir()))==3
        assert sha256(model)==base
        result=dict(schema=1,status='PASS',scope='Actual tiny CPU classification and three durable rounds through both actual CLIs and authenticated PCC HTTP, not language-model quality',
            policy_id=policy_id,reports=reports,native_job_ids=native_jobs,real_native_updates=48,both_actual_cli_clients=True,accepted_improvement_and_retained_parent_on_no_gain=True,
            actual_native_evaluation=True,controlled_scores_injected=False,training_and_evaluation_prefixes_disjoint=True,
            original_native_process_identities_recorded=True,reopened_between_rounds=True,duplicate_steps_not_retrained=True,
            untrusted_scores_and_stale_revision_refused=True,base_unchanged=True,
            creation_intent_recovered_on_startup_without_model_calls=faults['creation'],
            original_start_replay_did_not_reset_progress=True,retired_policy_history_remains_readable=True,
            interrupted_after_evaluation_file_recovered_without_new_model_calls=faults['baseline_commit'],
            lost_acceptance_and_before_dispatch_gap_recovered_once=faults['dispatch_gap'],
            lost_acceptance_after_native_job_submitted_did_not_train_twice=faults['after_submit'],
            machinery_assessment_does_not_expand_or_claim_model_ceiling=True,
            next_actions_discoverable_and_enforced=True,stale_dispatch_did_not_rewind_newer_phase=True,
            historical_reports_reread_through_both_clients=True,changed_historical_report_refused=True,promoted=False)
        (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('reports','native_job_ids')}));return result
    finally:server.shutdown();server.server_close();thread.join();service.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root','bw-root','executable','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.pcc_root,args.bw_root,args.executable,args.output)
