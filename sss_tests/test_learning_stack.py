"""Owner factory/mix controls with explicitly controlled panels, no model or approval."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch

from sss.adapters.learning_stack import configured_learning_stack
from sss.adapters.cow_learning import configured_policies
from sss.records import digest
from sss_tests.test_learning_panels import ControlledPanel,ControlledProvider,lesson,MODEL,candidate


class ControlledFoundation(ControlledPanel):
    def __init__(self,name,model):
        super().__init__(name,before=[(True,True)],after=[(False,True)])
        self.base='b'*64;self.model=model;self.model_contract=MODEL
        value=lesson('controlled reviewed arithmetic')
        self.allowed_lessons={digest(value):value}

    def validate_lessons(self,records,previous_report):
        for row in records:
            if self.allowed_lessons.get(row['lesson_id'])!=row['lesson']:
                raise ValueError('Not installed controlled review')


class ControlledApproved(ControlledProvider):
    def __init__(self):super().__init__('controlled verified-code fixture');self.protected=False

    def binding(self):
        value=super().binding()
        value['registrations']=[dict(owner=dict(baseline_source_sha256=hashlib.sha256(
            b'protected'if self.protected else b'different owned practice').hexdigest()))]
        return value


@unittest.skipUnless(os.name=='posix','Private owner descriptor boundary')
class LearningStackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'stack.json'
        self.model=self.root/'controlled-model';self.model.write_bytes(b'not a real model')
        self.native=SimpleNamespace(config=dict(model=str(self.model),base_sha256='b'*64))
        self.profile=dict(model_path=str(self.model),model_weights_sha256='b'*64,model_contract_id=MODEL)
        self.approved=ControlledApproved();self.panels={}
        for role in ('target','workflow'):
            panel=ControlledPanel(role);panel.base='b'*64;panel.model=self.model;panel.model_contract=MODEL
            panel.cases=[SimpleNamespace(baseline_source=b'protected')];self.panels[role]=panel
        self.panels['retention']=ControlledFoundation('retention',self.model)
        self.config=dict(schema=1,kind='sss.learning-stack.v1',
            panels=[dict(panel_id=role,role=role,kind=kind,configuration=str(self.root/(role+'.json')))
                for role,kind in [('target','cow-artifact'),('workflow','bw-workflow'),('retention','cow-foundations')]],
            practice=[dict(provider_id='verified-code',role='target',kind='bw-verified',configuration=str(self.root/'approved.json')),
                dict(provider_id='mixed-review',role='review',kind='foundation-practice',panel_id='retention')],
            practice_mix=dict(minimum_target_lessons=1,minimum_review_lessons=1),
            policies=[dict(title='Controlled factory fixture; not real learning',
                training=dict(mode='full',steps=1,batch_size=2,learning_rate=1e-6,rank=16),
                max_rounds=2,assessment_purpose='machinery',minimum_skill_cases=3)])
        for name in ('target','workflow','retention','approved'):self.write(self.root/(name+'.json'),{})
        self.save()
        serve=ModuleType('serve');http=ModuleType('serve.cow_http');http.model_text_components=lambda *a,**k:{}
        fixtures=[patch.dict('sys.modules',{'serve':serve,'serve.cow_http':http}),
            patch('sss.adapters.artifact_evaluation.CowArtifactEvaluator',side_effect=lambda _:self.panels['target']),
            patch('sss.adapters.workflow_evaluation.BWWorkflowEvaluator',side_effect=lambda _:self.panels['workflow']),
            patch('sss.adapters.cow_learning.CowLearningEvaluator',side_effect=lambda *a:self.panels['retention']),
            patch('sss.adapters.verified_practice_registry.InstalledBWPractice',side_effect=lambda *a,**k:self.approved),
            patch('subprocess.Popen',side_effect=AssertionError('No native/process dispatch in controlled factory tests'))]
        for fixture in fixtures:fixture.start();self.addCleanup(fixture.stop)

    def write(self,path,value):path.write_text(json.dumps(value));path.chmod(0o600)
    def save(self):self.write(self.path,self.config)
    def install(self):return configured_learning_stack(self.path,self.native,self.profile,object())
    def policy(self):return next(iter(self.install().values()))
    def records(self,policy):return [dict(lesson_id=digest(v),lesson=v)for v in policy.evaluator.lessons()]

    def test_existing_pcc_factory_entry_installs_all_roles_and_exact_mix(self):
        policies=configured_policies(self.path,self.native,self.profile,object())
        self.assertEqual(len(policies),1);identity,policy=next(iter(policies.items()))
        self.assertEqual(identity,digest(policy.describe()))
        self.assertEqual({r['role']for r in policy.evaluator.binding()['panels']},{'target','workflow','retention'})
        policy.validate_lessons(self.records(policy),None)

    def test_target_only_and_review_only_selections_cannot_omit_mixed_review(self):
        policy=self.policy();records=self.records(policy)
        for row in records:
            with self.subTest(lesson=row['lesson_id']),self.assertRaisesRegex(ValueError,'target/review mix'):
                policy.validate_lessons([row],None)

    def test_review_cannot_be_approved_but_outside_first_native_batch(self):
        self.approved.values.append(lesson('another controlled code fixture'))
        policy=self.policy()
        with self.assertRaisesRegex(ValueError,'native training batch'):
            policy.validate_lessons(self.records(policy),None)

    def test_unknown_adapters_roles_and_missing_measurements_are_refused(self):
        original=copy.deepcopy(self.config)
        for defect in ('module','role','missing'):
            self.config=copy.deepcopy(original)
            if defect=='module':self.config['panels'][0]['kind']='user.arbitrary.module'
            elif defect=='role':self.config['panels'][1]['role']='target'
            else:self.config['panels'].pop()
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.install()

    def test_infeasible_mix_and_fixed_comparison_purpose_are_refused(self):
        original=copy.deepcopy(self.config)
        for defect in ('batch','purpose','mix'):
            self.config=copy.deepcopy(original)
            if defect=='batch':self.config['policies'][0]['training']['batch_size']=1
            elif defect=='purpose':self.config['policies'][0]['assessment_purpose']='fixed_comparison'
            else:self.config['practice_mix']['minimum_review_lessons']=True
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.install()

    def test_duplicate_policy_identity_and_duplicate_provider_names_are_refused(self):
        self.config['policies']*=2;self.save()
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.install()
        self.config['policies']=self.config['policies'][:1]
        self.config['practice'][1]['provider_id']='verified-code';self.save()
        with self.assertRaisesRegex(ValueError,'Unique'):self.install()

    def test_exact_protected_visible_source_cannot_become_practice(self):
        self.approved.protected=True
        with self.assertRaisesRegex(ValueError,'Protected assessment source'):self.install()

    def test_panel_and_training_bases_must_match(self):
        self.panels['workflow'].base='c'*64
        with self.assertRaisesRegex(ValueError,'exact training base'):self.install()
        self.panels['workflow'].base='b'*64;self.profile['model_weights_sha256']='c'*64
        with self.assertRaisesRegex(ValueError,'immutable base'):self.install()

    def test_owner_top_level_and_nested_bytes_are_rechecked(self):
        policy=self.policy();self.path.write_text(self.path.read_text()+' ')
        with self.assertRaises(ValueError):policy.verify()
        self.save();policy=self.policy();self.write(self.root/'retention.json',dict(changed=True))
        with self.assertRaises(ValueError):policy.verify()

    def test_private_metadata_and_symlink_changes_are_refused(self):
        policy=self.policy();self.path.chmod(0o644)
        with self.assertRaises(ValueError):policy.verify()
        self.path.chmod(0o600);other=self.root/'same-bytes';self.path.rename(other);self.path.symlink_to(other)
        with self.assertRaises(ValueError):self.install()

    def test_duplicate_owner_fields_do_not_select_a_different_registry(self):
        self.path.write_text('{"schema":1,"kind":"sss.learning-stack.v1","kind":"other"}')
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.install()

    def test_installation_file_identity_is_bound_and_rechecked(self):
        policy=self.policy();bound=policy.evaluator.binding()
        self.assertIn(str(self.path),bound['sources_sha256'])
        self.assertIn(str(self.root/'approved.json'),bound['sources_sha256'])
        self.assertFalse(policy.describe().get('promoted',False))


if __name__=='__main__':unittest.main()
