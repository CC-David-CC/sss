"""Bounded graph practice for the existing PCC lesson and S3 guard boundaries.

No model runner, GPU policy, tool grants or promotion lives here. The host supplies
its actual renderer and an owned, settled inference session for each candidate.
This small active pack is not the statistical mastery qualification suite.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json

from sss.curriculum import foundation_graph, exercise_for
from sss.evaluation import implementation_identity
from sss.foundations import Exercise, check, reference
from sss.guard import SkillTree
from sss.mastery import GATES
from sss.records import digest, canonical, file_sha256

SYSTEM = ('Follow the requested answer format exactly. This is a direct-answer '
          'assessment; no tools are available.')


def _write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value) + b'\n')


def build_pack(skills, *, seed, practice_per_gate=8, checks_per_gate=2, generation_profile="legacy-v1"):
    """Freeze explicit skills plus all prerequisites; never redraw a check.

    Each skill has independent/composed/recovery practice and separate
    development/blind checks. Repeated evaluation questions fail admission,
    including cross-split repeats. Practice repetition is recorded as rehearsal,
    never counted as distinct questions or independent mastery evidence.
    """
    if (type(seed) is not int or not skills or len(set(skills)) != len(skills)
            or type(practice_per_gate) is not int or not 2 <= practice_per_gate <= 128
            or type(checks_per_gate) is not int or not 1 <= checks_per_gate <= (32 if generation_profile in ("without-replacement-v1", "without-replacement-v2", "without-replacement-v3") else 16)):
        raise ValueError('Explicit bounded seed, skills and per-gate counts required')
    if generation_profile not in ('legacy-v1', 'without-replacement-v1', 'without-replacement-v2', 'without-replacement-v3'):
        raise ValueError('Unknown frozen generator profile')
    generator = exercise_for
    if generation_profile == 'without-replacement-v1':
        from sss.curriculum_unique import unique_exercise_for
        generator = unique_exercise_for
    elif generation_profile == 'without-replacement-v2':
        from sss.curriculum_unique_v2 import unique_exercise_for
        generator = unique_exercise_for
    elif generation_profile == 'without-replacement-v3':
        from sss.curriculum_unique_v3 import unique_exercise_for
        generator = unique_exercise_for
    graph = foundation_graph()
    included = set(skills)
    for key in skills:
        included.update(graph.prerequisites(key))
    ordered = [key for key in graph.order if key in included]
    if any(graph.nodes[key]['status'] != 'implemented' for key in ordered):
        raise ValueError('Every active prerequisite needs an implemented generator')
    if len(ordered) * len(GATES) * checks_per_gate * 2 > 2048:
        raise ValueError('Active guard exceeds its frozen evaluation case budget')
    rows = []
    seen = set()
    repeated_practice = 0
    for split, count in [('practice', practice_per_gate),
                         ('development', checks_per_gate), ('qualification', checks_per_gate)]:
        for gate in GATES:
            for index in range(count):
                for skill in ordered:
                    exercise = generator(skill, split, index, gate=gate, seed=seed)
                    key = hashlib.sha256(exercise.prompt.encode()).hexdigest()
                    if key in seen and split != 'practice':
                        raise ValueError('Repeated frozen question; no automatic redraw')
                    if key in seen:
                        repeated_practice += 1
                    seen.add(key)
                    rows.append(asdict(exercise))
    value = dict(schema=1, purpose='bounded_training_pilot', graph_id=graph.identity,
                 implementation_id=implementation_identity(), requested_skills=list(skills),
                 skills=ordered, requires={k: graph.nodes[k]['requires'] for k in ordered},
                 seed=seed, practice_per_gate=practice_per_gate, checks_per_gate=checks_per_gate,
                 exercises=rows, repeated_practice_questions=repeated_practice,
                 formal_mastery_qualification=False)
    if generation_profile in ('without-replacement-v2', 'without-replacement-v3'):
        from sss import curriculum_unique, curriculum_unique_v2
        modules = [curriculum_unique, curriculum_unique_v2]
        if generation_profile == 'without-replacement-v3':
            from sss import curriculum_unique_v3
            modules.append(curriculum_unique_v3)
        value.update(generation_profile=generation_profile,
            generation_sources_sha256={Path(m.__file__).name: file_sha256(Path(m.__file__))
                for m in modules})
    elif generation_profile != 'legacy-v1':
        from sss import curriculum_unique
        value.update(generation_profile=generation_profile,
                     generation_source_sha256=file_sha256(Path(curriculum_unique.__file__)))
    return dict(value, pack_id=digest(value))


def validate_pack(pack):
    if pack.get('pack_id') != digest({k: v for k, v in pack.items() if k != 'pack_id'}):
        raise ValueError('Practice pack identity differs')
    expected = build_pack(pack['requested_skills'], seed=pack['seed'],
                          practice_per_gate=pack['practice_per_gate'],
                          checks_per_gate=pack['checks_per_gate'],
                          generation_profile=pack.get('generation_profile', 'legacy-v1'))
    if pack != expected:
        raise ValueError('Pack differs from its frozen generator, graph or split contract')
    return [Exercise(**row) for row in pack['exercises']]


def initialize(service, pack, render, *, renderer_sha256, tokenizer_sha256,
               target_policy='actions_answer'):
    """Admit reference practice through PCC schema 2 with exact host rendering.

    render(exercise, checked_answer) returns PCC's verified rendered segments.
    Its boundaries and token limits are checked by the actual LessonService.
    This initializer generates no thinking text; a thought-bearing curriculum
    needs independently verified reasoning spans, not unverified model traces.
    """
    exercises = validate_pack(pack)
    provenance = service.root / ('foundation-pack-' + pack['pack_id'])
    provenance.mkdir(mode=0o700, exist_ok=False)
    _write(provenance / 'pack-private.json', pack)
    practice = {key: [] for key in pack['skills']}
    checks = {split: {key: [] for key in pack['skills']} for split in ('validation', 'blind')}
    # Stage and tokenize every lesson before recording any. An overlong example
    # is refused as a whole, never shortened or dropped from the curriculum.
    staged = []
    protected = [e.prompt for e in exercises if e.split != 'practice']
    for exercise in exercises:
        if exercise.split != 'practice':
            split = 'validation' if exercise.split == 'development' else 'blind'
            checks[split][exercise.skill_id].append(dict(
                id=hashlib.sha256(exercise.prompt.encode()).hexdigest(), prompt=exercise.prompt,
                checker=dict(name='exact-foundations-v1', version=1, case_id=exercise.identity)))
            continue
        answer = reference(exercise)
        if not check(exercise, answer):
            raise ValueError('Practice reference failed its independent checker')
        segments = render(exercise, answer)
        if any(row.get('kind') == 'thinking' for row in segments):
            raise ValueError('This initializer does not attest generated reasoning')
        text = ''.join(row['rendered'] for row in segments)
        if any(prompt in text for prompt in protected):
            raise ValueError('Protected material appeared inside rendered practice')
        evidence = dict(exercise=asdict(exercise), answer=answer, passed=True,
                        origin='owned synthetic practice; not an observed model failure')
        lesson = dict(schema=2, title=exercise.skill_id + ' ' + exercise.gate,
                      model_contract_id=service.model, skill_id=exercise.skill_id,
                      segments=segments, target_policy=target_policy, scope='owned-training',
                      evidence=dict(method='sss-verified-episode-v1', archive_sha256=digest(evidence),
                                    verification_sha256=digest(dict(exercise_id=exercise.identity,
                                        checker_id=pack['implementation_id'], answer=answer, passed=True)),
                                    renderer_sha256=renderer_sha256, tokenizer_sha256=tokenizer_sha256))
        service._example(lesson, digest(lesson))
        staged.append((exercise, lesson, evidence))
    for exercise, lesson, evidence in staged:
        _write(provenance / (exercise.identity + '.json'), evidence)
        accepted = service.submit('/cow/training/lessons', dict(
            operation_id='foundation-' + digest(lesson)[:48], lesson=lesson))
        practice[exercise.skill_id].append(accepted['lesson_id'])
    with (provenance / 'finished-training-examples.txt').open('x', encoding='utf-8') as stream:
        stream.write('OWNED SYNTHETIC PRACTICE — not evaluation data or a record of model success.\n')
        for exercise, lesson, evidence in staged:
            stream.write('\nExample ' + exercise.identity + '\nSkill: ' + exercise.skill_id
                         + '\nGate: ' + exercise.gate + '\nQuestion:\n' + exercise.prompt
                         + '\nChecked answer:\n' + evidence['answer'] + '\n')
    root = dict(id='foundation-pilot', title='Bounded foundation pilot', parent=None,
                minimum_accuracy=1., practice_lesson_ids=[], validation=[], blind=[])
    nodes = [root] + [dict(id=key, title=key, parent=root['id'], minimum_accuracy=1.,
                         practice_lesson_ids=practice[key], validation=checks['validation'][key],
                         blind=checks['blind'][key]) for key in pack['skills']]
    tree = SkillTree(dict(schema=1, model_contract_id=service.model, nodes=nodes))
    _write(provenance / 'active-tree-private.json', tree.document)
    _write(provenance / 'admission.json', dict(pack_id=pack['pack_id'], tree_id=tree.identity,
        lessons=sum(map(len, practice.values())), weights_updated=False,
        formal_mastery_qualification=False, prerequisites=pack['requires']))
    return tree


class FoundationGuardEvaluator:
    """Use a host-owned real inference session, with exact candidate bindings.

    session(candidate, path, inherited_worker_fd) is a context manager yielding
    (model_callback, receipt). The callback has the existing S3 OpenAIModel
    interface. The receipt has base_sha256, adapter_sha256 and runtime_id. The
    host owns GPU admission, timeouts, native profiles and actual settlement.
    No fallback, retries, answer repair, or evaluation-to-practice export occurs.
    """
    def __init__(self, tree, pack, session, *, base_sha256, runtime_id):
        exercises = validate_pack(pack)
        self.exercises = {e.identity: e for e in exercises if e.split != 'practice'}
        self.tree, self.session = tree, session
        self.base_sha256, self.runtime_id = base_sha256, runtime_id
        expected = {}
        for e in self.exercises.values():
            key = hashlib.sha256(e.prompt.encode()).hexdigest()
            expected[key] = dict(id=key, prompt=e.prompt,
                checker=dict(name='exact-foundations-v1', version=1, case_id=e.identity),
                split='validation' if e.split == 'development' else 'blind')
        if tree.cases != expected:
            raise ValueError('Active guard checks differ from the frozen practice pack')
        self.contract_id = digest(dict(pack_id=pack['pack_id'], tree_id=tree.identity,
            base_sha256=base_sha256, runtime_id=runtime_id,
            adapter_source_sha256=file_sha256(__file__)))

    def __call__(self, candidate, split, path, worker_fd):
        if split not in ('validation', 'blind'):
            raise ValueError('Unknown protected split')
        expected = dict(base_sha256=self.base_sha256, adapter_sha256=None, runtime_id=self.runtime_id)
        if candidate:
            if file_sha256(candidate['candidate_path']) != candidate['candidate_sha256']:
                raise ValueError('Candidate file differs before evaluation')
            if candidate['mode'] == 'full':
                expected['base_sha256'] = candidate['candidate_sha256']
            elif candidate['mode'] == 'lora':
                expected['adapter_sha256'] = candidate['candidate_sha256']
            else:
                raise ValueError('Unknown native candidate mode')
        path = Path(path); path.mkdir(mode=0o700, exist_ok=False)
        rows = []
        with self.session(candidate, path, worker_fd) as (model, receipt):
            if receipt != expected:
                raise ValueError('Inference session is not the requested candidate/runtime')
            _write(path / 'serving-identity.json', receipt)
            for row in self.tree.rows(split):
                e = self.exercises[row['checker']['case_id']]
                message, usage = model([dict(role='system', content=SYSTEM),
                    dict(role='user', content=e.prompt)], [], path / (row['id'] + '-intent.json'))
                if type(message) is not dict or type(message.get('content')) is not str:
                    raise ValueError('Missing model answer; infrastructure uncertainty is not a grade')
                record = dict(id=row['id'], passed=not message.get('tool_calls') and check(e, message['content']),
                              gate=e.gate, message=message, usage=usage)
                _write(path / (row['id'] + '-observation-private.json'), record)
                rows.append(record)
        _write(path / 'observations-private.json', rows)
        return rows
