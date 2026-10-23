"""Small, bounded operator entry points; never acquires hardware or trains a model."""
import argparse,json,os
from dataclasses import asdict
from pathlib import Path
from .catalogue import load_catalog,catalog_identity
from .profiles import ModelProfile,ContextPolicy
from .evaluation import freeze,thaw,evaluate
from .foundations import reference

def main(argv):
    p=argparse.ArgumentParser(prog='sss explore');sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('doctor')
    for name in ('prepare','reference'):
        q=sub.add_parser(name);q.add_argument('--directory',type=Path,required=True);q.add_argument('--skill',action='append',required=True);q.add_argument('--seed',type=int,default=0)
        if name=='prepare':q.add_argument('--profile',type=Path,required=True);q.add_argument('--qualification',action='store_true')
    q=sub.add_parser('run');q.add_argument('--directory',type=Path,required=True);q.add_argument('--endpoint',required=True);q.add_argument('--key-env',default='SSS_API_KEY');q.add_argument('--maximum-output',type=int,default=512);q.add_argument('--maximum-seconds',type=int,default=600)
    q=sub.add_parser('inspect');q.add_argument('--directory',type=Path,required=True)
    a=p.parse_args(argv)
    if a.action=='doctor':
        entries,policies,graph=load_catalog();value=dict(status='ready',skills=len(entries),implemented_bounded_families=sum(v['node']['status']=='implemented' for v in entries.values()),planned=sum(v['node']['status']=='planned' for v in entries.values()),catalog_id=catalog_identity(),graph_id=graph.identity,network_used=False,gpu_used=False)
    elif a.action in ('prepare','reference'):
        if a.action=='prepare':
            config=json.loads(a.profile.read_bytes())
            if any(type(v) is str and v.startswith('REPLACE_') for v in config.values()):raise ValueError('Replace example profile placeholders with inspected identities')
            config['context']=ContextPolicy(**config.get('context',{}));profile=ModelProfile(**config)
        else:profile=ModelProfile('deterministic-reference','v1','reference-utf8-byte-v1','owned-exercise-v1','sss-reference','v1')
        frozen=freeze(a.directory,profile,a.skill,qualify=a.action=='prepare' and a.qualification,seed=a.seed)
        value=dict(status='prepared',directory=str(a.directory),manifest_id=frozen[3]['manifest_id'],profile_id=profile.identity,cases=len(frozen[2]),network_used=False,gpu_used=False)
        if a.action=='reference':
            answers={e.prompt:reference(e) for e in frozen[2].values()}
            def model(messages,tools,intent):
                intent.write_text(json.dumps(dict(reference=True,prompt=messages[-1]['content']))+'\n')
                return dict(role='assistant',content=answers[messages[-1]['content']]),{}
            value=evaluate(frozen,model,model_inference=False)
            if any(g['passed']!=g['trials'] for x in value['assessments'] for g in x['gates'].values()):raise ValueError('Reference checker disagreement')
    elif a.action=='run':
        if not 1<=a.maximum_output<=8192 or not 1<=a.maximum_seconds<=14400:raise ValueError('Bounded campaign settings required')
        frozen=thaw(a.directory)
        from .tool_benchmark import OpenAIModel
        model=OpenAIModel(a.endpoint,frozen[3]['profile']['model_id'],os.environ.get(a.key_env,''),maximum=a.maximum_output,timeout=min(180,a.maximum_seconds))
        value=evaluate(frozen,model,maximum_seconds=a.maximum_seconds)
    else:
        path=a.directory/'assessment.json'
        if path.exists():value=json.loads(path.read_bytes())
        else:
            frozen=thaw(a.directory);out=a.directory/'outcomes'
            value=dict(status='interrupted_or_running' if out.exists() else 'prepared',manifest_id=frozen[3]['manifest_id'],outcome_files=len(list(out.glob('*.json'))) if out.exists() else 0,retry_original_run=False)
    print(json.dumps(value,indent=2));return 0
