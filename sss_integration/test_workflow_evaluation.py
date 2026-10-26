"""Read-only recovery/corruption checks against a genuine completed workflow probe."""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sss.adapters.workflow_evaluation import BWWorkflowEvaluator
from sss.records import file_sha256


class WorkflowEvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=os.environ.get('SSS_WORKFLOW_NATIVE_PROBE')
        if not folder:raise unittest.SkipTest('Set SSS_WORKFLOW_NATIVE_PROBE to an original completed probe')
        cls.root=Path(folder).absolute();cls.backend=cls.root/'backend'
        cls.panel=BWWorkflowEvaluator(cls.root/'owner-config-private.json')
        cls.result=cls.panel.recover(None,cls.backend)
        if cls.result is None:raise ValueError('Original completed workflow evidence required')
        cls.measured=cls.backend/'evaluation';cls.result_path=cls.measured/'result.json'
        cls.original_sha=file_sha256(cls.result_path)

    @classmethod
    def tearDownClass(cls):
        if file_sha256(cls.result_path)!=cls.original_sha:raise AssertionError('Read-only replay changed original result')

    def test_actual_original_workflow_recovers_without_dispatch(self):
        with (patch('subprocess.Popen',side_effect=AssertionError('no process dispatch')),
              patch('sss.adapters.bw_practice_oracle.observe',side_effect=AssertionError('no oracle execution'))):
            self.assertEqual(self.panel.recover(None,self.backend),self.result)
            self.panel.validate(self.result,None)

    def test_host_completion_and_consistent_summary_rewrite_cannot_replace_independent_grade(self):
        value=copy.deepcopy(self.result)
        index=next(i for i,r in enumerate(value['outcomes'])if r['finished'] and not r['passed'])
        value['outcomes'][index]['passed']=True;value['passed']+=1
        path=self.measured/('%04d'%index)/'observation-private.json'
        observed=json.loads(path.read_bytes());observed['outcome']=value['outcomes'][index]
        settlement=self.measured/'settlement.json';settled=json.loads(settlement.read_bytes())
        from sss.records import canonical
        import hashlib
        raw=json.dumps(value).encode();settled['result_sha256']=hashlib.sha256(raw).hexdigest()
        changed={self.result_path:raw,path:json.dumps(observed).encode(),settlement:json.dumps(settled).encode()}
        original=Path.read_bytes
        def corrupt(p):return changed[p]if p in changed else original(p)
        # Also alter the hash reader's result for the rewritten summary, so
        # rejection must come from original independent evidence, not its hash.
        import sss.adapters.workflow_evaluation as module
        sha=module.file_sha256
        with (patch.object(Path,'read_bytes',corrupt),
              patch.object(module,'file_sha256',lambda p:hashlib.sha256(raw).hexdigest()if p==self.result_path else sha(p))):
            with self.assertRaisesRegex(ValueError,'independent artifact score'):
                self.panel.validate(value,None)

    def test_changed_workflow_observation_cannot_replace_actual_ledger(self):
        path=self.measured/'0000/observation-private.json';value=json.loads(path.read_bytes())
        value['workflow']['tools']=[]
        original=Path.read_bytes
        def corrupt(p):return json.dumps(value).encode()if p==path else original(p)
        with patch.object(Path,'read_bytes',corrupt):
            with self.assertRaisesRegex(ValueError,'ledger observation'):
                self.panel.recover(None,self.backend)


if __name__=='__main__':unittest.main()
