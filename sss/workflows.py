"""Describe existing BW workflows; never execute or grant their capabilities."""
from pathlib import Path
import argparse,ast,json,hashlib,subprocess
from .catalogue import load_catalog,ROOT
from .records import digest

def workflows():
    graph=load_catalog()[2];result={}
    for path in sorted((ROOT/'workflows').glob('*.json')):
        row=json.loads(path.read_bytes())
        if row.get('schema')!=1 or row['id']!=path.stem or row['id'] in result:raise ValueError('Invalid workflow identity')
        if not set(row['skill_ids'])<=set(graph.nodes):raise ValueError('Workflow refers to an absent skill')
        result[row['id']]=row
    return result

def inspect_source(bw_root,selection=None):
    root=Path(bw_root).resolve(strict=True);rows=workflows();selected=[rows[selection]] if selection else list(rows.values())
    tree=ast.parse((root/'branchwrite/tool_registry.py').read_text());tools=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_TOOLS' for t in node.targets):tools=set(ast.literal_eval(node.value))
    if tools is None:raise ValueError('Cannot identify BW actual tool definition table')
    all_mapped={t for row in rows.values() for t in row['used_tools']};checks=[]
    for row in selected:
        missing=[];fingerprints={}
        for name in row['required_source_files']:
            path=root/name
            if not path.resolve().is_relative_to(root) or not path.is_file():missing.append(name)
            else:fingerprints[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        unknown=sorted(set(row['used_tools'])-tools)
        historical=None
        if row['historical_results']:
            result=json.loads((root/row['historical_results']).read_bytes())
            historical=next((x for x in result['examples'] if x['prompt']==row['historical_prompt']),None)
        checks.append(dict(id=row['id'],workflow_id=digest(row),source_ready=not missing and not unknown,missing=missing,unknown_tools=unknown,source_fingerprints=fingerprints,historical_evidence=historical,environment_status='operator_preparation_required',current_model_qualified=False))
    return dict(schema=1,checks=checks,unmapped_bw_tools=sorted(tools-all_mapped),executes_workflow=False,grants_capabilities=False,source_receipt_id=digest(checks))

def main(argv):
    p=argparse.ArgumentParser(prog='sss workflows');s=p.add_subparsers(dest='action',required=True)
    s.add_parser('list');q=s.add_parser('show');q.add_argument('id')
    q=s.add_parser('check');q.add_argument('--bw-root',type=Path,required=True);q.add_argument('--id')
    a=p.parse_args(argv);rows=workflows()
    if a.action=='list':value=[dict(id=k,title=v['title'],implementation=v['implementation'],sss_qualification=v['sss_qualification']) for k,v in rows.items()]
    elif a.action=='show':value=rows[a.id]
    else:value=inspect_source(a.bw_root,a.id)
    print(json.dumps(value,indent=2));return 0
