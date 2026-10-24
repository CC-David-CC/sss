"""Freeze and score direct foundation probes against a declared model profile.

These are evaluation artifacts, not a workflow runtime. Endpoint execution and
resource ownership remain with the operator/PCC; this module never starts a GPU.
"""
from dataclasses import asdict
from pathlib import Path
import json,time
from .curriculum import foundation_graph,exercise_for
from .catalogue import catalog_identity
from .foundations import check,Exercise
from .mastery import QualificationSuite,MasteryPolicy,GATES
from .records import canonical,digest

def freeze(root,profile,skills,*,qualify=False,seed=0,critical=(),retention=()):
    root=Path(root);root.mkdir(mode=0o700,parents=True,exist_ok=False)
    if not skills or len(set(skills))!=len(skills):raise ValueError('Distinct explicit skills required')
    graph=foundation_graph();suites=[];exercises={}
    for skill in skills:
        if skill not in graph.nodes or graph.nodes[skill]['status']!='implemented':raise ValueError('No implemented qualification family for '+skill)
        cases=[]
        for gate in GATES:
            for index in range(256 if qualify else 3):
                e=exercise_for(skill,'qualification' if qualify else 'development',index,gate=gate,seed=seed)
                exercises[e.identity]=e
                cases.append(dict(id=e.identity,purpose='qualification',gate=gate,trial_id=e.trial_id,family_id=e.family_id))
        for purpose,pack in [('critical',critical),('retention',retention)]:
            for e in pack:
                if e.split=='practice':raise ValueError('Practice cannot be a protected guard')
                exercises[e.identity]=e;cases.append(dict(id=e.identity,purpose=purpose,gate=e.gate,trial_id=e.trial_id,family_id=e.family_id))
        suites.append(QualificationSuite(graph.identity,profile.identity,skill,'bounded-v1',cases))
    manifest=dict(schema=2,implementation_id=implementation_identity(),profile=asdict(profile),profile_id=profile.identity,graph_id=graph.identity,catalog_id=catalog_identity(),purpose='qualification' if qualify else 'diagnostic_probe',seed=seed,
        suites=[dict(id=s.identity,binding=s.binding,policy=asdict(s.policy),cases=list(s.cases.values())) for s in suites],exercises=[asdict(e) for e in exercises.values()],reference_answers_included=False)
    manifest['manifest_id']=digest(manifest)
    path=root/'frozen-private.json'
    with path.open('xb') as out:out.write(canonical(manifest)+b'\n')
    path.chmod(0o400)
    return root,suites,exercises,manifest

def evaluate(frozen,model,*,maximum_seconds=3600,model_inference=True):
    root,suites,exercises,manifest=frozen
    if type(maximum_seconds) not in (int,float) or not 0<maximum_seconds<=14400:raise ValueError('Explicit bounded wall-clock campaign required')
    outcomes=root/'outcomes';outcomes.mkdir(mode=0o700,exist_ok=False)
    start=time.monotonic();rows={};evidence={}
    for key,e in exercises.items():
        path=outcomes/(key+'.json');intent=outcomes/(key+'-intent.json')
        if time.monotonic()-start>=maximum_seconds:record=dict(status='unavailable',reason='campaign_budget',called=False)
        else:
            try:
                message,usage=model([dict(role='system',content='Follow the requested answer format exactly. This is a direct-answer assessment; no tools are available.'),dict(role='user',content=e.prompt)],[],intent)
                if type(message) is not dict:raise ValueError('Invalid endpoint message')
                answer=message.get('content')
                passed=not message.get('tool_calls') and check(e,answer)
                record=dict(status='pass' if passed else 'fail',called=True,message=message,usage=usage)
            except Exception as error:
                record=dict(status='unavailable',reason=type(error).__name__,called=True)
                # Private original error retained; never put endpoint secrets in public reports.
                (outcomes/(key+'-error-private.txt')).write_text(str(error))
        record.update(case_id=key,profile_id=manifest['profile_id'])
        with path.open('xb') as out:out.write(canonical(record)+b'\n')
        rows[key]=record['status'];evidence[key]=digest(record)
    assessments=[]
    for suite in suites:
        assessment=suite.assess([dict(case_id=k,status=rows[k],evidence_sha256=evidence[k],suite_id=suite.identity) for k in suite.cases])
        assessment['evaluation_purpose']=manifest['purpose'];assessments.append(assessment)
    result=dict(schema=2,model_inference=model_inference,purpose=manifest['purpose'],profile_id=manifest['profile_id'],elapsed_seconds=time.monotonic()-start,assessments=assessments,weights_updated=False,promoted=False)
    with (root/'assessment.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    return result

def implementation_identity():
    import hashlib
    files=('foundations.py','extended_math.py','reasoning.py','curriculum.py','mastery.py','evaluation.py','profiles.py','graph.py','catalogue.py','records.py')
    return digest({name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files})

def thaw(root):
    root=Path(root);manifest=json.loads((root/'frozen-private.json').read_bytes())
    if manifest.get('manifest_id')!=digest({k:v for k,v in manifest.items() if k!='manifest_id'}):raise ValueError('Frozen evaluation was changed')
    if manifest['implementation_id']!=implementation_identity() or manifest['catalog_id']!=catalog_identity():raise ValueError('Code/catalog changed; inspect the original evaluation version')
    from .profiles import ModelProfile,ContextPolicy
    value=dict(manifest['profile']);value['context']=ContextPolicy(**value['context']);profile=ModelProfile(**value)
    if profile.identity!=manifest['profile_id'] or foundation_graph().identity!=manifest['graph_id']:raise ValueError('Frozen profile or graph mismatch')
    exercises={}
    for row in manifest['exercises']:
        exercise=Exercise(**row);exercises[exercise.identity]=exercise
    suites=[]
    for row in manifest['suites']:
        binding=row['binding'];suite=QualificationSuite(**binding,cases=row['cases'],policy=MasteryPolicy(**row['policy']))
        if suite.identity!=row['id'] or not set(suite.cases)<=set(exercises):raise ValueError('Frozen suite or case mismatch')
        suites.append(suite)
    return root,suites,exercises,manifest
