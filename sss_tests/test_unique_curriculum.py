import unittest
from pathlib import Path
import json
from sss.adapters.foundation_training import build_pack, validate_pack
from sss.foundations import check, reference
from sss.curriculum_unique import unique_exercise_for

class UniqueCurriculumTests(unittest.TestCase):
 def test_legacy_pilot_identity_is_preserved_and_extended_counts_are_explicit(self):
  manifest=json.loads((Path(__file__).resolve().parents[1]/'examples/finished-training-examples/minicpm-optimizer-pilot/manifest.json').read_text())
  pack=build_pack(['math.add.carry','math.subtract.borrow'],seed=0,practice_per_gate=2,checks_per_gate=1)
  self.assertEqual(pack['pack_id'],manifest['pack_id'])
  with self.assertRaises(ValueError):build_pack(['math.multiply'],seed=0,checks_per_gate=32)
 def test_all_96_per_skill_checks_are_distinct_and_pass_independent_references(self):
  pack=build_pack(['math.add.carry','math.fraction.add','state.registers'],seed=20261024,practice_per_gate=32,checks_per_gate=32,generation_profile='without-replacement-v1')
  cases=validate_pack(pack)
  protected=[c for c in cases if c.split!='practice']
  self.assertEqual(len(protected),1728)
  self.assertEqual(len({c.prompt for c in protected}),1728)
  self.assertFalse({c.prompt for c in cases if c.split=='practice'} & {c.prompt for c in protected})
  self.assertTrue(all(check(c,reference(c)) for c in cases))
  changed=dict(pack,generation_source_sha256='0'*64)
  from sss.records import digest
  changed['pack_id']=digest({k:v for k,v in changed.items() if k!='pack_id'})
  with self.assertRaisesRegex(ValueError,'frozen generator'):validate_pack(changed)
 def test_finite_families_refuse_exhaustion_instead_of_repeating(self):
  with self.assertRaisesRegex(ValueError,'exhausted'):unique_exercise_for('math.place_value','practice',100)
  with self.assertRaises(ValueError):build_pack(['math.multiply'],seed=0,checks_per_gate=33,generation_profile='without-replacement-v1')

if __name__=='__main__':unittest.main()
