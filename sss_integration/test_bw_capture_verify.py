"""Real BW archival captures checked by S³'s independent registered oracle.

Run on an authorized Linux host with BW_ROOT pointing at the matching BW
checkout. This constructs a controlled fixture; it is not a spontaneous model
failure or language-model evaluation.
"""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from sss_integration.bw_capture_verify import (
    VerificationRefused,
    admit_bw_practice_lesson,
    build_practice_lesson_from_capture_pair,
    main,
    verify_bw_capture_pair,
)
from sss.records import digest


@unittest.skipUnless(os.environ.get('BW_ROOT'), 'set BW_ROOT to the matching BranchWrite checkout')
class BwCaptureVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bw_root = Path(os.environ['BW_ROOT']).resolve(strict=True)
        sys.path.insert(0, str(bw_root))

    def test_exact_bw_failure_and_correction_are_independently_checked(self):
        from sss.adapters.bw_fixtures import task
        from branchwrite.lesson_capture import capture_failure, capture_correction
        with tempfile.TemporaryDirectory(prefix='sss-bw-capture-test-') as temporary:
            root = Path(temporary)
            captures = root / 'captures'
            captures.mkdir(mode=0o700)
            connection = dict(
                endpoint_url='http://127.0.0.1:1',
                endpoint_pin='fixture-only',
                model_contract_id='a' * 64,
                execution_profile_id='b' * 64,
                eos_tokens=[256],
            )
            failure_state = task(
                root / 'failed-work', connection, corrected=False, factor=2, name='double')
            failure = capture_failure(failure_state, captures / 'failure')
            correction_state = task(
                root / 'corrected-work', connection, corrected=True, factor=2,
                name='double', include_failed_check=True)
            correction = capture_correction(
                correction_state, captures / 'correction', captures / 'failure')

            receipt = verify_bw_capture_pair(
                failure_dir=captures / 'failure',
                correction_dir=captures / 'correction',
                failure_capture_id=failure.capture_id,
                correction_capture_id=correction.capture_id,
                case_id='python.double',
            )
            self.assertEqual(receipt['status'], 'verified')
            self.assertTrue(receipt['independently_verified'])
            self.assertFalse(receipt['training_approved'])
            self.assertFalse(receipt['lesson_created'])
            self.assertEqual([row['passed'] for row in receipt['checks']], [False, True])
            self.assertNotIn('observations', receipt)
            self.assertNotIn('rendered', receipt)
            self.assertEqual(receipt['receipt_sha256'], digest({
                key: value for key, value in receipt.items() if key != 'receipt_sha256'}))

            # A correction is evidence, not the target. The owner selects a
            # separate registered practice variation with a verified reference.
            from tools.pcc_lessons import LessonService
            contract = 'a' * 64
            tokenizer = lambda text: list(text.encode('utf-8'))

            def render(rows):
                return [dict(role=row['role'], kind=row['kind'],
                             rendered=('U:' if row['role'] == 'user' else 'A:') + row['content'],
                             verified=row['verified'], scope=row['scope'])
                        for row in rows]

            prepared = build_practice_lesson_from_capture_pair(
                failure_dir=captures / 'failure',
                correction_dir=captures / 'correction',
                failure_capture_id=failure.capture_id,
                correction_capture_id=correction.capture_id,
                case_id='python.double', practice_case_id='python.triple.practice',
                skill_id='code.python.debug', archive_path=root / 'practice-archive',
                model_contract_id=contract, renderer_sha256='c' * 64,
                tokenizer_sha256='d' * 64, render=render, tokenize=tokenizer)
            self.assertFalse(prepared['training_authorized'])
            self.assertFalse(prepared['weights_updated'])
            self.assertEqual(prepared['verification']['source_case_id'], 'python.double')
            self.assertEqual(prepared['verification']['practice_case_id'], 'python.triple.practice')
            self.assertNotEqual(prepared['lesson']['segments'][1]['rendered'],
                                correction.file_bytes('app.py').decode())
            service = LessonService(root / 'pcc-store', contract, tokenizer,
                                    lambda *args: None, rendered_tokenize=tokenizer,
                                    max_tokens=8192)
            try:
                admitted = admit_bw_practice_lesson(service, 'bw-derived-practice-1', prepared)
                self.assertTrue(admitted['pcc_admission_confirmed'])
                self.assertFalse(admitted['native_update_run'])
                self.assertFalse(admitted['training_authorized'])
                saved = service.lesson(admitted['lesson_id'])
                self.assertEqual(saved['example']['loss_mask'],
                                 prepared['expected_example']['loss_mask'])
            finally:
                service.close()

            with self.assertRaises(VerificationRefused):
                build_practice_lesson_from_capture_pair(
                    failure_dir=captures / 'failure',
                    correction_dir=captures / 'correction',
                    failure_capture_id=failure.capture_id,
                    correction_capture_id=correction.capture_id,
                    case_id='python.double', practice_case_id='python.double',
                    skill_id='code.python.debug', archive_path=root / 'bad-archive',
                    model_contract_id=contract, renderer_sha256='c' * 64,
                    tokenizer_sha256='d' * 64, render=render, tokenize=tokenizer)
            receipt_path = os.environ.get('SSS_BW_CAPTURE_TEST_RECEIPT')
            if receipt_path:
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
                descriptor = os.open(receipt_path, flags, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                    stream.write(json.dumps(receipt, sort_keys=True, separators=(',', ':')) + '\n')

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main([
                    '--failure', str(captures / 'failure'),
                    '--failure-capture-id', failure.capture_id,
                    '--correction', str(captures / 'correction'),
                    '--correction-capture-id', correction.capture_id,
                    '--case', 'python.double',
                ])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.getvalue())['status'], 'verified')

            with self.assertRaises(VerificationRefused):
                verify_bw_capture_pair(
                    failure_dir=captures / 'failure',
                    correction_dir=captures / 'correction',
                    failure_capture_id='0' * 64,
                    correction_capture_id=correction.capture_id,
                    case_id='python.double',
                )
            with self.assertRaises(VerificationRefused):
                verify_bw_capture_pair(
                    failure_dir=captures / 'failure',
                    correction_dir=captures / 'correction',
                    failure_capture_id=failure.capture_id,
                    correction_capture_id=correction.capture_id,
                    case_id='unregistered.case',
                )


if __name__ == '__main__':
    unittest.main()
