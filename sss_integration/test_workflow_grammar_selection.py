"""Selected grammar reaches the actual BW launch without changing task bounds."""
import json
import tempfile
from pathlib import Path
import unittest

from sss.artifact_assessment import ArtifactAssessmentCase
from sss.practice_oracle import AffineClampFoldCase
from sss.workflow_assessment import make_launch
from sss_integration.bw_verified_practice_cpu import BAD,ROWS

class WorkflowGrammarSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/'project';self.project.mkdir()
        (self.project/'task.py').write_bytes(BAD)
        self.case=ArtifactAssessmentCase(AffineClampFoldCase.install('owned-lark-probe','owned.syntax',ROWS),BAD,'code.repair.affine','composition')
        self.connection=dict(endpoint_url='http://127.0.0.1:1',endpoint_pin='owned-cpu',model_contract_id='a'*64,execution_profile_id='b'*64,eos_tokens=[256])
        self.limits=dict(maximum_tokens=256,maximum_requests=2,maximum_steps=128)

    def test_explicit_selection_reaches_validated_host_configuration(self):
        from branchwrite.run_cli import _config
        old=make_launch(self.case,self.project,self.connection,self.limits)
        self.assertNotIn('grammar_syntax',old['config']['cow'])
        new=make_launch(self.case,self.project,self.connection,dict(self.limits,grammar_syntax='lark'))
        self.assertEqual(_config(json.dumps(new['config']))['cow']['grammar_syntax'],'lark')
        self.assertEqual(new['config']['profiles'],old['config']['profiles'])
        self.assertEqual(new['config']['grant'],old['config']['grant'])
        self.assertEqual(new['config']['bindings'],old['config']['bindings'])
        self.assertNotEqual(new,old)

    def test_unsupported_syntax_never_dispatches(self):
        from unittest.mock import patch
        for syntax in (None,True,'automatic','json_schema'):
            with self.subTest(syntax=syntax),patch('subprocess.Popen',side_effect=AssertionError('no dispatch')):
                with self.assertRaises(ValueError):make_launch(self.case,self.project,self.connection,dict(self.limits,grammar_syntax=syntax))

if __name__=='__main__':unittest.main()
