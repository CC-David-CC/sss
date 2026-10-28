"""Composition contracts with controlled panels; no model or lesson approval.

The fixtures deliberately do not claim real BW, oracle or GPU qualification.
They exercise failure propagation, original-evidence recovery and policy reports.
Actual provider/renderer integration is a separate optional test.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sss.adapters.learning_panels import LearningPanelEvaluator, PanelLearningPolicy
from sss.records import canonical, digest


MODEL = 'a' * 64


def lesson(text='owned controlled fixture'):
    return dict(schema=2, model_contract_id=MODEL, scope='owned-training',
        segments=[dict(role='assistant', kind='answer', rendered=text,
                       verified=True, scope='practice')])


def candidate(sha='c', *, lora=False):
    return dict(mode='lora' if lora else 'full', candidate_path='/controlled/candidate',
                candidate_sha256=sha * 64)


class ControlledProvider:
    def __init__(self, text='owned controlled fixture'):
        self.values = [lesson(text)]
        self.validations = []
        self.available = True

    def binding(self):
        return dict(kind='controlled-test-provider', model_contract_id=MODEL,
                    checked_practice_lesson_ids=sorted(digest(v) for v in self.values))

    def verify(self):
        if not self.available:
            raise ValueError('Original provider proof unavailable')

    def lessons(self):
        return copy.deepcopy(self.values)

    def validate_lessons(self, records, previous_report):
        expected = {digest(v): v for v in self.values}
        for record in records:
            if expected.get(record['lesson_id']) != record['lesson']:
                raise ValueError('Controlled provider refused changed membership')
        self.validations.append(copy.deepcopy(records))


class ControlledPanel:
    def __init__(self, name, before=None, after=None):
        self.name = name
        self.before = before or [(False, True)]
        self.after = after or [(True, True)]
        self.source_version = 0
        self.calls = self.recovers = 0
        self.descriptors = []
        self.live = self.fail_before = self.fail_after = self.mutate_candidate = False

    def binding(self):
        return dict(kind='controlled-test-panel', model_contract_id=MODEL,
                    evaluation_id=digest(dict(panel=self.name, cases=len(self.before))),
                    source_version=self.source_version)

    def verify(self):
        pass

    def result(self, value):
        rows = self.before if value is None else self.after
        base = 'b' * 64
        adapters = []
        if value is not None:
            if value['mode'] == 'full':
                base = value['candidate_sha256']
            else:
                adapters = [dict(sha256=value['candidate_sha256'], scale=1.)]
        outcomes = [dict(id='case-'+str(i), skill_id='owned.shared-skill', gate='independent',
                         passed=p, finished=f) for i, (p, f) in enumerate(rows)]
        return dict(schema=1, status='COMPLETE', model_sha256=base,
            candidate_model_contract_id=digest(dict(base=base, adapters=adapters)),
            candidate_adapters=adapters, evaluation_id=self.binding()['evaluation_id'],
            runtime_id=digest(dict(runtime=self.name)), cases=len(rows),
            passed=sum(p for p, _ in rows), finished=sum(f for _, f in rows),
            outcomes=outcomes, weights_updated=False, promoted=False)

    def validate(self, result, value):
        if canonical(result) != canonical(self.result(value)):
            raise ValueError('Original controlled panel result changed')

    def __call__(self, value, directory, worker_fd):
        self.calls += 1
        self.descriptors.append(worker_fd)
        if self.fail_before:
            raise RuntimeError('Controlled interruption before original result')
        if self.mutate_candidate:
            value['candidate_sha256'] = 'f' * 64
        result = self.result(value)
        (Path(directory)/'original-result-private.json').write_text(json.dumps(result))
        if self.fail_after:
            raise RuntimeError('Controlled lost response after original result')
        return result

    def recover(self, value, directory):
        self.recovers += 1
        if self.live:
            raise ValueError('Original controlled child still live')
        path = Path(directory)/'original-result-private.json'
        if not path.exists():
            return None
        result = json.loads(path.read_bytes())
        self.validate(result, value)
        return result


@unittest.skipUnless(os.name == 'posix', 'POSIX owner evidence and lease tests')
class LearningPanelTests(unittest.TestCase):
    def setUp(self):
        import fcntl
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lease = (self.root/'worker.lock').open('a+')
        self.addCleanup(self.lease.close)
        fcntl.flock(self.lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.panels = [ControlledPanel(name) for name in ('target', 'workflow', 'retention')]
        self.provider = ControlledProvider()
        self.evaluator = self.install()

    def install(self, panels=None, providers=None):
        return LearningPanelEvaluator(
            panels if panels is not None else [(p.name,p.name,p) for p in self.panels],
            providers if providers is not None else [('owned',self.provider)],
            model_contract_id=MODEL)

    def values(self, value=None):
        return [p.result(value) for p in self.panels]

    def backend(self, name='backend'):
        p=self.root/name; p.mkdir(); return p

    def execute(self, value=None, name='backend'):
        path=self.backend(name)
        return self.evaluator(value,path,self.lease.fileno()),path

    def test_requires_every_measurement_role_and_unique_panel_names(self):
        for defect in ('missing','duplicate','unknown'):
            specs=[(p.name,p.name,p) for p in self.panels]
            if defect=='missing':specs[2]=('other','target',self.panels[2])
            elif defect=='duplicate':specs[2]=('target','retention',self.panels[2])
            else:specs[2]=('retention','unavailable',self.panels[2])
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.install(specs)

    def test_same_case_ids_in_different_panels_remain_distinct(self):
        value=self.evaluator.combine(self.values(),None)
        self.assertEqual(value['cases'],3)
        self.assertEqual(len({r['id'] for r in value['outcomes']}),3)
        self.assertEqual({r['panel_case_id'] for r in value['outcomes']},{'case-0'})
        self.assertEqual([r['role'] for r in value['panels']],['target','workflow','retention'])
        self.assertFalse(value['promoted'])

    def test_all_panels_must_measure_same_weights_and_hat(self):
        for lora in (False,True):
            rows=self.values(candidate(lora=lora));rows[-1]=self.panels[-1].result(candidate('d',lora=lora))
            with self.subTest(lora=lora),self.assertRaises(ValueError):self.evaluator._assemble(rows)

    def test_partial_candidate_identity_and_missing_panel_are_not_complete(self):
        rows=self.values();rows[1].pop('candidate_adapters')
        with self.assertRaises(ValueError):self.evaluator._assemble(rows)
        with self.assertRaises(ValueError):self.evaluator.combine(self.values()[:-1],None)
        rows=self.values();rows[1]=None
        with self.assertRaises(ValueError):self.evaluator._assemble(rows)

    def test_unavailable_panel_cannot_be_counted_as_zero_or_a_pass(self):
        for status in ('UNAVAILABLE','RUNNING','FAILED'):
            rows=self.values();rows[0]['status']=status
            with self.subTest(status=status),self.assertRaises(ValueError):self.evaluator._assemble(rows)

    def test_unknown_frozen_cases_and_inconsistent_counts_are_refused(self):
        for defect in ('case','count','evaluation','runtime'):
            rows=self.values()
            if defect=='case':rows[0]['outcomes'][0]['id']='replacement'
            elif defect=='count':rows[0]['passed']=99
            elif defect=='evaluation':rows[0]['evaluation_id']='0'*64
            else:rows[0]['runtime_id']='1'*64
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.evaluator.combine(rows,None)

    def test_exact_approved_membership_is_required_despite_verification_flags(self):
        approved=self.evaluator.lessons()[0]
        record=dict(lesson_id=digest(approved),lesson=approved)
        self.evaluator.validate_lessons([record],None)
        self.assertEqual(self.provider.validations,[[record]])
        changed=copy.deepcopy(record);changed['lesson']['segments'][0]['rendered']='unverified'
        changed['lesson_id']=digest(changed['lesson']);changed['verified']=True
        with self.assertRaises(ValueError):self.evaluator.validate_lessons([changed],None)
        for selected in ([],[record,record],[record,dict(lesson_id='f'*64,lesson=approved)]):
            with self.assertRaises(ValueError):self.evaluator.validate_lessons(selected,None)

    def test_multiple_providers_validate_their_own_exact_subset(self):
        second=ControlledProvider('independent second provider')
        evaluator=self.install(providers=[('first',self.provider),('second',second)])
        records=[dict(lesson_id=digest(v),lesson=v) for v in evaluator.lessons()]
        evaluator.validate_lessons(records,None)
        self.assertEqual(len(self.provider.validations[-1]),1)
        self.assertEqual(len(second.validations[-1]),1)

    def test_duplicate_lesson_across_providers_is_not_silently_collapsed(self):
        with self.assertRaises(ValueError):self.install(providers=[('first',self.provider),('second',ControlledProvider())])

    def test_source_provider_and_binding_drift_require_a_new_policy(self):
        self.panels[0].source_version=False  # False == 0 must not hide typed drift.
        with self.assertRaises(ValueError):self.evaluator.verify()
        self.panels[0].source_version=0
        self.provider.values[0]['segments'][0]['rendered']='changed'
        with self.assertRaises(ValueError):self.evaluator.verify()

    def test_binding_and_lesson_views_are_detached(self):
        self.evaluator.binding()['panels'].clear()
        self.evaluator.lessons()[0]['scope']='development'
        self.evaluator.verify()
        self.assertEqual(len(self.evaluator.binding()['panels']),3)

    def test_changed_composition_order_or_implementation_is_refused(self):
        self.evaluator._panels.reverse()
        with self.assertRaises(ValueError):self.evaluator.verify()
        self.evaluator._panels.reverse()
        with patch('sss.adapters.learning_panels.file_sha256',return_value='0'*64):
            with self.assertRaises(ValueError):self.evaluator.verify()

    def test_execute_passes_original_lease_once_and_preserves_it(self):
        import fcntl
        value,path=self.execute(candidate())
        self.evaluator.validate(value,candidate())
        for panel in self.panels:
            self.assertEqual(panel.calls,1);self.assertEqual(panel.descriptors,[self.lease.fileno()])
        with (self.root/'worker.lock').open('a+') as other:
            with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with self.assertRaises(ValueError):self.evaluator(candidate(),path,self.lease.fileno())

    def test_a_panel_cannot_mutate_the_callers_candidate(self):
        value=candidate();original=copy.deepcopy(value);self.panels[0].mutate_candidate=True
        with self.assertRaises(ValueError):self.evaluator(value,self.backend(),self.lease.fileno())
        self.assertEqual(value,original)

    def test_complete_recovery_rechecks_original_panels_without_model_calls(self):
        value,path=self.execute(candidate())
        recovered=self.evaluator.recover(candidate(),path)
        self.assertEqual(recovered,value)
        self.assertEqual([p.calls for p in self.panels],[1,1,1])
        self.assertEqual([p.recovers for p in self.panels],[1,1,1])

    def test_missing_parent_summary_recovers_original_last_panel_result(self):
        self.panels[-1].fail_after=True;path=self.backend()
        with self.assertRaisesRegex(RuntimeError,'lost response'):
            self.evaluator(candidate(),path,self.lease.fileno())
        value=self.evaluator.recover(candidate(),path)
        self.assertEqual(value['passed'],3)
        self.assertTrue((path/'panel-result-private.json').exists())
        self.assertEqual([p.calls for p in self.panels],[1,1,1])

    def test_live_original_child_blocks_recovery_even_with_copied_summaries(self):
        _,path=self.execute();self.panels[1].live=True
        with self.assertRaisesRegex(ValueError,'still live'):self.evaluator.recover(None,path)
        self.assertEqual([p.calls for p in self.panels],[1,1,1])

    def test_missing_original_evidence_cannot_be_replaced_by_copied_result(self):
        _,path=self.execute();(path/'panel-01/original-result-private.json').unlink()
        with self.assertRaisesRegex(ValueError,'recoverable'):self.evaluator.recover(None,path)
        self.assertEqual([p.calls for p in self.panels],[1,1,1])

    def test_unstarted_later_panel_is_a_hold_and_is_not_dispatched_by_recovery(self):
        self.panels[0].fail_after=True;path=self.backend()
        with self.assertRaises(RuntimeError):self.evaluator(None,path,self.lease.fileno())
        with self.assertRaisesRegex(ValueError,'never dispatched'):self.evaluator.recover(None,path)
        self.assertEqual([p.calls for p in self.panels],[1,0,0])

    def test_changed_original_intent_or_copied_result_is_not_recovered(self):
        _,path=self.execute(candidate())
        with self.assertRaisesRegex(ValueError,'intent'):self.evaluator.recover(candidate('d'),path)
        p=path/'panel-01-result-private.json';raw=json.loads(p.read_bytes());raw['passed']=7;p.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError,'differs'):self.evaluator.recover(candidate(),path)

    def test_duplicate_receipt_fields_and_boolean_schema_alias_are_refused(self):
        value,path=self.execute()
        changed=copy.deepcopy(value);changed['schema']=True
        with self.assertRaises(ValueError):self.evaluator.inspect(changed)
        p=path/'panel-00-start-private.json';raw=p.read_text().rstrip();p.write_text(raw[:-1]+',"role":"target"}')
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.evaluator.recover(None,path)

    def test_malformed_composition_does_not_pass_through_summary_inspection(self):
        value=self.evaluator.combine(self.values(),None)
        for row in (None,{},dict(evaluation=None)):
            changed=copy.deepcopy(value);changed['panels'][0]=row
            with self.assertRaises(ValueError):self.evaluator.inspect(changed)

    def test_owner_directory_symlinks_are_refused(self):
        target=self.backend('target');alias=self.root/'alias';alias.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ValueError):self.evaluator(None,alias,self.lease.fileno())
        with self.assertRaises(ValueError):self.evaluator.recover(None,alias)

    def test_report_preserves_retention_loss_hidden_by_net_learning_gain(self):
        panels=[ControlledPanel('target',[(False,True)]*2,[(True,True)]*2),
                ControlledPanel('workflow'),ControlledPanel('retention',[(True,True)],[(False,True)])]
        evaluator=self.install([(p.name,p.name,p) for p in panels])
        policy=PanelLearningPolicy(evaluator,dict(mode='full'),title='controlled',max_rounds=1,
                                   assessment_purpose='machinery',minimum_skill_cases=3)
        baseline=evaluator.combine([p.result(None) for p in panels],None)
        trained=evaluator.combine([p.result(candidate()) for p in panels],candidate())
        result=policy.analyze(baseline,baseline,trained)
        self.assertEqual(result['working_parent'],'candidate')
        self.assertEqual(result['report']['aggregate']['working_decision'],'KEEP_AND_REPAIR')
        self.assertEqual(result['report']['aggregate']['strict_preservation_status'],'REJECTED')
        retention=result['report']['panels'][-1]
        self.assertEqual(retention['role'],'retention')
        self.assertEqual(retention['report']['parent_answer_losses'],1)
        self.assertEqual(retention['report']['working_decision'],'RETAIN_PARENT')
        self.assertFalse(result['report']['promoted'])
        self.assertNotIn('outcomes',retention['report'])
        self.assertEqual(result['assessment']['anchor_evaluation_id'],trained['evaluation_id'])

    def test_changed_panel_runtime_cannot_be_reported_as_weight_learning(self):
        baseline=self.evaluator.combine(self.values(),None)
        rows=self.values(candidate());rows[0]['runtime_id']='f'*64
        changed=self.evaluator._assemble(rows)
        policy=PanelLearningPolicy(self.evaluator,dict(mode='full'),title='controlled',max_rounds=1)
        with self.assertRaises(ValueError):policy.analyze(baseline,baseline,changed)


if __name__ == '__main__':unittest.main()
