import unittest

from sss.learning_levels import (
    score_answer, score_composed, score_format, score_reasoning_composed,
    response_target_segments, target_policy_for_condition, validate_condition,
)


class LearningLevelTests(unittest.TestCase):
    def condition(self, level, **overrides):
        value = dict(
            level=level,
            answer_mode='direct',
            supervision={'answer': 'answer_only', 'format': 'format_only',
                         'composed': 'format_and_answer'}[level],
            format_policy='none' if level == 'answer' else 'task_native',
            answer_source='provided_answer' if level == 'format' else 'skill_task',
            answer_checker=None if level == 'format' else 'math-exact-v1',
            format_checker=None if level == 'answer' else 'json-number-v1',
            reasoning_checker=None,
            split='development',
        )
        value.update(overrides)
        return value

    def test_three_levels_bind_distinct_inputs_and_targets(self):
        for level in ('answer', 'format', 'composed'):
            self.assertEqual(validate_condition(self.condition(level))['level'], level)
        with self.assertRaises(ValueError):
            validate_condition(self.condition('format', answer_source='skill_task'))

    def test_answer_failure_and_format_failure_are_independent(self):
        self.assertEqual(
            score_composed('The answer is 12.', lambda _: True, lambda _: False),
            dict(answer='pass', format='fail', joint='fail'),
        )
        self.assertEqual(
            score_composed('{"answer": 13}', lambda _: False, lambda _: True),
            dict(answer='fail', format='pass', joint='fail'),
        )

    def test_format_only_checks_known_answer_preservation(self):
        self.assertEqual(
            score_format('{"value": 12}', 12,
                         lambda output, expected: dict(
                             format_valid=output == '{"value": 12}',
                             content_preserved=expected == 12)),
            dict(answer='not_measured', format='pass', content_preserved='pass', joint='pass'),
        )

    def test_checker_failure_is_unscorable_not_model_failure(self):
        self.assertEqual(
            score_answer('12', lambda _: (_ for _ in ()).throw(TimeoutError())),
            dict(answer='unscorable', format='not_measured', joint='not_applicable'),
        )
        with self.assertRaises(ValueError):
            score_answer('12', lambda _: 'yes')

    def test_reasoning_is_an_independent_score_in_composed_mode(self):
        self.assertEqual(
            score_reasoning_composed(
                'reasoning; answer=12', lambda _: False, lambda _: True,
                lambda _: True),
            dict(reasoning='fail', answer='pass', format='pass', joint='fail'),
        )

    def test_reasoning_target_policy_is_distinct_from_direct_and_format(self):
        base = self.condition('answer')
        self.assertEqual(target_policy_for_condition(base), 'answer_only')
        reasoning = self.condition(
            'answer', answer_mode='reasoning', supervision='reasoning_and_answer',
            reasoning_checker='verified-reasoning-v1')
        self.assertEqual(target_policy_for_condition(reasoning), 'reasoning_and_answer')
        spans = [dict(role='assistant', kind='thinking', verified=True),
                 dict(role='assistant', kind='answer', verified=True),
                 dict(role='assistant', kind='format', verified=True)]
        self.assertEqual(response_target_segments(spans, 'reasoning_and_answer'),
                         [True, True, False])


if __name__ == '__main__':
    unittest.main()
