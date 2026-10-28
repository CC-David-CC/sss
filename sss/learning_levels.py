"""Separate answer, formatting, and composed learning/evaluation conditions.

This module defines evidence semantics only. It does not call a model, create a
dataset, construct PCC loss masks, train weights, or promote a candidate.
"""

LEVELS = ('answer', 'format', 'composed')
ANSWER_MODES = ('direct', 'reasoning')
SUPERVISION = ('answer_only', 'reasoning_and_answer', 'format_only',
               'format_and_answer', 'reasoning_format_and_answer')
FORMATS = ('none', 'task_native', 'declared_schema')


class CheckerContractError(ValueError):
    """A checker returned evidence outside the declared scoring contract."""


def validate_condition(condition):
    """Validate one immutable lesson/evaluation condition description.

    Required checker IDs bind the condition to task-specific graders. The IDs are
    labels only; the caller must separately bind them to trusted checker code.
    """
    required = {
        'level', 'answer_mode', 'supervision', 'format_policy',
        'answer_source', 'answer_checker', 'format_checker', 'reasoning_checker',
        'split',
    }
    if type(condition) is not dict or set(condition) != required:
        raise ValueError('Condition must declare every level, checker, source, and split field')
    if condition['level'] not in LEVELS:
        raise ValueError('Unknown learning level')
    if condition['answer_mode'] not in ANSWER_MODES:
        raise ValueError('Unknown answer mode')
    if condition['supervision'] not in SUPERVISION:
        raise ValueError('Unknown supervised target')
    if condition['format_policy'] not in FORMATS:
        raise ValueError('Unknown format policy')
    if condition['answer_source'] not in ('skill_task', 'provided_answer'):
        raise ValueError('Unknown answer source')
    for field in ('answer_checker', 'format_checker', 'reasoning_checker', 'split'):
        value = condition[field]
        if value is not None and (type(value) is not str or not value.strip()):
            raise ValueError('Checker and split identities must be nonempty strings or null')

    level = condition['level']
    if level == 'answer':
        if condition['answer_source'] != 'skill_task' or condition['answer_checker'] is None:
            raise ValueError('Answer level requires a skill task and semantic answer checker')
        if condition['format_policy'] != 'none' or condition['format_checker'] is not None:
            raise ValueError('Answer level must not impose a formatting condition')
        expected = 'reasoning_and_answer' if condition['answer_mode'] == 'reasoning' else 'answer_only'
        if condition['supervision'] != expected:
            raise ValueError('Answer level supervision must match its direct/reasoning mode')
    elif level == 'format':
        if condition['answer_source'] != 'provided_answer':
            raise ValueError('Format level must supply the correct answer')
        if condition['answer_checker'] is not None:
            raise ValueError('Format level does not test skill-task correctness')
        if condition['format_policy'] == 'none' or condition['format_checker'] is None:
            raise ValueError('Format level requires a declared task format and checker')
        if condition['answer_mode'] != 'direct' or condition['supervision'] != 'format_only':
            raise ValueError('Format-only lessons have no reasoning target')
    else:
        if condition['answer_source'] != 'skill_task' or condition['answer_checker'] is None:
            raise ValueError('Composed level requires a skill task and semantic answer checker')
        if condition['format_policy'] == 'none' or condition['format_checker'] is None:
            raise ValueError('Composed level requires a declared task format and checker')
        expected = ('reasoning_format_and_answer' if condition['answer_mode'] == 'reasoning'
                    else 'format_and_answer')
        if condition['supervision'] != expected:
            raise ValueError('Composed supervision must cover its answer, format, and reasoning mode')

    if condition['answer_mode'] == 'reasoning':
        if condition['supervision'] not in ('reasoning_and_answer', 'reasoning_format_and_answer') or condition['reasoning_checker'] is None:
            raise ValueError('Reasoning mode requires a reasoning target and checker')
    elif condition['reasoning_checker'] is not None:
        raise ValueError('Direct mode must not bind a reasoning checker')

    return dict(condition)


def _verdict(value, name):
    if value is None:
        return 'unscorable'
    if type(value) is not bool:
        raise CheckerContractError(name + ' checker must return bool or None')
    return 'pass' if value else 'fail'


def score_answer(completion, checker):
    """Score semantic answer correctness independently of output-format validity."""
    try:
        answer = _verdict(checker(completion), 'Answer')
    except CheckerContractError:
        raise
    except Exception:
        answer = 'unscorable'
    return dict(answer=answer, format='not_measured', joint='not_applicable')


def score_reasoning(completion, checker):
    """Score checkable reasoning separately from the final answer."""
    try:
        reasoning = _verdict(checker(completion), 'Reasoning')
    except CheckerContractError:
        raise
    except Exception:
        reasoning = 'unscorable'
    return dict(reasoning=reasoning)


def score_format(completion, provided_answer, checker):
    """Score a format-only response against content supplied in the prompt.

    The task-specific checker returns exactly ``format_valid`` and
    ``content_preserved`` booleans (or null when that field cannot be scored).
    """
    try:
        result = checker(completion, provided_answer)
        if type(result) is not dict or set(result) != {'format_valid', 'content_preserved'}:
            raise CheckerContractError('Format checker must return two independent verdicts')
        format_status = _verdict(result['format_valid'], 'Format')
        content_status = _verdict(result['content_preserved'], 'Content-preservation')
    except CheckerContractError:
        raise
    except Exception:
        format_status = content_status = 'unscorable'
    joint = ('pass' if format_status == content_status == 'pass' else
             'fail' if 'fail' in (format_status, content_status) else 'unscorable')
    return dict(answer='not_measured', format=format_status,
                content_preserved=content_status, joint=joint)


def score_composed(completion, answer_checker, format_checker):
    """Score a fresh solve-and-format response with independent graders.

    The semantic checker should recover the task answer when possible even from
    malformed output. The format checker must inspect the task-native schema. A
    formatting failure therefore does not automatically become an answer failure.
    """
    try:
        answer = _verdict(answer_checker(completion), 'Answer')
    except CheckerContractError:
        raise
    except Exception:
        answer = 'unscorable'
    try:
        format_status = _verdict(format_checker(completion), 'Format')
    except CheckerContractError:
        raise
    except Exception:
        format_status = 'unscorable'
    joint = ('pass' if answer == format_status == 'pass' else
             'fail' if 'fail' in (answer, format_status) else 'unscorable')
    return dict(answer=answer, format=format_status, joint=joint)


def score_reasoning_composed(completion, reasoning_checker, answer_checker, format_checker):
    """Score a reasoning-mode composed response without hiding component failures."""
    reasoning = score_reasoning(completion, reasoning_checker)['reasoning']
    answer = score_answer(completion, answer_checker)['answer']
    format_status = score_composed(completion, lambda _: True, format_checker)['format']
    statuses = (reasoning, answer, format_status)
    joint = ('pass' if all(value == 'pass' for value in statuses) else
             'fail' if 'fail' in statuses else 'unscorable')
    return dict(reasoning=reasoning, answer=answer, format=format_status, joint=joint)
