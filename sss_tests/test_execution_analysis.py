import copy
import json
import tempfile
import unittest
from pathlib import Path
from sss.studies.execution_analysis import analyze_assessments


def fixture(root, label):
    directory = root/label; directory.mkdir()
    result = dict(status='COMPLETE', evaluation_id='a'*64, runtime_id='b'*64,
                  model_sha256='c'*64, weights_updated=False, promoted=False, cases=2, passed=1, finished=2,
                  outcomes=[dict(id='case-'+str(i), skill_id='math.add', gate='independent',
                                 passed=i == 0, finished=True) for i in range(2)])
    (directory/'result.json').write_text(json.dumps(result))
    (directory/'settlement.json').write_text(json.dumps(dict(status='COMPLETE', allocated_seconds=4., execution_wall_seconds=5.)))
    for i, outcome in enumerate(result['outcomes']):
        row = dict(outcome, index=i, seconds=1., model_sha256='c'*64, runtime_id='b'*64, evaluation_id='a'*64,
            completion=dict(prefill_tokens=12, model_calls=3, cow_receipt=dict(request_seconds=.8, generation_seconds=.5,
                counters=dict(checkpoint_export_bytes=100, checkpoint_import_bytes=50))))
        (directory/f'{i:04d}-private.json').write_text(json.dumps(row))
    return str(directory)


class ExecutionAnalysisTests(unittest.TestCase):
    def test_serial_and_parallel_merge_have_identical_content_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); inputs = {label: fixture(root, label) for label in ['right', 'left']}
            serial = analyze_assessments(inputs, workers=1)
            parallel = analyze_assessments(inputs, workers=2)
            self.assertEqual(serial['report_id'], parallel['report_id'])
            self.assertEqual(serial['assessments'], parallel['assessments'])
            self.assertEqual([r['assessment'] for r in serial['assessments']], ['left', 'right'])
            self.assertEqual(serial['assessments'][0]['case_seconds'], 2.)
            self.assertEqual(serial['assessments'][0]['checkpoint_export_bytes'], 200)

    def test_missing_record_and_wrong_candidate_are_rejected(self):
        for defect in ['missing', 'model', 'outcome', 'index']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); path = Path(fixture(root, 'one')); row = path/'0001-private.json'
                if defect == 'missing': row.unlink()
                else:
                    data = json.loads(row.read_text())
                    if defect == 'model': data['model_sha256'] = 'd'*64
                    if defect == 'outcome': data['passed'] = True
                    if defect == 'index': data['index'] = 0
                    row.write_text(json.dumps(data))
                with self.assertRaises(ValueError): analyze_assessments({'one': path})

    def test_incomplete_settlement_and_invalid_nested_times_are_rejected(self):
        for defect in ['settlement', 'nan', 'nested']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); path = Path(fixture(root, 'one'))
                if defect == 'settlement':
                    (path/'settlement.json').write_text(json.dumps(dict(status='FAILED')))
                else:
                    p = path/'0001-private.json'; data = json.loads(p.read_text())
                    if defect == 'nan': data['seconds'] = float('nan')
                    else: data['completion']['cow_receipt']['generation_seconds'] = 2.
                    p.write_text(json.dumps(data))
                with self.assertRaises(ValueError): analyze_assessments({'one': path})

    def test_read_only_reporting_does_not_change_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(fixture(Path(temp), 'one'))
            before = {f.name: f.read_bytes() for f in path.iterdir()}
            analyze_assessments({'one': path}, workers=1)
            self.assertEqual(before, {f.name: f.read_bytes() for f in path.iterdir()})


if __name__ == '__main__': unittest.main()
