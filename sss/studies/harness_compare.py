"""Frozen, offline comparisons of host-owned harness executions.

This module plans comparisons and checks evidence. It cannot execute a tool,
call a model, acquire a GPU, grant permissions, retry a job, or adopt a recipe.
Original host receipts remain authoritative. See docs/HARNESS-COMPARISON.md.
"""
import argparse
import json
import math
from pathlib import Path
import re

from sss.records import canonical, digest


CONDITIONS = ('baseline', 'general_probe', 'task_probe', 'composed')
SURFACES = ('instructions', 'tool_guidance', 'memory_instructions', 'skills')
COUNTERS = ('model_calls', 'input_tokens', 'output_tokens', 'tool_calls', 'wall_seconds')
HEX = re.compile(r'[0-9a-f]{64}\Z')
NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}\Z')


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys.split()):
        raise ValueError('Unexpected or missing fields; expected: ' + keys)


def _name(value):
    if type(value) is not str or not NAME.fullmatch(value):
        raise ValueError('A bounded explicit identifier is required')


def _sha(value):
    if type(value) is not str or not HEX.fullmatch(value):
        raise ValueError('An explicit SHA-256 identity is required')


def _text(value):
    if type(value) is not str or not value or len(value) > 16384:
        raise ValueError('Bounded nonempty text is required')


def _unique(rows, key):
    if type(rows) is not list:
        raise ValueError('Expected a list')
    result = {}
    for row in rows:
        if type(row) is not dict or key not in row:
            raise ValueError('Missing record identity')
        identity = row[key]
        _text(identity)
        if identity in result:
            raise ValueError('Duplicate record identity: ' + identity)
        result[identity] = row
    return result


def _counts(value, *, optional=False):
    _keys(value, ' '.join(COUNTERS))
    for key, count in value.items():
        if optional and count is None:
            continue
        if key == 'wall_seconds':
            valid = type(count) in (int, float) and math.isfinite(count) and count >= 0
        else:
            valid = type(count) is int and count >= 0
        if not valid:
            raise ValueError('Invalid usage count: ' + key)


def _case(case):
    _keys(case, 'id input_sha256 fixture_sha256 checker_sha256 check_ids')
    _name(case['id'])
    for key in ('input_sha256', 'fixture_sha256', 'checker_sha256'):
        _sha(case[key])
    ids = case['check_ids']
    if type(ids) is not list or not 1 <= len(ids) <= 128:
        raise ValueError('Each task needs explicit independent check IDs')
    for value in ids:
        _name(value)
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate check ID')


class HarnessStudy:
    """A detached specification, not a scheduling or execution ledger."""
    def __init__(self, document):
        data = json.loads(canonical(document))
        _keys(data, 'schema name evidence_kind model environment budget editor harnesses tasks')
        if type(data['schema']) is not int or data['schema'] != 1:
            raise ValueError('Unsupported comparison schema')
        _name(data['name'])
        if data['evidence_kind'] not in ('synthetic_contract', 'host_observed'):
            raise ValueError('Distinguish synthetic contract fixtures from actual host observations')
        for key, fields in (
                ('model', 'weights_sha256 tokenizer_sha256 template_sha256 sampling_sha256 runtime_sha256'),
                ('environment', 'capabilities_sha256 isolation_sha256 tools_sha256'),
                ('editor', 'model_sha256 configuration_sha256')):
            _keys(data[key], fields)
            for value in data[key].values():
                _sha(value)
        _counts(data['budget'])
        if any(value <= 0 for value in data['budget'].values()):
            raise ValueError('Positive per-execution budgets are required')
        harnesses = _unique(data['harnesses'], 'id')
        tasks = _unique(data['tasks'], 'id')
        if not 1 <= len(harnesses) <= 16 or not 1 <= len(tasks) <= 128:
            raise ValueError('Study size is outside the bounded comparison')
        for harness in harnesses.values():
            _keys(harness, 'id revision base_sha256 transport adapter_revision qualification_sha256')
            _name(harness['id'])
            for key in ('revision', 'transport', 'adapter_revision'):
                _text(harness[key])
            _sha(harness['base_sha256'])
            if harness['qualification_sha256'] is not None:
                _sha(harness['qualification_sha256'])
        all_cases = []
        for task in tasks.values():
            _keys(task, 'id development transfer retention')
            _name(task['id'])
            for key in ('transfer', 'retention'):
                if type(task[key]) is not list or len(task[key]) > 64:
                    raise ValueError('Bounded follow-up case lists are required')
            cases = [task['development'], *task['transfer'], *task['retention']]
            for case in cases:
                _case(case)
            _unique(cases, 'id')
            all_cases.extend(cases)
        # Follow-up questions cannot be relabelled versions of a development
        # input, including development tasks elsewhere in the same study.
        inputs = [case['input_sha256'] for case in all_cases]
        if len(inputs) != len(set(inputs)):
            raise ValueError('Development/transfer/retention inputs must be distinct')
        self._bytes = canonical(data)

    @property
    def identity(self):
        return digest(self.document())

    def document(self):
        return json.loads(self._bytes)

    def plan(self):
        data = self.document()
        rows = []
        for harness in data['harnesses']:
            for task in data['tasks']:
                for phase in ('development', 'transfer', 'retention'):
                    cases = [task[phase]] if phase == 'development' else task[phase]
                    conditions = CONDITIONS if phase == 'development' else ('baseline', 'composed')
                    for case in cases:
                        for condition in conditions:
                            row = dict(harness=harness['id'], task=task['id'], case=case['id'],
                                       phase=phase, condition=condition)
                            row['execution_id'] = digest([self.identity, row])
                            rows.append(row)
        units = len(data['tasks']) * len(data['harnesses'])
        return dict(schema=1, study_sha256=self.identity,
                    development_executions=4 * units,
                    followup_executions=len(rows) - 4 * units,
                    minimum_editor_sessions=3 * units,
                    editor_calls_included_in_task_count=False, executions=rows)


def _case_for(data, slot):
    task = next(t for t in data['tasks'] if t['id'] == slot['task'])
    cases = [task['development']] if slot['phase'] == 'development' else task[slot['phase']]
    return next(case for case in cases if case['id'] == slot['case'])


def _dependencies(slots, harness, task, condition):
    names = ('baseline',) if condition in ('general_probe', 'task_probe') else CONDITIONS[:3]
    return [slot['execution_id'] for slot in slots.values()
            if slot['harness'] == harness and slot['task'] == task
            and slot['phase'] == 'development' and slot['condition'] in names]


def _validate(study, evidence):
    """Check binding and causal visibility; never infer real execution from names."""
    data = study.document()
    evidence = json.loads(canonical(evidence))
    _keys(evidence, 'schema study_sha256 variants runs grades traces')
    if evidence['schema'] != 1 or evidence['study_sha256'] != study.identity:
        raise ValueError('Evidence belongs to a different frozen study')
    slots = _unique(study.plan()['executions'], 'execution_id')
    runs = _unique(evidence['runs'], 'execution_id')
    grades = _unique(evidence['grades'], 'execution_id')
    traces = _unique(evidence['traces'], 'execution_id')
    harnesses = _unique(data['harnesses'], 'id')
    variants = {}
    operations = set()
    for variant in evidence['variants']:
        _keys(variant, 'harness task condition base_sha256 changes evidence editor_sha256 editor_usage hypothesis')
        key = (variant['harness'], variant['task'], variant['condition'])
        if key in variants or key[0] not in harnesses or key[2] not in CONDITIONS[1:]:
            raise ValueError('Unknown or duplicate variant')
        if key[1] not in {t['id'] for t in data['tasks']}:
            raise ValueError('Unknown variant task')
        if variant['base_sha256'] != harnesses[key[0]]['base_sha256']:
            raise ValueError('Every variant starts from this harness base')
        if type(variant['changes']) is not dict or not set(variant['changes']) <= set(SURFACES):
            raise ValueError('Variant changes an unsupported surface or execution authority')
        for value in variant['changes'].values():
            _sha(value)
        _text(variant['hypothesis'])
        if variant['editor_sha256'] != digest(data['editor']):
            raise ValueError('Proposer/composer model or configuration differs')
        _counts(variant['editor_usage'])
        if variant['editor_usage']['model_calls'] < 1:
            raise ValueError('Record the actual proposer/composer calls separately')
        dependencies = _dependencies(slots, *key)
        refs = _unique(variant['evidence'], 'execution_id')
        if set(refs) != set(dependencies):
            raise ValueError('Variant lacks required earlier probes or includes future/held-out evidence')
        for execution, ref in refs.items():
            _keys(ref, 'execution_id receipt_sha256 trace_sha256')
            run = runs.get(execution)
            if not run or not run['settled'] or run['outcome'] != 'complete':
                raise ValueError('Reconcile prior executions before proposing or composing')
            if any(ref[k] != run[k] for k in ('receipt_sha256', 'trace_sha256')):
                raise ValueError('Variant evidence differs from original host observations')
        variants[key] = variant
    for execution, run in runs.items():
        _keys(run, 'execution_id operation_id receipt_sha256 trace_sha256 artifact_sha256 '
                   'model_sha256 environment_sha256 harness_sha256 task_sha256 budget_sha256 '
                   'configuration_sha256 variant_sha256 '
                   'settled outcome usage')
        if execution not in slots:
            raise ValueError('Unplanned execution or seed repeat')
        slot = slots[execution]
        harness = harnesses[slot['harness']]
        _text(run['operation_id'])
        operation = (slot['harness'], run['operation_id'])
        if operation in operations:
            raise ValueError('An original host operation cannot stand for two executions')
        operations.add(operation)
        for field in ('receipt_sha256', 'trace_sha256', 'artifact_sha256'):
            _sha(run[field])
        if (run['model_sha256'] != digest(data['model'])
                or run['environment_sha256'] != digest(data['environment'])):
            raise ValueError('Model, sampling, tools, permissions or isolation differs')
        if (run['harness_sha256'] != digest(harness)
                or run['task_sha256'] != digest(_case_for(data, slot))
                or run['budget_sha256'] != digest(data['budget'])):
            raise ValueError('Harness, task, starting files or admitted budget differs')
        if run['outcome'] not in ('complete', 'infrastructure_error', 'uncertain'):
            raise ValueError('Unknown host outcome; wrong answers use separate grading')
        if type(run['settled']) is not bool or (run['outcome'] == 'uncertain') == run['settled']:
            raise ValueError('Uncertain operations cannot release their ownership')
        _counts(run['usage'], optional=run['outcome'] != 'complete')
        changes = {}
        variant_id = None
        if slot['condition'] != 'baseline':
            key = (slot['harness'], slot['task'], slot['condition'])
            if key not in variants:
                raise ValueError('Execution lacks its frozen variant')
            changes = variants[key]['changes']
            variant_id = digest(variants[key])
        expected = digest(dict(base_sha256=harness['base_sha256'], changes=changes))
        if run['configuration_sha256'] != expected or run['variant_sha256'] != variant_id:
            raise ValueError('Applied configuration differs from the frozen variant')
        if slot['phase'] != 'development':
            prior = next(s['execution_id'] for s in slots.values()
                         if s['task'] == slot['task'] and s['harness'] == slot['harness']
                         and s['phase'] == 'development' and s['condition'] == 'composed')
            if prior not in runs or runs[prior]['outcome'] != 'complete':
                raise ValueError('Follow-up evaluation requires the frozen composed execution')
    for execution, grade in grades.items():
        _keys(grade, 'execution_id receipt_sha256 artifact_sha256 checker_sha256 checks')
        run = runs.get(execution)
        if not run or run['outcome'] != 'complete':
            raise ValueError('Infrastructure failure or missing execution cannot be graded')
        case = _case_for(data, slots[execution])
        if any(grade[k] != run[k] for k in ('receipt_sha256', 'artifact_sha256')):
            raise ValueError('Grading is not bound to the original execution artifact')
        if grade['checker_sha256'] != case['checker_sha256']:
            raise ValueError('Independent checker identity changed')
        if (type(grade['checks']) is not dict or set(grade['checks']) != set(case['check_ids'])
                or any(type(v) is not bool for v in grade['checks'].values())):
            raise ValueError('Every frozen check needs a Boolean verdict')
    for execution, trace in traces.items():
        _keys(trace, 'execution_id events')
        run = runs.get(execution)
        if not run or digest(trace) != run['trace_sha256']:
            raise ValueError('Behavior trace is not bound to the host receipt')
        if type(trace['events']) is not list or len(trace['events']) > 4096 or len(canonical(trace)) > 4194304:
            raise ValueError('Trace exceeds the declared evidence view bound')
        for event in trace['events']:
            _keys(event, 'kind operation_id text')
            if event['kind'] not in ('assistant', 'tool_call', 'tool_result', 'environment_error'):
                raise ValueError('Only executor-visible behavior belongs in an editor view')
            _text(event['operation_id'])
            _text(event['text'])
    return data, slots, runs, variants, grades, traces


def editor_view(study, evidence, *, harness, task, condition):
    """A behavior-only projection; grader files must also be inaccessible to hosts."""
    if condition not in CONDITIONS[1:]:
        raise ValueError('Select a proposal or composition')
    data, slots, runs, variants, grades, traces = _validate(study, evidence)
    dependencies = _dependencies(slots, harness, task, condition)
    if not dependencies:
        raise ValueError('Unknown harness/task pair')
    observations = []
    for execution in dependencies:
        if execution not in runs or execution not in traces or runs[execution]['outcome'] != 'complete':
            raise ValueError('Complete host observations are required; never rerun an uncertain operation')
        observations.append(dict(execution_id=execution, condition=slots[execution]['condition'],
                                 receipt_sha256=runs[execution]['receipt_sha256'],
                                 trace_sha256=runs[execution]['trace_sha256'],
                                 usage=runs[execution]['usage'], events=traces[execution]['events']))
    return dict(schema=1, study_sha256=study.identity, harness=harness, task=task,
                condition=condition, allowed_surfaces=list(SURFACES),
                untrusted_observations=observations,
                grading_exposed=False, permissions_changed=False)


def compare(study, evidence):
    data, slots, runs, variants, grades, traces = _validate(study, evidence)
    rows = []
    for execution, slot in slots.items():
        run = runs.get(execution)
        grade = grades.get(execution)
        over = [] if not run else [k for k in COUNTERS if run['usage'][k] is not None
                                  and run['usage'][k] > data['budget'][k]]
        state = 'missing' if not run else run['outcome']
        if state == 'complete':
            state = 'ungraded' if not grade else ('passed' if all(grade['checks'].values()) else 'failed')
        if over:
            state = 'budget_exceeded'
        rows.append(dict(**slot, state=state, budget_exceeded=over))
    units = []
    for harness in data['harnesses']:
        for task in data['tasks']:
            selected = [s for s in rows if s['harness'] == harness['id'] and s['task'] == task['id']]
            deltas = []
            for phase in ('development', 'transfer', 'retention'):
                cases = [task[phase]] if phase == 'development' else task[phase]
                for case in cases:
                    pair = {s['condition']: s for s in selected if s['phase'] == phase and s['case'] == case['id']}
                    base, after = (grades.get(pair[c]['execution_id']) for c in ('baseline', 'composed'))
                    if base and after:
                        gained = [k for k, v in after['checks'].items() if v and not base['checks'][k]]
                        lost = [k for k, v in base['checks'].items() if v and not after['checks'][k]]
                        deltas.append(dict(phase=phase, case=case['id'], gained=gained, lost=lost))
            complete = all(s['state'] in ('passed', 'failed') for s in selected)
            development_gain = any(d['gained'] for d in deltas if d['phase'] == 'development')
            preserved = not any(d['lost'] for d in deltas)
            transfer_pass = all(s['state'] == 'passed' for s in selected
                                if s['phase'] == 'transfer' and s['condition'] == 'composed')
            development_pass = all(s['state'] == 'passed' for s in selected
                                   if s['phase'] == 'development' and s['condition'] == 'composed')
            retention_controls = sum(sum(grades.get(s['execution_id'], {}).get('checks', {}).values())
                                     for s in selected if s['phase'] == 'retention' and s['condition'] == 'baseline')
            screen = (complete and development_gain and preserved and transfer_pass
                      and development_pass and retention_controls > 0
                      and bool(task['transfer']) and bool(task['retention'])
                      and harness['qualification_sha256'] is not None)
            units.append(dict(harness=harness['id'], task=task['id'],
                              compatibility_evidence_present=harness['qualification_sha256'] is not None,
                              complete=complete, bounded_transfer_screen_passed=bool(screen),
                              previously_passed_retention_checks=retention_controls,
                              comparisons=deltas,
                              surfaces={c: sorted(variants.get((harness['id'], task['id'], c), {}).get('changes', {}))
                                        for c in CONDITIONS[1:]}))
    totals = {key: sum(r['usage'][key] or 0 for r in runs.values()) for key in COUNTERS}
    unknown = {key: sum(r['usage'][key] is None for r in runs.values()) for key in COUNTERS}
    editor = {key: sum(v['editor_usage'][key] for v in variants.values()) for key in COUNTERS}
    return dict(schema=1, study_sha256=study.identity, evidence_kind=data['evidence_kind'],
                plan=study.plan(), executions=rows,
                comparisons=units, task_usage_observed=totals, task_usage_unknown_counts=unknown,
                editor_usage_observed=editor, promoted=False,
                scope='Offline evidence audit; no model, tool execution, weight update or deployment',
                limitation='One fixed-sampling cycle is not replicated statistical evidence or general mastery')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'report', 'editor-view'))
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--harness')
    parser.add_argument('--task')
    parser.add_argument('--condition', choices=CONDITIONS[1:])
    args = parser.parse_args(argv)
    try:
        study = HarnessStudy(json.loads(args.spec.read_bytes()))
        if args.action == 'plan':
            value = study.plan()
        else:
            if args.evidence is None:
                raise ValueError('--evidence is required')
            evidence = json.loads(args.evidence.read_bytes())
            if args.action == 'report':
                value = compare(study, evidence)
            else:
                value = editor_view(study, evidence, harness=args.harness, task=args.task, condition=args.condition)
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, 'Invalid comparison evidence: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
