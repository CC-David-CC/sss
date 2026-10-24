"""Paired frozen-result assessment; never trains, executes or promotes a model."""
import re
from .records import digest

POLICY = dict(preserve_every_answer_pass=True,preserve_every_finished_response=True,
              require_answer_or_completion_gain=True,require_sealed_qualification_after_development_selection=True,
              no_training_from_protected_questions=True)

def compare_frozen_evaluations(baseline,candidate,policy):
    if policy != POLICY:
        raise ValueError('Unsupported acceptance policy; do not silently relax the frozen gate')
    for key in ('evaluation_id','runtime_id'):
        if not re.fullmatch('[a-f0-9]{64}',str(baseline.get(key,''))) or baseline.get(key) != candidate.get(key):
            raise ValueError('Paired evaluations must use the same frozen cases and runtime')
    indexed=[]
    for result in (baseline,candidate):
        if result.get('status') != 'COMPLETE' or result.get('weights_updated') is not False or result.get('promoted') is not False:
            raise ValueError('Complete, immutable evaluation evidence required')
        rows=result.get('outcomes')
        if type(rows) is not list or not rows or any(type(row) is not dict or type(row.get('id')) is not str or type(row.get('skill_id')) is not str or row.get('gate') not in ('independent','composition','transfer_recovery') or any(type(row.get(k)) is not bool for k in ('passed','finished')) for row in rows):
            raise ValueError('Each case needs an explicit skill, gate, answer and completion outcome')
        index={row['id']:row for row in rows}
        if len(index)!=len(rows) or type(result.get('cases')) is not int or result['cases']!=len(rows) or any(type(result.get(k)) is not int or result[k]!=sum(row[k] for row in rows) for k in ('passed','finished')):
            raise ValueError('Complete unique outcomes and aggregate counts required')
        if not re.fullmatch('[a-f0-9]{64}',str(result.get('model_sha256',''))):
            raise ValueError('Measured model identity required')
        indexed.append(index)
    left,right=indexed
    if left.keys()!=right.keys() or any((left[k]['skill_id'],left[k]['gate']) != (right[k]['skill_id'],right[k]['gate']) for k in left):
        raise ValueError('Case identity, skill or mastery gate changed between evaluations')
    groups={}
    for key,a in left.items():
        b=right[key];group=groups.setdefault((a['skill_id'],a['gate']),dict(skill_id=a['skill_id'],gate=a['gate'],cases=0,answer_gains=0,answer_losses=0,completion_gains=0,completion_losses=0))
        group['cases']+=1
        for field,label in [('passed','answer'),('finished','completion')]:
            group[label+'_gains']+=int(not a[field] and b[field]);group[label+'_losses']+=int(a[field] and not b[field])
    totals={k:sum(row[k] for row in groups.values()) for k in ('answer_gains','answer_losses','completion_gains','completion_losses')}
    eligible=not totals['answer_losses'] and not totals['completion_losses'] and bool(totals['answer_gains'] or totals['completion_gains'])
    result=dict(schema=1,status='DEVELOPMENT_ELIGIBLE' if eligible else 'REJECTED',scope='Paired development behavior only; sealed qualification still required',
                evaluation_id=baseline['evaluation_id'],runtime_id=baseline['runtime_id'],baseline_model_sha256=baseline['model_sha256'],candidate_model_sha256=candidate['model_sha256'],
                baseline_evidence_id=digest(baseline),candidate_evidence_id=digest(candidate),cases=len(left),**totals,
                groups=[groups[k] for k in sorted(groups)],sealed_qualification_required=True,promoted=False)
    result['assessment_id']=digest(result);return result
