import unittest
from sss.suites.admin_tool_fixtures import cases, execute_reference, grade

class AdminToolFixturesTest(unittest.TestCase):
    def test_references_and_missing_work(self):
        for case in cases():
            with self.subTest(case=case.id):
                self.assertEqual(grade(case, execute_reference(case, case.reference))['status'], 'pass')
                self.assertEqual(grade(case, execute_reference(case, ()))['status'], 'fail')

    def test_wrong_answer_and_protected_file_are_rejected(self):
        case=next(x for x in cases() if x.id=='admin.repair_port')
        calls=list(case.reference)
        calls.insert(2, {'tool':'write_file','arguments':{'path':'protected.txt','content':'changed'}})
        self.assertEqual(grade(case, execute_reference(case,calls))['status'], 'fail')
        case=cases()[0]
        calls=list(case.reference);calls[-1]={'tool':'finish','arguments':{'answer':'9999'}}
        self.assertEqual(grade(case,execute_reference(case,calls))['status'], 'fail')

    def test_missing_observations_are_not_passes(self):
        self.assertEqual(grade(cases()[0],{})['status'],'unavailable')

    def test_malformed_calls_fail_without_crashing(self):
        case=cases()[0]
        for bad in (None, [], 'read_file', {}, {'tool':'read_file','arguments':[]},
                    {'tool':'read_file','arguments':{'path':4}},
                    {'tool':'read_file','arguments':{'path':'service.conf'},'extra':True}):
            with self.subTest(call=bad):
                observation=execute_reference(case,(bad,)+case.reference)
                self.assertEqual(grade(case,observation)['status'],'fail')

    def test_protected_change_and_restore_is_still_failure(self):
        case=next(x for x in cases() if x.id=='admin.repair_port')
        calls=({'tool':'write_file','arguments':{'path':'protected.txt','content':'changed'}},
               {'tool':'write_file','arguments':{'path':'protected.txt','content':case.files['protected.txt']}})+case.reference
        result=execute_reference(case,calls)
        self.assertEqual(result['files']['protected.txt'],case.files['protected.txt'])
        self.assertEqual(grade(case,result)['status'],'fail')

    def test_observation_outputs_support_recovery(self):
        case=cases()[1]
        result=execute_reference(case,case.reference)
        self.assertEqual(result['outputs'][0]['error'],'not_found')
        self.assertEqual(result['outputs'][1]['paths'],['service.conf.example'])
        self.assertEqual(result['outputs'][2]['content'],'port=9000\n')

    def test_post_finish_actions_and_wrong_order_fail(self):
        case=cases()[0]
        self.assertEqual(grade(case,execute_reference(case,case.reference+case.reference))['status'],'fail')
        self.assertEqual(grade(case,execute_reference(case,tuple(reversed(case.reference))))['status'],'fail')

    def test_invalid_observations_are_unavailable(self):
        for value in (None, [], {'events':[None],'files':{}}, {'events':'read','files':{}}):
            self.assertEqual(grade(cases()[0],value)['status'],'unavailable')

    def test_task_does_not_require_unrequested_completion_wording(self):
        for case,answer in [(cases()[2],'Done'),(cases()[3],'The error code is E42: permission denied.')]:
            calls=case.reference[:-1]+({'tool':'finish','arguments':{'answer':answer}},)
            self.assertEqual(grade(case,execute_reference(case,calls))['status'],'pass')
        case=cases()[3]
        calls=case.reference[:-1]+({'tool':'finish','arguments':{'answer':'E42 or E43'}},)
        self.assertEqual(grade(case,execute_reference(case,calls))['status'],'fail')
