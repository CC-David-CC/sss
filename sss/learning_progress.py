"""Pure operator guidance over explicit receipts; grants no execution authority."""
def next_action(state):
    """Return one bounded action. Actual source/receipt verification stays with owners.

    Callers supply trusted, verified observations, never student assertions.
    Passing a preliminary screen does not set qualified/mastered status.
    """
    if type(state) is not dict:raise ValueError('State must be a mapping')
    allowed={'infrastructure_error','assessment_complete','lessons_verified',
             'policy_bound','candidate_exists','evaluation_complete','decision_recorded',
             'artifacts_preserved'}
    if set(state)-allowed or any(type(v) is not bool for v in state.values()):
        raise ValueError('Unknown field or non-boolean observation')
    if state.get('infrastructure_error'):
        return dict(action='repair_infrastructure',repeat_training=False,
                    required_evidence=['original failure','identified cause','passing recovery check'])
    stages=(('assessment_complete','assess', ['per-skill independent results','model and checker identities']),
            ('lessons_verified','prepare_lessons',['new practice partition','reference checks','mixed-review membership']),
            ('policy_bound','bind_policy',['parent checkpoint identity','installed policy identity','admitted lesson IDs']),
            ('candidate_exists','train_candidate',['native completion receipt','candidate identity','optimizer state']),
            ('evaluation_complete','evaluate_candidate',['target results','retention results','per-domain gains and losses']),
            ('decision_recorded','record_decision',['candidate and parent identities','working-parent or rejection reason']),
            ('artifacts_preserved','preserve',['verified best and final artifact receipts','report']))
    missing=False
    for key,_,_ in stages:
        if not state.get(key):missing=True
        elif missing:raise ValueError('Later evidence without preceding stage')
    for key,action,evidence in stages:
        if not state.get(key):return dict(action=action,required_evidence=evidence,repeat_training=False)
    return dict(action='start_next_cycle',required_evidence=['new cycle identity','retained parent identity'],repeat_training=False)
