import copy
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import unittest

from sss.adapters.foundation_training import build_pack, validate_pack
from sss.curriculum_unique_v2 import unique_exercise_for
from sss.foundations import check, reference
from sss.records import digest


SKILLS = ['math.add.carry', 'math.add.no_carry', 'math.add.signed', 'math.divide',
          'math.fraction', 'math.fraction.add', 'math.multiply', 'math.place_value', 'state.registers']


class FractionUniqueV2Tests(unittest.TestCase):
    def test_original_collision_is_refused_and_new_profile_covers_entire_mixed_panel(self):
        with self.assertRaisesRegex(ValueError, 'Repeated frozen question'):
            build_pack(SKILLS, seed=2026102601, practice_per_gate=2, checks_per_gate=32,
                       generation_profile='without-replacement-v1')
        pack = build_pack(SKILLS, seed=2026102601, practice_per_gate=2, checks_per_gate=32,
                          generation_profile='without-replacement-v2')
        cases = validate_pack(pack)
        self.assertEqual(len(cases), 1782)
        self.assertEqual(len({e.prompt for e in cases}), len(cases))
        self.assertTrue(all(check(e, reference(e)) for e in cases))
        self.assertEqual(len([e for e in cases if e.split == 'development']), 864)
        self.assertFalse(pack['formal_mastery_qualification'])
        self.assertEqual(set(pack['generation_sources_sha256']), {'curriculum_unique.py', 'curriculum_unique_v2.py'})
        changed = copy.deepcopy(pack)
        changed['generation_sources_sha256']['curriculum_unique.py'] = '0' * 64
        changed['pack_id'] = digest({k: v for k, v in changed.items() if k != 'pack_id'})
        with self.assertRaisesRegex(ValueError, 'frozen generator'):
            validate_pack(changed)

    def test_fraction_permutation_is_injective_and_split_operands_are_disjoint(self):
        for size in (40, 60, 180):
            self.assertEqual(math.gcd(7919, size * size), 1)
        for seed in (0, 2026102601, -7):
            operands = {}
            for split in ('practice', 'development', 'qualification'):
                rows = [unique_exercise_for('math.fraction', split, i, gate=g, seed=seed)
                        for g in ('independent', 'composition', 'transfer_recovery') for i in range(128)]
                pairs = {(e.payload['n'], e.payload['d']) for e in rows}
                self.assertEqual(len(pairs), 384)
                self.assertTrue(all(e.payload['d'] != 0 for e in rows))
                self.assertTrue(all(check(e, reference(e)) for e in rows))
                for e in rows:
                    answer = reference(e)
                    if e.gate == 'transfer_recovery':
                        answer = json.loads(answer)['answer']
                    self.assertEqual(Fraction(answer), Fraction(e.payload['n'], e.payload['d']))
                operands[split] = {v for pair in pairs for v in pair}
            self.assertFalse(operands['practice'] & operands['development'])
            self.assertFalse(operands['practice'] & operands['qualification'])
            self.assertFalse(operands['development'] & operands['qualification'])
        with self.assertRaises(ValueError):
            unique_exercise_for('math.fraction', 'practice', 128)


if __name__ == '__main__':
    unittest.main()
