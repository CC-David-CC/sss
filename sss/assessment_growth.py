"""Pure assessment-expansion proposals, separate from fixed comparisons.

Saturation of a finite panel is not a model ceiling. No questions, training,
resource grants or difficulty qualifications are manufactured by this planner.
"""
from .records import digest
from .paired import compare_frozen_evaluations, measured_candidate_binding, POLICY

PURPOSES=('machinery','fixed_comparison','adaptive_learning')
GATES=('independent','composition','transfer_recovery')


def plan(evaluation,*,purpose,minimum_skill_cases=96):
    if purpose not in PURPOSES:raise ValueError('Declare machinery, fixed comparison or adaptive learning')
    if type(minimum_skill_cases) is not int or not 3<=minimum_skill_cases<=1000000:
        raise ValueError('Explicit bounded per-skill coverage target required')
    compare_frozen_evaluations(evaluation,evaluation,POLICY)
    result=dict(schema=1,kind='sss.assessment-growth.v1',purpose=purpose,
        anchor_evaluation_id=evaluation['evaluation_id'],runtime_id=evaluation['runtime_id'],
        measured_model=dict(model_sha256=evaluation['model_sha256'],**measured_candidate_binding(evaluation)),
        input_evidence_id=digest(evaluation),minimum_skill_cases=minimum_skill_cases,
        changes_frozen_comparison=False,protected_answers_exported=False,
        questions_generated=0,weights_updated=False,execution_authorized=False,
        capability_ceiling_established=False)
    groups={}
    for row in evaluation['outcomes']:
        group=groups.setdefault(row['skill_id'],dict(cases=0,passed=0,finished=0,gates={}))
        group['cases']+=1;group['passed']+=row['passed'];group['finished']+=row['finished']
        gate=group['gates'].setdefault(row['gate'],dict(cases=0,passed=0,finished=0))
        gate['cases']+=1;gate['passed']+=row['passed'];gate['finished']+=row['finished']
    suggestions=[];probes=[];minimum_gate_cases=(minimum_skill_cases+2)//3
    for skill,value in sorted(groups.items()):
        saturated=value['passed']==value['cases'];stopped=value['finished']==value['cases']
        missing=[gate for gate in GATES if gate not in value['gates']]
        for gate in GATES:
            row=value['gates'].get(gate,dict(cases=0,passed=0,finished=0))
            full=bool(row['cases']) and row['passed']==row['cases']
            if purpose=='machinery':action='MACHINERY_RESULT_NOT_CAPABILITY_CEILING'
            elif purpose=='fixed_comparison':action='KEEP_MATCHING_QUESTIONS_FOR_FIXED_COMPARISON'
            elif not row['cases']:action='ADD_MISSING_GATE_EVIDENCE'
            elif full and row['cases']<minimum_gate_cases:action='EXPAND_SAMPLE_AT_SAME_DIFFICULTY'
            elif full and row['finished']<row['cases']:action='EXPAND_COVERAGE_AND_REPAIR_STOPPING'
            elif full:action='PROBE_ONE_HARDER_AXIS'
            else:action='PRACTICE_AND_REVIEW_CURRENT_CELL'
            probes.append(dict(skill_id=skill,gate=gate,**row,observed_answer_saturation=full,
                minimum_gate_cases=minimum_gate_cases,
                additional_cases_to_coverage_target=max(0,minimum_gate_cases-row['cases']),action=action))
        suggestions.append(dict(skill_id=skill,**value,observed_answer_saturation=saturated,
            observed_completion_saturation=stopped,missing_gates=missing,
            additional_cases_to_coverage_target=sum(max(0,minimum_gate_cases-value['gates'].get(g,{'cases':0})['cases']) for g in GATES)))
    expand=purpose=='adaptive_learning' and any(p['observed_answer_saturation'] or not p['cases'] for p in probes)
    result.update(requires_assessment_expansion=expand,skills=suggestions,probes=probes,
        action='PROPOSE_EXPANDED_ASSESSMENT' if expand else 'KEEP_FIXED_COMPARISON' if purpose=='fixed_comparison'
            else 'MACHINERY_CHECK_ONLY' if purpose=='machinery' else 'CONTINUE_CURRENT_SKILL_PRACTICE',
        transition_rules=dict(retain_old_questions_as_anchor=True,register_new_panel_identity=True,
            reevaluate_original_baseline=True,reevaluate_current_working_parent=True,
            compare_parent_and_candidate_on_same_new_panel=True,
            never_compare_raw_scores_across_different_panels=True,
            keep_new_assessment_questions_out_of_practice=True,
            require_separate_sealed_qualification=True),
        difficulty_rules=dict(one_axis_per_probe=True,
            axes=['composition_depth','context_tokens','environment_complexity','autonomy'],
            context_dependence_includes=['distributed_evidence','conflicting_claims','delayed_references'],
            require_qualified_prerequisites=True,require_supported_model_and_harness_context=True,
            require_environment_setup_before_world_skill=True,
            no_automatic_mastery_or_resource_authorization=True))
    result['plan_id']=digest(result);return result


def main(argv=None):
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation',type=Path,required=True)
    parser.add_argument('--purpose',choices=PURPOSES,required=True)
    parser.add_argument('--minimum-skill-cases',type=int,default=96)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    value=plan(json.loads(args.evaluation.read_bytes()),purpose=args.purpose,minimum_skill_cases=args.minimum_skill_cases)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(plan_id=value['plan_id'],action=value['action'],execution_authorized=False)));return 0


if __name__=='__main__':raise SystemExit(main())
