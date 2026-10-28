import unittest
from sss.primitive_rewrite import cases,expected
from sss.foundations import check

class PrimitiveRewriteTests(unittest.TestCase):
    def test_all_references_and_distinct_tasks(self):
        for skill,count in [('logic.and',4),('logic.or',4),('logic.xor',4),('logic.not',2),('math.round',8),('logic.deduction',4)]:
            rows=cases(skill)
            self.assertEqual(len(rows),count)
            self.assertEqual(len({r.prompt for r in rows}),count)
            for row in rows:
                with self.subTest(skill=skill,prompt=row.prompt):
                    self.assertTrue(check(row,expected(row)))
                    self.assertEqual(row.gate,'independent')
    def test_unsupported_family_is_not_silently_rewritten(self):
        with self.assertRaises(ValueError):cases('math.add.carry')
