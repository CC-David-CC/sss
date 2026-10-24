"""Next-block learning policy: retain useful checkpoints and propose practice.

Pure result analysis, without workflow execution, GPU authority or lesson labels.
A failed preservation gate can still produce a valuable working parent.
"""
from .paired import compare_frozen_evaluations,POLICY
from .records import digest

def next_skill_block(baseline,parent,candidate):
    original=compare_frozen_evaluations(baseline,candidate,POLICY)
    immediate=compare_frozen_evaluations(parent,candidate,POLICY)
    prior=compare_frozen_evaluations(baseline,parent,POLICY)
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
    result=dict(schema=1,kind='sss.next-skill-block.v1',working_decision='KEEP_AND_REPAIR' if advance and repairs else 'KEEP_AND_ADVANCE' if advance else 'RETAIN_PARENT',
                next_parent_sha256=candidate['model_sha256'] if advance else parent['model_sha256'],preserve_candidate=relation in ('dominates','tradeoff'),pareto_relation_to_parent=relation,
                candidate_sha256=candidate['model_sha256'],baseline_sha256=baseline['model_sha256'],parent_sha256=parent['model_sha256'],
                parent_answer_delta=answer_delta,parent_completion_delta=completion_delta,baseline_answer_delta=candidate['passed']-baseline['passed'],baseline_completion_delta=candidate['finished']-baseline['finished'],
                baseline_answer_losses=original['answer_losses'],parent_answer_losses=immediate['answer_losses'],previous_baseline_answer_losses=prior['answer_losses'],
                strict_preservation_status=original['status'],repair_groups=repairs,review_groups=review,forward_learning_groups=forward,
                label_policy='Generate and verify separate practice variations; no protected questions, answers or case IDs exported',
                baseline_evidence_id=digest(baseline),parent_evidence_id=digest(parent),candidate_evidence_id=digest(candidate),promoted=False)
    result['proposal_id']=digest(result);return result
