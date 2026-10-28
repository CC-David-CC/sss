"""Paired learning evidence must name the actual hat, not just its base file."""
import copy
import unittest
from sss.paired import compare_frozen_evaluations,POLICY
from sss_tests.test_paired import evidence

class CompositePairedTests(unittest.TestCase):
    def bound(self,rows,contract,adapters):
        result=evidence(rows)
        result.update(candidate_model_contract_id=contract,candidate_adapters=adapters)
        return result

    def test_same_base_different_hats_remain_identified_in_the_assessment(self):
        a=self.bound([(False,False)],'d'*64,[dict(sha256='e'*64,scale=1.)])
        b=self.bound([(True,True)],'f'*64,[dict(sha256='0'*64,scale=.5)])
        self.assertEqual(a['model_sha256'],b['model_sha256'])
        result=compare_frozen_evaluations(a,b,POLICY)
        self.assertEqual(result['baseline_candidate_model_contract_id'],'d'*64)
        self.assertEqual(result['candidate_model_contract_id'],'f'*64)
        self.assertEqual(result['baseline_candidate_adapters'],a['candidate_adapters'])
        self.assertEqual(result['candidate_adapters'],b['candidate_adapters'])
        self.assertEqual(result['answer_gains'],1)
        self.assertFalse(result['promoted']);self.assertTrue(result['sealed_qualification_required'])
        b['candidate_adapters'][0]['scale']=2.
        self.assertEqual(result['candidate_adapters'][0]['scale'],.5)

    def test_partial_or_malformed_composite_evidence_is_not_a_model_failure(self):
        a=self.bound([(False,False)],'d'*64,[])
        for defect in ('partial','identity','scale','unbound'):
            b=copy.deepcopy(a)
            if defect=='partial':b.pop('candidate_model_contract_id');b.pop('candidate_adapters')
            if defect=='identity':b['candidate_model_contract_id']='bad'
            if defect=='scale':b['candidate_adapters']=[dict(sha256='e'*64,scale=float('nan'))]
            if defect=='unbound':b.pop('candidate_model_contract_id')
            with self.subTest(defect=defect),self.assertRaises(ValueError):compare_frozen_evaluations(a,b,POLICY)

    def test_one_contract_cannot_name_different_weights_hat_or_scale(self):
        a=self.bound([(False,False)],'d'*64,[dict(sha256='e'*64,scale=1.)])
        for defect in ('base','hat','scale'):
            b=copy.deepcopy(a)
            if defect=='base':b['model_sha256']='f'*64
            if defect=='hat':b['candidate_adapters'][0]['sha256']='0'*64
            if defect=='scale':b['candidate_adapters'][0]['scale']=.5
            with self.subTest(defect=defect),self.assertRaises(ValueError):compare_frozen_evaluations(a,b,POLICY)

    def test_legacy_base_only_comparisons_keep_their_existing_shape_and_policy(self):
        a=evidence([(True,True),(False,False)]);b=evidence([(False,True),(True,True)])
        result=compare_frozen_evaluations(a,b,POLICY)
        self.assertNotIn('candidate_model_contract_id',result)
        self.assertEqual(result['status'],'REJECTED');self.assertEqual(result['answer_losses'],1)

if __name__=='__main__':unittest.main()
