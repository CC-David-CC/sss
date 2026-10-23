"""Broad capability map. Tool availability is not a measured model skill."""
from sss.records import digest

def catalog():
    groups={
        'tools':('Tool-use foundations',[
            ('files.read','Read files and extract the requested facts','file-tool-trace'),
            ('files.write','Create the requested content exactly','file-tool-trace'),
            ('files.edit','Observe first; make bounded edits; preserve other content','file-tool-trace'),
            ('tasks.finish','Finish only after checking the requested result','file-tool-trace'),
            ('arguments','Choose tools and provide correctly typed arguments','file-tool-trace'),
            ('outputs','Extract facts from noisy tool results','file-tool-trace'),
            ('chains','Carry identifiers and dependencies across multiple calls','file-tool-trace'),
            ('errors.recover','Interpret failures and recover without false success','file-tool-trace'),
            ('boundaries.scope','Respect the granted file and machine scope','file-tool-trace'),
            ('receipts','Reconcile unknown operations without duplicating effects','planned')]),
        'linux':('Linux administration',[
            ('diagnosis','Inspect before changing; distinguish symptom from cause','planned'),
            ('services','Read service state/logs; repair and verify a service','planned'),
            ('storage','Understand paths, capacity, mounts and permissions','planned'),
            ('network','Diagnose ports, DNS, routing and SSH failures','planned'),
            ('configuration','Edit configuration, validate it and restore it if needed','planned'),
            ('packages','Install or update only within the assigned environment','planned'),
            ('gpu_jobs','Inspect allocated GPUs and manage only owned jobs','planned')]),
        'code':('Coding and scripting',[
            ('read','Understand unfamiliar source and relevant dependencies','planned'),
            ('patch','Make small correct changes with bounded scope','planned'),
            ('scripts','Write scripts with correct quoting, paths and error handling','planned'),
            ('tests','Choose checks that distinguish the bug from the repair','planned'),
            ('review','Inspect changes and explain evidence and remaining limits','planned')]),
        'reasoning':('Supporting reasoning',[
            ('arithmetic.add','Integer addition','arithmetic-expression'),
            ('arithmetic.multiply','Integer multiplication','arithmetic-expression'),
            ('arithmetic.abs','Absolute value','arithmetic-expression'),
            ('arithmetic.floor','Signed floor division','arithmetic-expression'),
            ('arithmetic.ceil','Signed ceiling division','arithmetic-expression'),
            ('units','Units, memory sizes, rates and capacity estimates','planned'),
            ('instructions','Follow constraints and distinguish instructions from data','planned')])}
    nodes=[dict(id='assistant',title='Useful coding and administration assistant',parent=None,model_proficiency='unmeasured')]
    for group,(title,leaves) in groups.items():
        nodes.append(dict(id=group,title=title,parent='assistant',model_proficiency='unmeasured'))
        for suffix,label,harness in leaves:
            nodes.append(dict(id=group+'.'+suffix,title=label,parent=group,harness=harness,
                              model_proficiency='unmeasured',training_eligible=False))
    return dict(schema=1,name='Skills³',meaning=['Skills','Scoring','Stability'],nodes=nodes,
                catalog_id=digest(nodes),scope='Capability map, not a claim that any model passed these skills')

def format_tree(document):
    rows=document['nodes'];by_parent={}
    for row in rows:by_parent.setdefault(row['parent'],[]).append(row)
    lines=['Skills³ (S³): Skills, Scoring, Stability']
    def visit(parent,depth):
        for row in by_parent.get(parent,[]):
            state=row.get('model_proficiency',row.get('status','unmeasured'))
            harness=row.get('harness')
            suffix='; harness: '+harness if harness else ''
            lines.append('  '*depth+'- '+row['title']+' ['+state+suffix+']');visit(row['id'],depth+1)
    visit(None,0);return '\n'.join(lines)
