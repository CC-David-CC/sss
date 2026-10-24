from dataclasses import replace
import unittest

from sss.curriculum import exercise_for
from sss.foundations import check, reference
from sss.studies.paired_rates import failure_rate, paired_rates


class PairedRateTests(unittest.TestCase):
    def test_wilson_known_middle_and_endpoint_intervals(self):
        low, high = failure_rate(16, 32)['wilson_95']
        self.assertAlmostEqual(low, 0.3363088287, places=8)
        self.assertAlmostEqual(high, 0.6636911713, places=8)
        self.assertAlmostEqual(failure_rate(0, 100)['wilson_95'][1], 0.0369934982, places=8)
        self.assertAlmostEqual(failure_rate(100, 100)['wilson_95'][0], 0.9630065018, places=8)
        for bad in ((0, 0), (-1, 2), (3, 2), (True, 2)):
            with self.assertRaises(ValueError): failure_rate(*bad)

    def test_paired_direction_and_exact_small_sample_probability(self):
        baseline = dict(a=False, b=False, c=False, d=True, e=True)
        candidate = dict(a=True, b=True, c=True, d=False, e=True)
        result = paired_rates(baseline, candidate)
        self.assertEqual((result['newly_correct'], result['newly_wrong']), (3, 1))
        self.assertEqual(result['mcnemar_exact_two_sided_p'], 0.625)
        self.assertEqual(result['failure_rate_change'], -0.4)
        self.assertEqual(paired_rates(dict(a=True), dict(a=True))['mcnemar_exact_two_sided_p'], 1.)
        self.assertEqual(paired_rates(dict(a=True), dict(a=False))['mcnemar_exact_two_sided_p'], 1.)
        with self.assertRaises(ValueError): paired_rates(dict(a=True), dict(b=True))
        with self.assertRaises(ValueError): paired_rates(dict(a=1), dict(a=True))

    def test_place_value_composition_requires_computing_an_unstated_number(self):
        for index in range(32):
            e = exercise_for('math.place_value', 'development', index, gate='composition', seed=20261023)
            self.assertIn('expression', e.payload)
            self.assertIn('First evaluate', e.prompt)
            self.assertNotIn(' in ' + str(e.payload['n']) + ';', e.prompt)
            self.assertTrue(check(e, reference(e)))
            bad = replace(e, payload=dict(e.payload, n=e.payload['n']+1))
            self.assertFalse(check(bad, reference(e)))


if __name__ == '__main__':
    unittest.main()
