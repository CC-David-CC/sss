import json,unittest
from sss.research import experiment,finding,check_finding
from sss.worlds import LaneWorld

class ResearchWorlds(unittest.TestCase):
    def test_controls_counterexample_and_reproduction(self):
        rows=[experiment(907,128,n) for n in (1,2,64)]
        answer=finding(rows)
        self.assertTrue(answer['universal_claim_refuted']);self.assertTrue(answer['indexed_wins'])
        self.assertTrue(check_finding(rows,json.dumps(answer)))
        answer['established']='Always faster'
        self.assertFalse(check_finding(rows,json.dumps(answer)))
        rows[0]['linear_cost']=0
        with self.assertRaises(ValueError):finding(rows)
    def test_timing_is_separate_from_correct_action(self):
        w=LaneWorld('owned-env',True);obs=w.observe(1)
        _,fast=w.act(obs,'left',20);_,slow=w.act(obs,'left',101)
        self.assertTrue(fast['passed']);self.assertTrue(slow['collision_free']);self.assertFalse(slow['on_time'])
        with self.assertRaises(ValueError):LaneWorld('not-ready',False).observe(0)
        with self.assertRaises(ValueError):w.act(dict(obs,step=99),'left',20)
