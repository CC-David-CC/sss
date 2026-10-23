import json,tempfile,unittest
from pathlib import Path
from sss.workflows import workflows,inspect_source

class WorkflowRecipes(unittest.TestCase):
    def test_domains_are_separate_from_qualification(self):
        rows=workflows()
        self.assertEqual(set(rows),{'web','writing','pdf','cad-plate','cad-components','blender','remote-admin','followup'})
        self.assertIn('cad.measurement',rows['cad-plate']['skill_ids'])
        self.assertIn('blender.video',rows['blender']['skill_ids'])
        self.assertTrue(all(r['sss_qualification']=='not-qualified' for r in rows.values()))
    def test_source_preflight_detects_missing_and_new_tools(self):
        rows=workflows()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'branchwrite').mkdir()
            tools={name:None for row in rows.values() for name in row['used_tools']};tools['new_unknown_tool']=None
            (root/'branchwrite/tool_registry.py').write_text('_TOOLS='+repr(tools))
            (root/'examples/prompts').mkdir(parents=True)
            (root/'examples/prompts/results.json').write_text(json.dumps(dict(examples=[])))
            result=inspect_source(root,'blender')
            self.assertFalse(result['checks'][0]['source_ready'])
            self.assertEqual(result['unmapped_bw_tools'],['new_unknown_tool'])
            self.assertFalse(result['executes_workflow']);self.assertFalse(result['grants_capabilities'])
