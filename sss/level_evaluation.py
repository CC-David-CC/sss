"""Frozen, matched answer/format/composition probes for exact scalar skills.

This first format adapter is intentionally scoped to scalar-answer task families.
It never applies its JSON object schema to proof, array, tool, or other task types.
It uses the same model callback shape and private, one-shot evidence pattern as
``sss.evaluation``; it does not train or promote a model.
"""
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time

from .catalogue import catalog_identity
from .curriculum import exercise_for
from .foundations import Exercise, check, number, reference
from .learning_levels import score_answer, score_composed, score_format, validate_condition
from .profiles import ContextPolicy, ModelProfile
from .records import canonical, digest, file_sha256

FORMAT_SCHEMA = 'math.exact-scalar.answer-object.v1'
ANSWER_CHECKER = 'exact-foundations-tolerant-scalar-v1'
FORMAT_CHECKER = FORMAT_SCHEMA
SCALAR_KINDS = frozenset({
    'add', 'subtract', 'multiply', 'divide', 'remainder', 'equal', 'greater',
    'less', 'minimum', 'maximum', 'absolute', 'power', 'floor', 'ceil',
    'and', 'or', 'not', 'xor', 'place_value', 'round', 'fraction', 'ratio',
    'units', 'area', 'volume', 'linear_equation', 'polynomial_value',
    'definite_integral', 'determinant', 'probability', 'bayes', 'mean',
    'median', 'variance', 'quadratic_minimum',
})
LEVELS = ('answer', 'format', 'composed')


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def _json_load(text):
    return json.loads(text, parse_float=str, object_pairs_hook=_unique_pairs)


def _extract_scalar(completion):
    """Return an unambiguous exact scalar, or None when it cannot be recovered."""
    if type(completion) is not str or len(completion.encode('utf-8')) > 65536:
        return None
    text = completion.strip()
    try:
        value = _json_load(text)
    except Exception:
        value = None
    if type(value) is dict and set(value) == {'answer'}:
        candidate = value['answer']
    elif type(value) in (str, int, Decimal):
        candidate = value
    else:
        candidate = text
    if type(candidate) not in (str, int, Decimal):
        return None
    try:
        number(candidate)
    except Exception:
        return None
    return str(candidate)


def _condition(level, split):
    common = dict(
        level=level, answer_mode='direct', split=split,
        reasoning_checker=None,
    )
    if level == 'answer':
        common.update(supervision='answer_only', format_policy='none',
                      answer_source='skill_task', answer_checker=ANSWER_CHECKER,
                      format_checker=None)
    elif level == 'format':
        common.update(supervision='format_only', format_policy='task_native',
                      answer_source='provided_answer', answer_checker=None,
                      format_checker=FORMAT_CHECKER)
    elif level == 'composed':
        common.update(supervision='format_and_answer', format_policy='task_native',
                      answer_source='skill_task', answer_checker=ANSWER_CHECKER,
                      format_checker=FORMAT_CHECKER)
    else:
        raise ValueError('Unknown response level')
    return validate_condition(common)


def _format_prompt(answer):
    return (
        'This is a formatting exercise. The correct exact numeric answer is '
        + json.dumps(str(answer)) + '. Do not solve another problem. Return a '
        'JSON object with exactly one key, "answer", whose value is a string '
        'containing that exact numeric answer. Example: {"answer":"3/4"}.'
    )


def _composed_prompt(exercise):
    return exercise.prompt + (
        ' For this numeric-answer task, return a JSON object with exactly one '
        'key, "answer", whose value is a string containing the exact numeric '
        'answer. Do not include markdown or extra keys.'
    )


def _format_result(completion, expected):
    try:
        value = _json_load(completion)
    except Exception:
        value = None
    valid = (type(value) is dict and set(value) == {'answer'}
             and type(value['answer']) is str)
    if valid:
        try:
            number(value['answer'])
        except Exception:
            valid = False
    candidate = value['answer'] if valid else _extract_scalar(completion)
    preserved = None
    if candidate is not None:
        try:
            preserved = number(candidate) == number(expected)
        except Exception:
            preserved = False
    return dict(format_valid=valid, content_preserved=preserved)


def _score(level, exercise, expected, completion):
    if level == 'answer':
        return score_answer(completion, lambda text: _semantic(exercise, text))
    if level == 'format':
        return score_format(completion, expected,
                            lambda text, gold: _format_result(text, gold))
    return score_composed(
        completion,
        lambda text: _semantic(exercise, text),
        lambda text: _format_result(text, expected)['format_valid'],
    )


def _semantic(exercise, completion):
    candidate = _extract_scalar(completion)
    if candidate is None:
        return None
    return check(exercise, candidate)


def freeze_level_panel(root, profile, skills, *, cases_per_skill=32, seed=0,
                       split='development'):
    """Create a private matched triplet panel for explicitly supported skills."""
    root = Path(root)
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    if type(cases_per_skill) is not int or not 1 <= cases_per_skill <= 4096:
        raise ValueError('Use an explicit bounded case count')
    if split not in ('development', 'qualification'):
        raise ValueError('Only held-out development or qualification cases are allowed')
    if not skills or len(set(skills)) != len(skills):
        raise ValueError('Distinct explicit skills required')
    graph = __import__('sss.curriculum', fromlist=['foundation_graph']).foundation_graph()
    all_cases = []
    for skill in skills:
        if skill not in graph.nodes or graph.nodes[skill]['status'] != 'implemented':
            raise ValueError('No implemented skill family for ' + skill)
        for index in range(cases_per_skill):
            exercise = exercise_for(skill, split, index, gate='independent', seed=seed)
            if exercise.kind not in SCALAR_KINDS:
                raise ValueError('No qualified task-native scalar format for ' + exercise.kind)
            expected = reference(exercise)
            if not check(exercise, expected):
                raise ValueError('Reference answer did not pass the independent skill checker')
            for level in LEVELS:
                condition = _condition(level, split)
                prompt = (exercise.prompt if level == 'answer' else
                          _format_prompt(expected) if level == 'format' else
                          _composed_prompt(exercise))
                binding = dict(
                    exercise_id=exercise.identity, skill_id=skill, level=level,
                    format_schema=FORMAT_SCHEMA if level != 'answer' else None,
                    condition=condition,
                )
                case_id = digest(binding)
                all_cases.append(dict(
                    id=case_id, **binding, prompt=prompt,
                    expected_answer=expected, exercise=asdict(exercise),
                ))
    source_files = ('foundations.py', 'reasoning.py', 'extended_math.py',
                    'learning_levels.py', 'level_evaluation.py', 'curriculum.py',
                    'catalogue.py', 'graph.py', 'records.py')
    source_hashes = {name: file_sha256(Path(__file__).with_name(name))
                     for name in source_files}
    manifest = dict(
        schema=1, profile=asdict(profile), profile_id=profile.identity,
        catalog_id=catalog_identity(), split=split, seed=seed,
        cases_per_skill=cases_per_skill, cases=all_cases,
        levels=list(LEVELS), format_schema=FORMAT_SCHEMA,
        checker_ids=dict(answer=ANSWER_CHECKER, format=FORMAT_CHECKER),
        source_hashes=source_hashes,
        evaluation_scope='exact scalar skill families only; diagnostic panel, not mastery qualification',
        weights_updated=False,
    )
    manifest['manifest_id'] = digest(manifest)
    with (root / 'frozen-private.json').open('xb') as stream:
        stream.write(canonical(manifest) + b'\n')
    (root / 'frozen-private.json').chmod(0o400)
    return thaw_level_panel(root)


def thaw_level_panel(root):
    root = Path(root)
    manifest = json.loads((root / 'frozen-private.json').read_bytes())
    if manifest.get('manifest_id') != digest({k: v for k, v in manifest.items()
                                                if k != 'manifest_id'}):
        raise ValueError('Frozen level panel was changed')
    current = {name: file_sha256(Path(__file__).with_name(name))
               for name in manifest['source_hashes']}
    if current != manifest['source_hashes']:
        raise ValueError('Checker or generator source changed after freezing')
    from .profiles import ModelProfile
    value = dict(manifest['profile'])
    value['context'] = ContextPolicy(**value['context'])
    profile = ModelProfile(**value)
    if profile.identity != manifest['profile_id'] or catalog_identity() != manifest['catalog_id']:
        raise ValueError('Frozen profile or catalog mismatch')
    cases = {}
    for row in manifest['cases']:
        exercise = Exercise(**row['exercise'])
        if exercise.identity != row['exercise_id'] or row['id'] in cases:
            raise ValueError('Frozen exercise or level identity mismatch')
        if row['level'] not in LEVELS or row['skill_id'] != exercise.skill_id:
            raise ValueError('Invalid frozen level case')
        if _condition(row['level'], manifest['split']) != row['condition']:
            raise ValueError('Frozen condition mismatch')
        cases[row['id']] = dict(row, exercise=exercise)
    return root, cases, manifest


def evaluate_level_panel(frozen, model, *, maximum_seconds=3600):
    """Run each frozen task once and retain independent component verdicts."""
    root, cases, manifest = frozen
    if type(maximum_seconds) not in (int, float) or not 0 < maximum_seconds <= 14400:
        raise ValueError('Explicit bounded wall-clock campaign required')
    outcomes = root / 'outcomes'
    outcomes.mkdir(mode=0o700, exist_ok=False)
    started = time.monotonic()
    grouped = {}
    for case_id, case in cases.items():
        path = outcomes / (case_id + '.json')
        intent = outcomes / (case_id + '-intent.json')
        if time.monotonic() - started >= maximum_seconds:
            record = dict(status='unavailable', reason='campaign_budget', called=False)
            record.update(case_id=case_id, level=case['level'], skill_id=case['skill_id'],
                          profile_id=manifest['profile_id'])
            with path.open('xb') as stream:
                stream.write(canonical(record) + b'\n')
            key = (case['skill_id'], case['level'])
            grouped.setdefault(key, []).append(record)
            continue
        try:
            message, usage = model([
                dict(role='system', content='Answer the task directly. Follow its declared response contract.'),
                dict(role='user', content=case['prompt']),
            ], [], intent)
            if type(message) is not dict or type(message.get('content')) is not str or message.get('tool_calls'):
                raise ValueError('Unsupported endpoint response shape')
            completion = message['content']
            score = _score(case['level'], case['exercise'], case['expected_answer'], completion)
            record = dict(status='scored', score=score, completion=completion,
                          usage=usage, called=True)
        except Exception as error:
            record = dict(status='unavailable', reason=type(error).__name__, called=True)
        record.update(case_id=case_id, level=case['level'], skill_id=case['skill_id'],
                      profile_id=manifest['profile_id'])
        with path.open('xb') as stream:
            stream.write(canonical(record) + b'\n')
        key = (case['skill_id'], case['level'])
        grouped.setdefault(key, []).append(record)

    assessments = []
    for (skill_id, level), records in sorted(grouped.items()):
        names = ('answer', 'format', 'content_preserved', 'joint')
        if level == 'answer':
            names = ('answer',)
        elif level == 'format':
            names = ('format', 'content_preserved', 'joint')
        else:
            names = ('answer', 'format', 'joint')
        metrics = {}
        for name in names:
            statuses = [r.get('score', {}).get(name) for r in records
                        if r.get('status') == 'scored' and r.get('score', {}).get(name)
                        not in ('not_measured', 'not_applicable')]
            pass_count = statuses.count('pass')
            fail_count = statuses.count('fail')
            unscorable_count = statuses.count('unscorable')
            planned = len(records)
            metrics[name] = dict(
                passed=pass_count, failed=fail_count, unscorable=unscorable_count,
                unavailable=sum(r.get('status') != 'scored' for r in records),
                planned=planned, scored=pass_count + fail_count,
                pass_rate=(pass_count / (pass_count + fail_count)
                           if pass_count + fail_count else None),
            )
        assessments.append(dict(skill_id=skill_id, level=level, metrics=metrics,
                                qualification='not_attempted'))
    result = dict(
        schema=1, manifest_id=manifest['manifest_id'], profile_id=manifest['profile_id'],
        format_schema=manifest['format_schema'], assessments=assessments,
        elapsed_seconds=time.monotonic() - started, weights_updated=False,
        promoted=False, scope=manifest['evaluation_scope'],
    )
    with (root / 'assessment.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result
