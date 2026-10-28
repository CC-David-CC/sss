import json
import unittest
from sss_integration.curriculum_pack_audit import audit


class CurriculumPackAuditTests(unittest.TestCase):
    def test_audit_reports_only_sanitized_counts_and_stable_identity(self):
        result=audit(['math.add.no_carry'])
        self.assertEqual(result,audit(['math.add.no_carry']))
        self.assertEqual(result['selected_skills'],1)
        self.assertEqual(result['combined_pack']['status'],'ready_for_admission_checks')
        self.assertFalse(result['training_admission_granted'])
        self.assertFalse(result['semantic_disjointness_established'])
        self.assertNotIn('prompt',json.dumps(result))
        self.assertNotIn('answer',json.dumps(result))

    def test_duplicate_finite_domain_remains_a_blocker(self):
        result=audit(['logic.not'])
        self.assertEqual(result['combined_pack']['status'],'not_ready')
        self.assertEqual(result['combined_pack']['reason'],'duplicate_question_across_protected_splits')
        self.assertTrue(result['combined_pack']['duplicate_coordinates'])
        self.assertTrue(all(row['repeated']['split']!='practice'
                            for row in result['combined_pack']['duplicate_coordinates']))
        self.assertFalse(result['mastery_established'])

    def test_unknown_or_duplicate_skills_refused(self):
        with self.assertRaises(ValueError):audit(['not-a-skill'])
        with self.assertRaises(ValueError):audit(['math.add.no_carry','math.add.no_carry'])


if __name__=='__main__':
    unittest.main()
