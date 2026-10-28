import copy,unittest
from sss.paired import compare_frozen_evaluations,POLICY

def evidence(outcomes):
 rows=[dict(id=str(i),skill_id='math.add',gate='independent',passed=p,finished=f) for i,(p,f) in enumerate(outcomes)]
 return dict(status='COMPLETE',evaluation_id='a'*64,runtime_id='b'*64,model_sha256='c'*64,cases=len(rows),passed=sum(r['passed'] for r in rows),finished=sum(r['finished'] for r in rows),outcomes=rows,weights_updated=False,promoted=False)
class PairedTests(unittest.TestCase):
 def test_higher_total_cannot_hide_lost_prior_success(self):
  a=evidence([(True,True),(False,False),(False,False)]);b=evidence([(False,True),(True,True),(True,True)])
  r=compare_frozen_evaluations(a,b,POLICY);self.assertEqual(r['status'],'REJECTED');self.assertEqual(r['answer_gains'],2);self.assertEqual(r['answer_losses'],1)
 def test_completion_is_separate_and_no_result_promotes(self):
  a=evidence([(True,False)]);b=evidence([(True,True)]);r=compare_frozen_evaluations(a,b,POLICY)
  self.assertEqual(r['status'],'DEVELOPMENT_ELIGIBLE');self.assertEqual(r['answer_gains'],0);self.assertEqual(r['completion_gains'],1);self.assertFalse(r['promoted']);self.assertTrue(r['sealed_qualification_required'])
  self.assertEqual(compare_frozen_evaluations(b,a,POLICY)['status'],'REJECTED')
 def test_unchanged_candidate_has_not_learned(self):
  a=evidence([(True,True),(False,False)]);self.assertEqual(compare_frozen_evaluations(a,a,POLICY)['status'],'REJECTED')
 def test_missing_duplicate_or_inconsistent_results_are_invalid_not_model_failures(self):
  a=evidence([(True,True),(False,False)])
  for change in [dict(status='FAILED'),dict(cases=1),dict(passed=0),dict(outcomes=[a['outcomes'][0]]*2),dict(outcomes=a['outcomes'][:1])]:
   b=copy.deepcopy(a);b.update(change)
   with self.assertRaises(ValueError):compare_frozen_evaluations(a,b,POLICY)
 def test_changed_checker_cases_gates_or_policy_refuse_comparison(self):
  a=evidence([(True,True)])
  for key in ('evaluation_id','runtime_id'):
   b=copy.deepcopy(a);b[key]='e'*64
   with self.assertRaises(ValueError):compare_frozen_evaluations(a,b,POLICY)
  for key,value in [('gate','composition'),('id','other'),('finished',1)]:
   b=copy.deepcopy(a);b['outcomes'][0][key]=value
   with self.assertRaises(ValueError):compare_frozen_evaluations(a,b,POLICY)
  with self.assertRaises(ValueError):compare_frozen_evaluations(a,a,dict(POLICY,preserve_every_answer_pass=False))
if __name__=='__main__':unittest.main()
