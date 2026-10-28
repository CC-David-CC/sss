"""Recovery must reuse original evidence and reject changed grades or live work."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock
import copy
import json
import os
import tempfile
import unittest
from sss.adapters.cow_learning import CowLearningEvaluator, process_identity, write_once
from sss.foundations import generate, reference
from sss.records import file_sha256


class CowLearningRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.e = CowLearningEvaluator.__new__(CowLearningEvaluator)
        self.e.verify = Mock()
        self.e.identity = 'e' * 64
        self.e.profile = Mock(return_value={'model_path': '/owned/model'})
        self.e._command = Mock(return_value=['original-command'])
        self.e.expected_runtime = Mock(return_value={'runtime': 'original'})
        # The full model/runtime validator is exercised by the GPU qualification;
        # these CPU tests isolate recovery and raw-record validation.
        self.e.validate = Mock()
        self.e.paths = {'cases': self.root / 'cases.json'}
        self.e.pins = {str(self.e.paths['cases']): 'a' * 64}
        self.e.config = {'maximum_tokens': 4, 'stop_token_ids': [9]}
        exercise = generate('add', 'development', 7)
        self.e.case_index = {exercise.identity: (exercise.skill_id, exercise.gate)}
        self.e.data = {'cases': [{'exercise_id': exercise.identity, 'exercise': asdict(exercise)}]}
        answer = reference(exercise)
        self.e.decoder = SimpleNamespace(decode=lambda tokens: answer if tokens == [2] else 'wrong')
        self.directory = self.root / 'backend'
        self.directory.mkdir()
        evaluation = self.directory / 'evaluation'
        evaluation.mkdir()
        self.save('adapter-intent-private.json', dict(schema=1, evaluator_id=self.e.identity,
            profile=self.e.profile(None), command=['original-command'], no_implicit_retry=True))
        self.save('candidate-profile.json', self.e.profile(None))
        self.save('evaluation/intent.json', dict(runtime={'runtime': 'original'},
            cow_profile=self.e.profile(None), cases_sha256='a'*64,
            cow_profile_sha256=file_sha256(self.directory/'candidate-profile.json')))
        self.outcome = dict(id=exercise.identity,skill_id=exercise.skill_id,
            gate=exercise.gate,passed=True,finished=True)
        self.value = dict(model_sha256='b'*64,runtime_id='c'*64,evaluation_id='d'*64,
            outcomes=[self.outcome])
        self.save('evaluation/result.json', self.value)
        self.save('evaluation/settlement.json', dict(status='COMPLETE',weights_updated=False,completed_cases=1))
        self.raw = dict(self.outcome,model_sha256='b'*64,runtime_id='c'*64,evaluation_id='d'*64,
            completion=dict(sampled_token_ids=[2,9],stop_reason='eos',stop_token_id=9,
                cow_receipt={'tokens':[2,9]},text=answer))
        self.save('evaluation/0000-private.json', self.raw)
        self.save('child-process-private.json',dict(pid=999999999,start_ticks=1,boot_id='old'))
        self.save('child-exit-private.json',dict(status='EXITED',returncode=0))

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, name, value):
        (self.directory/name).write_text(json.dumps(value))

    def test_completed_original_evidence_recovers_without_dispatch(self):
        with patch('sss.adapters.cow_learning.subprocess.Popen') as dispatch:
            self.assertEqual(self.e.recover(None,self.directory),self.value)
            dispatch.assert_not_called()
        self.e.verify.assert_called()

    def test_live_original_process_blocks_even_complete_evidence(self):
        self.save('child-process-private.json',process_identity(os.getpid()))
        with self.assertRaisesRegex(ValueError,'still present'):
            self.e.recover(None,self.directory)

    def test_missing_dispatch_receipt_is_not_permission_to_recover(self):
        (self.directory/'child-process-private.json').unlink()
        self.assertIsNone(self.e.recover(None,self.directory))

    def test_lost_parent_exit_receipt_can_use_complete_original_evidence(self):
        (self.directory/'child-exit-private.json').unlink()
        self.assertEqual(self.e.recover(None,self.directory),self.value)

    def test_known_failed_or_timed_out_child_is_not_a_success(self):
        for value in (dict(status='EXITED',returncode=1),dict(status='TIMEOUT',returncode=-9)):
            self.save('child-exit-private.json',value)
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'did not exit successfully'):
                self.e.recover(None,self.directory)

    def test_raw_grade_tokens_text_and_stopping_cannot_be_rewritten(self):
        for defect in ('grade','tokens','text','stop','receipt','model'):
            raw=copy.deepcopy(self.raw)
            if defect=='grade':raw['passed']=False
            if defect=='tokens':raw['completion']['sampled_token_ids']=[3,9]
            if defect=='text':raw['completion']['text']='wrong'
            if defect=='stop':raw['completion']['stop_reason']='limit'
            if defect=='receipt':raw['completion']['cow_receipt']['tokens']=[3,9]
            if defect=='model':raw['model_sha256']='f'*64
            self.save('evaluation/0000-private.json',raw)
            with self.subTest(defect=defect),self.assertRaisesRegex(ValueError,'Original case'):
                self.e.recover(None,self.directory)

    def test_changed_original_runtime_and_incomplete_settlement_refused(self):
        intent=json.loads((self.directory/'evaluation/intent.json').read_text())
        intent['runtime']={'runtime':'other'}
        self.save('evaluation/intent.json',intent)
        with self.assertRaisesRegex(ValueError,'intent or settlement'):
            self.e.recover(None,self.directory)
        intent['runtime']={'runtime':'original'};self.save('evaluation/intent.json',intent)
        self.save('evaluation/settlement.json',dict(status='COMPLETE',weights_updated=False,completed_cases=0))
        with self.assertRaisesRegex(ValueError,'intent or settlement'):
            self.e.recover(None,self.directory)

    def test_unverified_lesson_never_enters_registered_practice(self):
        self.e.allowed_lessons={'a':{'answer':'original'}}
        self.e.validate_lessons([dict(lesson_id='a',lesson={'answer':'original'})],None)
        with self.assertRaisesRegex(ValueError,'independently checked practice'):
            self.e.validate_lessons([dict(lesson_id='a',lesson={'answer':'changed'})],None)

    def test_write_once_cannot_replace_original_intent(self):
        path=self.root/'new-intent.json';write_once(path,{'original':True})
        with self.assertRaises(FileExistsError):write_once(path,{'original':False})
        self.assertEqual(json.loads(path.read_text()),{'original':True})


if __name__=='__main__':unittest.main()
