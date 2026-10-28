"""Read-only real-probe recovery and injected read-corruption controls.

Requires a completed owner probe from this exact source version. No model,
GPU, training, network or oracle execution is dispatched by these checks.
Injected bytes exist only in the test reader; original files stay unchanged.
"""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sss.adapters.artifact_evaluation import CowArtifactEvaluator
from sss.records import file_sha256


class ArtifactEvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=os.environ.get('SSS_ARTIFACT_NATIVE_PROBE')
        if not folder:raise unittest.SkipTest('Set SSS_ARTIFACT_NATIVE_PROBE to a completed owner probe')
        cls.root=Path(folder).absolute();cls.backend=cls.root/'backend'
        cls.panel=CowArtifactEvaluator(cls.root/'owner-config-private.json')
        cls.result=cls.panel.recover(None,cls.backend)
        if cls.result is None:raise ValueError('Original completed artifact probe required')
        cls.measured=cls.backend/'evaluation'
        cls.result_path=cls.measured/'result.json'
        cls.original_sha=file_sha256(cls.result_path)

    @classmethod
    def tearDownClass(cls):
        if file_sha256(cls.result_path)!=cls.original_sha:
            raise AssertionError('Read-only replay changed original result bytes')

    def test_actual_original_evidence_recovers_with_no_dispatch(self):
        import subprocess
        with (patch.object(subprocess,'Popen',side_effect=AssertionError('no process dispatch')),
              patch('sss.adapters.bw_practice_oracle.observe',side_effect=AssertionError('no oracle rerun'))):
            self.assertEqual(self.panel.recover(None,self.backend),self.result)
            self.panel.validate(self.result,None)

    def test_changed_sampled_tokens_are_refused(self):
        path=self.measured/'0000-private.json';value=json.loads(path.read_bytes())
        value['completion']['sampled_token_ids'].insert(0,self.panel.config['stop_token_ids'][0])
        original=Path.read_bytes
        def corrupt(p):return json.dumps(value).encode() if p==path else original(p)
        with patch.object(Path,'read_bytes',corrupt),self.assertRaises(ValueError):
            self.panel.recover(None,self.backend)

    def test_score_and_count_rewrite_cannot_replace_independent_oracle(self):
        value=copy.deepcopy(self.result)
        index=next(i for i,r in enumerate(value['outcomes']) if r['passed'])
        value['outcomes'][index]['passed']=False;value['passed']-=1
        path=self.measured/('%04d-private.json'%index)
        observed=json.loads(path.read_bytes());observed['outcome']=value['outcomes'][index]
        changed={self.result_path:json.dumps(value).encode(),path:json.dumps(observed).encode()}
        original=Path.read_bytes
        def corrupt(p):return changed.get(p,original(p))
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'isolated artifact grade'):
            self.panel.validate(value,None)

    def test_changed_saved_oracle_verdict_is_refused(self):
        index=next(i for i,r in enumerate(self.result['outcomes']) if not r['passed'])
        path=self.measured/('oracle-%04d'%index)/'result-private.json'
        value=json.loads(path.read_bytes());value['status']='pass'
        import sss.adapters.bw_verified_practice as proof
        original=proof._read
        def corrupt(p,*args,**kwargs):
            return json.dumps(value).encode() if p==path else original(p,*args,**kwargs)
        with patch.object(proof,'_read',corrupt),self.assertRaises(ValueError):
            self.panel.recover(None,self.backend)


if __name__=='__main__':unittest.main()
