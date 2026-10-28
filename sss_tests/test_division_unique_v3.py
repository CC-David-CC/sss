import copy
import math
import unittest

from sss.adapters.foundation_training import build_pack, validate_pack
from sss.curriculum_unique_v2 import unique_exercise_for as previous
from sss.curriculum_unique_v3 import unique_exercise_for
from sss.foundations import check, reference
from sss.records import digest

SKILLS = ['math.add.carry', 'math.add.no_carry', 'math.add.signed', 'math.divide',
          'math.fraction', 'math.fraction.add', 'math.multiply', 'math.place_value', 'state.registers']


class DivisionUniqueV3Tests(unittest.TestCase):
    def test_recorded_v2_refusal_remains_and_v3_admits_the_same_seed(self):
        with self.assertRaisesRegex(ValueError, 'Repeated frozen question'):
            build_pack(SKILLS, seed=2026102603, practice_per_gate=2, checks_per_gate=32,
                       generation_profile='without-replacement-v2')
        pack = build_pack(SKILLS, seed=2026102603, practice_per_gate=2, checks_per_gate=32,
                          generation_profile='without-replacement-v3')
        cases = validate_pack(pack)
        self.assertEqual(len(cases), 1782)
        self.assertEqual(len({c.prompt for c in cases}), len(cases))
        self.assertEqual(sum(c.split == 'development' for c in cases), 864)
        self.assertTrue(all(check(c, reference(c)) for c in cases))
        self.assertEqual(set(pack['generation_sources_sha256']),
                         {'curriculum_unique.py', 'curriculum_unique_v2.py', 'curriculum_unique_v3.py'})
        changed = copy.deepcopy(pack)
        changed['generation_sources_sha256']['curriculum_unique_v3.py'] = '0' * 64
        changed['pack_id'] = digest({k: v for k, v in changed.items() if k != 'pack_id'})
        with self.assertRaisesRegex(ValueError, 'frozen generator'):
            validate_pack(changed)

    def test_all_division_ordinals_are_unique_and_keep_split_operands_separate(self):
        for size in [40, 60, 180]:
            self.assertEqual(math.gcd(7919, size ** 2), 1)
        for seed in [0, -7, 2026102603]:
            operands = {}
            for split in ['practice', 'development', 'qualification']:
                cases = [unique_exercise_for('math.divide', split, index, gate=gate, seed=seed)
                         for gate in ['independent', 'composition', 'transfer_recovery']
                         for index in range(128)]
                pairs = []
                for case in cases:
                    expression = case.payload['expression']
                    if case.gate == 'composition':
                        expression = expression[1][1]
                    self.assertEqual(expression[0], 'divide')
                    self.assertNotEqual(expression[2], 0)
                    pairs.append(tuple(expression[1:]))
                    self.assertTrue(check(case, reference(case)))
                self.assertEqual(len(set(pairs)), 384)
                self.assertEqual(len({c.prompt for c in cases}), 384)
                operands[split] = {n for pair in pairs for n in pair}
            for left, right in [('practice', 'development'), ('practice', 'qualification'),
                                ('development', 'qualification')]:
                self.assertFalse(operands[left] & operands[right])

    def test_nondivision_questions_are_not_migrated(self):
        for skill in [s for s in SKILLS if s != 'math.divide']:
            for gate in ['independent', 'composition', 'transfer_recovery']:
                self.assertEqual(unique_exercise_for(skill, 'development', 7, gate=gate, seed=2026102603),
                                 previous(skill, 'development', 7, gate=gate, seed=2026102603))

    def test_bounds_refuse_instead_of_redrawing(self):
        for index in [-1, 128, True]:
            with self.assertRaises(ValueError):
                unique_exercise_for('math.divide', 'practice', index)


if __name__ == '__main__':
    unittest.main()
