import unittest
from sss.adapters.code_check import pure_function
from sss.suites.code_foundations import cases,practice_cases,grade

class CodeCheckTests(unittest.TestCase):
    def test_reject_exit_zero_and_checker_tampering(self):
        for code in ('import sys\nsys.exit(0)','def total(values):\n    return __import__("os")._exit(0)\n','def total(values):\n    return open("/etc/shadow").read()\n'):
            self.assertFalse(pure_function(code,'total'))
    def test_real_references_fit_explicit_pure_contract(self):
        for case in cases():
            if case.language=='python':
                names={'python.sum_empty':'total','python.binary_search':'locate','python.stable_unique':'unique','python.double':'double'}
                source_name='app.py' if case.id=='python.double' else 'task.py'
                self.assertTrue(pure_function(case.reference[source_name],names[case.id]))
    def test_practice_variations_are_separate_and_reference_checked(self):
        assessment_ids={case.id for case in cases()}
        self.assertNotIn('python.triple.practice',assessment_ids)
        practice=practice_cases()
        self.assertEqual([case.id for case in practice],['python.triple.practice'])
        case=practice[0]
        self.assertNotIn(case.id,assessment_ids)
        self.assertTrue({'code.python.tests','code.python.debug'} <= set(case.skills))
        self.assertTrue(pure_function(case.reference['app.py'],'triple'))
    def test_process_zero_exit_is_not_checker_success(self):
        case=cases()[0]
        self.assertEqual(grade(case,[dict(settled=True,exit_code=0)],case.reference)['status'],'unavailable')
