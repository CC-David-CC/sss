import copy
import unittest
from sss.graph import SkillGraph
from sss.mastery import *
from sss.profiles import *

class GraphTests(unittest.TestCase):
    def document(self):
        return dict(schema=2,name='fixture',nodes=[dict(id=k,title=k,domains=['math'],requires=req,bands=['small'],checker='integer',status='implemented') for k,req in [('add',[]),('mul',[]),('compose',['add','mul'])]])
    def test_convergence_and_no_global_barrier(self):
        graph=SkillGraph(self.document())
        self.assertTrue(graph.readiness('add',[])['ready'])
        self.assertEqual(graph.readiness('compose',['add'])['missing'],['mul'])
        self.assertTrue(graph.readiness('compose',['mul','add'])['ready'])
    def test_cycles_missing_and_duplicates(self):
        for kind in ('cycle','missing','duplicate'):
            doc=self.document()
            if kind=='cycle':doc['nodes'][0]['requires']=['compose']
            elif kind=='missing':doc['nodes'][0]['requires']=['unknown']
            else:doc['nodes'].append(doc['nodes'][0])
            with self.assertRaises(ValueError):SkillGraph(doc)
    def test_profile_modes_separate(self):
        base=dict(model_id='wen',model_revision='sha',tokenizer_id='tok',template_id='tpl',harness_id='bw',harness_revision='rev')
        self.assertNotEqual(ModelProfile(**base).identity,ModelProfile(**base,thinking='on').identity)
        policy=ContextPolicy()
        self.assertTrue(policy.check(98304,4096)['compact_required'])
        self.assertFalse(policy.check(130000,2048)['admitted'])
    def test_training_selection_not_inference_selection(self):
        rows=[dict(role='user',kind='question',verified=False),dict(role='assistant',kind='thinking',verified=True),dict(role='assistant',kind='answer',verified=True)]
        self.assertEqual(target_segments(rows),[False,True,True])
        self.assertEqual(target_segments(rows,'actions_answer'),[False,False,True])
        rows[1]['verified']=False
        with self.assertRaises(ValueError):target_segments(rows)
        self.assertEqual(target_segments(rows,'actions_answer'),[False,False,True])

class MasteryTests(unittest.TestCase):
    def suite(self):
        cases=[dict(id=f'{g}-{i}',purpose='qualification',gate=g,trial_id=str(i),family_id='frozen-owned') for g in GATES for i in range(256)]
        cases += [dict(id='guard',purpose='critical',gate='guard',trial_id='g',family_id='guard'),dict(id='old',purpose='retention',gate='guard',trial_id='o',family_id='old')]
        return QualificationSuite('graph','profile','addition','small',cases)
    def outcomes(self,suite):return [dict(case_id=k,status='pass',evidence_sha256='a'*64,suite_id=suite.identity) for k in suite.cases]
    def test_exact_bounds(self):
        self.assertAlmostEqual(lower_bound(256,256),(.05/3)**(1/256),places=12)
        self.assertGreater(lower_bound(251,256),.95)
        self.assertLess(lower_bound(250,256),.95)
        self.assertAlmostEqual(binomial_survival(2,3,.5),.5)
    def test_all_gates_and_critical_veto(self):
        suite=self.suite();rows=self.outcomes(suite)
        self.assertTrue(suite.assess(rows)['qualified'])
        for row in rows[:5]:row['status']='fail'
        self.assertTrue(suite.assess(rows)['qualified'])
        rows[5]['status']='fail'
        self.assertFalse(suite.assess(rows)['qualified'])
        rows=self.outcomes(suite);rows[-2]['status']='fail'
        self.assertFalse(suite.assess(rows)['qualified'])
    def test_missing_infra_wrong_binding_retention(self):
        suite=self.suite();rows=self.outcomes(suite)
        self.assertEqual(suite.assess(rows[:-1])['status'],'insufficient_evidence')
        rows[-1]['status']='fail';self.assertEqual(suite.assess(rows)['status'],'regressed')
        rows[-1]['status']='unavailable';self.assertEqual(suite.assess(rows)['status'],'unavailable')
        rows[-1]['suite_id']='other'
        with self.assertRaises(ValueError):suite.assess(rows)
    def test_duplicate_evidence_and_trial(self):
        suite=self.suite();rows=self.outcomes(suite)
        with self.assertRaises(ValueError):suite.assess(rows+[rows[0]])
        cases=list(suite.cases.values());cases[1]=dict(cases[1],trial_id=cases[0]['trial_id'])
        with self.assertRaises(ValueError):QualificationSuite('g','p','s','b',cases)
