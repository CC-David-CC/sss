"""Checked synthetic school-day fixture, using the existing immutable archive.

This is a deterministic teaching record, not a model session, scheduler or claim
about human learning. Original assumptions must be reread after a short note.
"""
from dataclasses import replace

from .curriculum import exercise_for
from .episodes import compact_reference, verify_note
from .foundations import check, reference
from .reasoning import ArgumentProblem, practice_evidence
from .records import canonical


def append_delayed_revisit(archive, morning_case):
    if morning_case.skill_id != 'logic.joint_premises' or morning_case.split != 'practice':
        raise ValueError('Delayed fixture starts with owned joint-premise practice')
    morning = archive.records()
    question = next(row for row in morning if row['question_id'] == 'exercise')
    if question['text'] != morning_case.prompt:
        raise ValueError('Original question differs from the declared exercise')
    # Visit another subject. Identical quantities require different operations.
    for index in range(4):
        case = exercise_for('math.method_selection', 'practice', index)
        answer = reference(case)
        if not check(case, answer):
            raise ValueError('Independent arithmetic checker failed')
        q = archive.append('user', 'question', case.prompt, topic=case.skill_id,
                           question_id=f'math-{index}')
        archive.append('assistant', 'answer', answer, verified=True,
                       topic=case.skill_id, refs=[q], resolves=f'math-{index}')
    boundary = len(archive.records()) - 1
    note = compact_reference(archive, boundary, count=lambda text: len(text.encode()),
                             budget=700, unit='utf8-byte-reference')
    verify_note(archive, note)
    # The original, already answered question is intentionally absent from this
    # causal note. No future question was passed to the compactor.
    if any(entry['record_id'] == question['id'] for entry in note['entries']):
        raise ValueError('Fixture did not exercise a missing original question')
    archive._exclusive(archive.path / 'revisit-note.json', canonical(note) + b'\n')
    archive.append('system', 'summary', canonical(note).decode(), topic='working-note',
                   refs=[row['id'] for row in archive.records(through=boundary)
                         if any(entry['record_id'] == row['id'] for entry in note['entries'])])

    original = ArgumentProblem(morning_case.payload['problem']).document()
    # Select a joint-premise fact from the earlier problem, not a later answer.
    joint = next((rule for rule in original['rules']
                  if len(rule['premises']) > 1 and set(rule['premises']) <= set(original['facts'])), None)
    removed = joint['premises'][0] if joint else original['facts'][0]
    current = dict(original, facts=[x for x in original['facts'] if x != removed])
    payload = dict(problem=current, original_facts=original['facts'], removed=removed)
    prompt = (f'Evening revisit: retrieve the original problem from archive record {question["id"]}. '
              f'Withdraw fact {removed}; keep its other facts and rules. Does its query still follow? '
              'Return {"status":"entailed","proof":[rule IDs]} or '
              '{"status":"not_entailed","counterexample":{every atom:true or false}}. '
              'A counterexample must satisfy all remaining facts and rules and make the query false.')
    followup = replace(morning_case, skill_id='logic.premise_robustness', kind='premise_removal',
                       gate='independent', family_id='practice-delayed-premise-v1',
                       trial_id=morning_case.trial_id + ':delayed-premise', payload=payload, prompt=prompt)
    q = archive.append('user', 'question', prompt, topic=followup.skill_id,
                       question_id='evening-revisit', refs=[question['id']])
    hits = archive.search('logic.joint_premises', through=boundary)
    if question['id'] not in {row['id'] for row in hits}:
        raise ValueError('Original question could not be located in the visible archive')
    restored = archive.read(question['id'], through=boundary)
    reread = archive.append('tool', 'observation', restored['text'], verified=True,
                            topic='archive-reread', refs=[question['id'], q])
    answer = reference(followup)
    if not check(followup, answer):
        raise ValueError('Independent delayed-premise checker failed')
    receipt = practice_evidence(followup, answer, q)
    receipt.update(retrieved_question_record_id=question['id'],
                   visible_through=boundary, compaction_note_id=note['note_id'])
    # Identity must include the extra provenance, not just the original receipt.
    from .records import digest
    receipt['evidence_id'] = digest({k: v for k, v in receipt.items() if k != 'evidence_id'})
    archive._exclusive(archive.path / 'revisit-evidence.json', canonical(receipt) + b'\n')
    archive.append('assistant', 'answer', answer, verified=True, topic=followup.skill_id,
                   refs=[q, reread], resolves='evening-revisit')
    return archive
