import json
import tempfile
import unittest
from pathlib import Path

from sss.level_evaluation import evaluate_level_panel, freeze_level_panel
from sss.curriculum import exercise_for
from sss.learning_lessons import (
    admit_scalar_pcc_lesson, build_scalar_lesson, build_scalar_pcc_lesson,
)
from sss.learning_levels import response_target_segments
from sss.episodes import training_tokens
from sss.profiles import ModelProfile
from sss.records import digest


class LevelEvaluationTests(unittest.TestCase):
    def profile(self):
        return ModelProfile('fixture', 'rev1', 'tok1', 'template1', 'harness1', 'rev1')

    def freeze(self, root, skill='math.add.no_carry'):
        return freeze_level_panel(Path(root) / 'panel', self.profile(), [skill],
                                  cases_per_skill=2, seed=11)

    def test_three_matched_levels_keep_answer_and_format_scores_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            frozen = self.freeze(temp)
            expected_by_prompt = {row['prompt']: row for row in frozen[1].values()}

            def model(messages, tools, intent):
                row = expected_by_prompt[messages[-1]['content']]
                intent.write_text('fixture inference')
                if row['level'] == 'answer':
                    content = row['expected_answer']
                else:
                    content = json.dumps({'answer': row['expected_answer']})
                return dict(content=content), {}

            result = evaluate_level_panel(frozen, model)
            self.assertEqual({row['level'] for row in result['assessments']},
                             {'answer', 'format', 'composed'})
            for row in result['assessments']:
                self.assertEqual(row['qualification'], 'not_attempted')
                for metric in row['metrics'].values():
                    self.assertEqual(metric['passed'], 2)
                    self.assertEqual(metric['failed'], 0)

    def test_correct_answer_with_wrong_format_is_not_a_knowledge_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            frozen = self.freeze(temp)
            expected_by_prompt = {row['prompt']: row for row in frozen[1].values()}

            def model(messages, tools, intent):
                row = expected_by_prompt[messages[-1]['content']]
                intent.write_text('fixture inference')
                if row['level'] == 'composed':
                    return dict(content=row['expected_answer']), {}
                if row['level'] == 'answer':
                    return dict(content=row['expected_answer']), {}
                return dict(content=json.dumps({'answer': row['expected_answer']})), {}

            result = evaluate_level_panel(frozen, model)
            composed = next(row for row in result['assessments'] if row['level'] == 'composed')
            self.assertEqual(composed['metrics']['answer']['passed'], 2)
            self.assertEqual(composed['metrics']['format']['failed'], 2)
            self.assertEqual(composed['metrics']['joint']['failed'], 2)

    def test_proof_tasks_are_not_given_the_numeric_json_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'No qualified task-native scalar format'):
                freeze_level_panel(Path(temp) / 'panel', self.profile(), ['logic.proof'],
                                   cases_per_skill=1)

    def test_practice_lessons_train_answer_format_and_composition_spans_separately(self):
        exercise = exercise_for('math.add.no_carry', 'practice', 0,
                                gate='independent', seed=12)

        def identity_renderer(rows):
            return [dict(role=row['role'], kind=row['kind'], rendered=row['content'],
                         verified=row['verified'], scope=row['scope']) for row in rows]

        lessons = {level: build_scalar_lesson(exercise, level, identity_renderer)
                   for level in ('answer', 'format', 'composed')}
        answer = lessons['answer']
        fmt = lessons['format']
        composed = lessons['composed']
        self.assertEqual(answer['target_policy'], 'answer_only')
        self.assertEqual(fmt['target_policy'], 'format_only')
        self.assertEqual(composed['target_policy'], 'answer_and_format')
        self.assertEqual(response_target_segments(answer['segments'], answer['target_policy']), [False, True])
        self.assertEqual(response_target_segments(fmt['segments'], fmt['target_policy']), [False, True])
        self.assertEqual(response_target_segments(composed['segments'], composed['target_policy']),
                         [False, True, True, True])
        for lesson in lessons.values():
            result = training_tokens(lesson['segments'], tokenize=lambda text: list(text.encode()),
                                     policy=lesson['target_policy'], maximum=8192)
            expected = sum(len(row['rendered'].encode()) for row, selected in
                           zip(lesson['segments'], response_target_segments(
                               lesson['segments'], lesson['target_policy'])) if selected)
            self.assertEqual(sum(result['loss_mask']), expected)
        self.assertTrue(all(lesson['verification']['reference_passed'] for lesson in lessons.values()))
        self.assertTrue(all(not lesson['verification']['actual_token_masks_confirmed']
                            for lesson in lessons.values()))

    def test_lessons_cannot_be_built_from_assessment_items_or_transfer_tasks(self):
        assessment = exercise_for('math.add.no_carry', 'development', 0,
                                  gate='independent', seed=12)
        with self.assertRaisesRegex(ValueError, 'practice items'):
            build_scalar_lesson(assessment, 'answer', lambda rows: [])
        recovery = exercise_for('math.add.no_carry', 'practice', 0,
                                gate='transfer_recovery', seed=12)
        with self.assertRaisesRegex(ValueError, 'matched independent'):
            build_scalar_lesson(recovery, 'answer', lambda rows: [])

    def test_s3_builds_and_reconciles_pcc_lesson_mask_without_updating_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            exercise = exercise_for('math.add.no_carry', 'practice', 1,
                                    gate='independent', seed=13)

            def renderer(rows):
                return [dict(role=row['role'], kind=row['kind'],
                             rendered=('U:' if row['role'] == 'user' else 'A:') + row['content'],
                             verified=row['verified'], scope=row['scope']) for row in rows]

            prepared = build_scalar_pcc_lesson(
                exercise, 'composed', renderer,
                archive_path=Path(temp) / 'archive', model_contract_id='a'*64,
                renderer_sha256='b'*64, tokenizer_sha256='c'*64,
                tokenize=lambda text: list(text.encode()), maximum=8192)
            self.assertEqual(prepared['lesson']['schema'], 2)
            self.assertEqual(prepared['lesson']['target_policy'], 'answer_and_format')
            self.assertFalse(prepared['weights_updated'])

            class Service:
                model='a'*64

                def submit(self, route, request):
                    self.asserted=(route, request)
                    self.saved=dict(lesson=request['lesson'], example=dict(
                        id='d'*64, tokens=prepared['expected_example']['tokens'],
                        targets=prepared['expected_example']['targets'],
                        loss_mask=prepared['expected_example']['loss_mask'],
                        verified=True, provenance_sha256=digest(request['lesson']['evidence'])))
                    return dict(lesson_id='d'*64)

                def lesson(self, lesson_id):
                    return self.saved

            service = Service()
            receipt = admit_scalar_pcc_lesson(service, 'response-level-training-example', prepared)
            self.assertTrue(receipt['pcc_admission_confirmed'])
            self.assertFalse(receipt['native_update_run'])
            self.assertFalse(receipt['weights_updated'])
            self.assertEqual(receipt['supervised_tokens'],
                             sum(prepared['expected_example']['loss_mask']))


if __name__ == '__main__':
    unittest.main()
