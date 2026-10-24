from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sss.records import digest
from sss.studies.harness_compare import HarnessStudy, compare, editor_view, CONDITIONS, COUNTERS


def case(name):
    return dict(id=name, input_sha256=digest(['input', name]), fixture_sha256=digest(['files', name]),
                checker_sha256=digest('checker-v1'), check_ids=['correct', 'preserved'])


def specification(*, followups=True):
    return dict(schema=1, name='synthetic-contract-only', evidence_kind='synthetic_contract',
                model={k: digest(k) for k in ('weights_sha256', 'tokenizer_sha256', 'template_sha256', 'sampling_sha256', 'runtime_sha256')},
                environment={k: digest(k) for k in ('capabilities_sha256', 'isolation_sha256', 'tools_sha256')},
                budget=dict(model_calls=8, input_tokens=32768, output_tokens=4096, tool_calls=8, wall_seconds=300),
                editor=dict(model_sha256=digest('editor-model'), configuration_sha256=digest('editor-config')),
                harnesses=[dict(id=h, revision='fixture-v1', base_sha256=digest(['base', h]),
                                transport='fixture', adapter_revision='fixture-v1', qualification_sha256=digest(['qualification', h]))
                           for h in ('bw', 'opencode', 'codex', 'pi')],
                tasks=[dict(id='repair', development=case('repair-dev'),
                            transfer=[case('repair-transfer')] if followups else [],
                            retention=[case('read-retention')] if followups else [])])


def counts(calls=1):
    return dict(model_calls=calls, input_tokens=100, output_tokens=30, tool_calls=1, wall_seconds=0.5)


def fixture(study, *, stages=4, changes_by_harness=None):
    """Synthetic host observations for testing the auditor, never model evidence."""
    data = study.document()
    evidence = dict(schema=1, study_sha256=study.identity, variants=[], runs=[], grades=[], traces=[])
    plan = study.plan()['executions']
    for harness in data['harnesses']:
        for task in data['tasks']:
            unit = [s for s in plan if s['harness'] == harness['id'] and s['task'] == task['id']]
            recipes = {}
            for slot in unit:
                condition = slot['condition']
                if CONDITIONS.index(condition) >= stages or (slot['phase'] != 'development' and stages < 4):
                    continue
                if condition != 'baseline' and slot['phase'] == 'development':
                    parents = ['baseline'] if condition != 'composed' else list(CONDITIONS[:3])
                    parent_ids = [s['execution_id'] for s in unit if s['phase'] == 'development' and s['condition'] in parents]
                    refs = [{k: r[k] for k in ('execution_id', 'receipt_sha256', 'trace_sha256')}
                            for r in evidence['runs'] if r['execution_id'] in parent_ids]
                    recipe = dict(harness=harness['id'], task=task['id'], condition=condition,
                                  base_sha256=harness['base_sha256'],
                                  changes=(deepcopy(changes_by_harness[harness['id']][condition]) if changes_by_harness
                                           else {'instructions': digest([harness['id'], condition])}),
                                  evidence=refs, editor_sha256=digest(data['editor']), editor_usage=counts(),
                                  hypothesis='Synthetic fixture: inspect state, then verify the final artifact.')
                    evidence['variants'].append(recipe)
                    recipes[condition] = recipe
                recipe = recipes.get(condition)
                source = task['development'] if slot['phase'] == 'development' else next(c for c in task[slot['phase']] if c['id'] == slot['case'])
                execution = slot['execution_id']
                trace = dict(execution_id=execution, events=[dict(kind='tool_result', operation_id='read-1',
                                                                  text='Observed the owned fixture; this is a synthetic trace.')])
                run = dict(execution_id=execution, operation_id='host-' + execution,
                           receipt_sha256=digest(['receipt', execution]), trace_sha256=digest(trace),
                           artifact_sha256=digest(['artifact', execution]), model_sha256=digest(data['model']),
                           environment_sha256=digest(data['environment']), harness_sha256=digest(harness),
                           task_sha256=digest(source), budget_sha256=digest(data['budget']),
                           configuration_sha256=digest(dict(base_sha256=harness['base_sha256'], changes=recipe['changes'] if recipe else {})),
                           variant_sha256=digest(recipe) if recipe else None,
                           settled=True, outcome='complete', usage=counts())
                checks = dict(correct=(condition != 'baseline' or slot['phase'] == 'retention'), preserved=True)
                grade = dict(execution_id=execution, receipt_sha256=run['receipt_sha256'],
                             artifact_sha256=run['artifact_sha256'], checker_sha256=source['checker_sha256'], checks=checks)
                evidence['runs'].append(run)
                evidence['grades'].append(grade)
                evidence['traces'].append(trace)
    return evidence


class HarnessComparisonTests(unittest.TestCase):
    def setUp(self):
        self.study = HarnessStudy(specification())
        self.evidence = fixture(self.study)

    def test_four_task_executions_are_not_four_model_calls(self):
        plan = self.study.plan()
        self.assertEqual(plan['development_executions'], 16)
        self.assertEqual(plan['followup_executions'], 16)
        self.assertEqual(plan['minimum_editor_sessions'], 12)
        self.assertEqual(len({s['execution_id'] for s in plan['executions']}), 32)
        result = compare(self.study, self.evidence)
        self.assertEqual(result['task_usage_observed']['model_calls'], 32)
        self.assertEqual(result['editor_usage_observed']['model_calls'], 12)
        self.assertFalse(result['promoted'])
        self.assertEqual(result['evidence_kind'], 'synthetic_contract')
        self.assertTrue(all(r['bounded_transfer_screen_passed'] for r in result['comparisons']))

    def test_spec_is_detached_and_no_mutation_thaws_a_plan(self):
        original = specification()
        study = HarnessStudy(original)
        identity = study.identity
        original['model']['weights_sha256'] = digest('different')
        study.document()['budget']['model_calls'] = 9000
        study.plan()['executions'].clear()
        self.assertEqual(study.identity, identity)
        self.assertEqual(study.document()['budget']['model_calls'], 8)

    def test_harnesses_optimize_different_surfaces_from_their_own_behavior(self):
        surfaces = dict(bw='memory_instructions', opencode='skills', codex='tool_guidance', pi='instructions')
        changes = {h: {c: {surface: digest([h, c, 'distinct-content'])} for c in CONDITIONS[1:]}
                   for h, surface in surfaces.items()}
        evidence = fixture(self.study, changes_by_harness=changes)
        report = compare(self.study, evidence)
        for row in report['comparisons']:
            harness = row['harness']
            self.assertTrue(row['bounded_transfer_screen_passed'])
            self.assertEqual(row['surfaces'], {c: [surfaces[harness]] for c in CONDITIONS[1:]})
            view = editor_view(self.study, evidence, harness=harness, task='repair', condition='composed')
            own = {s['execution_id'] for s in self.study.plan()['executions']
                   if s['harness'] == harness and s['phase'] == 'development'}
            self.assertTrue(all(r['execution_id'] in own for r in view['untrusted_observations']))
        # Another harness's valid baseline is not evidence for this harness's proposal.
        other = next(s for s in self.study.plan()['executions']
                     if s['harness'] == 'codex' and s['condition'] == 'baseline' and s['phase'] == 'development')
        original = next(r for r in evidence['runs'] if r['execution_id'] == other['execution_id'])
        variant = next(v for v in evidence['variants'] if v['harness'] == 'bw' and v['condition'] == 'general_probe')
        variant['evidence'] = [{k: original[k] for k in ('execution_id', 'receipt_sha256', 'trace_sha256')}]
        with self.assertRaises(ValueError):
            compare(self.study, evidence)

    def test_editor_sees_only_prior_behavior_even_if_grades_are_present(self):
        view = editor_view(self.study, self.evidence, harness='bw', task='repair', condition='composed')
        self.assertEqual([r['condition'] for r in view['untrusted_observations']], list(CONDITIONS[:3]))
        text = json.dumps(view)
        for forbidden in ('checker_sha256', 'checks', 'correct', 'repair-transfer', 'read-retention', 'hypothesis'):
            self.assertNotIn(forbidden, text)
        self.assertFalse(view['grading_exposed'])
        general = editor_view(self.study, self.evidence, harness='bw', task='repair', condition='general_probe')
        self.assertEqual(len(general['untrusted_observations']), 1)

    def test_held_out_answers_cannot_be_added_as_editor_fields(self):
        evidence = deepcopy(self.evidence)
        evidence['traces'][0]['events'][0]['expected_answer'] = 'protected'
        with self.assertRaises(ValueError):
            editor_view(self.study, evidence, harness='bw', task='repair', condition='general_probe')
        evidence = deepcopy(self.evidence)
        evidence['runs'][0]['score'] = 1.0
        with self.assertRaises(ValueError):
            compare(self.study, evidence)

    def test_missing_baseline_or_probe_cannot_support_composition(self):
        for index in (0, 1, 2):
            evidence = deepcopy(self.evidence)
            del evidence['runs'][index]
            with self.assertRaises(ValueError):
                compare(self.study, evidence)
        evidence = fixture(self.study, stages=2)
        with self.assertRaises(ValueError):
            editor_view(self.study, evidence, harness='bw', task='repair', condition='composed')

    def test_profile_drift_is_not_a_matched_comparison(self):
        for field in ('model_sha256', 'environment_sha256', 'harness_sha256', 'task_sha256',
                      'budget_sha256', 'configuration_sha256', 'variant_sha256'):
            with self.subTest(field=field):
                evidence = deepcopy(self.evidence)
                evidence['runs'][3][field] = digest('different')
                with self.assertRaises(ValueError):
                    compare(self.study, evidence)

    def test_wrong_or_stale_grader_cannot_create_a_pass(self):
        for field in ('receipt_sha256', 'artifact_sha256', 'checker_sha256'):
            evidence = deepcopy(self.evidence)
            evidence['grades'][3][field] = digest('different')
            with self.assertRaises(ValueError):
                compare(self.study, evidence)
        evidence = deepcopy(self.evidence)
        evidence['grades'][3]['checks']['correct'] = 1
        with self.assertRaises(ValueError):
            compare(self.study, evidence)

    def test_infrastructure_and_uncertainty_are_unscored_and_not_retried(self):
        study = HarnessStudy(specification(followups=False))
        evidence = fixture(study, stages=1)
        first = evidence['runs'][0]
        for outcome, settled in (('infrastructure_error', True), ('uncertain', False)):
            bad = deepcopy(evidence)
            bad['runs'][0].update(outcome=outcome, settled=settled, usage={k: None for k in COUNTERS})
            bad['grades'] = [g for g in bad['grades'] if g['execution_id'] != first['execution_id']]
            result = compare(study, bad)
            self.assertEqual(result['executions'][0]['state'], outcome)
            self.assertEqual(result['task_usage_unknown_counts']['model_calls'], 1)
            self.assertFalse(any(r['bounded_transfer_screen_passed'] for r in result['comparisons']))
            with self.assertRaises(ValueError):
                editor_view(study, bad, harness='bw', task='repair', condition='general_probe')

    def test_reusing_a_host_operation_or_extra_seed_run_is_rejected(self):
        for mutate in (
                lambda e: e['runs'].append(deepcopy(e['runs'][0])),
                lambda e: e['runs'][1].update(operation_id=e['runs'][0]['operation_id']),
                lambda e: e['runs'][3].update(execution_id=digest('extra-seed'))):
            evidence = deepcopy(self.evidence)
            mutate(evidence)
            with self.assertRaises(ValueError):
                compare(self.study, evidence)

    def test_regression_remains_visible_despite_a_new_gain(self):
        self.evidence['grades'][3]['checks']['preserved'] = False
        report = compare(self.study, self.evidence)['comparisons'][0]
        self.assertEqual(report['comparisons'][0]['gained'], ['correct'])
        self.assertEqual(report['comparisons'][0]['lost'], ['preserved'])
        self.assertFalse(report['bounded_transfer_screen_passed'])

    def test_transfer_failure_retention_loss_and_empty_controls_block_screen(self):
        # First unit slots: four development, two transfer, two retention.
        for index, key in ((5, 'correct'), (7, 'preserved')):
            evidence = deepcopy(self.evidence)
            evidence['grades'][index]['checks'][key] = False
            self.assertFalse(compare(self.study, evidence)['comparisons'][0]['bounded_transfer_screen_passed'])
        evidence = deepcopy(self.evidence)
        evidence['grades'][6]['checks'] = dict(correct=False, preserved=False)
        self.assertFalse(compare(self.study, evidence)['comparisons'][0]['bounded_transfer_screen_passed'])
        study = HarnessStudy(specification(followups=False))
        self.assertFalse(any(r['bounded_transfer_screen_passed'] for r in compare(study, fixture(study))['comparisons']))

    def test_budget_overrun_is_preserved_but_ineligible(self):
        self.evidence['runs'][3]['usage']['model_calls'] = 9
        result = compare(self.study, self.evidence)
        self.assertEqual(result['executions'][3]['state'], 'budget_exceeded')
        self.assertEqual(result['task_usage_observed']['model_calls'], 40)
        self.assertFalse(result['comparisons'][0]['bounded_transfer_screen_passed'])

    def test_authority_edits_future_evidence_and_editor_changes_are_rejected(self):
        for mutate in (
                lambda v: v['changes'].update(permissions=digest('unrestricted')),
                lambda v: v.update(base_sha256=digest('last-task-composition')),
                lambda v: v.update(editor_sha256=digest('different-editor')),
                lambda v: v['evidence'][0].update(trace_sha256=digest('rewritten-trace')),
                lambda v: v['evidence'].append(dict(execution_id='future', receipt_sha256=digest('x'), trace_sha256=digest('y')))):
            evidence = deepcopy(self.evidence)
            mutate(evidence['variants'][0])
            with self.assertRaises(ValueError):
                compare(self.study, evidence)

    def test_qualification_and_question_separation_are_explicit(self):
        spec = specification()
        spec['tasks'][0]['transfer'][0]['input_sha256'] = spec['tasks'][0]['development']['input_sha256']
        with self.assertRaises(ValueError):
            HarnessStudy(spec)
        spec = specification()
        spec['harnesses'][0]['qualification_sha256'] = None
        study = HarnessStudy(spec)
        self.assertFalse(compare(study, fixture(study))['comparisons'][0]['bounded_transfer_screen_passed'])

    def test_cli_plans_and_reports_without_host_runtimes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'spec.json').write_text(json.dumps(self.study.document()))
            (root / 'evidence.json').write_text(json.dumps(self.evidence))
            common = [sys.executable, '-m', 'sss', 'study', 'harness', '--spec', str(root / 'spec.json')]
            plan = subprocess.run(common + ['plan'], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(plan.stdout)['development_executions'], 16)
            report = subprocess.run(common + ['report', '--evidence', str(root / 'evidence.json')], capture_output=True, text=True, check=True)
            self.assertEqual(len(json.loads(report.stdout)['comparisons']), 4)


if __name__ == '__main__':
    unittest.main()
