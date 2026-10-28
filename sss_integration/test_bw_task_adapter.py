"""Contract tests for the public S³-to-BW shell fixture adapter."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sss_integration.bw_task_adapter import prepare_public_bw_task


class PublicBwTaskAdapterTests(unittest.TestCase):
    def test_failure_status_fixture_is_relative_and_matches_s3_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'project'
            result = prepare_public_bw_task('shell.failure_status', project)
            self.assertEqual(result['read_paths'], ['check.sh'])
            self.assertEqual(result['edit_paths'], ['check.sh'])
            self.assertNotIn('/home/', result['test_command'])
            self.assertNotIn('check_failure_status.py', result['test_command'])
            self.assertEqual((project / 'check.sh').read_text(),
                             '#!/bin/sh\ngrep -q READY "$1"\necho checked\n')
            self.assertEqual((project / 'tests' / 'ready.txt').read_bytes(), b'READY\n')
            self.assertEqual((project / 'tests' / 'not-ready.txt').read_bytes(), b'not ready\n')
            self.assertEqual(set(result['fixture_sha256']), {
                'check.sh', 'tests/not-ready.txt', 'tests/ready.txt'})
            self.assertTrue(result['qualification_only'])
            self.assertTrue(result['visible_to_model'])
            self.assertTrue(result['host_checker_remains_authoritative'])

    def test_quoted_filename_fixture_is_a_distinct_shell_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'project'
            result = prepare_public_bw_task('shell.quoted_filename', project)
            self.assertEqual(result['read_paths'], ['copy.sh'])
            self.assertEqual(result['edit_paths'], ['copy.sh'])
            self.assertEqual((project / 'copy.sh').read_text(), '#!/bin/sh\ncat $1 > $2\n')
            expected = 'one\nUnicode: α\n'.encode('utf-8')
            self.assertEqual((project / 'source one.txt').read_bytes(), expected)
            self.assertEqual((project / 'semi;colon.txt').read_bytes(), expected)
            self.assertNotIn('/home/', result['test_command'])
            self.assertIn("'literal $name.txt'", result['test_command'])

    @unittest.skipUnless(os.name == 'posix', 'the fixture command requires POSIX sh')
    def test_exact_commands_reject_broken_sources_and_accept_references(self):
        from sss.suites.code_foundations import cases
        case_map = {row.id: row for row in cases()}
        for case_id, filename in [('shell.failure_status', 'check.sh'),
                                  ('shell.quoted_filename', 'copy.sh')]:
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as temporary:
                case = case_map[case_id]
                project = Path(temporary) / 'project'
                result = prepare_public_bw_task(case_id, project)
                command = subprocess.run(
                    ['/bin/sh', '-c', result['test_command']], cwd=project,
                    capture_output=True, text=True, check=False)
                self.assertNotEqual(command.returncode, 0, command.stdout + command.stderr)
                (project / filename).write_text(case.reference[filename])
                command = subprocess.run(
                    ['/bin/sh', '-c', result['test_command']], cwd=project,
                    capture_output=True, text=True, check=False)
                self.assertEqual(command.returncode, 0, command.stdout + command.stderr)

    def test_unknown_case_and_nonempty_destination_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'project'
            with self.assertRaises(ValueError):
                prepare_public_bw_task('shell.not-registered', project)
            project.mkdir()
            marker = project / 'keep.txt'
            marker.write_text('keep')
            with self.assertRaises(ValueError):
                prepare_public_bw_task('shell.failure_status', project)
            self.assertEqual(marker.read_text(), 'keep')

    @unittest.skipUnless(os.name == 'posix' and os.environ.get('BW_ROOT'),
                         'run on POSIX with BW_ROOT set to the matching BranchWrite checkout')
    def test_adapter_output_is_accepted_by_bw_coding_launcher(self):
        bw_root = Path(os.environ['BW_ROOT']).resolve(strict=True)
        sys.path.insert(0, str(bw_root))
        from branchwrite.coding_cli import build_launch
        connection = dict(endpoint_url='http://127.0.0.1:1', endpoint_pin='fixture-only',
                          model_contract_id='a' * 64, execution_profile_id='b' * 64,
                          eos_tokens=[256])
        with tempfile.TemporaryDirectory() as temporary:
            for case_id, source_path in [('shell.failure_status', 'check.sh'),
                                         ('shell.quoted_filename', 'copy.sh')]:
                with self.subTest(case_id=case_id):
                    project = Path(temporary) / case_id.replace('.', '-')
                    task = prepare_public_bw_task(case_id, project)
                    launch = build_launch(
                        project, task['task'], connection,
                        branch='sss-shell-adapter-' + case_id.replace('.', '-'),
                        read_paths=task['read_paths'], edit_paths=task['edit_paths'],
                        test_commands=[task['test_command']])
                    config = launch['config']
                    self.assertEqual(config['verification']['commands'][0], {
                        'command': task['test_command'], 'disposition': 'exited', 'exit_code': 0})
                    self.assertTrue(config['grant']['allow_shell'])
                    self.assertEqual(config['grant']['edit_paths'], [source_path])


if __name__ == '__main__':
    unittest.main()
