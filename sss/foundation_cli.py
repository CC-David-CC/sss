"""Graph, curriculum, checked examples and offline reports."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .curriculum import foundation_graph,exercise_for,student_day,BY_ID
from .foundations import check,reference
from .episodes import EpisodeArchive,export_text
from .reporting import write_report
from .records import digest

def example_archive(root,skill,index=0):
    case=exercise_for(skill,'practice',index,gate='transfer_recovery')
    answer=reference(case)
    if not check(case,answer):raise ValueError('Reference did not pass independent checker')
    archive=EpisodeArchive(root,create=True,metadata=dict(origin='synthetic',skill_id=skill,case_id=case.identity,checker='exact-foundations-v1',reference_kind='deterministic checked demonstration',trained=False))
    q=archive.append('user','question',case.prompt,topic=skill,question_id='exercise')
    # A checked verification explanation, not a claim to capture a model's private thoughts.
    details=json.loads(answer)
    reasoning='The earlier proposed answer is '+('correct' if details['previous_correct'] else 'incorrect')+'. The independently checked response is '+details['answer']+'.'
    archive.append('assistant','thinking',reasoning,verified=True,topic=skill,refs=[q])
    archive.append('assistant','answer',answer,verified=True,topic=skill,refs=[q],resolves='exercise')
    return archive

def main(argv):
    parser=argparse.ArgumentParser(prog='sss')
    subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('graph');p.add_argument('--json',action='store_true')
    p=subs.add_parser('exercise');p.add_argument('--skill',required=True);p.add_argument('--split',choices=['practice','development','qualification'],default='practice');p.add_argument('--gate',choices=['independent','composition','transfer_recovery'],default='independent');p.add_argument('--index',type=int,default=0);p.add_argument('--reference',action='store_true')
    p=subs.add_parser('school-day');p.add_argument('--day',type=int,default=0);p.add_argument('--qualified',nargs='*',default=[])
    p=subs.add_parser('report');p.add_argument('--output',type=Path,required=True);p.add_argument('--assessments',type=Path)
    p=subs.add_parser('teaching-example');p.add_argument('--skill',required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv);graph=foundation_graph()
    if args.command=='graph':
        if not args.json:
            print('\n'.join(f"{k}: {graph.nodes[k]['title']} [{graph.nodes[k]['status']}] <- {', '.join(graph.nodes[k]['requires']) or 'root'}" for k in graph.order));return 0
        value=dict(graph.document(),graph_id=graph.identity)
    elif args.command=='exercise':
        case=exercise_for(args.skill,args.split,args.index,gate=args.gate);value=case.public()
        if args.reference:
            if args.split!='practice':parser.error('Reference export is restricted to practice; holdout answers stay with the evaluator')
            answer=reference(case);value.update(answer=answer,reference_verified=check(case,answer),model_inference=False)
    elif args.command=='school-day':value=student_day(graph,args.qualified,args.day)
    elif args.command=='report':
        records=json.loads(args.assessments.read_bytes()) if args.assessments else []
        if type(records) is dict:records=records['assessments']
        value=write_report(graph,args.output,records)
    else:
        archive=example_archive(args.output,args.skill);value=export_text(archive,args.output/'conversation.txt',public=True)
    print(json.dumps(value,indent=2,ensure_ascii=False));return 0
