import json
from pathlib import Path
import tempfile
import unittest
from sss.records import digest
from sss.studies.quantization import quantization_report
from sss_integration.quantization_report import collect


def measured(family, fmt, passes, finished=None):
    if finished is None:
        finished = [True]*len(passes)
    outcomes = [dict(id=str(i), skill_id='math.add', gate='independent', passed=p, finished=f)
                for i, (p, f) in enumerate(zip(passes, finished))]
    result = dict(status='COMPLETE', evaluation_id='a'*64, runtime_id='b'*64,
                  model_sha256=digest([family, fmt]), cases=len(passes), passed=sum(passes),
                  finished=sum(finished), outcomes=outcomes, weights_updated=False, promoted=False)
    return dict(family=family, format=fmt, bytes=100 if fmt == 'F32' else 50, result=result)


class QuantizationTests(unittest.TestCase):
    def test_net_one_loss_reports_both_changed_directions(self):
        rows = [measured('original', 'F32', [True, False, False, False]),
                measured('original', 'F16', [True, False, False, False]),
                measured('trained', 'F32', [True, True, True, False]),
                measured('trained', 'F16', [False, True, False, True])]
        report = quantization_report(rows, ['F32', 'F16'])
        self.assertEqual(report['status'], 'COMPLETE')
        row = report['rows'][-1]
        self.assertEqual((row['versus_own_F32']['answer_gains'], row['versus_own_F32']['answer_losses']), (1, 2))
        self.assertEqual((row['versus_original_same_format']['answer_gains'], row['versus_original_same_format']['answer_losses']), (2, 1))
        self.assertNotIn('outcomes', json.dumps(report))
        self.assertFalse(report['promoted'])

    def test_partial_and_completion_are_explicit(self):
        row = measured('original', 'F16', [True, False], [False, True])
        report = quantization_report([row], ['F32', 'F16', 'Q4_K_M'])
        self.assertEqual((report['measured_variants'], report['expected_variants']), (1, 6))
        self.assertEqual(report['status'], 'IN_PROGRESS')
        self.assertEqual(sum(r['status'] == 'UNMEASURED' for r in report['rows']), 5)
        self.assertNotIn('versus_own_F32', report['rows'][2])

    def test_refuse_mixed_runtime_cases_and_inconsistent_counts(self):
        row = measured('original', 'F32', [True, False])
        for key, value in [('runtime_id', 'e'*64), ('evaluation_id', 'e'*64), ('passed', 2), ('status', 'FAILED')]:
            other = measured('trained', 'F32', [True, False])
            other['result'][key] = value
            with self.assertRaises(ValueError): quantization_report([row, other], ['F32'])
        other = measured('trained', 'F32', [True, False]);other['result']['outcomes'][0]['id'] = 'different'
        with self.assertRaises(ValueError): quantization_report([row, other], ['F32'])

    def test_duplicate_unknown_and_invalid_declarations_refused(self):
        row = measured('original', 'F32', [True])
        for rows, formats in [([row, row], ['F32']), ([dict(row, bytes=True)], ['F32']),
                              ([dict(row, format='Q8')], ['F32']), ([], ['F32']),
                              ([row], ['F32', 'F32']), ([row], ['F16'])]:
            with self.assertRaises(ValueError): quantization_report(rows, formats)

    def test_actual_file_collection_refuses_changed_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);row = measured('original', 'F32', [True, False]);result = row['result']
            summary = dict(result, family=row['family'], format=row['format'], bytes=row['bytes'])
            (root/'original-F32').mkdir()
            (root/'original-F32/result.json').write_text(json.dumps(result))
            path = root/'original-F32-summary.json';path.write_text(json.dumps(summary))
            report = collect(root, ['F32', 'F16'])
            self.assertEqual(len(report['source_sha256']), 2)
            self.assertEqual(report['report_id'], digest({k:v for k,v in report.items() if k != 'report_id'}))
            summary['passed'] = 0;path.write_text(json.dumps(summary))
            with self.assertRaises(ValueError): collect(root, ['F32', 'F16'])

    def test_failed_inference_is_visible_without_a_model_score(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);row = measured('original', 'F32', [True, False]);result = row['result']
            (root/'original-F32').mkdir()
            (root/'original-F32/result.json').write_text(json.dumps(result))
            (root/'original-F32-summary.json').write_text(json.dumps(dict(result, family='original', format='F32', bytes=100)))
            (root/'trained-F32-summary.json').write_text(json.dumps(dict(family='trained', format='F32', status='INFRASTRUCTURE_INCOMPLETE')))
            report = collect(root, ['F32', 'F16'])
            self.assertEqual(report['status'], 'INCOMPLETE')
            self.assertEqual(report['rows'][1]['status'], 'INFRASTRUCTURE_INCOMPLETE')
            self.assertNotIn('passed', report['rows'][1])


if __name__ == '__main__':
    unittest.main()
