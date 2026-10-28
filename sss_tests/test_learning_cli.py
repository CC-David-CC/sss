"""The actual offline CLI preserves evidence and cannot overwrite a proposal."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from sss_tests import test_learning_composite as fixture


class LearningCliTests(unittest.TestCase):
    def invoke(self, root):
        return subprocess.run([
            sys.executable, '-m', 'sss', 'study', 'next-block',
            '--baseline', str(root / 'baseline.json'), '--parent', str(root / 'parent.json'),
            '--candidate', str(root / 'candidate.json'), '--output', str(root / 'proposal.json'),
        ], capture_output=True, text=True, timeout=15,
            env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1])))

    def prepare(self, root):
        inputs = fixture.CompositeLearningTests().inputs()
        for name, value in zip(('baseline', 'parent', 'candidate'), inputs):
            (root / (name + '.json')).write_text(json.dumps(value))
        return inputs

    def test_real_cli_emits_the_measured_hat_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.prepare(root)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = self.invoke(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            proposal = json.loads((root / 'proposal.json').read_text())
            self.assertEqual(proposal['next_parent']['candidate_adapters'][0]['sha256'], '2' * 64)
            self.assertEqual(proposal['schema'], 2)
            self.assertFalse(proposal['promoted'])
            self.assertNotIn('outcomes', proposal)
            self.assertFalse(json.loads(result.stdout)['promoted'])
            self.assertTrue(all((root / name).read_bytes() == raw for name, raw in before.items()))
            original = (root / 'proposal.json').read_bytes()
            again = self.invoke(root)
            self.assertEqual(again.returncode, 2)
            self.assertEqual((root / 'proposal.json').read_bytes(), original)

    def test_partial_binding_is_refused_before_writing_a_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.prepare(root)
            path = root / 'candidate.json'
            value = json.loads(path.read_text())
            value.pop('candidate_adapters')
            path.write_text(json.dumps(value))
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = self.invoke(root)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / 'proposal.json').exists())
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


if __name__ == '__main__':
    unittest.main()
