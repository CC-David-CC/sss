import json,tempfile,unittest
from pathlib import Path
from sss.catalogue import load_catalog,catalog_identity
from sss.curriculum import foundation_graph
from sss.escalation import Difficulty,recommendation
from sss.reporting import report_html

class CatalogueTests(unittest.TestCase):
    def test_files_are_authoritative_and_bound(self):
        entries,policies,graph=load_catalog()
        self.assertEqual(graph.identity,foundation_graph().identity)
        self.assertEqual(len(entries),len(graph.nodes))
        self.assertEqual(len(catalog_identity()),64)
        self.assertEqual(entries['math.add.carry']['node']['requires'],['math.add.no_carry'])
    def test_only_one_coordinate_changes(self):
        current=Difficulty();later=current.advance('context_tokens',8192)
        self.assertEqual(later.composition_depth,current.composition_depth)
        self.assertNotEqual(later.identity,current.identity)
        with self.assertRaises(ValueError):current.advance('autonomy',0)
    def test_missing_coverage_does_not_advance(self):
        g=foundation_graph();c=Difficulty();a=dict(graph_id=g.identity,skill_id='math.place_value',profile_id='model-a',band=c.identity,status='qualified',qualified=True)
        self.assertEqual(recommendation(g,'math.place_value','model-a',c,a,[],supported_cells=[])['action'],'coverage_unavailable')
        self.assertEqual(recommendation(g,'math.place_value','model-a',c,a,[],supported_cells=[c.identity])['action'],'eligible_for_one_axis_probe')
        with self.assertRaises(ValueError):recommendation(g,'math.place_value','model-b',c,a,[],supported_cells=[c.identity])
    def test_report_blocks_script_termination_and_changed_graph(self):
        from sss.graph import SkillGraph
        doc=foundation_graph().document();doc['nodes'][0]['title']='</script><script>alert(1)</script>'
        g=SkillGraph(doc);rendered=report_html(g)
        self.assertNotIn('</script><script>alert(1)',rendered)
        g.nodes[doc['nodes'][0]['id']]['title']='changed'
        with self.assertRaises(ValueError):report_html(g)
