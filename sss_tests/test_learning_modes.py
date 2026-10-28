import unittest
from sss.learning_modes import validate_mode

class LearningModesTests(unittest.TestCase):
    def test_modes_are_distinct(self):
        for answer,loss in [('direct','answer_only'),('reasoning','answer_only'),('reasoning','reasoning_and_answer')]:
            mode=dict(answer_mode=answer,supervision=loss,format_policy='structured')
            self.assertEqual(validate_mode(mode),mode)
    def test_conflated_or_implicit_modes_rejected(self):
        for mode in [{},dict(answer_mode='direct',supervision='reasoning_and_answer',format_policy='exact')]:
            with self.assertRaises(ValueError):validate_mode(mode)
