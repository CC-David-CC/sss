import hashlib
import unittest
from sss.guard import SkillTree, SkillGuardRunner


class GuardedSegments(unittest.TestCase):
    def guard(self, lesson):
        def case(prompt):
            return dict(id=hashlib.sha256(prompt.encode()).hexdigest(), prompt=prompt,
                        checker=dict(name='owned-fixture', version=1, case_id=prompt))
        rows = [dict(id='root', title='Fixture', parent=None, minimum_accuracy=1.,
                     practice_lesson_ids=[], validation=[], blind=[]),
                dict(id='skill', title='One owned skill', parent='root', minimum_accuracy=1.,
                     practice_lesson_ids=['b'*64], validation=[case('Protected question')],
                     blind=[case('Blind question')])]
        tree = SkillTree(dict(schema=1, model_contract_id='a'*64, nodes=rows))
        guard = SkillGuardRunner(lambda *args: None, tree, lambda *args: None, round_examples=2)

        def make_example(value, identity):
            if value['schema'] == 1:
                text = value['prompt'] + value['completion']
            else:
                text = ''.join(r['rendered'] for r in value['segments'])
            tokens = list(text.lower().encode())
            return dict(tokens=tokens[:-1], targets=tokens[1:])

        guard.bind(lambda identity: dict(lesson=lesson), make_example,
                   lambda text: list(text.lower().encode()), 'a'*64)
        return guard

    def test_legacy_practice_still_materializes(self):
        lesson = dict(schema=1, skill_id='skill', prompt='Own practice?', completion=' Answer.')
        lessons, pools = self.guard(lesson)._materialize(dict(lesson_ids=[]))
        self.assertEqual(pools, {'skill': ['b'*64]})
        self.assertEqual(lessons['b'*64], lesson)

    def test_multi_turn_practice_does_not_require_legacy_prompt_field(self):
        lesson = dict(schema=2, skill_id='skill', segments=[
            dict(rendered='User: own problem.'), dict(rendered='Assistant: answer.')])
        self.assertEqual(self.guard(lesson)._materialize(dict(lesson_ids=[]))[1], {'skill': ['b'*64]})

    def test_protected_question_inside_multi_turn_context_is_refused(self):
        lesson = dict(schema=2, skill_id='skill', segments=[
            dict(rendered='Earlier unrelated context. User: PROTECTED QUESTION'),
            dict(rendered=' Assistant: answer.')])
        with self.assertRaisesRegex(ValueError, 'Evaluation prompt/token'):
            self.guard(lesson)._materialize(dict(lesson_ids=[]))

    def test_blind_material_inside_a_completion_is_also_refused(self):
        lesson = dict(schema=1, skill_id='skill', prompt='Own practice?',
                      completion=' This quotes a blind question from the protected pack.')
        with self.assertRaisesRegex(ValueError, 'Evaluation prompt/token'):
            self.guard(lesson)._materialize(dict(lesson_ids=[]))
