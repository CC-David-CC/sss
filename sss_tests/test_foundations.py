import json
import unittest
from sss.foundations import *

class FoundationTests(unittest.TestCase):
    def test_reference_and_corrupt_answers_all_families(self):
        for kind in OPERATORS+SPECIAL:
            for split in SPLITS:
                for gate in ('independent','composition','transfer_recovery'):
                    for index in range(4):
                        case=generate(kind,split,index,gate=gate)
                        answer=reference(case)
                        with self.subTest(kind=kind,split=split,gate=gate,index=index):
                            self.assertTrue(check(case,answer),answer)
                            self.assertFalse(check(case,'999999999999999999999'))
                            self.assertFalse(check(case,'{"__claim__":"passed"}'))
    def test_semantic_equivalence_and_limits(self):
        case=generate('divide','practice',0)
        answer=number(reference(case))
        self.assertTrue(check(case,f'{answer.numerator*17}/{answer.denominator*17}'))
        self.assertFalse(check(case,'1/0'))
        self.assertFalse(check(case,'1'*70000))
        with self.assertRaises(ValueError):generate('add','blind-pretending-to-be-practice',0)
    def test_proof_kernel_rejects_circular_and_invented_assumptions(self):
        case=generate('proof','qualification',0)
        self.assertFalse(check(case,json.dumps([dict(assumption=999)])))
        self.assertFalse(check(case,json.dumps([dict(mp=[0,0])])) )
        steps=json.loads(reference(case));steps[-1]={'axiom':case.payload['conclusion']}
        self.assertFalse(check(case,json.dumps(steps)))
    def test_independent_known_results_and_edge_cases(self):
        fixture=lambda kind,p:Exercise('f',kind,'practice','f','t','independent',p,'fixed')
        self.assertTrue(check(fixture('round',dict(n=-125,d=100,places=1)),'-1.3'))
        self.assertFalse(check(fixture('round',dict(n=-125,d=100,places=1)),'-1.2'))
        self.assertTrue(check(fixture('definite_integral',dict(coefficients=[0,0,0,1],a=-2,b=3)),'65/4'))
        self.assertTrue(check(fixture('variance',dict(values=[1,2,3])),'2/3'))
        self.assertFalse(check(fixture('linear_system',dict(matrix=[[2,1],[1,-1]],rhs=[5,1])),'[1,3]'))
        self.assertTrue(check(fixture('linear_system',dict(matrix=[[2,1],[1,-1]],rhs=[5,1])),'[2,1]'))
    def test_splits_are_reproducible_and_distinct(self):
        ids={generate('add',s,i).identity for s in SPLITS for i in range(10)}
        self.assertEqual(len(ids),30)
        self.assertEqual(generate('add','practice',1).identity,generate('add','practice',1).identity)
