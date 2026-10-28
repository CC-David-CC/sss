"""Real Linux flocks around controlled records; no PCC/GPU/model dependency."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from sss_integration.cow_learning_audit import idle_evidence_lease


class RecordView:
    """Only the original-record read interface needed by the lease helper."""
    def __init__(self, root):
        self.root = root
        self.read_calls = []
        self.observe_read = None
    def _read(self, path):
        self.read_calls.append(path)
        if self.observe_read:
            self.observe_read(path)
        if path.is_symlink():
            raise ValueError('Fixture refuses record links')
        return json.loads(path.read_bytes())


@unittest.skipUnless(os.name == 'posix', 'Requires Linux flock semantics')
class IdleEvidenceLeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sss-audit-lease-')
        self.root = Path(self.temp.name)
        (self.root / 'operations').mkdir()
        self.locks = [self.root / name for name in ('records.lock', 'worker.lock')]
        for path in self.locks:
            path.write_bytes(('existing ' + path.name + ' bytes\n').encode())
        self.service = RecordView(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def assert_free(self, path):
        with path.open('r+b') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(stream, fcntl.LOCK_UN)

    def assert_busy(self, path):
        with path.open('r+b') as stream:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @contextmanager
    def hold(self, path):
        with path.open('r+b') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def test_both_real_locks_held_without_changing_original_bytes(self):
        op = self.root / 'operations' / 'complete.json'
        op.write_text(json.dumps(dict(state='complete')))
        before = self.snapshot()
        with idle_evidence_lease(self.service):
            for path in self.locks:
                self.assert_busy(path)
        self.assertEqual(self.snapshot(), before)
        for path in self.locks:
            self.assert_free(path)
        self.assertEqual(self.service.read_calls, [op])

    def test_nfs_compatible_write_capable_existing_handles_never_create_or_truncate(self):
        # NFS emulates exclusive flock using write locks. An rb-only descriptor
        # can fail there even though the same test succeeds on a local fs.
        observed = []
        original_open = Path.open
        def tracked_open(path, mode='r', *args, **kwargs):
            if path in self.locks:
                self.assertIn(mode, ('r+b', 'rb+'))
                observed.append((path.name, mode))
            return original_open(path, mode, *args, **kwargs)
        before = self.snapshot()
        with patch.object(Path, 'open', tracked_open):
            with idle_evidence_lease(self.service):
                pass
        self.assertEqual([name for name, mode in observed], ['records.lock', 'worker.lock'])
        self.assertEqual(before, self.snapshot())

    def test_queued_and_running_operations_refuse_admission_and_release_records_lock(self):
        op = self.root / 'operations' / 'active.json'
        for state in ('queued', 'running'):
            op.write_text(json.dumps(dict(state=state)))
            before = self.snapshot()
            with self.subTest(state=state), self.assertRaises(ValueError):
                with idle_evidence_lease(self.service):
                    self.fail('An active original operation was admitted')
            self.assertEqual(before, self.snapshot())
            for path in self.locks:
                self.assert_free(path)

    def test_operation_scan_already_owns_records_and_has_not_taken_worker_yet(self):
        op = self.root / 'operations' / 'complete.json'
        op.write_text(json.dumps(dict(state='complete')))
        def observe_read(path):
            self.assertEqual(path, op)
            self.assert_busy(self.locks[0])
            self.assert_free(self.locks[1])
        self.service.observe_read = observe_read
        with idle_evidence_lease(self.service):
            self.assert_busy(self.locks[0])
            self.assert_busy(self.locks[1])

    def test_busy_records_refuses_before_scanning_any_operation(self):
        (self.root / 'operations' / 'complete.json').write_text(json.dumps(dict(state='complete')))
        before = self.snapshot()
        with self.hold(self.locks[0]):
            with self.assertRaises(ValueError):
                with idle_evidence_lease(self.service):
                    self.fail('Busy records lock was admitted')
            self.assertEqual(self.service.read_calls, [])
            self.assert_free(self.locks[1])
        self.assertEqual(before, self.snapshot())
        self.assert_free(self.locks[0])

    def test_busy_worker_refuses_without_leaking_the_records_lock(self):
        before = self.snapshot()
        with self.hold(self.locks[1]):
            with self.assertRaises(ValueError):
                with idle_evidence_lease(self.service):
                    self.fail('Busy worker lock was admitted')
            self.assert_free(self.locks[0])
        self.assertEqual(before, self.snapshot())
        self.assert_free(self.locks[1])

    def test_error_inside_audit_releases_both_locks(self):
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, 'controlled audit error'):
            with idle_evidence_lease(self.service):
                raise RuntimeError('controlled audit error')
        for path in self.locks:
            self.assert_free(path)
        self.assertEqual(before, self.snapshot())

    def test_record_read_error_releases_admission_lock(self):
        (self.root / 'operations' / 'bad.json').write_text('{')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            with idle_evidence_lease(self.service):
                self.fail('Malformed original operation was admitted')
        for path in self.locks:
            self.assert_free(path)
        self.assertEqual(before, self.snapshot())

    def test_missing_lock_files_are_not_recreated(self):
        for path in self.locks:
            saved = path.read_bytes()
            path.unlink()
            before = self.snapshot()
            with self.subTest(name=path.name), self.assertRaises(ValueError):
                with idle_evidence_lease(self.service):
                    self.fail('Missing original lease was admitted')
            self.assertFalse(path.exists())
            self.assertEqual(before, self.snapshot())
            path.write_bytes(saved)
            for lock in self.locks:
                self.assert_free(lock)

    def test_lock_symlinks_are_refused_without_touching_the_target(self):
        target = self.root / 'unrelated-owned-target'
        target.write_bytes(b'target stays unchanged')
        for path in self.locks:
            saved = path.read_bytes()
            path.unlink()
            path.symlink_to(target)
            with self.subTest(name=path.name), self.assertRaises(ValueError):
                with idle_evidence_lease(self.service):
                    self.fail('Symlink lease was admitted')
            self.assertTrue(path.is_symlink())
            self.assertEqual(target.read_bytes(), b'target stays unchanged')
            path.unlink()
            path.write_bytes(saved)
            for lock in self.locks:
                self.assert_free(lock)


if __name__ == '__main__':
    unittest.main()
