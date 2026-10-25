"""Next-block learning policy: retain useful checkpoints and propose practice.

Pure result analysis, without workflow execution, GPU authority or lesson labels.
A failed preservation gate can still produce a valuable working parent.
"""
from .paired import compare_frozen_evaluations,measured_candidate_binding,POLICY
from .records import digest

def _candidate_reference(evaluation):
    """Preserve the measured candidate; a base hash cannot identify its hat."""
    binding=measured_candidate_binding(evaluation)
    return dict(base_model_sha256=evaluation['model_sha256'],
                binding_kind='measured-composite' if binding else 'base-weights-only',**binding)

def next_skill_block(baseline,parent,candidate):
    original=compare_frozen_evaluations(baseline,candidate,POLICY)
    immediate=compare_frozen_evaluations(parent,candidate,POLICY)
    prior=compare_frozen_evaluations(baseline,parent,POLICY)
    # A repeated measurement of the same artifact is not a weight update.
    # Paired analysis can measure that variation, but it cannot select a new
    # training parent on the fiction that unchanged weights learned something.
    for left,right in ((baseline,parent),(parent,candidate),(baseline,candidate)):
        if (_candidate_reference(left)==_candidate_reference(right)
                and {row['id']:(row['passed'],row['finished']) for row in left['outcomes']}
                    !={row['id']:(row['passed'],row['finished']) for row in right['outcomes']}):
            raise ValueError('Unchanged candidate has different outcomes; investigate evaluation variation before selecting a training parent')
    answer_delta=candidate['passed']-parent['passed'];completion_delta=candidate['finished']-parent['finished']
    relation=('dominates' if answer_delta>=0 and completion_delta>=0 and (answer_delta or completion_delta)
              else 'dominated' if answer_delta<=0 and completion_delta<=0 and (answer_delta or completion_delta)
              else 'equal' if not answer_delta and not completion_delta else 'tradeoff')
    # Preserve frontier alternatives. Prefer increased exact task success as the
    # next working parent; every loss remains visible and becomes practice focus.
    advance=answer_delta>0 or (answer_delta==0 and completion_delta>0)
    working=candidate if advance else parent
    left={(x['skill_id'],x['gate']):x for x in (original if advance else prior)['groups']}
    self_comparison=immediate if advance else compare_frozen_evaluations(parent,parent,POLICY)
    right={(x['skill_id'],x['gate']):x for x in self_comparison['groups']}
    scores={}
    for row in working['outcomes']:
        group=scores.setdefault((row['skill_id'],row['gate']),dict(cases=0,passed=0,finished=0))
        group['cases']+=1;group['passed']+=row['passed'];group['finished']+=row['finished']
    repairs=[];review=[];forward=[]
    for key,score in sorted(scores.items()):
        row=dict(skill_id=key[0],gate=key[1],**score,baseline_answer_losses=left[key]['answer_losses'],parent_answer_losses=right[key]['answer_losses'],baseline_completion_losses=left[key]['completion_losses'],parent_completion_losses=right[key]['completion_losses'])
        review.append(dict(skill_id=key[0],gate=key[1]))
        if any(row[k] for k in ('baseline_answer_losses','parent_answer_losses','baseline_completion_losses','parent_completion_losses')):repairs.append(row)
        if score['passed']<score['cases']:forward.append(row)
    repairs.sort(key=lambda x:(-x['parent_answer_losses'],-x['baseline_answer_losses'],-x['parent_completion_losses'],x['skill_id'],x['gate']))
    forward.sort(key=lambda x:(x['passed']/x['cases'],x['skill_id'],x['gate']))
    result=dict(schema=2,kind='sss.next-skill-block.v2',working_decision='KEEP_AND_REPAIR' if advance and repairs else 'KEEP_AND_ADVANCE' if advance else 'RETAIN_PARENT',
                next_parent=_candidate_reference(working),preserve_candidate=relation in ('dominates','tradeoff'),pareto_relation_to_parent=relation,
                candidate=_candidate_reference(candidate),baseline=_candidate_reference(baseline),parent=_candidate_reference(parent),
                parent_answer_delta=answer_delta,parent_completion_delta=completion_delta,baseline_answer_delta=candidate['passed']-baseline['passed'],baseline_completion_delta=candidate['finished']-baseline['finished'],
                baseline_answer_losses=original['answer_losses'],parent_answer_losses=immediate['answer_losses'],previous_baseline_answer_losses=prior['answer_losses'],
                strict_preservation_status=original['status'],repair_groups=repairs,review_groups=review,forward_learning_groups=forward,
                label_policy='Generate and verify separate practice variations; no protected questions, answers or case IDs exported',
                baseline_evidence_id=digest(baseline),parent_evidence_id=digest(parent),candidate_evidence_id=digest(candidate),promoted=False)
    result['proposal_id']=digest(result);return result


def main(argv=None):
    """Write an offline recommendation; never allocate, train or promote."""
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','parent','candidate'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        inputs=[json.loads(getattr(args,name).read_text()) for name in ('baseline','parent','candidate')]
        value=next_skill_block(*inputs)
        payload=json.dumps(value,indent=2,allow_nan=False)+'\n'
        with args.output.open('x') as stream:stream.write(payload)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,'Cannot plan the next skill block: '+str(exc)+'\n')
    print(json.dumps(dict(kind=value['kind'],proposal_id=value['proposal_id'],
        working_decision=value['working_decision'],promoted=False)))
    return 0
