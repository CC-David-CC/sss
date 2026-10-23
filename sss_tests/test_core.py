import hashlib
import unittest
from sss import SkillTree
from sss.catalog import catalog

def case(name):return dict(id=hashlib.sha256(name.encode()).hexdigest(),prompt=name,kind='add',parameters=['a','b'])
def tree():
    root=dict(id='root',title='Root',parent=None,minimum_accuracy=.9,practice_lesson_ids=[],validation=[],blind=[])
    leaf=dict(id='read',title='Read',parent='root',minimum_accuracy=.5,practice_lesson_ids=['a'*64],
              validation=[case('read a'),case('read b'),case('read c')],blind=[case('blind read')])
    return SkillTree(dict(schema=1,model_contract_id='b'*64,nodes=[root,leaf]))

class Core(unittest.TestCase):
    def test_catalog_never_equates_harness_availability_with_model_proficiency(self):
        doc=catalog();self.assertTrue(all(n['model_proficiency']=='unmeasured' for n in doc['nodes']))
        ids={n['id'] for n in doc['nodes']};self.assertTrue({'tools.files.read','tools.files.write','tools.files.edit','tools.tasks.finish','linux.services','code.tests'}<=ids)
    def test_case_level_preservation_blocks_a_same_score_swap(self):
        t=tree();a,b,c=[v['id'] for v in t.rows('validation')]
        before=t.assess([dict(id=a,passed=True),dict(id=b,passed=True),dict(id=c,passed=False)],'validation')
        after=t.assess([dict(id=a,passed=False),dict(id=b,passed=True),dict(id=c,passed=True)],'validation',before['passed_ids'])
        self.assertEqual(after['scores']['read']['passed'],2);self.assertEqual(after['regressed_ids'],[a]);self.assertFalse(after['qualified'])
    def test_uncovered_leaf_is_not_an_active_passing_skill(self):
        doc=tree().document;doc['nodes'][1]['blind']=[]
        with self.assertRaises(ValueError):SkillTree(doc)
    def test_unknown_and_missing_outcomes_fail_coverage(self):
        t=tree()
        with self.assertRaises(ValueError):t.assess([], 'validation')
        with self.assertRaises(ValueError):t.assess([dict(id=v['id'],passed=None) for v in t.rows('validation')],'validation')

if __name__=='__main__':unittest.main()
