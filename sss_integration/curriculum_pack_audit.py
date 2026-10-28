"""Audit whether an S³ foundation curriculum can be prepared for a training run.

This emits only skill IDs, counts, pack identities and reason codes. It neither
starts training nor writes protected prompts, answers or model responses.
"""
import argparse
import hashlib
import json

from sss.adapters.foundation_training import build_pack
from sss.curriculum import foundation_graph
from sss.foundations import Exercise, check, reference
from sss.curriculum_unique import unique_exercise_for
from sss.mastery import GATES


def _duplicates(graph, selected, seed, practice_per_gate, checks_per_gate, generation_profile):
    """Report split/skill coordinates of repeated prompts, without their text."""
    included=set(selected)
    for skill in selected:included.update(graph.prerequisites(skill))
    ordered=[key for key in graph.order if key in included]
    if generation_profile=='mixed66-v1':
        from sss.curriculum_mixed66 import exercise_for as generator
    else:generator=unique_exercise_for
    seen={};collisions=[]
    for split,count in (('practice',practice_per_gate),('development',checks_per_gate),
                        ('qualification',checks_per_gate)):
        for gate in GATES:
            for index in range(count):
                for skill in ordered:
                    exercise=generator(skill,split,index,gate=gate,seed=seed)
                    identity=hashlib.sha256(exercise.prompt.encode('utf-8')).hexdigest()
                    coordinate=dict(skill_id=skill,split=split,gate=gate,index=index)
                    if identity in seen and split!='practice':
                        collisions.append(dict(first=seen[identity],repeated=coordinate))
                    else:
                        seen.setdefault(identity,coordinate)
    return collisions


def _qualify(skills, seed, practice_per_gate, checks_per_gate, generation_profile):
    try:
        pack=build_pack(skills,seed=seed,practice_per_gate=practice_per_gate,
                        checks_per_gate=checks_per_gate,generation_profile=generation_profile)
        for row in pack['exercises']:
            exercise=Exercise(**row)
            if not check(exercise,reference(exercise)):
                return dict(status='not_ready',reason='reference_checker_mismatch')
        return dict(status='ready_for_admission_checks',pack_id=pack['pack_id'],
                    skill_count=len(pack['skills']),exercise_count=len(pack['exercises']),
                    repeated_practice_questions=pack['repeated_practice_questions'],
                    finite_boolean_truth_inputs_shared_across_splits=pack.get('finite_boolean_truth_inputs_shared_across_splits',False))
    except ValueError as error:
        reason=('duplicate_question_across_protected_splits'
                if str(error)=='Repeated frozen question; no automatic redraw'
                else 'generator_or_pack_validation_error')
        return dict(status='not_ready',reason=reason)


def audit(skills=None, *, seed=20261028, practice_per_gate=2, checks_per_gate=1,
          generation_profile='without-replacement-v1'):
    graph=foundation_graph()
    selected=([key for key in graph.order if graph.nodes[key]['status']=='implemented']
              if skills is None else list(skills))
    if not selected or len(set(selected))!=len(selected) or any(
            key not in graph.nodes or graph.nodes[key]['status']!='implemented' for key in selected):
        raise ValueError('Select distinct implemented skill IDs')
    if generation_profile not in ('without-replacement-v1','mixed66-v1'):
        raise ValueError('Unknown audit generator profile')
    rows=[dict(skill_id=skill,**_qualify([skill],seed,practice_per_gate,checks_per_gate,generation_profile))
          for skill in selected]
    combined=_qualify(selected,seed,practice_per_gate,checks_per_gate,generation_profile)
    if combined.get('reason')=='duplicate_question_across_protected_splits':
        combined['duplicate_coordinates']=_duplicates(graph,selected,seed,practice_per_gate,checks_per_gate,generation_profile)
    ready=sum(row['status']=='ready_for_admission_checks' for row in rows)
    return dict(schema=1,scope='bounded generator and reference/checker preflight',
                graph_id=graph.identity,seed=seed,generation_profile=generation_profile,practice_per_gate=practice_per_gate,
                checks_per_gate=checks_per_gate,selected_skills=len(selected),
                individual_packs_ready=ready,individual_packs_not_ready=len(rows)-ready,
                combined_pack=combined,skills=rows,
                training_admission_granted=False,model_evaluated=False,mastery_established=False,
                semantic_disjointness_established=False,
                interpretation='Passing this small generator check is not lesson admission, model evaluation, semantic split qualification, or approval to train.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill',action='append',dest='skills')
    parser.add_argument('--seed',type=int,default=20261028)
    parser.add_argument('--practice-per-gate',type=int,default=2)
    parser.add_argument('--checks-per-gate',type=int,default=1)
    parser.add_argument('--generation-profile',choices=('without-replacement-v1','mixed66-v1'),default='without-replacement-v1')
    args=parser.parse_args()
    result=audit(args.skills,seed=args.seed,practice_per_gate=args.practice_per_gate,
                 checks_per_gate=args.checks_per_gate,generation_profile=args.generation_profile)
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result['combined_pack']['status']=='ready_for_admission_checks' else 2


if __name__=='__main__':
    raise SystemExit(main())
