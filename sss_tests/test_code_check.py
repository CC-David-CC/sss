import unittest
from sss.adapters.code_check import pure_function
from sss.suites.code_foundations import cases,grade

class CodeCheckTests(unittest.TestCase):
    def test_reject_exit_zero_and_checker_tampering(self):
        for code in ('import sys\nsys.exit(0)','def total(values):\n    return __import__("os")._exit(0)\n','def total(values):\n    return open("/etc/shadow").read()\n'):
            self.assertFalse(pure_function(code,'total'))
    def test_real_references_fit_explicit_pure_contract(self):
        for case in cases():
            if case.language=='python':
                names={'python.sum_empty':'total','python.binary_search':'locate','python.stable_unique':'unique'}
                self.assertTrue(pure_function(case.reference['task.py'],names[case.id]))
    def test_process_zero_exit_is_not_checker_success(self):
        case=cases()[0]
        self.assertEqual(grade(case,[dict(settled=True,exit_code=0)],case.reference)['status'],'unavailable')
