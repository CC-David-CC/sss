"""Compose owner-installed measurements and exact practice into PCC policies.

PCC retains the learning-round and worker lease. Each panel retains its existing
execution and original-evidence validator. This module supplies no model client,
sampler, training backend, dynamic import registry, or implicit retry.
"""
import copy
from pathlib import Path
import re

from sss.adapters.cow_learning import write_once
from sss.adapters.learning_policy import LearningPolicy
from sss.assessment_growth import plan as growth_plan
from sss.learning import next_skill_block
from sss.paired import compare_frozen_evaluations, measured_candidate_binding, POLICY
from sss.records import canonical, digest, file_sha256


_NAME = re.compile(r'[a-z][a-z0-9_-]{0,63}\Z')
_HASH = re.compile(r'[a-f0-9]{64}\Z')
_ROLES = {'target', 'workflow', 'retention'}


def _hash(value):
    return type(value) is str and _HASH.fullmatch(value) is not None


def _read(path):
    import json
    # The owner evidence directory is not a request-facing configuration surface.
    # Duplicate fields nevertheless cannot rewrite an original durable receipt.
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate original panel receipt field')
            value[key] = item
        return value
    value = json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)
    canonical(value)
    return value


class LearningPanelEvaluator:
    """Explicit target/workflow/retention conjunction over existing evaluators.

    ``panels`` is an ordered sequence of (name, role, installed evaluator).
    ``providers`` is an ordered sequence of (name, installed practice provider).
    These are privileged owner objects, never implementations chosen by a
    student request. At least one panel of every role is mandatory. Multiple
    harness panels are permitted and retain separate measurements.
    """
    def __init__(self, panels, providers, *, model_contract_id, installation_files=None):
        if not _hash(model_contract_id):
            raise ValueError('Exact original model contract required')
        if (type(panels) not in (list, tuple) or not 3 <= len(panels) <= 32
                or type(providers) not in (list, tuple) or not 1 <= len(providers) <= 32):
            raise ValueError('Bounded explicit panels and approved practice providers required')
        self.model = model_contract_id
        self._panels, self._providers = [], []
        seen, roles = set(), set()
        for row in panels:
            if type(row) not in (list, tuple) or len(row) != 3:
                raise ValueError('Exact panel name, role and installed evaluator required')
            name, role, evaluator = row
            if (type(name) is not str or not _NAME.fullmatch(name) or name in seen
                    or type(role) is not str or role not in _ROLES
                    or any(not callable(getattr(evaluator, key, None))
                           for key in ('binding', 'verify', 'validate', 'recover', '__call__'))):
                raise ValueError('Unique panel name and complete installed evaluator required')
            binding = copy.deepcopy(evaluator.binding())
            if (type(binding) is not dict or binding.get('model_contract_id') != self.model
                    or not _hash(binding.get('evaluation_id'))):
                raise ValueError('Every panel must bind this model and a frozen evaluation')
            canonical(binding)
            self._panels.append((name, role, evaluator, binding))
            seen.add(name); roles.add(role)
        if roles != _ROLES:
            raise ValueError('Target, actual workflow and retention panels are all required')
        seen = set()
        for row in providers:
            if type(row) not in (list, tuple) or len(row) != 2:
                raise ValueError('Exact provider name and installed practice provider required')
            name, provider = row
            if (type(name) is not str or not _NAME.fullmatch(name) or name in seen
                    or any(not callable(getattr(provider, key, None))
                           for key in ('binding', 'verify', 'lessons', 'validate_lessons'))):
                raise ValueError('Unique complete installed practice provider required')
            bound = copy.deepcopy(provider.binding())
            if type(bound) is not dict or bound.get('model_contract_id') != self.model:
                raise ValueError('Installed practice must bind this model contract')
            canonical(bound)
            self._providers.append((name, provider, bound)); seen.add(name)
        self._lessons, self._owners = self._materialize_lessons()
        self._sources = {str(Path(p).resolve()): file_sha256(p)
                         for p in (__file__, write_once.__code__.co_filename,
                                   compare_frozen_evaluations.__code__.co_filename,
                                   canonical.__code__.co_filename)}
        if installation_files is not None:
            if type(installation_files) is not dict or not 1<=len(installation_files)<=128:
                raise ValueError('Bounded owner installation source/input pins required')
            for name,expected in installation_files.items():
                if (type(name) is not str or not Path(name).is_absolute() or not _hash(expected)
                        or name in self._sources and self._sources[name]!=expected):
                    raise ValueError('Exact absolute installation file/hash required')
            self._sources.update(installation_files)
        self._binding = dict(schema=1, kind='sss.learning-panels.v1',
            model_contract_id=self.model, sources_sha256=copy.deepcopy(self._sources),
            panels=[dict(panel_id=n, role=r, evaluator=b) for n, r, _, b in self._panels],
            practice_providers=[dict(provider_id=n, provider=b) for n, _, b in self._providers],
            checked_practice_lesson_ids=sorted(self._lessons), no_implicit_retry=True)
        self.identity = digest(self._binding)
        self.verify()

    def _materialize_lessons(self):
        lessons, owners = {}, {}
        for name, provider, bound in self._providers:
            provider.verify()
            if canonical(provider.binding()) != canonical(bound):
                raise ValueError('Installed provider binding changed')
            values = provider.lessons()
            if type(values) is not list or not 1 <= len(values) <= 4096:
                raise ValueError('Bounded nonempty installed lesson membership required')
            selected = []
            for lesson in values:
                if (type(lesson) is not dict or lesson.get('schema') != 2
                        or type(lesson.get('schema')) is not int
                        or lesson.get('model_contract_id') != self.model
                        or lesson.get('scope') != 'owned-training'):
                    raise ValueError('Exact schema-2 owned practice required')
                identity = digest(lesson)
                if identity in lessons:
                    raise ValueError('Duplicate approved lesson across installed providers')
                lessons[identity] = copy.deepcopy(lesson); owners[identity] = name
                selected.append(identity)
            if bound.get('checked_practice_lesson_ids') != sorted(selected):
                raise ValueError('Provider declared membership differs from exact lessons')
        return lessons, owners

    def binding(self):
        return copy.deepcopy(self._binding)

    def verify(self):
        current = dict(schema=1, kind='sss.learning-panels.v1',
            model_contract_id=self.model, sources_sha256=copy.deepcopy(self._sources),
            panels=[dict(panel_id=n, role=r, evaluator=b) for n, r, _, b in self._panels],
            practice_providers=[dict(provider_id=n, provider=b) for n, _, b in self._providers],
            checked_practice_lesson_ids=sorted(self._lessons), no_implicit_retry=True)
        if canonical(current) != canonical(self._binding) or digest(self._binding) != self.identity:
            raise ValueError('Original panel composition binding changed')
        for path, expected in self._sources.items():
            if file_sha256(path) != expected:
                raise ValueError('Panel composition source changed; install a new policy')
        for _, _, panel, bound in self._panels:
            panel.verify()
            if canonical(panel.binding()) != canonical(bound):
                raise ValueError('Original panel binding changed; new baseline required')
        lessons, owners = self._materialize_lessons()
        if lessons != self._lessons or owners != self._owners:
            raise ValueError('Original approved practice changed; new policy required')

    def lessons(self):
        self.verify()
        return [copy.deepcopy(self._lessons[k]) for k in sorted(self._lessons)]

    def validate_lessons(self, records, previous_report):
        self.verify()
        if type(records) is not list or not 1 <= len(records) <= 4096:
            raise ValueError('Explicit bounded exact lesson selection required')
        selected, grouped = set(), {}
        for record in records:
            if type(record) is not dict or not {'lesson_id', 'lesson'} <= set(record):
                raise ValueError('Actual stored lesson records required')
            identity = record['lesson_id']
            if (not _hash(identity) or identity in selected or identity not in self._lessons
                    or record['lesson'] != self._lessons[identity]
                    or digest(record['lesson']) != identity):
                raise ValueError('Selected lesson is not exact installed practice')
            selected.add(identity)
            grouped.setdefault(self._owners[identity], []).append(record)
        for name, provider, _ in self._providers:
            if name in grouped:
                provider.validate_lessons(grouped[name], previous_report)

    def _assemble(self, values):
        if type(values) is not list or len(values) != len(self._panels):
            raise ValueError('Every declared panel needs complete original evidence')
        outcomes, panels, candidate = [], [], None
        for (name, role, _, bound), value in zip(self._panels, values):
            if type(value) is not dict:
                raise ValueError('Each panel requires a complete result object')
            compare_frozen_evaluations(value, value, POLICY)
            if value['evaluation_id'] != bound['evaluation_id']:
                raise ValueError('Frozen panel evaluation changed')
            measured = measured_candidate_binding(value)
            if not measured:
                raise ValueError('Every panel needs the actual composite candidate identity')
            identity = dict(model_sha256=value['model_sha256'], **measured)
            if candidate is not None and identity != candidate:
                raise ValueError('Panels measured different model weights or adapters')
            candidate = identity
            for row in value['outcomes']:
                outcomes.append(dict(id=digest(dict(panel_id=name, case_id=row['id'])),
                    panel_id=name, panel_case_id=row['id'],
                    **{k: row[k] for k in ('skill_id', 'gate', 'passed', 'finished')}))
            panels.append(dict(panel_id=name, role=role, evidence_id=digest(value),
                               evaluation=copy.deepcopy(value)))
        result = dict(schema=1, kind='sss.learning-panel-evaluation.v1', status='COMPLETE',
            evaluator_id=self.identity, evaluation_id=digest(dict(evaluator_id=self.identity)),
            runtime_id=digest(dict(kind='sss.learning-panel-runtime.v1',
                sources=self._sources, panels=[dict(panel_id=p['panel_id'], role=p['role'],
                    runtime_id=p['evaluation']['runtime_id']) for p in panels])),
            **candidate, cases=len(outcomes), passed=sum(r['passed'] for r in outcomes),
            finished=sum(r['finished'] for r in outcomes), outcomes=outcomes, panels=panels,
            weights_updated=False, promoted=False)
        compare_frozen_evaluations(result, result, POLICY)
        return result

    def combine(self, values, candidate):
        self.verify()
        # Panel validators retain authority over their raw runtime evidence.
        if type(values) is not list or len(values) != len(self._panels):
            raise ValueError('Every declared panel needs complete original evidence')
        for (_, _, panel, _), value in zip(self._panels, values):
            panel.validate(value, copy.deepcopy(candidate))
        return self._assemble(values)

    def inspect(self, value):
        """Recheck committed composition; raw evidence is checked by validate/recover."""
        self.verify()
        if (type(value) is not dict or type(value.get('panels')) is not list
                or len(value['panels']) != len(self._panels)
                or any(type(p) is not dict or set(p) != {'panel_id','role','evidence_id','evaluation'}
                       for p in value['panels'])):
            raise ValueError('Complete original panel composition required')
        expected = self._assemble([p['evaluation'] for p in value['panels']])
        if canonical(value) != canonical(expected):
            raise ValueError('Original panel composition or aggregate was changed')
        return [copy.deepcopy(p['evaluation']) for p in value['panels']]

    def validate(self, value, candidate):
        values = self.inspect(value)
        if canonical(self.combine(values, candidate)) != canonical(value):
            raise ValueError('Panel candidate evidence changed')

    def _intent(self, candidate):
        canonical(candidate)
        return dict(schema=1, evaluator_id=self.identity, candidate=copy.deepcopy(candidate),
                    binding=self.binding(), no_implicit_retry=True)

    def __call__(self, candidate, directory, worker_fd):
        self.verify(); directory = Path(directory).absolute()
        if directory.is_symlink() or not directory.is_dir() or any(directory.iterdir()):
            raise ValueError('Fresh owner-created evaluation directory required')
        if type(worker_fd) is not int or worker_fd < 0:
            raise ValueError('Existing PCC worker lease descriptor required')
        write_once(directory / 'panel-intent-private.json', self._intent(candidate))
        values = []
        for index, (name, role, panel, _) in enumerate(self._panels):
            child = directory / ('panel-%02d' % index); child.mkdir(mode=0o700)
            write_once(directory / ('panel-%02d-start-private.json' % index),
                       dict(panel_id=name, role=role, evaluator_id=self.identity))
            value = panel(copy.deepcopy(candidate), child, worker_fd)
            panel.validate(value, copy.deepcopy(candidate))
            write_once(directory / ('panel-%02d-result-private.json' % index), value)
            values.append(value)
        result = self.combine(values, candidate)
        write_once(directory / 'panel-result-private.json', result)
        return result

    def recover(self, candidate, directory):
        self.verify(); directory = Path(directory).absolute()
        if directory.is_symlink():
            raise ValueError('Original owner evaluation directory cannot be a symlink')
        intent = directory / 'panel-intent-private.json'
        if not intent.is_file():
            return None
        if canonical(_read(intent)) != canonical(self._intent(candidate)):
            raise ValueError('Original composite evaluation intent changed')
        values = []
        for index, (name, role, panel, _) in enumerate(self._panels):
            start = directory / ('panel-%02d-start-private.json' % index)
            if not start.is_file():
                raise ValueError('Panel never dispatched; no implicit continuation or retry')
            if canonical(_read(start)) != canonical(dict(panel_id=name, role=role, evaluator_id=self.identity)):
                raise ValueError('Original panel dispatch intent changed')
            # Always delegate original-process and raw-evidence checks, even when
            # the parent's copied result survived. A copied summary is not proof.
            value = panel.recover(copy.deepcopy(candidate), directory / ('panel-%02d' % index))
            if value is None:
                raise ValueError('Original panel has no recoverable complete evidence')
            panel.validate(value, copy.deepcopy(candidate))
            copied = directory / ('panel-%02d-result-private.json' % index)
            if copied.exists():
                if canonical(_read(copied)) != canonical(value):
                    raise ValueError('Saved panel result differs from original evidence')
            else:
                write_once(copied, value)
            values.append(value)
        result = self.combine(values, candidate)
        final = directory / 'panel-result-private.json'
        if final.exists():
            if canonical(_read(final)) != canonical(result):
                raise ValueError('Saved aggregate differs from original panels')
        else:
            write_once(final, result)
        return result


class PanelLearningPolicy(LearningPolicy):
    """Existing PCC learning policy with visible per-panel learning/forgetting."""
    def __init__(self, evaluator, training, **options):
        if not isinstance(evaluator, LearningPanelEvaluator):
            raise ValueError('Installed complete learning-panel evaluator required')
        super().__init__(evaluator, training, **options)

    def analyze(self, baseline, parent, candidate):
        self.verify()
        panel_sets = [self.evaluator.inspect(value) for value in (baseline, parent, candidate)]
        result = super().analyze(baseline, parent, candidate)
        panels = []
        for index, (name, role, _, _) in enumerate(self.evaluator._panels):
            left, middle, right = [values[index] for values in panel_sets]
            panels.append(dict(panel_id=name, role=role,
                report=next_skill_block(left, middle, right),
                assessment=growth_plan(right, **self.assessment)))
        report = dict(schema=1, kind='sss.panel-learning-report.v1',
            aggregate=result['report'], panels=panels,
            working_parent=result['working_parent'], promoted=False)
        report['report_id'] = digest(report)
        result['report'] = report
        return result
