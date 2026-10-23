"""Real lesson-store/controller boundaries with explicitly controlled evaluations."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from tools.pcc_lessons import LessonService,digest
from sss import SkillTree,SkillGuardRunner
from sss.suites.arithmetic import generated

def case(prompt):return dict(id=hashlib.sha256(prompt.encode()).hexdigest(),prompt=prompt,kind='ceil',parameters=['a','b'])

class Skills(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.calls=[];self.evaluations=[]
        self.service=LessonService(self.root/'store','a'*64,lambda x:list(x.encode()),self.native,max_tokens=256,max_steps=32)
        nodes=[dict(id='math',title='Math',parent=None,minimum_accuracy=.9,practice_lesson_ids=[],validation=[],blind=[])]
        for skill in ['math.ceil','math.floor','math.abs']:
            ids=[]
            for index in range(10):
                lesson=dict(schema=1,title='Owned '+skill,model_contract_id='a'*64,prompt=skill+str(index)+':',completion=' 1',
                    skill_id=skill,rationale='Controlled test record, not observed model behavior',scope='owned-training',evidence=dict(
                    method='host-verified-replay-v1',failed_result_sha256='b'*64,corrected_result_sha256='c'*64,verification_sha256='d'*64))
                ids.append(self.service.submit('/cow/training/lessons',dict(operation_id='p-'+skill.replace('.','-')+str(index),lesson=lesson))['lesson_id'])
            nodes.append(dict(id=skill,title=skill,parent='math',minimum_accuracy=.9,practice_lesson_ids=ids,
                validation=[case(skill+' check '+str(i)) for i in range(3)],blind=[case(skill+' blind '+str(i)) for i in range(2)]))
        self.tree=SkillTree(dict(schema=1,model_contract_id='a'*64,nodes=nodes));self.count=0
        self.behavior='repair'
        self.guard=SkillGuardRunner(self.native,self.tree,self.evaluate,round_examples=12,max_rounds=3)
        self.service.close();self.service=LessonService(self.root/'store','a'*64,lambda x:list(x.encode()),self.guard,max_tokens=256,max_steps=32)
    def tearDown(self):self.service.close();self.temp.cleanup()
    def native(self,request,examples,path,parent,fd):
        self.count=getattr(self,'count',0)+1;self.calls.append(dict(request=request,parent=parent,examples=examples))
        return dict(mode=request['mode'],candidate_sha256=digest(dict(run=self.count)),candidate_path=str(path/'candidate.gguf'),
                    receipt=dict(steps=[],example_cursor=len(examples)))
    def records(self,split,failed=()):
        return [dict(id=v['id'],passed=self.tree.case_skill[v['id']] not in failed) for v in self.tree.rows(split)]
    def evaluate(self,candidate,split,path,fd):
        self.evaluations.append((split,path.name))
        if self.behavior=='infrastructure':raise OSError('Controlled evaluator unavailable')
        if path.name=='baseline':return self.records(split,['math.ceil'])
        if split=='blind':return self.records(split,['math.floor'] if self.behavior=='blind_failure' and path.name=='blind-candidate' else [])
        if self.behavior=='never_repair' or path.name=='check-0':return self.records(split,['math.floor'])
        return self.records(split)
    def request(self,op='guarded'):
        return dict(operation_id=op,lesson_ids=[self.tree.leaves['math.ceil']['practice_lesson_ids'][0]],
            mode='lora',rank=4,batch_size=4,steps=9,learning_rate=.001,parent_job_id=None,skill_guard=dict(policy_id=self.guard.policy_id))
    def wait(self,op):
        for _ in range(500):
            value=self.service.job(op)
            if value['state'] not in ('queued','running'):return value
            time.sleep(.01)
        self.fail('Controlled job did not settle')
    def test_tree_rejects_cycles_unknown_leaves_and_test_labels(self):
        for change in ['cycle','uncovered','label']:
            d=copy.deepcopy(self.tree.document)
            if change=='cycle':d['nodes'][0]['parent']='math.ceil'
            if change=='uncovered':d['nodes'][1]['blind']=[]
            if change=='label':d['nodes'][1]['validation'][0]['completion']='hidden answer'
            with self.assertRaises(ValueError,msg=change):SkillTree(d)
    def test_case_regression_is_detected_even_if_skill_accuracy_is_unchanged(self):
        baseline=self.records('validation');ids=[v['id'] for v in self.tree.leaves['math.ceil']['validation']]
        baseline=copy.deepcopy(baseline);next(v for v in baseline if v['id']==ids[2])['passed']=False
        before=self.tree.assess(baseline,'validation')
        after=copy.deepcopy(baseline);next(v for v in after if v['id']==ids[2])['passed']=True;next(v for v in after if v['id']==ids[0])['passed']=False
        verdict=self.tree.assess(after,'validation',before['passed_ids'])
        self.assertEqual(verdict['scores']['math.ceil']['passed'],2);self.assertEqual(verdict['regressed_ids'],[ids[0]])
    def test_missing_check_cannot_count_as_pass(self):
        with self.assertRaises(ValueError):self.tree.assess(self.records('validation')[:-1],'validation')
    def test_mixed_round_repair_and_original_operation_reconciliation(self):
        request=self.request();accept=self.service.submit('/cow/training/jobs',request);job=self.wait('guarded')
        self.assertEqual(job['state'],'complete');report=job['skill_guard'];self.assertTrue(report['qualified'])
        self.assertFalse(job['promoted']);self.assertEqual(len(self.calls),2)
        self.assertEqual(report['rounds'][1]['focus_skills'],['math.floor'])
        for row in report['rounds']:self.assertEqual(set(row['distribution']),set(self.tree.leaves))
        self.assertGreater(report['rounds'][1]['distribution']['math.floor'],report['rounds'][1]['distribution']['math.ceil'])
        self.assertEqual(self.calls[1]['parent']['candidate_sha256'],report['rounds'][0]['candidate_sha256'])
        self.assertEqual(self.service.submit('/cow/training/jobs',request),accept);self.assertEqual(len(self.calls),2)
        self.assertNotIn('protected_pass_ids',report)
    def test_repair_stops_at_budget_without_opening_blind_set(self):
        self.behavior='never_repair';request=self.request();request['steps']=3
        self.service.submit('/cow/training/jobs',request);report=self.wait('guarded')['skill_guard']
        self.assertFalse(report['qualified']);self.assertEqual(report['state'],'round_budget_exhausted')
        self.assertEqual(len(self.calls),1);self.assertFalse(any(split=='blind' for split,_ in self.evaluations))
    def test_blind_failure_rejects_hat_without_training_on_that_failure(self):
        self.behavior='blind_failure';self.service.submit('/cow/training/jobs',self.request())
        report=self.wait('guarded')['skill_guard'];self.assertEqual(report['state'],'blind_failed');self.assertFalse(report['qualified'])
        self.assertEqual(len(self.calls),2)
    def test_wrong_policy_and_too_small_step_budget_reject_before_work(self):
        for override in [dict(skill_guard=dict(policy_id='f'*64)),dict(steps=1)]:
            with self.assertRaises(ValueError):self.service.submit('/cow/training/jobs',dict(self.request(),**override))
        self.assertFalse(self.calls);self.assertFalse(self.evaluations)
    def test_test_prompt_is_not_recycled_as_a_practice_lesson(self):
        lesson=copy.deepcopy(self.service.lesson(self.request()['lesson_ids'][0])['lesson'])
        lesson['prompt']=self.tree.leaves['math.ceil']['validation'][0]['prompt']
        identity=self.service.submit('/cow/training/lessons',dict(operation_id='leaked',lesson=lesson))['lesson_id']
        request=dict(self.request(),lesson_ids=[identity]);self.service.submit('/cow/training/jobs',request)
        self.assertEqual(self.wait('guarded')['state'],'failed');self.assertFalse(self.calls);self.assertFalse(self.evaluations)
    def test_infrastructure_failure_is_not_used_as_a_model_training_failure(self):
        self.behavior='infrastructure';self.service.submit('/cow/training/jobs',self.request())
        self.assertEqual(self.wait('guarded')['state'],'failed');self.assertFalse(self.calls)
    def test_ordinary_training_still_uses_exactly_the_original_request(self):
        request=self.request();request.pop('skill_guard');self.service.submit('/cow/training/jobs',request)
        self.assertEqual(self.wait('guarded')['state'],'complete');self.assertEqual(len(self.calls),1);self.assertFalse(self.evaluations)
        self.assertEqual(self.calls[0]['request'],request)
    def test_generated_practice_and_check_families_are_disjoint_and_semantic(self):
        prompts=set()
        for kind in ['add','multiply','abs','floor','ceil']:
            for split in ['practice','validation','blind']:
                for row,_ in generated(kind,split,16):
                    self.assertNotIn(row['prompt'],prompts);prompts.add(row['prompt'])
    def test_unqualified_parent_cannot_become_an_ongoing_hat(self):
        self.behavior='never_repair';self.service.submit('/cow/training/jobs',self.request());self.wait('guarded');count=len(self.calls)
        self.service.submit('/cow/training/jobs',dict(self.request('next'),parent_job_id='guarded'))
        self.assertEqual(self.wait('next')['state'],'failed');self.assertEqual(len(self.calls),count)

if __name__=='__main__':unittest.main()
