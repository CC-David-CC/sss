"""Cross-project admission check; run on Linux with PCC tools on PYTHONPATH."""
from pathlib import Path
import tempfile
import unittest

from sss.curriculum import exercise_for
from sss.learning_lessons import admit_scalar_pcc_lesson, build_scalar_pcc_lesson
from tools.pcc_lessons import LessonService


class ResponseLevelPCCIntegration(unittest.TestCase):
    def test_each_level_reaches_pcc_with_only_its_declared_loss_spans(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = 'a' * 64
            tokenizer = lambda text: list(text.encode())
            service = LessonService(root / 'store', contract, tokenizer,
                                    lambda *args: None, rendered_tokenize=tokenizer,
                                    max_tokens=8192)
            try:
                exercise = exercise_for('math.add.no_carry', 'practice', 3,
                                        gate='independent', seed=17)

                def render(rows):
                    return [dict(role=row['role'], kind=row['kind'],
                                 rendered=('U:' if row['role'] == 'user' else 'A:') + row['content'],
                                 verified=row['verified'], scope=row['scope'])
                            for row in rows]

                for level, policy in [('answer', 'answer_only'),
                                      ('format', 'format_only'),
                                      ('composed', 'answer_and_format')]:
                    prepared = build_scalar_pcc_lesson(
                        exercise, level, render,
                        archive_path=root / ('archive-' + level),
                        model_contract_id=contract, renderer_sha256='b' * 64,
                        tokenizer_sha256='c' * 64, tokenize=tokenizer,
                        maximum=8192)
                    self.assertEqual(prepared['lesson']['target_policy'], policy)
                    receipt = admit_scalar_pcc_lesson(
                        service, 'response-level-' + level, prepared)
                    self.assertTrue(receipt['pcc_admission_confirmed'])
                    self.assertFalse(receipt['native_update_run'])
                    saved = service.lesson(receipt['lesson_id'])
                    self.assertEqual(saved['lesson']['target_policy'], policy)
                    self.assertEqual(saved['example']['loss_mask'],
                                     prepared['expected_example']['loss_mask'])
            finally:
                service.close()


if __name__ == '__main__':
    unittest.main()
