"""Acceptance must use exactly the policy frozen before a training job."""
import copy
import unittest
from sss.guard import SkillTree, SkillGuardRunner
from sss_tests.test_core import tree


class FrozenGuardPolicy(unittest.TestCase):
    def strict(self):
        document = tree().document
        document['nodes'][1]['minimum_accuracy'] = 1.0
        return document, SkillTree(document)

    def partial(self, active):
        return [dict(id=row['id'], passed=index != 0)
                for index, row in enumerate(active.rows('validation'))]

    def test_caller_cannot_relax_the_live_threshold_after_freezing(self):
        document, active = self.strict()
        identity = active.identity
        document['nodes'][1]['minimum_accuracy'] = 0.5
        self.assertFalse(active.assess(self.partial(active), 'validation')['qualified'])
        self.assertEqual(active.identity, identity)

    def test_caller_cannot_replace_nested_checker_or_practice(self):
        document, active = self.strict()
        original = copy.deepcopy(active.document)
        document['nodes'][1]['validation'][0]['parameters'].append('injected')
        document['nodes'][1]['practice_lesson_ids'].append('f'*64)
        self.assertEqual(active.nodes['read'], original['nodes'][1])

    def test_internal_policy_mutation_is_refused_before_assessment(self):
        for target in ('document', 'nodes', 'leaves', 'cases', 'case_skill', 'children'):
            with self.subTest(target=target):
                _, active = self.strict()
                records = self.partial(active)
                if target == 'document':
                    active.document['nodes'][1]['minimum_accuracy'] = .5
                elif target in ('nodes', 'leaves'):
                    getattr(active, target)['read']['minimum_accuracy'] = .5
                elif target == 'cases':
                    next(iter(active.cases.values()))['parameters'].append('injected')
                elif target == 'case_skill':
                    active.case_skill[next(iter(active.case_skill))] = 'root'
                else:
                    active.children['root'] = []
                with self.assertRaisesRegex(ValueError, 'changed after freezing'):
                    active.assess(records, 'validation')

    def test_unknown_split_is_refused_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'Unknown evaluation split'):
            tree().rows('typo')

    def test_guard_settings_cannot_change_under_an_existing_policy_id(self):
        for field, value in [('focus_fraction', .75), ('round_examples', 4), ('max_rounds', 1)]:
            with self.subTest(field=field):
                guard = SkillGuardRunner(lambda *a: None, tree(), lambda *a: None, round_examples=2)
                setattr(guard, field, value)
                with self.assertRaisesRegex(ValueError, 'changed after freezing'):
                    guard.describe_skills()

    def test_evaluator_contract_drift_is_refused(self):
        class Evaluator:
            contract_id = 'a'*64
        evaluator = Evaluator()
        guard = SkillGuardRunner(lambda *a: None, tree(), evaluator, round_examples=2)
        evaluator.contract_id = 'b'*64
        with self.assertRaisesRegex(ValueError, 'changed after freezing'):
            guard.describe_skills()
