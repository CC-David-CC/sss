"""Actual BW tools/COW grammar/OS, scripted proposals only; no model training."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sss.artifact_assessment import ArtifactAssessmentCase
from sss.practice_oracle import AffineClampFoldCase
from sss.workflow_assessment import SENTINEL,workflow_question,observe_capture
from sss_integration.bw_verified_practice_cpu import BAD,GOOD,ROWS,captured_pair


class WorkflowAssessmentTests(unittest.TestCase):
    def test_real_failed_and_finished_workflow_capture_and_no_dispatch_replay(self):
        from branchwrite.coding_cli import read_launch
        from branchwrite.lesson_capture import capture_assessment,capture_failure
        case=ArtifactAssessmentCase(AffineClampFoldCase.install('workflow-cpu-01','assessment.workflow-cpu',ROWS),
            BAD,'code.repair.affine','composition')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with captured_pair(root/'bw',task_override=workflow_question(case),project_sentinel=SENTINEL) as pair:
                failed=capture_assessment(pair['failed_state'],root/'failed-archive')
                fixed=capture_assessment(pair['corrected_state'],root/'fixed-archive')
                failed_launch=read_launch(pair['failed_state']);fixed_launch=read_launch(pair['corrected_state'])
                left,left_source=observe_capture(case,failed,failed_launch)
                right,right_source=observe_capture(case,fixed,fixed_launch)
                self.assertFalse(left['finished']);self.assertEqual(left_source,BAD)
                self.assertTrue(right['finished']);self.assertTrue(right['read_edit_check_finish'])
                self.assertEqual(right_source,GOOD);self.assertGreater(right['native_receipts'],0)
                pair['project'].rename(root/'retired-project')
            with patch('subprocess.Popen',side_effect=AssertionError('no dispatch')):
                self.assertEqual(observe_capture(case,fixed,fixed_launch),(right,GOOD))
            # A failure archive is not a standalone assessment, even when valid.
            with self.assertRaisesRegex(ValueError,'standalone'):
                observe_capture(case,pair['failure'],failed_launch)
            # A passing host workflow does not establish semantic correctness.
            self.assertFalse(left['host_verified']);self.assertTrue(right['host_verified'])


if __name__=='__main__':unittest.main()
