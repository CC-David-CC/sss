from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import copy
import hashlib
import tempfile
import unittest

from sss.adapters.foundation_training import build_pack, validate_pack, initialize, FoundationGuardEvaluator
from sss.foundations import Exercise, reference
from sss.guard import SkillTree, SkillGuardRunner
from sss.records import digest


class MemoryLessons:
    """Admission spy only; actual PCC tokenizer/native integration is separate."""
    def __init__(self, root):
        self.root = root; self.model = 'a' * 64; self.records = {}; self.admitted = []

    def _example(self, lesson, identity):
        text = ''.join(row['rendered'] for row in lesson['segments'])
        if len(text) > 10000:
            raise ValueError('overlong')
        self.admitted.append(identity)
        tokens = list(text.encode())
        return dict(tokens=tokens[:-1], targets=tokens[1:])

    def submit(self, path, request):
        lesson = request['lesson']; identity = digest(lesson)
        self.records[identity] = dict(lesson=lesson)
        return dict(lesson_id=identity)


def render(exercise, answer):
    return [dict(role='user', kind='question', rendered='User: ' + exercise.prompt + '\nAssistant: ',
                 verified=False, scope='practice'),
            dict(role='assistant', kind='answer', rendered=answer + '\n', verified=True, scope='practice')]


class FoundationTrainingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = build_pack(['math.add.carry', 'math.fraction.add', 'state.registers'],
                               seed=20261023, practice_per_gate=4, checks_per_gate=2)

    def initialize(self, renderer=render):
        service = MemoryLessons(self.root)
        tree = initialize(service, self.pack, renderer,
                          renderer_sha256='b'*64, tokenizer_sha256='c'*64)
        return service, tree

    def test_prerequisite_closure_split_counts_and_rehearsal_are_explicit(self):
        self.assertEqual(len(self.pack['skills']), 9)
        self.assertIn('math.place_value', self.pack['requires']['math.add.no_carry'])
        self.assertEqual(len(validate_pack(self.pack)), 216)
        self.assertEqual(self.pack['repeated_practice_questions'], 1)
        self.assertFalse(self.pack['formal_mastery_qualification'])
        changed = copy.deepcopy(self.pack)
        changed['exercises'][0]['split'] = 'qualification'
        changed['pack_id'] = digest({k:v for k,v in changed.items() if k != 'pack_id'})
        with self.assertRaisesRegex(ValueError, 'frozen generator'):
            validate_pack(changed)

    def test_full_practice_admission_and_guard_preserve_all_protected_prompts(self):
        service, tree = self.initialize()
        self.assertEqual(len(service.records), 108)
        self.assertEqual(len(tree.rows('validation')), 54)
        self.assertEqual(len(tree.rows('blind')), 54)
        guard = SkillGuardRunner(lambda *a: None, tree, lambda *a: None, round_examples=18)
        guard.bind(service.records.__getitem__, service._example, lambda t:list(t.encode()), service.model)
        lessons, pools = guard._materialize(dict(lesson_ids=[]))
        self.assertEqual(len(lessons), 108)
        from collections import Counter
        picked = guard._select(pools, ['math.add.carry'], Counter(), [])
        skills = [lessons[k]['skill_id'] for k in picked]
        self.assertEqual(set(skills), set(self.pack['skills']))
        self.assertEqual(len(picked), 18)
        txt = next(self.root.glob('foundation-pack-*/finished-training-examples.txt')).read_text()
        self.assertIn('Checked answer:', txt)
        for row in tree.cases.values():
            self.assertNotIn(row['prompt'], txt)

    def test_overlong_or_unverified_thinking_is_refused_before_any_submission(self):
        service = MemoryLessons(self.root)
        with self.assertRaisesRegex(ValueError, 'overlong'):
            initialize(service, self.pack, lambda e,a:render(e,a + 'x'*11000),
                       renderer_sha256='b'*64, tokenizer_sha256='c'*64)
        self.assertFalse(service.records)

    def test_forged_reference_thinking_is_not_attested(self):
        service = MemoryLessons(self.root)
        def thoughts(e,a):
            rows = render(e,a); rows[-1]['kind'] = 'thinking'; return rows
        with self.assertRaisesRegex(ValueError, 'does not attest'):
            initialize(service, self.pack, thoughts,
                       renderer_sha256='b'*64, tokenizer_sha256='c'*64)
        self.assertFalse(service.records)

    def test_candidate_binding_and_original_failure_are_preserved(self):
        _, tree = self.initialize()
        exercises = {e.prompt:e for e in validate_pack(self.pack)}
        settled = []
        @contextmanager
        def session(candidate, path, fd):
            def model(messages, tools, intent):
                intent.write_text('original intent')
                e = exercises[messages[-1]['content']]
                return dict(content=reference(e) if e.gate != 'composition' else 'incorrect'), {}
            try:
                yield model, dict(base_sha256='d'*64, adapter_sha256=None, runtime_id='e'*64)
            finally:
                settled.append(True)
        evaluator = FoundationGuardEvaluator(tree,self.pack,session,base_sha256='d'*64,runtime_id='e'*64)
        rows = evaluator(None,'validation',self.root/'baseline',9)
        self.assertEqual(sum(row['passed'] for row in rows),36)
        self.assertEqual(len(rows),54)
        self.assertEqual(len(settled),1)
        candidate = self.root/'adapter.gguf'; candidate.write_bytes(b'owned fixture')
        with self.assertRaisesRegex(ValueError, 'not the requested candidate'):
            evaluator(dict(candidate_path=str(candidate),candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                           mode='lora'),'validation',self.root/'wrong-model',9)
        self.assertEqual(len(settled),2)
        self.assertFalse(list((self.root/'wrong-model').glob('*-intent.json')))

    def test_changed_checker_contract_is_rejected(self):
        _, tree = self.initialize()
        changed = copy.deepcopy(tree.document)
        changed['nodes'][1]['validation'][0]['checker']['case_id']='unknown'
        with self.assertRaisesRegex(ValueError, 'checks differ'):
            FoundationGuardEvaluator(SkillTree(changed),self.pack,None,base_sha256='d'*64,runtime_id='e'*64)


if __name__ == '__main__':
    unittest.main()
