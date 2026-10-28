import copy
import hashlib
import json
import unittest
import tempfile
import builtins
from pathlib import Path
from unittest.mock import patch
from sss.practice_oracle import AffineClampFoldCase, exact, grade_observation, strict_json
from sss.adapters.bw_practice_oracle import validate_source, observe

ROWS = [dict(values=[],scale=2,offset=-3,low=-5,high=5),
        dict(values=[-8,-2,0,2,8],scale=3,offset=-1,low=-6,high=7),
        dict(values=[3,-4,3],scale=-2,offset=4,low=-3,high=10),
        dict(values=[0,1,-1],scale=0,offset=9,low=2,high=2)]
CORRECT = b"def solve(values,scale,offset,low,high):\n    transformed=[min(high,max(low,scale*x+offset)) for x in values]\n    return {'values':transformed,'total':sum(transformed)}\n"

# All passed the legacy spelling-only gate, which intentionally remains intact.
AUTHORITY_BYPASSES = (
    b'def solve(values,scale,offset,low,high,solve=eval):\n return solve("1+1")\n',
    b'def solve(values,scale,offset,low,high):\n min=eval\n return min("1+1")\n',
    b'def solve(values,scale,offset,low,high):\n return sorted(["1+1"],key=eval)\n',
    b'def solve(values,scale,offset,low,high):\n [eval for eval in []]\n return sorted(["1+1"],key=eval)\n',
    b'def solve(values,scale,offset,low,high):\n return sorted(["__import__(chr(111)+chr(115))._exit(0)"],key=eval)\n',
    b'''def solve(values,scale,offset,low,high,solve=eval):
 return solve("(__import__('sys').stdout.write('PASS'), __import__('sys').stdout.flush(), __import__('os')._exit(0))")
''',
)

def case():
    return AffineClampFoldCase.install('synthetic.affine.001','practice-bn',copy.deepcopy(ROWS))

def observation(c):
    # Fault-injection unit fixture, NOT an executed BW receipt.
    return dict(disposition='exited',exit_code=0,output_truncated=False,source_unchanged=True,captured_execution_source_matches=True,
        isolation=dict(kind='bubblewrap-terminal-v1',worker_exited=True,namespace_members_after=[]),
        stdout=json.dumps(c.expected()))

class PracticeCoreTests(unittest.TestCase):
    def test_authority_bypasses_refused_despite_legacy_admission(self):
        from sss.adapters.code_check import pure_function
        for source in AUTHORITY_BYPASSES:
            with self.subTest(source=source):
                self.assertTrue(pure_function(source.decode(),'solve'))
                self.assertFalse(validate_source(source,hashlib.sha256(source).hexdigest()))

    def test_exact_signature_no_shadowing_nested_defs_or_annotations(self):
        variants=(
            CORRECT.replace(b'(values,scale,offset,low,high)',b'(values,scale,offset,low,high=1)'),
            CORRECT.replace(b'(values,scale,offset,low,high)',b'(values,scale,offset,low,high,**kwargs)'),
            CORRECT.replace(b'(values,scale,offset,low,high)',b'(values,scale,offset,low,*,high)'),
            CORRECT.replace(b'(values,scale,offset,low,high)',b'(values:int,scale,offset,low,high)'),
            CORRECT.replace(b'high):',b'high)->int:'),
            b'def solve(values,scale,offset,low,high):\n def other():\n  return 1\n return other\n',
            b'def solve(values,scale,offset,low,high):\n try:\n  return 1\n except 1 as min:\n  return min\n',
            b'def solve(values,scale,offset,low,high):\n match values:\n  case min:\n   return min\n',
            b'def solve(values,scale,offset,low,high):\n x:int=1\n return x\n',
            b'def solve(values,scale,offset,low,high):\n return [min for min in values]\n',
            b'def solve(values,scale,offset,low,high):\n solve=1\n return solve\n',
        )
        for source in variants:
            with self.subTest(source=source):
                self.assertFalse(validate_source(source,hashlib.sha256(source).hexdigest()))

    def test_immutable_install_and_explicit_pins(self):
        rows=copy.deepcopy(ROWS); c=AffineClampFoldCase.install('one','practice',rows)
        rows[1]['values'].clear()
        self.assertEqual(c.rows,ROWS)
        self.assertEqual(c.pins['inputs_sha256'],hashlib.sha256(c.inputs_json).hexdigest())
        self.assertNotEqual(c.pins['case_sha256'],case().pins['case_sha256'])

    def test_reject_invalid_install(self):
        for rows in ([],[dict(ROWS[0],scale=True)],[dict(ROWS[0],low=10,high=1)],
                     [dict(ROWS[0],values=[True])],[dict(ROWS[0],extra=0)],
                     [dict(ROWS[0],values=[0]*65)],[ROWS[0]]*33,
                     [dict(ROWS[0],offset=1000001)]):
            with self.subTest(rows=str(rows)[:100]),self.assertRaises(ValueError):
                AffineClampFoldCase.install('one','practice',rows)
        with self.assertRaises(ValueError):
            AffineClampFoldCase('one','practice',b'[]','student-module')
        with self.assertRaises(ValueError):
            AffineClampFoldCase('one','practice',b'['*2000+b']'*2000)

    def test_wrong_pin_oversize_nonutf8_and_contract(self):
        with self.assertRaises(ValueError): validate_source(CORRECT,'0'*64)
        for raw in (b'x'*32769,b'\xff'):
            with self.assertRaises((ValueError,UnicodeError)):
                validate_source(raw,hashlib.sha256(raw).hexdigest())
        for raw in (b'raise SystemExit(0)',b"def solve(values,scale,offset,low,high):\n open('task.py','w').write('x')\n",b'def solve(*args):\n print("forged")\n'):
            self.assertFalse(validate_source(raw,hashlib.sha256(raw).hexdigest()))
        self.assertTrue(validate_source(CORRECT,hashlib.sha256(CORRECT).hexdigest()))

    def test_observe_revalidates_forged_case_before_execution(self):
        c=case(); object.__setattr__(c,'inputs_json',b'[{"values":[],"scale":true,"offset":0,"low":0,"high":0}]')
        with self.assertRaises(ValueError): observe(c,CORRECT,hashlib.sha256(CORRECT).hexdigest(),'/does-not-create')

    def test_strict_json(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":-Infinity}','{"x":1e999}','{}{}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError): strict_json(raw)
        self.assertFalse(exact(True,1));self.assertFalse(exact(1.0,1))

    def test_fault_injected_unsettled_never_failed_skill(self):
        c=case()
        for patch in (dict(disposition='timeout'),dict(disposition='output_limit'),dict(output_truncated=True),
                      dict(source_unchanged=False),dict(captured_execution_source_matches=False),dict(isolation={}),
                      dict(isolation=dict(kind='bubblewrap-terminal-v1',worker_exited=True,namespace_members_after=[123]))):
            o=observation(c);o.update(patch)
            self.assertEqual(grade_observation(c,o)['status'],'unavailable')
        o=observation(c);del o['captured_execution_source_matches']
        self.assertEqual(grade_observation(c,o)['status'],'unavailable')

    def test_fault_injected_forged_zero_boolean_duplicate_nonfinite(self):
        c=case()
        for stdout in ('', 'PASS', '{}', '{"results":[],"results":[]}', '{"x":NaN}'):
            o=observation(c);o['stdout']=stdout
            self.assertEqual(grade_observation(c,o)['status'],'fail')
        o=observation(c); value=c.expected();value['results'][0]['total']=False;o['stdout']=json.dumps(value)
        self.assertEqual(grade_observation(c,o)['status'],'fail')
        self.assertEqual(grade_observation(c,observation(c))['status'],'pass')

    def test_fault_injected_missing_optional_runtime_unavailable(self):
        original=builtins.__import__
        def missing(name,*args,**kwargs):
            if name == 'branchwrite' or name.startswith('branchwrite.'):
                raise ImportError('fault-injected missing optional BW runtime')
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as root,patch('builtins.__import__',side_effect=missing):
            result=observe(case(),CORRECT,hashlib.sha256(CORRECT).hexdigest(),Path(root)/'run')
        self.assertEqual(result['status'],'unavailable')
        self.assertFalse(result['execution_attempted'])

if __name__=='__main__': unittest.main()
