import unittest
from sss.curriculum import *
from sss.foundations import check,reference

class CurriculumTests(unittest.TestCase):
    def test_every_implemented_node_has_checked_variants(self):
        graph=foundation_graph()
        for key in BY_ID:
            for split in ('practice','development','qualification'):
                for gate in ('independent','composition','transfer_recovery'):
                    case=exercise_for(key,split,0,gate=gate)
                    self.assertTrue(check(case,reference(case)),(key,split,gate))
    def test_branch_gates_and_missing_coverage_are_honest(self):
        graph=foundation_graph();day=student_day(graph,[],0)
        self.assertFalse(graph.readiness('research.findings',[])['ready'])
        self.assertTrue(any(row['activity']=='coverage_unavailable' for row in day['schedule']))
        for row in day['schedule']:
            if row.get('skill_id'):self.assertTrue(graph.readiness(row['skill_id'],[])['ready'])
    def test_arithmetic_subskills(self):
        for key in ('math.add.no_carry','math.add.carry','math.subtract.no_borrow','math.subtract.borrow'):
            case=exercise_for(key,'qualification',3)
            a,b=case.payload['expression'][1:]
            aa=list(map(int,str(a).zfill(4)));bb=list(map(int,str(b).zfill(4)))
            if key.endswith('no_carry'):self.assertTrue(all(x+y<10 for x,y in zip(aa,bb)))
            elif key.endswith('carry'):self.assertTrue(all(x+y>=10 for x,y in zip(aa,bb)))
            elif key.endswith('no_borrow'):self.assertTrue(all(x>=y for x,y in zip(aa,bb)))
            else:self.assertTrue(any(x<y for x,y in zip(aa,bb)))
