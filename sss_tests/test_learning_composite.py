"""A working-parent recommendation must identify the actual measured adapter."""
import copy
import unittest
from sss.learning import next_skill_block
from sss_tests.test_paired import evidence


def bound(rows, contract, adapter=None, scale=1.):
    value = evidence(rows)
    value.update(candidate_model_contract_id=contract * 64,
                 candidate_adapters=[] if adapter is None else [dict(sha256=adapter * 64, scale=scale)])
    return value


class CompositeLearningTests(unittest.TestCase):
    def inputs(self):
        return (bound([(False, False), (False, False)], 'd'),
                bound([(True, True), (False, False)], 'e', '1'),
                bound([(True, True), (True, True)], 'f', '2'))

    def test_advance_preserves_hat_identity_despite_equal_base_hashes(self):
        baseline, parent, candidate = self.inputs()
        result = next_skill_block(baseline, parent, candidate)
        self.assertEqual(result['working_decision'], 'KEEP_AND_ADVANCE')
        self.assertEqual(result['next_parent'], result['candidate'])
        self.assertNotEqual(result['next_parent'], result['parent'])
        self.assertEqual(result['next_parent']['base_model_sha256'], parent['model_sha256'])
        self.assertEqual(result['next_parent']['candidate_model_contract_id'], 'f' * 64)
        self.assertEqual(result['next_parent']['candidate_adapters'], [dict(sha256='2' * 64, scale=1.)])
        self.assertEqual(result['baseline']['candidate_adapters'], [])
        self.assertNotIn('next_parent_sha256', result)
        self.assertNotIn('outcomes', result)
        self.assertFalse(result['promoted'])
        candidate['candidate_adapters'][0]['scale'] = 2.
        self.assertEqual(result['next_parent']['candidate_adapters'][0]['scale'], 1.)

    def test_retaining_parent_does_not_accidentally_select_the_rejected_hat(self):
        baseline, parent, _ = self.inputs()
        bad = bound([(False, False), (False, False)], '0', '3')
        result = next_skill_block(baseline, parent, bad)
        self.assertEqual(result['working_decision'], 'RETAIN_PARENT')
        self.assertEqual(result['next_parent'], result['parent'])
        self.assertNotEqual(result['next_parent'], result['candidate'])
        self.assertEqual(result['next_parent']['candidate_adapters'][0]['sha256'], '1' * 64)

    def test_scale_is_part_of_the_selected_candidate(self):
        baseline, parent, _ = self.inputs()
        changed_scale = bound([(True, True), (True, True)], '0', '1', .5)
        result = next_skill_block(baseline, parent, changed_scale)
        self.assertEqual(result['next_parent']['candidate_adapters'][0]['sha256'], '1' * 64)
        self.assertEqual(result['next_parent']['candidate_adapters'][0]['scale'], .5)
        self.assertEqual(result['parent']['candidate_adapters'][0]['scale'], 1.)

    def test_conflicting_composite_identity_is_invalid_evidence_not_learning(self):
        baseline, parent, candidate = self.inputs()
        candidate['candidate_model_contract_id'] = parent['candidate_model_contract_id']
        with self.assertRaises(ValueError):
            next_skill_block(baseline, parent, candidate)

    def test_different_outcomes_for_an_unchanged_hat_are_not_a_weight_gain(self):
        baseline, parent, candidate = self.inputs()
        candidate['candidate_model_contract_id'] = parent['candidate_model_contract_id']
        candidate['candidate_adapters'] = [dict(a) for a in parent['candidate_adapters']]
        with self.assertRaisesRegex(ValueError, 'Unchanged candidate'):
            next_skill_block(baseline, parent, candidate)

    def test_missing_identity_or_adapter_path_cannot_enter_a_recommendation(self):
        for defect in ('partial', 'path'):
            baseline, parent, candidate = self.inputs()
            if defect == 'partial':
                candidate.pop('candidate_adapters')
            else:
                candidate['candidate_adapters'][0]['path'] = '/untrusted/adapter'
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                next_skill_block(baseline, parent, candidate)


if __name__ == '__main__':
    unittest.main()
