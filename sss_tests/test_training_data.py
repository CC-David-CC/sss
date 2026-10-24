import copy,unittest
from sss.records import digest
from sss.adapters.training_data import validate_training_document,validate_optimizer_program

def document(kind,key):
    d=dict(schema=1,purpose=kind,model_sha256='b'*64,model_contract_id='c'*64,
           protected_cases_exported=False,target_policy='actions_answer',
           examples=[dict(id='a'*64,verified=True)],selection=[dict(lesson_id='a'*64)])
    d[key]=digest(d);return d
class TrainingDocumentTests(unittest.TestCase):
 def test_distinct_identity_kinds_are_verified_and_detached(self):
  for kind,key in [('actual_model_optimizer_mechanics_pilot','pilot_id'),('fixed_compute_optimizer_study_practice','practice_id')]:
   d=document(kind,key);result=validate_training_document(d);self.assertEqual(result['identity_field'],key)
   d['examples'][0]['verified']=False;self.assertTrue(result['examples'][0]['verified'])
 def test_rehashed_protected_or_misaligned_material_is_still_refused(self):
  for change in [dict(protected_cases_exported=True),dict(target_policy='unverified_thoughts'),dict(selection=[dict(lesson_id='x')])]:
   d=document('fixed_compute_optimizer_study_practice','practice_id');d.update(change);d['practice_id']=digest({k:v for k,v in d.items() if k!='practice_id'})
   with self.assertRaises(ValueError):validate_training_document(d)
 def test_aliasing_or_changed_identity_cannot_be_used_as_another_kind(self):
  d=document('fixed_compute_optimizer_study_practice','practice_id');d['pilot_id']=d['practice_id']
  with self.assertRaises(ValueError):validate_training_document(d)
  d=document('fixed_compute_optimizer_study_practice','practice_id');d['examples'][0]['id']='changed'
  with self.assertRaises(ValueError):validate_training_document(d)
def study():
 d=document('fixed_compute_optimizer_study_practice','practice_id');d['pack_id']='d'*64
 d['examples']=[];d['selection']=[]
 # Source admission is gate-major; execution must explicitly interleave it.
 for gate in ('independent','composition','transfer_recovery'):
  for skill in ('skill_z','skill_a'):
   for n in range(2):
    name=skill+'_'+gate+'_'+str(n)
    d['examples'].append(dict(id=name,verified=True))
    d['selection'].append(dict(lesson_id=name,skill_id=skill,gate=gate))
 d['practice_id']=digest({k:v for k,v in d.items() if k!='practice_id'})
 order=[skill+'_'+gate+'_'+str(n) for n in range(2) for skill in ('skill_z','skill_a') for gate in ('independent','composition','transfer_recovery')]
 p=dict(schema=1,kind='sss.optimizer-learning-program.v1',practice_id=d['practice_id'],pack_id=d['pack_id'],model_sha256=d['model_sha256'],ordering='round-skill-gate-v1',ordered_example_ids=order,batch_size=6,training_budget_seconds=300.,step_cap=1000,arms=[dict(id='control',optimizer='adamw',learning_rate=1e-6,settings=dict(schema=1))])
 p['program_id']=digest(p);return p,d
class OptimizerProgramTests(unittest.TestCase):
 def test_every_update_interleaves_every_skill_and_gate(self):
  p,d=study();v=validate_optimizer_program(p,d,'control')
  self.assertEqual([e['id'] for e in v['examples']],p['ordered_example_ids']);self.assertEqual(v['batch_size'],6)
  p['arms'][0]['settings']['schema']=9;self.assertEqual(v['arm']['settings']['schema'],1)
 def test_omitted_repeated_or_wrongly_interleaved_occurrences_refused(self):
  for transform in [lambda p:p['ordered_example_ids'].pop(),lambda p:p['ordered_example_ids'].__setitem__(0,p['ordered_example_ids'][1]),lambda p:p.update(ordered_example_ids=sorted(p['ordered_example_ids']))]:
   p,d=study();transform(p);p['program_id']=digest({k:v for k,v in p.items() if k!='program_id'})
   with self.assertRaises(ValueError):validate_optimizer_program(p,d,'control')
 def test_program_is_pinned_to_admitted_model_pack_and_practice(self):
  for key in ('practice_id','pack_id','model_sha256'):
   p,d=study();p[key]='e'*64;p['program_id']=digest({k:v for k,v in p.items() if k!='program_id'})
   with self.assertRaises(ValueError):validate_optimizer_program(p,d,'control')
  p,d=study();p['training_budget_seconds']=299.
  with self.assertRaises(ValueError):validate_optimizer_program(p,d,'control')
 def test_partial_gate_review_or_invalid_budget_cannot_be_rehashed_into_validity(self):
  for change in [dict(batch_size=3),dict(training_budget_seconds=True),dict(training_budget_seconds=3600.),dict(step_cap=0)]:
   p,d=study();p.update(change);p['program_id']=digest({k:v for k,v in p.items() if k!='program_id'})
   with self.assertRaises(ValueError):validate_optimizer_program(p,d,'control')
 def test_unregistered_or_duplicate_arm_refused(self):
  p,d=study()
  with self.assertRaises(ValueError):validate_optimizer_program(p,d,'invented')
  p['arms']*=2;p['program_id']=digest({k:v for k,v in p.items() if k!='program_id'})
  with self.assertRaises(ValueError):validate_optimizer_program(p,d,'control')
if __name__=='__main__':unittest.main()

