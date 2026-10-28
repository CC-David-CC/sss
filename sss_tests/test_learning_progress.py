import unittest
from sss.learning_progress import next_action

class LearningProgressTests(unittest.TestCase):
    def test_empty_and_recovery(self):
        self.assertEqual(next_action({})['action'],'assess')
        self.assertEqual(next_action({'infrastructure_error':True})['action'],'repair_infrastructure')
    def test_bad_state_cannot_skip_training_guards(self):
        for state in ({'candidate_exists':True},{'assessment_complete':'true'},{'approved':True}):
            with self.assertRaises(ValueError):next_action(state)
    def test_candidate_recovery_evaluates_without_training_again(self):
        state=dict(assessment_complete=True,lessons_verified=True,policy_bound=True,candidate_exists=True)
        result=next_action(state)
        self.assertEqual(result['action'],'evaluate_candidate')
        self.assertFalse(result['repeat_training'])
