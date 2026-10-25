"""Saturation proposals must preserve matched comparisons and gate independence."""
import copy,unittest
from sss.assessment_growth import plan
from sss.machinery import catalogue


def evaluation(count,passed=None):
    rows=[dict(id='owned-'+str(i),skill_id='owned.skill',gate=('independent','composition','transfer_recovery')[i%3],
        passed=True if passed is None else passed(i),finished=True) for i in range(count)]
    return dict(status='COMPLETE',evaluation_id='a'*64,runtime_id='b'*64,model_sha256='c'*64,
        cases=count,passed=sum(r['passed'] for r in rows),finished=count,outcomes=rows,weights_updated=False,promoted=False)


class AssessmentGrowth(unittest.TestCase):
    def test_four_of_four_requests_more_evidence_without_claiming_ceiling(self):
        value=evaluation(4);original=copy.deepcopy(value)
        result=plan(value,purpose='adaptive_learning')
        self.assertTrue(result['requires_assessment_expansion'])
        self.assertEqual(result['skills'][0]['additional_cases_to_coverage_target'],92)
        self.assertEqual({p['action'] for p in result['probes']},{'EXPAND_SAMPLE_AT_SAME_DIFFICULTY'})
        self.assertFalse(result['capability_ceiling_established']);self.assertFalse(result['execution_authorized'])
        self.assertEqual(result['questions_generated'],0);self.assertEqual(value,original)

    def test_fixed_and_machinery_purposes_never_expand_matching_panel(self):
        for purpose in ('machinery','fixed_comparison'):
            with self.subTest(purpose=purpose):
                value=plan(evaluation(4),purpose=purpose)
                self.assertFalse(value['requires_assessment_expansion'])
                self.assertFalse(value['changes_frozen_comparison'])
                self.assertFalse(value['weights_updated'])
        description=catalogue()
        self.assertFalse(description['part_of_frozen_68_update_comparison'])
        self.assertTrue(all(not row['counts_toward_model_mastery'] for row in description['suites']))

    def test_a_saturated_gate_can_advance_while_other_gates_need_practice(self):
        result=plan(evaluation(96,lambda i:i%3==0),purpose='adaptive_learning')
        actions={p['gate']:p['action'] for p in result['probes']}
        self.assertEqual(actions['independent'],'PROBE_ONE_HARDER_AXIS')
        self.assertEqual(actions['composition'],'PRACTICE_AND_REVIEW_CURRENT_CELL')
        self.assertEqual(actions['transfer_recovery'],'PRACTICE_AND_REVIEW_CURRENT_CELL')
        rules=result['transition_rules']
        self.assertTrue(rules['reevaluate_current_working_parent'])
        self.assertTrue(rules['compare_parent_and_candidate_on_same_new_panel'])
        self.assertTrue(rules['never_compare_raw_scores_across_different_panels'])
        self.assertTrue(result['difficulty_rules']['require_environment_setup_before_world_skill'])

    def test_unbound_purpose_and_incomplete_results_refused(self):
        with self.assertRaises(ValueError):plan(evaluation(4),purpose='guess')
        value=evaluation(4);value['cases']=5
        with self.assertRaises(ValueError):plan(value,purpose='adaptive_learning')


if __name__=='__main__':unittest.main()
