"""Read the shipped, inspectable curriculum data; never load executable plugins."""
import json
from pathlib import Path
from .graph import SkillGraph,identifier
from .records import digest

ROOT=Path(__file__).with_name('catalog')

def load_catalog(root=ROOT):
    root=Path(root);entries={};policies={}
    for path in sorted((root/'escalations').glob('*.json')):
        value=json.loads(path.read_bytes());key=identifier(value['id'])
        if value.get('schema')!=1 or key in policies:raise ValueError('Invalid escalation policy')
        if set(value['axes'])!={'composition_depth','context_tokens','environment_complexity','autonomy'}:raise ValueError('Four independent axes required')
        if value['qualification_gates']!=['independent','composition','transfer_recovery']:raise ValueError('Three gates required')
        policies[key]=value
    for path in sorted((root/'skills').rglob('*.json')):
        value=json.loads(path.read_bytes())
        if set(value)!={'schema','node','exercise','escalation_policy','coverage_note'} or value['schema']!=1:raise ValueError('Invalid skill document')
        key=identifier(value['node']['id'])
        expected=root/'skills'/Path(*key.split('.')).with_suffix('.json')
        if path!=expected or key in entries:raise ValueError('Skill path/identity mismatch')
        if value['escalation_policy'] not in policies:raise ValueError('Unknown escalation policy')
        if any(b not in policies[value['escalation_policy']]['current_bands'] for b in value['node']['bands']):raise ValueError('Unknown coverage band')
        spec=value['exercise']
        if spec is not None and (set(spec)!={'engine','family'} or spec['engine']!='exact-foundations-v1'):raise ValueError('Unknown generator binding')
        entries[key]=value
    graph=SkillGraph(dict(schema=2,name='Skills cubed foundations and convergence',nodes=[v['node'] for v in entries.values()]))
    return entries,policies,graph

def catalog_identity(root=ROOT):
    entries,policies,graph=load_catalog(root)
    return digest(dict(skills=entries,escalations=policies,graph_id=graph.identity))
