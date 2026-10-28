"""Create checker-verified scalar practice lessons for response levels and modes.

The caller must supply the model-specific renderer. These examples are synthetic
practice, not extracted failure observations, and are not submitted to PCC here.
"""
import hashlib
import re
from pathlib import Path
from . import foundations, learning_levels
from .adapters.episode_lessons import pcc_lesson
from .episodes import EpisodeArchive, training_tokens
from .foundations import check, number, reference
from .level_evaluation import (
    SCALAR_KINDS, _composed_prompt, _format_prompt, _format_result, _semantic,
)
from .learning_levels import (
    ADDITION_REASONING_CHECKER, check_addition_reasoning,
    checked_addition_reasoning, response_target_segments,
)
from .records import digest, file_sha256

POLICIES = {
    ('answer', 'direct'): 'answer_only',
    ('answer', 'reasoning'): 'reasoning_and_answer',
    ('format', 'direct'): 'format_only',
    ('composed', 'direct'): 'answer_and_format',
    ('composed', 'reasoning'): 'reasoning_answer_and_format',
}
SHA256 = re.compile(r'[a-f0-9]{64}\Z')


def build_scalar_lesson(exercise, level, render, *, answer_mode='direct'):
    """Build one practice-only lesson with separately labeled target spans.

    ``render`` receives logical role/kind/content rows and must return the exact
    rendered rows PCC will tokenize, retaining each kind boundary. Model-specific
    control tokens and tokenizer behavior stay outside S³'s generic generator.
    """
    if getattr(exercise, 'split', None) != 'practice':
        raise ValueError('Only practice items may become training lessons')
    if exercise.gate != 'independent':
        raise ValueError('Response-level lessons require matched independent skill cases')
    if exercise.kind not in SCALAR_KINDS:
        raise ValueError('No task-native scalar lesson adapter for ' + exercise.kind)
    if (level, answer_mode) not in POLICIES:
        raise ValueError('Unknown scalar response level')
    if level == 'format' and answer_mode != 'direct':
        raise ValueError('Format-only lessons are direct; they do not train reasoning')
    answer = reference(exercise)
    if not check(exercise, answer):
        raise ValueError('Reference answer failed the task checker')
    number(answer)

    reasoning = checked_addition_reasoning(exercise, answer) if answer_mode == 'reasoning' else None
    if level == 'answer':
        prompt = exercise.prompt
        if reasoning is not None:
            prompt += ' Show a brief checkable arithmetic equation in the reasoning section before giving the exact answer.'
        target_parts = ([] if reasoning is None else [('thinking', reasoning)]) + [('answer', answer)]
    elif level == 'format':
        prompt = _format_prompt(answer)
        target_parts = [('format', '{"answer":"' + answer + '"}')]
    else:
        prompt = _composed_prompt(exercise)
        if reasoning is not None:
            prompt += ' Show a brief checkable arithmetic equation in the reasoning section, then return only the requested JSON object as the final answer.'
        target_parts = ([] if reasoning is None else [('thinking', reasoning)]) + [
            ('format', '{"answer":"'), ('answer', answer), ('format', '"}')]
    if level in ('format', 'composed'):
        formatted = ''.join(content for kind, content in target_parts
                            if kind in ('format', 'answer'))
        result = _format_result(formatted, answer)
        if result != dict(format_valid=True, content_preserved=True):
            raise ValueError('Authored format target failed schema or content-preservation check')
        if level == 'composed' and _semantic(exercise, formatted) is not True:
            raise ValueError('Authored composed target failed the task semantic checker')

    logical = [dict(role='user', kind='question', content=prompt,
                    verified=False, scope='practice')]
    logical.extend(dict(role='assistant', kind=kind, content=content,
                        verified=True, scope='practice')
                   for kind, content in target_parts)
    rendered = render(logical)
    if type(rendered) is not list or len(rendered) != len(logical):
        raise ValueError('Renderer must preserve every logical span boundary')
    for source, row in zip(logical, rendered):
        if (type(row) is not dict or set(row) != {'role', 'kind', 'rendered', 'verified', 'scope'}
                or any(row[key] != source[key] for key in ('role', 'kind', 'verified', 'scope'))
                or type(row['rendered']) is not str or not row['rendered']):
            raise ValueError('Renderer changed the verified target structure')
    policy = POLICIES[(level, answer_mode)]
    targets = response_target_segments(rendered, policy)
    if sum(targets) != len(target_parts):
        raise ValueError('Target policy does not select exactly the authored spans')

    verification = dict(
        schema=1, origin='owned-synthetic-practice', level=level,
        answer_mode=answer_mode,
        exercise_id=exercise.identity, skill_id=exercise.skill_id,
        task_checker='exact-foundations-v1',
        task_checker_sha256=file_sha256(foundations.__file__),
        target_checker='sss-response-levels-v1',
        target_checker_sha256=file_sha256(learning_levels.__file__),
        source_generator_sha256=file_sha256(__file__),
        answer_sha256=digest(answer), reference_passed=True,
        reasoning_checker=(ADDITION_REASONING_CHECKER if reasoning is not None else None),
        reasoning_sha256=(digest(reasoning) if reasoning is not None else None),
        reasoning_passed=(None if reasoning is None else
                          check_addition_reasoning(exercise, answer, reasoning)),
        target_policy=policy, actual_token_masks_confirmed=False,
    )
    verification['verification_id'] = digest(verification)
    return dict(schema=1, level=level, answer_mode=answer_mode, skill_id=exercise.skill_id,
                exercise_id=exercise.identity, target_policy=policy,
                segments=rendered, verification=verification,
                training_authorized=False)


def _archive_identity(path):
    path = Path(path)
    files = [path / 'metadata.json'] + sorted((path / 'events').glob('*.json'))
    digestor = hashlib.sha256()
    for item in files:
        relative = item.relative_to(path).as_posix().encode()
        content = item.read_bytes()
        digestor.update(len(relative).to_bytes(4, 'big'))
        digestor.update(relative)
        digestor.update(len(content).to_bytes(8, 'big'))
        digestor.update(content)
    return digestor.hexdigest()


def build_scalar_pcc_lesson(exercise, level, render, *, archive_path,
                             model_contract_id, renderer_sha256,
                             tokenizer_sha256, tokenize, maximum=8192,
                             answer_mode='direct'):
    """Create an immutable S³ archive and exact PCC schema-2 scalar lesson.

    This prepares/admission-checks the lesson only. It does not submit it to PCC
    or run a native optimizer update.
    """
    for value, name in ((model_contract_id, 'model contract'),
                        (renderer_sha256, 'renderer'),
                        (tokenizer_sha256, 'tokenizer')):
        if type(value) is not str or not SHA256.fullmatch(value):
            raise ValueError('Exact ' + name + ' SHA-256 identity required')
    prepared = build_scalar_lesson(exercise, level, render, answer_mode=answer_mode)
    archive = EpisodeArchive(
        archive_path, create=True,
        metadata=dict(origin='synthetic', lesson_level=level, answer_mode=answer_mode,
                      exercise_id=exercise.identity, skill_id=exercise.skill_id,
                      generator='sss-response-level-practice-v1'),
    )
    question_id = digest(dict(exercise_id=exercise.identity, level=level,
                              answer_mode=answer_mode))
    rows = prepared['segments']
    user = rows[0]
    archive.append(user['role'], 'question', user['rendered'], verified=False,
                   scope='practice', topic=exercise.skill_id, question_id=question_id)
    for index, row in enumerate(rows[1:]):
        archive.append(row['role'], row['kind'], row['rendered'],
                       verified=row['verified'], scope='practice',
                       topic=exercise.skill_id,
                       resolves=question_id if index == len(rows[1:]) - 1 else '')
    archived = EpisodeArchive(archive_path)
    if archived.head != archive.head or len(archived.records()) != len(rows):
        raise ValueError('Reopened S³ evidence archive differs from generated lesson')
    archive_sha256 = _archive_identity(archive_path)
    verification = dict(prepared['verification'], archive_head=archive.head,
                        archive_sha256=archive_sha256,
                        renderer_sha256=renderer_sha256,
                        tokenizer_sha256=tokenizer_sha256)
    lesson = pcc_lesson(
        exercise.skill_id + ' ' + level, model_contract_id, rows,
        archive_sha256=archive_sha256,
        verification_sha256=digest(verification),
        renderer_sha256=renderer_sha256, tokenizer_sha256=tokenizer_sha256,
        skill_id=exercise.skill_id, target_policy=prepared['target_policy'],
    )
    expected_example = training_tokens(rows, tokenize=tokenize,
                                       policy=prepared['target_policy'],
                                       maximum=maximum)
    verification_id = digest(verification)
    return dict(schema=1, lesson=lesson, level=level, answer_mode=answer_mode,
                exercise_id=exercise.identity,
                archive_head=archive.head, archive_sha256=archive_sha256,
                verification=verification, verification_id=verification_id,
                expected_example=expected_example, weights_updated=False,
                pcc_admission_confirmed=False)


def admit_scalar_pcc_lesson(service, operation_id, prepared):
    """Submit once and reconcile PCC's persisted tokens and mask with S³'s plan."""
    lesson = prepared['lesson']
    if getattr(service, 'model', None) != lesson['model_contract_id']:
        raise ValueError('PCC lesson service is bound to another model contract')
    acceptance = service.submit('/cow/training/lessons',
                                dict(operation_id=operation_id, lesson=lesson))
    lesson_id = acceptance.get('lesson_id') if type(acceptance) is dict else None
    if type(lesson_id) is not str or not lesson_id:
        raise ValueError('PCC did not return an immutable lesson identity')
    saved = service.lesson(lesson_id)
    if type(saved) is not dict or saved.get('lesson') != lesson:
        raise ValueError('PCC stored lesson differs from the checked S³ lesson')
    example = saved.get('example')
    expected = prepared['expected_example']
    if type(example) is not dict or any(example.get(key) != expected.get(key)
                                        for key in ('tokens', 'targets', 'loss_mask')):
        raise ValueError('PCC tokenizer output or native loss mask differs from S³ expectation')
    if (example.get('verified') is not True
            or example.get('provenance_sha256') != digest(lesson['evidence'])):
        raise ValueError('PCC did not retain the S³ verification provenance')
    return dict(schema=1, lesson_id=lesson_id, level=prepared['level'],
                target_policy=lesson['target_policy'],
                token_count=len(example['tokens']),
                supervised_tokens=sum(example['loss_mask']),
                token_sha256=digest(example['tokens']),
                loss_mask_sha256=digest(example['loss_mask']),
                archive_sha256=prepared['archive_sha256'],
                verification_id=prepared['verification_id'],
                pcc_admission_confirmed=True, native_update_run=False,
                weights_updated=False, promoted=False)
