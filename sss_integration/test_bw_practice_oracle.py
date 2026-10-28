"""Explicit optional CPU integration: real BW namespaces; no model/GPU."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sss.adapters.bw_practice_oracle import observe
from sss_tests.test_practice_oracle import CORRECT, AUTHORITY_BYPASSES, case

class BWPracticeTests(unittest.TestCase):
    def run_source(self,raw):
        with tempfile.TemporaryDirectory(prefix='sss-practice-bn-') as root:
            result=observe(case(),raw,hashlib.sha256(raw).hexdigest(),Path(root)/'observation')
            saved=json.loads((Path(root)/'observation/result-private.json').read_bytes())
            self.assertEqual(saved,result)
            self.assertIs(result['lesson_approved'],False)
            return result

    def test_actual_correct_reference(self):
        result=self.run_source(CORRECT)
        self.assertEqual(result['status'],'pass',result)
        o=result['observation'];self.assertEqual(o['exit_code'],0)
        self.assertTrue(o['source_unchanged']);self.assertTrue(o['isolation']['worker_exited'])
        self.assertEqual(o['isolation']['namespace_members_after'],[])
        self.assertEqual([r['path'] for r in o['details']['inputs']],['task.py'])
        self.assertIs(o['captured_execution_source_matches'],True)

    def test_fault_injected_projection_pin_mismatch_is_unavailable(self):
        from branchwrite.terminal import execute_command
        def altered(*args,**kwargs):
            receipt=execute_command(*args,**kwargs)
            receipt.details['inputs'][0]['sha256']='0'*64
            return receipt
        with patch('branchwrite.terminal.execute_command',side_effect=altered):
            result=self.run_source(CORRECT)
        self.assertEqual(result['status'],'unavailable')
        self.assertTrue(result['observation']['source_unchanged'])
        self.assertFalse(result['observation']['captured_execution_source_matches'])

    def test_actual_broken_logic_zero_exit_and_mutator(self):
        for source in (CORRECT.replace(b'scale*x+offset',b'x+offset'),
            b"def solve(values,scale,offset,low,high):\n return {'values':[],'total':0}\n",
            CORRECT.replace(b'    transformed=',b'    values.append(999)\n    transformed='),
            CORRECT.replace(b"'total':sum(transformed)",b"'total':False")):
            with self.subTest(source=source):
                result=self.run_source(source)
                self.assertEqual(result['status'],'fail',result)
                self.assertEqual(result['observation']['exit_code'],0)

    def test_contract_invalid_not_fake_execution(self):
        for source in (b'raise SystemExit(0)',b'def solve(*args):\n print("PASS")\n',
                       b"def solve(*args):\n open('task.py','w').write('forged')\n"):
            result=self.run_source(source)
            self.assertEqual(result['status'],'fail');self.assertFalse(result['execution_attempted'])
            self.assertNotIn('observation',result)

    def test_actual_forging_attempts_refused_before_namespace_execution(self):
        for source in AUTHORITY_BYPASSES:
            with self.subTest(source=source):
                result=self.run_source(source)
                self.assertEqual(result['status'],'fail')
                self.assertFalse(result['execution_attempted'])
                self.assertNotIn('observation',result)

    def test_actual_namespace_readonly_self_edit(self):
        # Boundary-level negative, not accepted pure-function program.
        from branchwrite.execution import Executor, Grant
        from branchwrite.terminal import NamedCommand, execute_command
        with tempfile.TemporaryDirectory(prefix='sss-readonly-bn-') as tmp:
            root=Path(tmp);src=root/'source';src.mkdir();(src/'task.py').write_bytes(CORRECT)
            command=NamedCommand('readonly',('/usr/bin/python3','-I','-B','-c',"from pathlib import Path;Path('task.py').write_text('forged')"),5)
            e=Executor.create(src,root/'world',commands=(command,),project_input=True)
            r=execute_command(e,'readonly',Grant((),False,read_paths=('task.py',),command_names=('readonly',)),'readonly')
            self.assertEqual(r.disposition,'exited');self.assertNotEqual(r.exit_code,0)
            self.assertIn(b'Read-only file system',r.stderr.read_bytes())
            self.assertEqual((e.workspace/'task.py').read_bytes(),CORRECT)
            self.assertTrue(r.details['isolation']['worker_exited'])
            self.assertEqual(r.details['isolation']['namespace_members_after'],[])

if __name__=='__main__': unittest.main()
