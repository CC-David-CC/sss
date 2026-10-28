"""Real PCC readers and state wire format; explicitly controlled nonmodel fixtures.

No native executable, inference, training or model-quality result is produced.
The policy's evaluator reads fixture records while real S3 analysis checks them.
"""
from pathlib import Path
import copy
import json
import tempfile
import unittest
from unittest.mock import patch
try:
    from tools.pcc_lessons import LessonService
    from tools.pcc_native_training import optimizer_dataset_sha256
    from tools.pcc_optimizer_profiles import identity, profiles
except ModuleNotFoundError:
    raise unittest.SkipTest('Optional integration: add the authorized PCC checkout to PYTHONPATH')
from sss.records import digest, file_sha256
from sss.learning import next_skill_block
from sss.paired import compare_frozen_evaluations, POLICY
from sss.assessment_growth import plan as growth_plan
from sss_integration.cow_learning_audit import audit_rounds, idle_evidence_lease


def evidence(rows, model, adapters):
    outcomes=[dict(id=str(i),skill_id='fixture.math',gate='independent',passed=p,finished=f)
              for i,(p,f) in enumerate(rows)]
    return dict(status='COMPLETE',evaluation_id='a'*64,runtime_id='b'*64,
        model_sha256=model,candidate_adapters=adapters,
        candidate_model_contract_id=digest(dict(base=model,adapters=adapters)),
        cases=len(rows),passed=sum(p for p,f in rows),finished=sum(f for p,f in rows),
        outcomes=outcomes,weights_updated=False,promoted=False)


class PolicyFixture:
    max_rounds=4
    def __init__(self,training):self.training=copy.deepcopy(training)
    def describe(self):
        return dict(schema=1,title='Controlled audit fixture; no model execution',adapter_id='4'*64,
            training=copy.deepcopy(self.training),max_rounds=self.max_rounds,
            assessment=dict(purpose='machinery',minimum_skill_cases=96))
    def verify(self):pass
    def recover_evaluation(self,candidate,path):
        return json.loads((path/'original.json').read_text())
    def validate_evaluation(self,value,candidate):
        compare_frozen_evaluations(value,value,POLICY)
    def validate_lessons(self,lessons,previous_report):
        if not lessons:raise ValueError('Expected selected fixture lessons')
    def analyze(self,baseline,parent,candidate):
        report=next_skill_block(baseline,parent,candidate)
        return dict(report=report,working_parent='parent' if report['working_decision']=='RETAIN_PARENT' else 'candidate',
            assessment=growth_plan(candidate,purpose='machinery',minimum_skill_cases=96))


class PanelReportFixture(PolicyFixture):
    """Controlled report shape only; real installed panels are tested separately."""
    def analyze(self,baseline,parent,candidate):
        decision=super().analyze(baseline,parent,candidate)
        aggregate=decision['report']
        report=dict(schema=1,kind='sss.panel-learning-report.v1',aggregate=aggregate,
            panels=[dict(panel_id='controlled-report',role='retention',
                         report=copy.deepcopy(aggregate),assessment=decision['assessment'])],
            working_parent=decision['working_parent'],promoted=False)
        report['report_id']=digest(report)
        return dict(decision,report=report)


class OriginalAuditTests(unittest.TestCase):
    def setUp(self):self.build()
    def tearDown(self):self.temp.cleanup()
    def build(self,*,mode='full',initial=False,timed=False,panels=False):
        self.temp=tempfile.TemporaryDirectory(prefix='sss-controlled-audit-');self.root=Path(self.temp.name)
        self.mode=mode;self.timed=timed;self.rank=4
        self.service=LessonService.__new__(LessonService)
        self.service.root=self.root;self.service.model='c'*64
        self.service.tokenize=lambda text:list(text.encode())
        self.service.rendered_tokenize=self.service.tokenize
        self.service.max_tokens=128;self.service.sequence_profile='dense-llama-short-v1'
        for name in ('operations','runs','lessons','learning/example'):(self.root/name).mkdir(parents=True,exist_ok=True)
        for name in ('records.lock','worker.lock'):(self.root/name).write_bytes(b'original fixture lease')
        self.directory=self.root/'learning/example'
        self.base_path=self.root/'controlled-base-nonmodel.gguf';self.base_path.write_bytes(b'not a model; audit fixture base')
        self.executable=self.root/'not-an-executable';self.executable.write_bytes(b'never execute this controlled fixture')
        self.base_sha=file_sha256(self.base_path)
        self.service.audit_base_sha256=self.base_sha;self.service.audit_model_path=self.base_path
        profile=dict(schema=1,title='Controlled native recipe; no execution',optimizer='adamw',learning_rate=.001,
            optimizer_settings=dict(schema=1,beta1=.9,beta2=.999,epsilon=1e-8,weight_decay=0.),
            state_policy='fresh',training_budget_seconds=1. if timed else None)
        if mode=='lora':profile.update(schema=2,mode='lora',rank=self.rank)
        self.profile_id=identity(profile)
        self.service.audit_optimizer_profiles=profiles({self.profile_id:profile},
            sequence_profile=self.service.sequence_profile,deadline=3600)
        self.profile=self.service.audit_optimizer_profiles[self.profile_id]
        self.policy=(PanelReportFixture if panels else PolicyFixture)(dict(mode=mode,rank=self.rank,batch_size=1,steps=3 if timed else 1,
            learning_rate=.001,optimizer_profile_id=self.profile_id))
        self.policy_id=digest(self.policy.describe())
        self.base=self.make_evidence([(True,True),(False,False),(False,False)])
        self.baseline_ref=self.evaluation('baseline',self.base)
        self.parent=self.base;self.parent_id=None;self.parent_candidate=None;self.parent_ref=self.baseline_ref
        self.initial_id=None
        if initial:
            lesson_id,example=self.lesson('initial')
            request=dict(mode=mode,rank=self.rank,batch_size=1,steps=1,learning_rate=.001,
                operation_id='initial-sgd-parent',lesson_ids=[lesson_id],parent_job_id=None)
            self.initial_candidate=self.native_job('initial-sgd-parent',request,[example],None,None)
            self.initial_id=self.parent_id='initial-sgd-parent';self.parent_candidate=self.initial_candidate
            self.parent=self.make_evidence([(True,True),(False,False),(False,False)],self.initial_candidate)
            self.parent_ref=self.evaluation('initial-parent',self.parent)
        self.creation_request=dict(operation_id='example',policy_id=self.policy_id,parent_job_id=self.initial_id,
            expected_parent_sha256=None if self.initial_id is None else self.initial_candidate['candidate_sha256'])
        creation=dict(schema=1,run_id='example',policy_id=self.policy_id,creation_request=copy.deepcopy(self.creation_request),
            phase='baseline_pending',revision=0,round=1,completed_rounds=0,
            initial_parent_job_id=self.initial_id,working_parent_job_id=self.initial_id)
        self.operation('example','/cow/training/learning-runs',self.creation_request,creation_record=creation)
        self.add_round(1,[(True,True),(True,True),(False,False)])
    def reconfigure(self,**kwargs):
        self.temp.cleanup();self.build(**kwargs)
    def save(self,path,value,checksum=False):
        if checksum:value=dict(value,record_sha256=digest(value))
        self.service._write(path,value)
    def operation(self,identity,path,request,**metadata):
        value=dict(path=path,state='complete',request=copy.deepcopy(request),
            acceptance=dict(operation_id=identity,request_sha256=digest([path,request])),**metadata)
        self.save(self.root/'operations'/(identity+'.json'),value)
    def lesson(self,tag):
        value=dict(schema=1,title='Fixture checked correction '+str(tag),model_contract_id='c'*64,
            prompt='2 + 2 = ',completion='4 .',rationale='Explicit fixture only',scope='owned-training',
            evidence=dict(method='host-verified-correction-v1',failed_result_sha256='1'*64,
                corrected_result_sha256='2'*64,verification_sha256='3'*64))
        lesson_id=digest(value);example=self.service._example(value,lesson_id)
        self.save(self.root/'lessons'/(lesson_id+'.json'),dict(lesson_id=lesson_id,lesson=value,example=example))
        return lesson_id,example
    def native_job(self,identity,request,examples,parent,profile):
        folder=self.root/'runs'/identity;folder.mkdir()
        target=folder/'candidate.gguf';target.write_bytes(('controlled nonmodel candidate '+identity).encode())
        candidate_sha=file_sha256(target)
        model=self.base_path if request['mode']=='lora' or parent is None else Path(parent['candidate_path'])
        base_sha=file_sha256(model)
        native=dict(model=str(model),base_sha256=base_sha,candidate=str(target),examples=copy.deepcopy(examples),
            **{k:request[k] for k in ('mode','rank','batch_size','steps','learning_rate')},
            backprop_mode='standard',optimizer='sgd' if profile is None else profile['optimizer'],
            sequence_profile=self.service.sequence_profile,memory_profile='allocator-v1',
            devices=['CPU'],device_budget_bytes={'CPU':1<<20},reserve_bytes=4096,deadline_seconds=3600)
        parent_sha=None
        if request['mode']=='lora' and parent is not None:
            parent_sha=parent['candidate_sha256'];native.update(initial_adapter=parent['candidate_path'],initial_adapter_sha256=parent_sha)
        state_path=folder/'optimizer-state.bin'
        if profile is not None:
            native.update(optimizer_settings=copy.deepcopy(profile['optimizer_settings']),optimizer_state_mode='fresh',
                optimizer_state_output=str(state_path))
            if profile['training_budget_seconds'] is not None:native['training_budget_seconds']=profile['training_budget_seconds']
        native_path=folder/'request-private.json';native_path.write_text(json.dumps(native,sort_keys=True,indent=2)+'\n')
        launch=dict(executable=str(self.executable),executable_sha256=file_sha256(self.executable),
            request_sha256=file_sha256(native_path),base_sha256=base_sha,parent_adapter_sha256=parent_sha,pid=999999999)
        self.save(folder/'launch.json',launch);(folder/'command.exit').write_text('0\n')
        completed=1 if self.timed and profile is not None else request['steps'];cursor=0;steps=[]
        for n in range(completed):
            count=min(request['batch_size'],len(examples)-cursor%len(examples));cursor+=count
            row=dict(step=n,examples=count,example_cursor=cursor,gradients=[dict(l2=1.)],before=1.,after=.5)
            if self.timed and profile is not None:
                row['timing']=dict(seconds=1.2,gradient_and_coverage_seconds=.5,optimizer_seconds=.3,post_update_evaluation_seconds=.4)
            steps.append(row)
        receipt=dict(native=True,backprop_mode='standard',mode=request['mode'],optimizer=native['optimizer'],steps=steps,example_cursor=cursor)
        candidate=dict(schema=1,mode=request['mode'],base_sha256=base_sha,candidate_path=str(target),
            candidate_sha256=candidate_sha,promoted=False)
        if profile is not None:
            dataset=optimizer_dataset_sha256(examples)
            config=dict(optimizer=profile['optimizer'],settings=profile['optimizer_settings'],learning_rate=request['learning_rate'])
            header=dict(schema=1,kind='pcc.completed-optimizer-state.v1',storage='le-f32',
                model_sha256=candidate_sha,dataset_sha256=dataset,example_cursor=cursor,completed_steps=completed,
                config=config,tensors=[])
            raw=json.dumps(header,sort_keys=True).encode()
            state_path.write_bytes(b'PCCOPT1\n'+len(raw).to_bytes(8,'little')+raw)
            state_sha=file_sha256(state_path)
            receipt['optimizer_checkpoint']=dict(path=str(state_path),sha256=state_sha,candidate_sha256=candidate_sha,
                dataset_sha256=dataset,example_cursor=cursor,completed_steps=completed,config=config)
            candidate.update(optimizer_state_path=str(state_path),optimizer_state_sha256=state_sha,
                optimizer_completed_steps=completed,optimizer_profile_id=request['optimizer_profile_id'],optimizer_state_policy='fresh')
            if self.timed:
                receipt['training_budget']=dict(schema=1,boundary='whole_update',clock='steady_training_phase',
                    requested_seconds=profile['training_budget_seconds'],step_cap=request['steps'],completed_updates=completed,
                    elapsed_seconds=1.2,overrun_seconds=.2,remaining_seconds=0.,stop_reason='training_budget')
        self.save(folder/'stdout-private.json',receipt)
        receipt.update(request_sha256=launch['request_sha256'],parent_adapter_sha256=parent_sha)
        candidate['receipt']=receipt
        self.operation(identity,'/cow/training/jobs',request,candidate=candidate)
        return candidate
    def make_evidence(self,rows,candidate=None):
        if self.mode=='lora':
            model=self.base_sha;adapters=[] if candidate is None else [dict(sha256=candidate['candidate_sha256'],scale=1.)]
        else:
            model=self.base_sha if candidate is None else candidate['candidate_sha256'];adapters=[]
        return evidence(rows,model,adapters)
    def evaluation(self,name,value):
        self.save(self.directory/(name+'-evaluation.json'),value)
        backend=self.directory/(name+'-backend');backend.mkdir()
        self.save(backend/'original.json',value)
        return dict(file=name+'-evaluation.json',sha256=digest(value))
    def job_id(self,n):return 'learning-job-'+digest(dict(run='example',round=n,policy=self.policy_id))
    def add_round(self,n,rows):
        identity=self.job_id(n);lesson_id,example=self.lesson(n)
        request=dict(self.policy.describe()['training'],operation_id=identity,parent_job_id=self.parent_id,lesson_ids=[lesson_id])
        if self.parent_candidate is not None:request['expected_parent_sha256']=self.parent_candidate['candidate_sha256']
        candidate=self.native_job(identity,request,[example],self.parent_candidate,self.profile)
        value=self.make_evidence(rows,candidate);ref=self.evaluation('candidate-%06d'%n,value)
        decision=self.policy.analyze(self.base,self.parent,value);report=decision['report']
        next_id=identity if decision['working_parent']=='candidate' else self.parent_id
        record=dict(round=n,status='complete',parent_job_id=self.parent_id,candidate_job_id=identity,
            lesson_ids=[lesson_id],training_request=request,candidate_evaluation=ref,report=report,
            report_sha256=digest(report),working_parent_job_id=next_id,assessment=decision['assessment'])
        self.save(self.directory/('report-%06d.json'%n),report)
        self.save(self.directory/('round-%06d.json'%n),record,checksum=True)
        if decision['working_parent']=='candidate':self.parent,self.parent_candidate,self.parent_ref=value,candidate,ref
        self.parent_id=next_id
        self.run=dict(schema=1,run_id='example',policy_id=self.policy_id,creation_request=copy.deepcopy(self.creation_request),
            phase='round_complete',revision=10*n,round=n,completed_rounds=n,initial_parent_job_id=self.initial_id,
            working_parent_job_id=self.parent_id,baseline_evaluation=self.baseline_ref,parent_evaluation=self.parent_ref,
            candidate_evaluation=ref,last_report=report,last_assessment=decision['assessment'])
        self.save_run()
    def save_run(self):self.save(self.directory/'run.json',self.run,checksum=True)
    def load_job(self,n=1):return json.loads((self.root/'operations'/(self.job_id(n)+'.json')).read_text())
    def save_job(self,value,n=1):self.save(self.root/'operations'/(self.job_id(n)+'.json'),value)
    def mutate_round(self,n,change):
        path=self.directory/('round-%06d.json'%n);value=json.loads(path.read_text());value.pop('record_sha256')
        change(value);self.save(path,value,checksum=True)
    def resign_native(self,n=1):
        value=self.load_job(n);folder=Path(value['candidate']['candidate_path']).parent;launch=json.loads((folder/'launch.json').read_text())
        launch['request_sha256']=file_sha256(folder/'request-private.json');self.save(folder/'launch.json',launch)
        value['candidate']['receipt']['request_sha256']=launch['request_sha256'];self.save_job(value,n)
    def stop_before_next_round(self):
        self.run.update(phase='stopped',round=self.run['completed_rounds']+1)
        for key in ('training_job_id','training_request','candidate_evaluation','pending_step_id'):self.run.pop(key,None)
        self.save_run()
    def audit(self):
        with idle_evidence_lease(self.service):return audit_rounds(self.service,self.policy,'example')
    def test_original_completed_round_audits_without_dispatch(self):
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch('subprocess.Popen',side_effect=AssertionError('Audit attempted dispatch')):result=self.audit()
        self.assertEqual(result['status'],'AUDITED_ORIGINAL_EVIDENCE');self.assertEqual(result['rounds'][0]['passed'],2)
        self.assertEqual(result['native_jobs_started'],0)
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_second_round_without_gain_retains_original_parent(self):
        self.add_round(2,[(True,True),(True,True),(False,False)])
        value=self.audit();self.assertEqual(value['distinct_referenced_native_jobs'],2)
        self.assertEqual(value['rounds'][-1]['working_decision'],'RETAIN_PARENT')
    def test_wrapped_reports_audit_multiple_rounds_without_dispatch_or_source_changes(self):
        self.reconfigure(panels=True)
        self.add_round(2,[(True,True),(False,True),(False,False)])
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch('subprocess.Popen',side_effect=AssertionError('Audit attempted dispatch')):
            value=self.audit()
        self.assertEqual(value['distinct_referenced_native_jobs'],2)
        self.assertEqual(value['rounds'][1]['working_decision'],'RETAIN_PARENT')
        self.assertEqual(value['rounds'][1]['parent_answer_delta'],-1)
        self.assertEqual(value['rounds'][1]['panels'][0]['parent_answer_delta'],-1)
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_wrapped_panel_analysis_is_recomputed_in_full(self):
        self.reconfigure(panels=True)
        path=self.directory/'round-000001.json';record=json.loads(path.read_text());record.pop('record_sha256')
        record['report']['panels'][0]['report']['parent_answer_delta']=99
        record['report_sha256']=digest(record['report'])
        self.save(self.directory/'report-000001.json',record['report']);self.save(path,record,checksum=True)
        with self.assertRaisesRegex(ValueError,'Recomputed learning'):self.audit()
    def test_wrapped_report_cannot_replace_missing_original_backend(self):
        self.reconfigure(panels=True)
        (self.directory/'candidate-000001-backend/original.json').unlink()
        with self.assertRaises(FileNotFoundError):self.audit()
    def test_initial_sgd_parent_without_optimizer_state_is_supported(self):
        for mode in ('full','lora'):
            self.reconfigure(mode=mode,initial=True)
            self.assertNotIn('optimizer_state_path',self.initial_candidate)
            with self.subTest(mode=mode):
                value=self.audit();self.assertEqual(value['original_backend_case_records_revalidated'],9)
    def test_declared_legacy_timed_recipe_uses_completed_count_not_step_cap(self):
        self.reconfigure(timed=True);value=self.audit()
        self.assertEqual(self.policy.training['steps'],3);self.assertEqual(value['rounds'][0]['native_updates'],1)
    def test_changed_lesson_training_tokens_rejected(self):
        path=next((self.root/'lessons').glob('*.json'));value=json.loads(path.read_text());value['example']['tokens'][0]+=1;self.save(path,value)
        with self.assertRaisesRegex(ValueError,'training tokens'):self.audit()
    def test_changed_candidate_or_state_rejected(self):
        for name in ('candidate.gguf','optimizer-state.bin'):
            path=self.root/'runs'/self.job_id(1)/name;original=path.read_bytes();path.write_bytes(b'changed')
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'bytes differ'):self.audit()
            path.write_bytes(original)
    def test_forged_analysis_rejected_even_with_updated_record_checksum(self):
        path=self.directory/'round-000001.json';record=json.loads(path.read_text());record.pop('record_sha256')
        record['report']['baseline_answer_delta']=99;record['report_sha256']=digest(record['report'])
        self.save(self.directory/'report-000001.json',record['report']);self.save(path,record,checksum=True)
        with self.assertRaisesRegex(ValueError,'Recomputed learning'):self.audit()
    def test_stale_or_wrong_future_parent_reference_rejected(self):
        self.run['parent_evaluation']=self.baseline_ref;self.save_run()
        with self.assertRaisesRegex(ValueError,'selected another parent'):self.audit()
    def test_stale_future_assessment_proposal_rejected(self):
        self.run['last_assessment']=dict(self.run['last_assessment'],plan_id='0'*64);self.save_run()
        with self.assertRaisesRegex(ValueError,'selected another parent'):self.audit()
    def test_in_progress_round_is_not_a_complete_audit(self):
        self.run['phase']='candidate_running';self.save_run()
        with self.assertRaisesRegex(ValueError,'completed round boundary'):self.audit()
    def test_changed_operation_request_binding_is_rejected(self):
        path=self.root/'operations'/(self.job_id(1)+'.json');value=json.loads(path.read_text());value['request']['steps']=2;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'original request binding'):self.audit()
    def test_wrong_derived_round_identity_rejected(self):
        self.mutate_round(1,lambda value:value.update(candidate_job_id='unrelated-native-job'))
        with self.assertRaisesRegex(ValueError,'derived round identity'):self.audit()
    def test_wrong_candidate_mode_and_profile_are_rejected(self):
        original=self.load_job()
        for key,value in (('mode','lora'),('optimizer_profile_id','e'*64)):
            changed=copy.deepcopy(original);changed['candidate'][key]=value;self.save_job(changed)
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'native dispatch'):self.audit()
        self.save_job(original)
    def test_wrong_optimizer_dataset_is_rejected(self):
        value=self.load_job();value['candidate']['receipt']['optimizer_checkpoint']['dataset_sha256']='e'*64;self.save_job(value)
        # Update original stdout too, so this reaches dataset/header binding.
        folder=Path(value['candidate']['candidate_path']).parent;raw=copy.deepcopy(value['candidate']['receipt'])
        for key in ('request_sha256','parent_adapter_sha256'):raw.pop(key)
        self.save(folder/'stdout-private.json',raw)
        with self.assertRaisesRegex(ValueError,'optimizer state'):self.audit()
    def test_original_stdout_receipt_cannot_be_replaced(self):
        folder=self.root/'runs'/self.job_id(1);value=json.loads((folder/'stdout-private.json').read_text());value['native']=False;self.save(folder/'stdout-private.json',value)
        with self.assertRaises(ValueError):self.audit()
    def test_changed_native_request_requires_original_launch_hash(self):
        folder=self.root/'runs'/self.job_id(1);path=folder/'request-private.json';value=json.loads(path.read_text());value['learning_rate']=.002;self.save(path,value)
        with self.assertRaisesRegex(ValueError,'native dispatch'):self.audit()
    def test_wrong_native_output_path_rejected_even_with_rebound_request_hash(self):
        folder=self.root/'runs'/self.job_id(1);path=folder/'request-private.json';value=json.loads(path.read_text())
        wrong=folder/'wrong-output.gguf';wrong.write_bytes((folder/'candidate.gguf').read_bytes())
        value['candidate']=str(wrong);self.save(path,value);self.resign_native()
        with self.assertRaises(ValueError):self.audit()
    def test_creation_request_cannot_be_replaced(self):
        self.run['creation_request']=dict(self.creation_request,expected_parent_sha256='e'*64);self.save_run()
        with self.assertRaisesRegex(ValueError,'creation approval'):self.audit()
    def test_initial_parent_requires_its_approved_sha(self):
        self.reconfigure(initial=True)
        path=self.root/'operations/example.json';operation=json.loads(path.read_text());operation['request']['expected_parent_sha256']=None
        operation['acceptance']['request_sha256']=digest([operation['path'],operation['request']]);self.save(path,operation)
        self.run['creation_request']=copy.deepcopy(operation['request']);self.save_run()
        with self.assertRaisesRegex(ValueError,'Initial parent'):self.audit()
    def test_initial_lora_parent_rank_must_match(self):
        self.reconfigure(mode='lora',initial=True)
        path=self.root/'operations/initial-sgd-parent.json';operation=json.loads(path.read_text());operation['request']['rank']=8
        operation['acceptance']['request_sha256']=digest([operation['path'],operation['request']]);self.save(path,operation)
        with self.assertRaisesRegex(ValueError,'Initial parent'):self.audit()
    def test_initial_parent_mode_must_match(self):
        self.reconfigure(initial=True)
        path=self.root/'operations/initial-sgd-parent.json';operation=json.loads(path.read_text());operation['candidate']['mode']='lora';self.save(path,operation)
        with self.assertRaisesRegex(ValueError,'Initial parent'):self.audit()
    def test_safe_stopped_untrained_next_round_preserves_completed_prefix(self):
        self.stop_before_next_round();value=self.audit()
        self.assertEqual(len(value['rounds']),1);self.assertEqual(value['rounds'][0]['passed'],2)
    def test_stopped_tail_with_started_or_ambiguous_round_is_rejected(self):
        self.stop_before_next_round();original=copy.deepcopy(self.run)
        for key,value in [('training_job_id',self.job_id(2)),('training_request',{}),
                          ('candidate_evaluation',self.baseline_ref),('pending_step_id','pending-step')]:
            self.run=copy.deepcopy(original);self.run[key]=value;self.save_run()
            with self.subTest(field=key),self.assertRaises(ValueError):self.audit()
    def test_stopped_tail_with_next_round_artifacts_is_rejected(self):
        self.stop_before_next_round()
        choices=[self.directory/'round-000002.json',self.root/'runs'/self.job_id(2),self.root/'operations'/(self.job_id(2)+'.json')]
        for target in choices:
            if target.parent.name=='runs':target.mkdir()
            elif target.parent.name=='operations':self.operation(self.job_id(2),'/cow/training/jobs',dict(operation_id=self.job_id(2)))
            else:target.write_text('{}')
            with self.subTest(name=target.name),self.assertRaises(ValueError):self.audit()
            if target.is_dir():target.rmdir()
            else:target.unlink()


if __name__=='__main__':unittest.main()
