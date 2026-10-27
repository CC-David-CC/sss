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

    def independent_review(self):
        """Controlled factory inputs, not a real model or renderer proof."""
        anchor=self.panels['retention']
        anchor.tokenizer_id='tokenizer';anchor.checker='checker'
        anchor.data=dict(renderer_sha256='renderer')
        anchor.pack=dict(exercises=[dict(split='development',prompt='protected development'),
            dict(split='qualification',prompt='protected qualification')])
        fresh=ControlledFoundation('fresh-practice',self.model)
        fresh.tokenizer_id=anchor.tokenizer_id;fresh.checker=anchor.checker
        fresh.data=copy.deepcopy(anchor.data)
        fresh.pack=dict(exercises=[dict(split='practice',prompt='fresh independent practice')])
        value=lesson('fresh independent practice')
        fresh.allowed_lessons={digest(value):value}
        self.write(self.root/'fresh.json',dict(controlled_fresh=True))
        self.config['practice'][1]=dict(provider_id='mixed-review',role='review',
            kind='foundation-practice-pack',panel_id='retention',configuration=str(self.root/'fresh.json'))
        self.save()
        return anchor,fresh

    def install_independent(self,fresh):
        with patch('sss.adapters.cow_learning.CowLearningEvaluator',side_effect=lambda config,*args:
                fresh if config.get('controlled_fresh') else self.panels['retention']):
            return self.policy()

    def test_fresh_practice_does_not_replace_protected_assessment_panel(self):
        anchor,fresh=self.independent_review();policy=self.install_independent(fresh)
        self.assertIs(policy.evaluator._panels[-1][2],anchor)
        self.assertEqual(len(policy.evaluator._panels),3)
        values=policy.evaluator.lessons()
        self.assertIn(next(iter(fresh.allowed_lessons.values())),values)
        self.assertNotIn(next(iter(anchor.allowed_lessons.values())),values)
        policy.validate_lessons(self.records(policy),None)
        self.assertIn(str(self.root/'fresh.json'),policy.evaluator.binding()['sources_sha256'])

    def test_independent_review_cannot_use_protected_development_or_qualification_prompt(self):
        anchor,fresh=self.independent_review()
        for row in anchor.pack['exercises']:
            fresh.pack['exercises'][0]['prompt']=row['prompt']
            with self.subTest(split=row['split']),self.assertRaisesRegex(ValueError,'overlaps protected'):
                self.install_independent(fresh)

    def test_independent_review_rechecks_model_tokenizer_checker_and_renderer(self):
        for field in ('base','model','model_contract','tokenizer_id','checker','renderer'):
            anchor,fresh=self.independent_review();policy=self.install_independent(fresh)
            if field=='renderer':fresh.data['renderer_sha256']='changed'
            elif field=='model':fresh.model=self.root/'different-model'
            else:setattr(fresh,field,'changed')
            with self.subTest(field=field),self.assertRaises(ValueError):policy.verify()

    def test_independent_review_keeps_anchor_and_configuration_immutable(self):
        anchor,fresh=self.independent_review();policy=self.install_independent(fresh)
        anchor.source_version+=1
        with self.assertRaisesRegex(ValueError,'binding changed|anchor changed'):policy.verify()
        anchor.source_version-=1;policy=self.install_independent(fresh)
        self.write(self.root/'fresh.json',dict(controlled_fresh=True,changed=True))
        with self.assertRaises(ValueError):policy.verify()

    def test_independent_review_requires_owner_path_review_role_and_foundation_anchor(self):
        for defect in ('path','role','anchor','extra'):
            anchor,fresh=self.independent_review();row=self.config['practice'][1]
            if defect=='path':row['configuration']='relative.json'
            elif defect=='role':row['role']='target'
            elif defect=='anchor':row['panel_id']='target'
            else:row['module']='untrusted.module'
            self.save()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.install_independent(fresh)


if __name__=='__main__':unittest.main()
