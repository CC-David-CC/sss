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

from sss.adapters.bw_fixtures import task
from sss_integration.bw_capture_verify import (
    VerificationRefused,
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
