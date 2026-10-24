import copy,unittest
from sss.learning import next_skill_block
from sss_tests.test_paired import evidence

class NextBlockTests(unittest.TestCase):
 def test_four_forward_one_back_is_a_working_parent_and_repair_not_discard(self):
  a=evidence([(True,True)]+[(False,False)]*4);b=evidence([(False,True)]+[(True,True)]*4);b['model_sha256']='d'*64
  r=next_skill_block(a,a,b);self.assertEqual(r['working_decision'],'KEEP_AND_REPAIR');self.assertTrue(r['preserve_candidate']);self.assertEqual(r['next_parent_sha256'],b['model_sha256']);self.assertEqual(r['strict_preservation_status'],'REJECTED');self.assertEqual(r['parent_answer_delta'],3);self.assertFalse(r['promoted'])
  self.assertNotIn('outcomes',r);self.assertNotIn('id',r['repair_groups'][0])
 def test_cumulative_losses_do_not_disappear_when_immediate_parent_also_failed(self):
  a=evidence([(True,True),(False,False),(False,False)]);b=evidence([(False,True),(True,True),(False,False)]);c=evidence([(False,True),(True,True),(True,True)])
  r=next_skill_block(a,b,c);self.assertEqual(r['parent_answer_losses'],0);self.assertEqual(r['baseline_answer_losses'],1);self.assertEqual(r['working_decision'],'KEEP_AND_REPAIR')
 def test_no_gain_does_not_replace_parent(self):
  a=evidence([(True,True),(False,False)]);r=next_skill_block(a,a,a);self.assertEqual(r['working_decision'],'RETAIN_PARENT');self.assertFalse(r['preserve_candidate'])
 def test_review_keeps_every_skill_gate_and_forward_learning_remains_visible(self):
  a=evidence([(False,False),(False,False)]);a['outcomes'][1].update(skill_id='state.registers',gate='composition');b=copy.deepcopy(a);b['outcomes'][0].update(passed=True,finished=True);b.update(passed=1,finished=1)
  r=next_skill_block(a,a,b);self.assertEqual(len(r['review_groups']),2);self.assertEqual(r['forward_learning_groups'][0]['skill_id'],'state.registers')
 def test_changed_runtime_cannot_be_called_a_training_gain(self):
  a=evidence([(False,False)]);b=evidence([(True,True)]);b['runtime_id']='e'*64
  with self.assertRaises(ValueError):next_skill_block(a,a,b)
if __name__=='__main__':unittest.main()
