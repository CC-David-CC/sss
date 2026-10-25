import unittest
from sss.studies.check_sensitivity import assess


def row(program, oracle, code):
    return dict(schema=1,kind='sss.bw-check-observation.v1',case_id='owned.fixture',
        program_sha256=program*64,command_sha256='a'*64,checker_id='b'*64,
        checker_implementation_sha256='c'*64,oracle_passed=oracle,oracle_evidence_sha256='d'*64,
        tool_disposition='exited',tool_exit_code=code,namespace_retired=True,source_unchanged=True,
        bw_ledger_sha256='e'*64,bw_outcome_sha256='f'*64,bw_interpreter_id=program*64,
        bw_implementation_sha256='0'*64)


class CheckSensitivityTests(unittest.TestCase):
    def test_check_must_pass_reference_and_detect_each_known_fault(self):
        reference=row('1',True,0);mutants=[row('2',False,1),row('3',False,0)]
        value=assess(reference,mutants)
        self.assertEqual(value['status'],'MISSES_DECLARED_MUTANTS')
        self.assertEqual((value['detected_mutants'],value['missed_mutants']),(1,1))
        mutants[1]['tool_exit_code']=7
        value=assess(reference,mutants)
        self.assertEqual(value['status'],'DETECTS_DECLARED_MUTANTS')
        self.assertFalse(value['training_approved']);self.assertFalse(value['promoted'])

    def test_broken_check_cannot_look_good_by_failing_every_program(self):
        value=assess(row('1',True,1),[row('2',False,1)])
        self.assertEqual(value['status'],'REFERENCE_CHECK_FAILED')

    def test_timeout_is_unavailable_instead_of_detected_or_missed(self):
        mutant=row('2',False,None);mutant['tool_disposition']='timeout'
        value=assess(row('1',True,0),[mutant])
        self.assertEqual(value['status'],'UNAVAILABLE')
        self.assertEqual((value['detected_mutants'],value['missed_mutants'],value['unavailable_mutants']),(0,0,1))
        self.assertTrue(value['reference_check_passed'])

    def test_passing_oracle_does_not_define_a_known_fault(self):
        value=assess(row('1',True,0),[row('2',True,1)])
        self.assertEqual(value['status'],'INVALID_VARIANT_SET')
        self.assertEqual(value['detected_mutants'],0)
        self.assertEqual(value['invalid_mutants'],1)

    def test_foreign_command_checker_or_implementation_is_refused(self):
        for field in ('command_sha256','checker_id','checker_implementation_sha256','bw_implementation_sha256'):
            mutant=row('2',False,1);mutant[field]='4'*64
            with self.subTest(field=field),self.assertRaises(ValueError):assess(row('1',True,0),[mutant])
        with self.assertRaises(ValueError):assess(row('1',True,0),[row('1',False,1)])

    def test_source_change_or_unretired_namespace_is_not_a_quality_pass(self):
        for field in ('source_unchanged','namespace_retired'):
            mutant=row('2',False,1);mutant[field]=False
            self.assertEqual(assess(row('1',True,0),[mutant])['status'],'UNAVAILABLE')


if __name__=='__main__':
    unittest.main()
