"""Mixed 66-skill pack provenance and finite-domain controls."""
import unittest

from sss.adapters.foundation_training import build_pack,validate_pack
from sss.curriculum import foundation_graph
from sss.foundations import Exercise,check,reference


class Mixed66CurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph=foundation_graph()
        cls.skills=[key for key in graph.order if graph.nodes[key]['status']=='implemented']
        cls.pack=build_pack(cls.skills,seed=20261028,practice_per_gate=4,
                            checks_per_gate=2,generation_profile='mixed66-v1')

    def test_combined_pack_covers_all_and_references_pass(self):
        self.assertEqual(len(self.skills),66)
        self.assertEqual(set(self.pack['skills']),set(self.skills))
        self.assertEqual(len(self.pack['exercises']),1584)
        self.assertEqual(len(validate_pack(self.pack)),1584)
        for row in self.pack['exercises']:
            exercise=Exercise(**row)
            self.assertTrue(check(exercise,reference(exercise)),exercise.skill_id)

    def test_finite_boolean_overlap_is_disclosed_and_wordings_are_distinct(self):
        self.assertTrue(self.pack['finite_boolean_truth_inputs_shared_across_splits'])
        self.assertFalse(self.pack['semantic_disjointness_established'])
        rows=[r for r in self.pack['exercises'] if r['skill_id']=='logic.not' and r['gate']=='independent']
        practice={tuple(r['payload']['expression'][1:]) for r in rows if r['split']=='practice'}
        qualification={tuple(r['payload']['expression'][1:]) for r in rows if r['split']=='qualification'}
        self.assertEqual(practice,{(0,),(1,)})
        self.assertEqual(qualification,practice)
        self.assertFalse({r['prompt'] for r in rows if r['split']=='practice'} &
                         {r['prompt'] for r in rows if r['split']=='qualification'})

    def test_logic_composition_uses_boolean_operations(self):
        rows=[r for r in self.pack['exercises'] if r['skill_id']=='logic.and' and r['gate']=='composition']
        for row in rows:
            expression=row['payload']['expression']
            self.assertEqual(expression[0],'not')
            self.assertEqual(expression[1][0],'not')
            self.assertEqual(expression[1][1][0],'and')

    def test_deduction_split_structures_differ(self):
        rows=[r for r in self.pack['exercises'] if r['skill_id']=='logic.deduction' and r['gate']=='independent']
        shapes={split:{str(r['payload']['clauses']) for r in rows if r['split']==split}
                for split in ('practice','development','qualification')}
        self.assertTrue(shapes['practice'].isdisjoint(shapes['development']))
        self.assertTrue(shapes['practice'].isdisjoint(shapes['qualification']))
        self.assertTrue(shapes['development'].isdisjoint(shapes['qualification']))

    def test_finite_boolean_evaluation_refuses_exhaustion(self):
        with self.assertRaisesRegex(ValueError,'truth table exhausted'):
            build_pack(['logic.not'],seed=1,practice_per_gate=2,checks_per_gate=3,
                       generation_profile='mixed66-v1')


if __name__=='__main__':
    unittest.main()
