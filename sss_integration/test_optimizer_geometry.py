"""Optional CPU integration: actual PCC saved GGUF/subset reader, no model inference."""
from pathlib import Path
import json, os, struct, sys, tempfile, unittest

from sss_integration.optimizer_geometry import run


class OptimizerGeometryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pcc=Path(os.environ['PCC_SOURCE_ROOT']).resolve(strict=True)
        sys.path.insert(0,str(cls.pcc))
        from experimental.native_training.make_llama_fixture import make_fixture
        from experimental.native_training.matrix_geometry import extract, sha
        from tools.gguf_reader import GGUFFile
        cls.make_fixture=staticmethod(make_fixture);cls.extract=staticmethod(extract)
        cls.sha=staticmethod(sha);cls.gguf=GGUFFile

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        base=self.make_fixture(self.root/'base.gguf',dtype='f32',layers=1)
        candidate=self.root/'candidate.gguf';candidate.write_bytes(base.read_bytes())
        info=self.gguf(candidate);tensor=next(t for t in info.tensors if t.name=='blk.0.attn_q.weight')
        with candidate.open('r+b') as stream:
            stream.seek(info.data_start+tensor.offset);value=struct.unpack('<f',stream.read(4))[0]
            stream.seek(info.data_start+tensor.offset);stream.write(struct.pack('<f',value+.125))
        names=['blk.0.attn_q.weight']
        self.extract(base,self.sha(base),names,self.root/'base')
        self.extract(candidate,self.sha(candidate),names,self.root/'candidate')
        self.scores=dict(status='PARTIAL_CURVE',baseline=dict(model_sha256=self.sha(base)),
            evaluation_id='a'*64,runtime_id='b'*64,points=[dict(arm='fixture',update=1,
            presentations=1,passed=1,finished=1,answer_gains=1,answer_losses=0,
            model_sha256=self.sha(candidate),evaluation_evidence_sha256='c'*64)])
        self.score_path=self.root/'scores.json';self.score_path.write_text(json.dumps(self.scores))
        self.manifest=dict(schema=1,baseline_subset=str(self.root/'base'),
            candidates=[dict(label='fixture',subset=str(self.root/'candidate'))],
            behavior_file=str(self.score_path),update=1)
        self.manifest_path=self.root/'manifest.json';self.manifest_path.write_text(json.dumps(self.manifest))

    def test_real_saved_matrices_join_only_the_scored_checkpoint(self):
        result=run(self.pcc,self.manifest_path,self.root/'report',workers=2,blas_threads=1)
        self.assertEqual(result['status'],'COMPLETE');self.assertEqual(len(result['results']),2)
        rows={row['arm']:row for row in result['results']}
        self.assertGreater(rows['fixture']['change_from_base']['frobenius_norm'],0)
        self.assertEqual(rows['original']['change_from_base']['frobenius_norm'],0)
        self.assertEqual(result['behavior'][0]['model_sha256'],self.scores['points'][0]['model_sha256'])
        self.assertFalse(result['gpu_used']);self.assertFalse(result['weights_updated']);self.assertFalse(result['promoted'])

    def test_foreign_scored_weights_are_refused_before_creating_report(self):
        self.scores['points'][0]['model_sha256']='0'*64
        self.score_path.write_text(json.dumps(self.scores))
        with self.assertRaises(ValueError):run(self.pcc,self.manifest_path,self.root/'report')
        self.assertFalse((self.root/'report').exists())

    def test_corrupted_saved_matrix_is_refused_before_analysis(self):
        (self.root/'candidate/000.npy').write_bytes(b'changed')
        with self.assertRaises(ValueError):run(self.pcc,self.manifest_path,self.root/'report')
        self.assertFalse((self.root/'report').exists())

    def test_report_cannot_be_created_inside_immutable_subset(self):
        with self.assertRaises(ValueError):run(self.pcc,self.manifest_path,self.root/'candidate/report')
        self.assertFalse((self.root/'candidate/report').exists())


if __name__=='__main__':unittest.main()
