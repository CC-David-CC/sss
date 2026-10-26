from pathlib import Path
from types import SimpleNamespace
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sss.adapters.artifact_evaluation import CowArtifactEvaluator
from sss.adapters.cow_learning import CowLearningEvaluator
from sss.adapters.runtime_sources import require_child_identity


class ChildInstallationTests(unittest.TestCase):
    def test_exact_child_identity_is_required(self):
        panel = SimpleNamespace(identity='a' * 64)
        require_child_identity(panel, 'a' * 64)
        for invalid in (None, '', 'A' * 64, 'a' * 63, 'b' * 64):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'original parent installation'):
                require_child_identity(panel, invalid)

    def test_api_and_execution_import_roots_are_preserved_in_actual_child(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host, execution, sss, bw = [root / n for n in ('api', 'execution', 'sss', 'bw')]
            for p in (host, execution, sss, bw, execution / 'experimental/branching_context/src'):
                p.mkdir(parents=True, exist_ok=True)
            (host / 'owner_api_probe.py').write_text('origin="parent-api"')
            (execution / 'owner_api_probe.py').write_text('origin="wrong-execution-api"')
            (execution / 'experimental/branching_context/src/owner_engine_probe.py').write_text('origin="qualified-engine"')
            for cls in (CowArtifactEvaluator, CowLearningEvaluator):
                panel = cls.__new__(cls)
                panel.sss, panel.host_pcc, panel.pcc, panel.bw = sss, host, execution, bw
                environment = panel._environment()
                output = subprocess.check_output([sys.executable, '-B', '-c',
                    'import owner_api_probe,owner_engine_probe;print(owner_api_probe.origin);print(owner_engine_probe.origin)'],
                    cwd=root, env=environment, text=True)
                self.assertEqual(output.splitlines(), ['parent-api', 'qualified-engine'])

    def test_artifact_mismatch_stops_before_candidate_read_or_gpu_entry(self):
        from sss_integration import artifact_evaluate
        with patch.object(artifact_evaluate, 'CowArtifactEvaluator', return_value=SimpleNamespace(identity='b' * 64)), \
                patch.object(artifact_evaluate, 'cow_session', side_effect=AssertionError('GPU must not be entered')) as gpu:
            with self.assertRaisesRegex(ValueError, 'original parent installation'):
                artifact_evaluate.run('/not-read', '/not-read', '/not-read', '/not-created', expected_evaluator_id='a' * 64)
            gpu.assert_not_called()


if __name__ == '__main__':
    unittest.main()
