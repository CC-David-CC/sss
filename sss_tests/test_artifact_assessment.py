"""Pure assessment contracts; no BW, PCC, native model or training imports."""
import copy
import unittest

from sss.artifact_assessment import ArtifactAssessmentCase,installed_cases,artifact_question
from sss.practice_oracle import AffineClampFoldCase


def case(name='dev-01',source=b'def solve(values, scale, offset, low, high):\n    return {}\n'):
    return ArtifactAssessmentCase(AffineClampFoldCase.install(name,'held-out-artifact',[
        dict(values=[271,-19],scale=-3,offset=107,low=-13,high=41)]),
        source,'code.affine-clamp-fold','transfer_recovery')


class ArtifactAssessmentTests(unittest.TestCase):
    def test_roundtrip_keeps_exact_source_mode_and_hidden_inputs(self):
        value=case();restored=ArtifactAssessmentCase.from_descriptor(value.descriptor())
        self.assertEqual(restored,value);self.assertEqual(restored.identity,value.identity)

    def test_development_descriptor_is_never_a_practice_registration(self):
        d=case().descriptor();d['split_role']='practice'
        with self.assertRaises(ValueError):ArtifactAssessmentCase.from_descriptor(d)

    def test_schema_alias_unknown_checker_and_extra_fields_are_refused(self):
        for defect in ('bool','extra','checker'):
            d=case().descriptor()
            if defect=='bool':d['schema']=True
            elif defect=='extra':d['approval']=True
            else:d['case']['family']='student-chosen-checker'
            with self.subTest(defect=defect),self.assertRaises(ValueError):ArtifactAssessmentCase.from_descriptor(d)

    def test_hidden_row_variations_are_not_counted_as_distinct_questions(self):
        a=case().descriptor();b=copy.deepcopy(a);b['case']['case_id']='dev-02'
        b['case']['rows'][0]['offset']=108
        with self.assertRaisesRegex(ValueError,'Identical visible task'):installed_cases([a,b])

    def test_duplicate_case_identity_is_refused_even_with_changed_visible_source(self):
        a=case().descriptor();b=copy.deepcopy(a);b['baseline_source']+='\n'
        with self.assertRaisesRegex(ValueError,'Duplicate'):installed_cases([a,b])

    def test_hidden_expected_outputs_and_checker_rows_do_not_enter_prompt(self):
        question=artifact_question(case())
        for secret in ('271','107','held-out-artifact','dev-01','inputs_after','results'):
            self.assertNotIn(secret,question)
        self.assertIn('task.py',question)
        self.assertIn('return {}',question)

    def test_source_and_mode_changes_bind_new_case_identity(self):
        a=case();b=case(source=a.baseline_source+b'\n')
        c=ArtifactAssessmentCase(a.case,a.baseline_source,a.skill_id,a.gate,0o600)
        self.assertEqual(len({a.identity,b.identity,c.identity}),3)

    def test_installed_case_inputs_are_detached_from_owner_dictionary(self):
        value=case().descriptor();installed=installed_cases([value])[0]
        expected=installed.identity;value['case']['rows'][0]['values'].append(555)
        self.assertEqual(installed.identity,expected)

    def test_explicit_source_skill_gate_and_mode_bounds(self):
        a=case()
        for field,value in [('baseline_source',b''),('baseline_source',b'\xff'),
                            ('skill_id','../other'),('gate','unknown'),('source_mode',True),('source_mode',0o755)]:
            kw=dict(case=a.case,baseline_source=a.baseline_source,skill_id=a.skill_id,gate=a.gate,source_mode=a.source_mode)
            kw[field]=value
            with self.subTest(field=field,value=value),self.assertRaises((ValueError,UnicodeError)):ArtifactAssessmentCase(**kw)


if __name__=='__main__':unittest.main()
