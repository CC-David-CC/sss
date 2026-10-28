"""Actual BW export/registry/PCC service with controlled measurement panels.

This is a machinery integration, not model inference, native training, or a
quality result. MiniCPM supplies its actual template/tokenizer. BW executes real
tools against an owned task; a scripted backend supplies the proposals. The
three scoring panels deliberately use controlled outcomes to test composition.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

try:
    from tools.pcc_lessons import LessonService, NativeRunner
    from tools.pcc_optimizer_profiles import identity
    from serve.cow_http import model_text_components
    import branchwrite
except ModuleNotFoundError:
    raise unittest.SkipTest('Optional integration needs the authorized BW and PCC checkouts')

from sss.adapters.bw_verified_practice import export_correction
from sss.adapters.verified_practice_registry import InstalledBWPractice
from sss.adapters.learning_panels import LearningPanelEvaluator, PanelLearningPolicy
from sss.records import digest, file_sha256
from sss_integration.bw_verified_practice_cpu import captured_pair, actual_renderer
from sss_tests.test_learning_panels import ControlledPanel, MODEL


class NoTrainingRunner(NativeRunner):
    """Keep the actual owner recipe validation; fail if this test dispatches training."""
    launches = 0

    def __call__(self, *args):
        self.launches += 1
        raise AssertionError('This machinery integration must never train or run a model')


@unittest.skipUnless(os.name == 'posix', 'POSIX owner runtime required')
class InstalledPanelCPUTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model = os.environ.get('SSS_PANEL_CPU_MODEL')
        if not model:
            raise unittest.SkipTest('Set SSS_PANEL_CPU_MODEL to an owned MiniCPM GGUF')
        cls.temp = tempfile.TemporaryDirectory(prefix='sss-installed-panels-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.model = Path(model).resolve(strict=True)
        cls.model_sha = file_sha256(cls.model)
        cls.renderer = actual_renderer(cls.model)
        with captured_pair(cls.root/'bw') as pair:
            cls.exported = export_correction(pair['owner'], pair['correction'].directory,
                correction_capture_id=pair['correction'].capture_id,
                failure_capture_id=pair['failure'].capture_id,
                renderer=cls.renderer, output=cls.root/'export')
            row = dict(owner=pair['owner'].descriptor(), renderer=cls.renderer.binding(),
                export_directory=str(cls.exported.directory), export_id=cls.exported.export_id,
                lesson_id=cls.exported.lesson_id, failure_capture_id=pair['failure'].capture_id,
                correction_capture_id=pair['correction'].capture_id)
        # Proof is self-contained after the operational BW/COW server is retired.
        (cls.root/'bw').rename(cls.root/'retired-operational-bw')
        cls.registry = cls.root/'registry-private.json'
        cls.registry.write_text(json.dumps(dict(schema=1,
            kind='sss.verified-bw-practice-registry.v1', registrations=[row])))
        cls.registry.chmod(0o600)
        components = model_text_components(cls.model, dict(enable_thinking=False), model_contract_id=MODEL)
        cls.provider = InstalledBWPractice(cls.registry, components=components, model_contract_id=MODEL)

    def setUp(self):
        self.panels = [ControlledPanel(name) for name in ('target', 'workflow', 'retention')]
        self.evaluator = LearningPanelEvaluator([(p.name,p.name,p) for p in self.panels],
            [('bw-artifact',self.provider)], model_contract_id=MODEL)
        profile = dict(schema=2, title='CPU machinery recipe; never dispatched', mode='full', rank=None,
            optimizer='adamw', learning_rate=.0001, optimizer_settings=dict(schema=1),
            state_policy='fresh', training_budget_seconds=None)
        self.recipe = dict(mode='full', rank=2, batch_size=1, steps=1,
            learning_rate=.0001, optimizer_profile_id=identity(profile))
        self.policy = PanelLearningPolicy(self.evaluator, self.recipe,
            title='Installed provider with controlled panels; no quality claim',
            max_rounds=2, assessment_purpose='machinery', minimum_skill_cases=3)
        self.policy_id = digest(self.policy.describe())
        self.config = dict(model=str(self.model), base_sha256=self.model_sha,
            executable='/not-invoked-by-this-test', devices=['CPU'], gpu_uuids=[],
            device_budget_bytes={'CPU':32<<30}, reserve_bytes=128<<20, host_reserve_bytes=128<<20,
            sequence_profile='dense-llama-short-v1', memory_profile='allocator-v1',
            timeout_seconds=60, optimizer_profiles={identity(profile):profile})
        self.store = self.root/self._testMethodName
        self.service = None
        self.open_service()
        self.addCleanup(self.close_service)

    def open_service(self):
        tokenize = lambda text:self.renderer.tokenizer.encode(text,parse_special=True)
        self.runner = NoTrainingRunner(self.config)
        self.service = LessonService(self.store, MODEL, tokenize, self.runner,
            max_tokens=512, max_steps=2, sequence_profile='dense-llama-short-v1',
            rendered_tokenize=tokenize, learning_policies={self.policy_id:self.policy})

    def close_service(self):
        if self.service is not None:
            self.service.close();self.service=None

    def create(self, name='installed-panels'):
        request=dict(operation_id=name,policy_id=self.policy_id,parent_job_id=None,expected_parent_sha256=None)
        receipt=self.service.submit('/cow/training/learning-runs',request)
        self.assertEqual(receipt['run_id'],name)
        return name

    def step(self, run, operation, **extra):
        state=self.service.learning.status(run)
        return self.service.submit('/cow/training/learning-steps',dict(
            operation_id=operation,run_id=run,expected_revision=state['revision'],action='advance',**extra))

    def settle_operation(self, operation):
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            record=self.service._read(self.store/'operations'/(operation+'.json'))
            if record['state'] not in ('queued','running'):return record
            time.sleep(.02)
        self.fail('Original PCC operation still owned; never redispatch on observation timeout')

    def test_real_export_admission_exact_membership_and_public_baseline(self):
        lesson=copy.deepcopy(self.exported.lesson)
        receipt=self.service.submit('/cow/training/lessons',dict(operation_id='admit-original',lesson=lesson))
        stored=self.service.lesson(receipt['lesson_id'])
        self.assertEqual(receipt['lesson_id'],self.exported.lesson_id)
        self.assertEqual(stored['example']['tokens'],self.exported.tokens['tokens'])
        self.assertEqual(stored['example']['targets'],self.exported.tokens['targets'])
        self.assertEqual(stored['example']['loss_mask'],self.exported.tokens['loss_mask'])
        self.policy.validate_lessons([stored],None)
        run=self.create();self.step(run,'measure-baseline')
        operation=self.settle_operation('measure-baseline')
        self.assertEqual(operation['state'],'complete',operation)
        state=self.service.learning.status(run)
        self.assertEqual(state['phase'],'choosing_lessons')
        evaluation=self.service._read(self.store/'learning'/run/'baseline-evaluation.json')
        self.assertEqual([p['role'] for p in evaluation['panels']],['target','workflow','retention'])
        self.assertEqual(evaluation['cases'],3)
        self.assertEqual(self.evaluator.recover(None,self.store/'learning'/run/'baseline-backend'),evaluation)
        # An owner-admitted lesson is not automatically a member of this policy.
        changed=copy.deepcopy(lesson);changed['segments'][-1]['rendered']+='\n# unapproved replacement'
        wrong=self.service.submit('/cow/training/lessons',dict(operation_id='admit-unregistered',lesson=changed))
        with self.assertRaises(ValueError):self.step(run,'refuse-unregistered',lesson_ids=[wrong['lesson_id']])
        self.assertEqual(self.service.learning.status(run)['phase'],'choosing_lessons')
        self.assertEqual(self.runner.launches,0)
        self.assertEqual([p.calls for p in self.panels],[1,1,1])

    def test_original_lost_baseline_response_recovers_after_service_restart(self):
        original=self.panels[-1].__class__.__call__
        # A process-level exit is outside PCC's Exception handler. The actual
        # service restart must mark its original queued/running receipt interrupted.
        def exit_after_original(panel,value,directory,worker_fd):
            result=original(panel,value,directory,worker_fd)
            if panel is self.panels[-1]:raise SystemExit('controlled coordinator exit after durable last panel')
            return result
        from unittest.mock import patch
        run=self.create('lost-response')
        with patch.object(ControlledPanel,'__call__',exit_after_original):
            self.step(run,'interrupted-baseline')
            # Executor shutdown waits for the original phase; no retry launches.
            self.close_service()
        self.open_service()
        operation=self.service._read(self.store/'operations/interrupted-baseline.json')
        self.assertEqual(operation['state'],'interrupted')
        state=self.service.learning.status(run)
        self.assertEqual(state['phase'],'baseline_running')
        self.assertIn('reconcile',{r['action'] for r in state['available_actions']})
        self.service.submit('/cow/training/learning-steps',dict(operation_id='recover-baseline',
            run_id=run,expected_revision=state['revision'],action='reconcile'))
        operation=self.settle_operation('recover-baseline')
        self.assertEqual(operation['state'],'complete',operation)
        self.assertEqual(self.service.learning.status(run)['phase'],'choosing_lessons')
        self.assertEqual([p.calls for p in self.panels],[1,1,1])
        self.assertEqual([p.recovers for p in self.panels],[1,1,1])
        self.assertEqual(self.runner.launches,0)


if __name__=='__main__':unittest.main()
