"""Synthetic contract tests for the optional PCC/BW recovery receipt auditor."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from sss_integration.native_completion_recovery import (
    EvidenceInvalid,
    EvidenceUnavailable,
    STAGES,
    verify_recovery_qualification,
)


def _json(path: Path, value) -> bytes:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(root: Path) -> tuple[str, str]:
    evidence = root / "actual-recovery-run-private"
    fixture = b"tiny generated base fixture"
    candidate = b"tiny trained candidate fixture"
    fixture_sha, candidate_sha = _digest(fixture), _digest(candidate)
    (root / "fixture-original-f16.gguf").write_bytes(fixture)

    job_id, run_id = "learning-job-test-01", "recovery-test-01"
    gate = {"schema": 1, "passed": True, "promoted": False,
            "final_batch_examples": 1,
            "absolute_error": 0.0, "absolute_bound": 0.0002}
    gate_bytes = _json(root / "store" / "runs" / job_id / "completion-gate.json", gate)
    crash = {
        "schema": 1,
        "artificial_failure": True,
        "fake_native_evidence": False,
        "exit_code": 73,
        "kind": "private.intentional-service-crash.v1",
        "stage": "after actual NativeRunner return; before service job completion commit",
        "candidate_sha256": candidate_sha,
    }
    crash_bytes = _json(root / "intentional-crash-observed-private.json", crash)
    guards = {"schema": 1, "mode": "recovery", "blocked_dispatch_attempts": []}
    guard_bytes = _json(root / "recovery-dispatch-guards-private.json", guards)
    stages = [
        {"stage": STAGES[0], "job_id": job_id, "run_id": run_id,
         "phase": "baseline_pending", "revision": 0},
        {"stage": STAGES[1], "job_id": job_id, "run_id": run_id,
         "phase": "baseline_pending", "revision": 0},
        {"stage": STAGES[2], "job_id": job_id, "run_id": run_id,
         "phase": "choosing_lessons", "revision": 2,
         "model_calls": 0, "weights_updated": False},
        {"stage": STAGES[3], "job_id": job_id, "run_id": run_id,
         "training_was_sent": True},
        {"stage": STAGES[4], "job_id": job_id, "run_id": run_id,
         "job_state": "running", "run_phase": "training",
         "candidate_sha256": candidate_sha, "crash_sha256": _digest(crash_bytes),
         "gate_sha256": _digest(gate_bytes), "service_exit_code": 73},
        {"stage": STAGES[5], "job_id": job_id, "run_id": run_id,
         "job_state": "interrupted", "phase": "training"},
        {"stage": STAGES[6], "job_id": job_id, "run_id": run_id,
         "job_state": "interrupted", "phase": "needs_operator",
         "reason_code": "native_job_unresolved",
         "status": {"exit_code": 0, "timed_out": False}},
        {"stage": STAGES[7], "job_id": job_id, "run_id": run_id,
         "state": "eligible", "candidate_sha256": candidate_sha,
         "evidence_sha256": "e" * 64},
        {"stage": STAGES[8], "job_id": job_id, "run_id": run_id,
         "candidate_sha256": candidate_sha, "promoted": False},
        {"stage": STAGES[9], "job_id": job_id, "run_id": run_id,
         "phase": "candidate_pending", "job_state": "complete",
         "candidate_sha256": candidate_sha, "promoted": False,
         "reconcile": {"exit_code": 0}},
        {"stage": STAGES[10], "job_id": job_id, "run_id": run_id,
         "blocked_dispatch_attempts": [], "guard_receipt_sha256": _digest(guard_bytes)},
    ]
    event_bytes = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in stages
    )
    (evidence / "events-private.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (evidence / "events-private.jsonl").write_bytes(event_bytes)
    summary = {
        "schema": 1,
        "state": "PASS",
        "scope": "tiny CPU recovery mechanics",
        "job_id": job_id,
        "run_id": run_id,
        "api_key_persisted": False,
        "promoted": False,
        "recovery_guard_attempts": [],
        "mode": "full",
        "optimizer": "AdamW",
        "devices": ["CPU"],
        "steps": 1,
        "batch_size": 1,
        "cpu_budget_bytes": {"CPU": 4 * 1024**3},
        "native_training_exit": 0,
        "pcc": "a" * 40,
        "bw": "b" * 40,
        "source": {"driver_sha256": "c" * 64, "service_sha256": "d" * 64},
        "events_sha256": _digest(event_bytes),
        "candidate_sha256": candidate_sha,
        "fixture_sha256": fixture_sha,
        "fixture_bytes": len(fixture),
        "completion_gate_sha256": _digest(gate_bytes),
    }
    _json(evidence / "qualification-summary-private.json", summary)

    run_dir = root / "store" / "runs" / job_id
    (run_dir / "candidate.gguf").write_bytes(candidate)
    _json(root / "store" / "operations" / (job_id + ".json"), {
        "state": "complete",
        "candidate": {"candidate_sha256": candidate_sha, "base_sha256": fixture_sha},
    })
    _json(root / "store" / "learning" / run_id / "run.json", {
        "run_id": run_id, "phase": "candidate_pending", "revision": 7,
        "training_job_id": job_id,
    })
    _json(root / "store" / "learning" / run_id / "round-000001.json", {"round": 1})
    (run_dir / "command.exit").write_text("0\n", encoding="ascii")
    (run_dir / "completion-reload" / "command.exit").parent.mkdir(parents=True, exist_ok=True)
    (run_dir / "completion-reload" / "command.exit").write_text("0\n", encoding="ascii")
    return job_id, candidate_sha


class NativeCompletionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.job_id, self.candidate_sha = _fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def _events(self):
        path = self.root / "actual-recovery-run-private" / "events-private.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def _write_events(self, rows):
        path = self.root / "actual-recovery-run-private" / "events-private.jsonl"
        data = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                        for row in rows)
        path.write_bytes(data)
        summary_path = self.root / "actual-recovery-run-private" / "qualification-summary-private.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["events_sha256"] = _digest(data)
        _json(summary_path, summary)

    def test_accepts_complete_recovery_and_returns_only_sanitized_receipt(self):
        report = verify_recovery_qualification(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["recovery"]["training_dispatches"], 1)
        self.assertEqual(report["recovery"]["recovery_dispatch_attempts"], 0)
        self.assertEqual(report["recovery"]["final_learning_phase"], "candidate_pending")
        self.assertFalse(report["recovery"]["promoted"])
        rendered = json.dumps(report)
        self.assertNotIn(self.job_id, rendered)
        self.assertNotIn(str(self.root), rendered)
        self.assertNotIn("run_directory", report)

    def test_second_training_dispatch_during_recovery_is_rejected(self):
        rows = self._events()
        rows[-1]["training_was_sent"] = True
        self._write_events(rows)
        with self.assertRaisesRegex(EvidenceInvalid, "recovery_dispatched_training_again"):
            verify_recovery_qualification(self.root)

    def test_candidate_cannot_change_between_fault_and_recovery(self):
        crash_path = self.root / "intentional-crash-observed-private.json"
        crash = json.loads(crash_path.read_text(encoding="utf-8"))
        crash["candidate_sha256"] = "f" * 64
        _json(crash_path, crash)
        rows = self._events()
        rows[4]["crash_sha256"] = _digest(crash_path.read_bytes())
        self._write_events(rows)
        with self.assertRaisesRegex(EvidenceInvalid, "fault_candidate_changed"):
            verify_recovery_qualification(self.root)

    def test_candidate_must_remain_pending_and_unpromoted(self):
        run_path = self.root / "store" / "learning" / "recovery-test-01" / "run.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        run["phase"] = "complete"
        _json(run_path, run)
        with self.assertRaisesRegex(EvidenceInvalid, "learning_run_binding_mismatch"):
            verify_recovery_qualification(self.root)

    def test_missing_records_are_hold_not_a_model_failure(self):
        (self.root / "recovery-dispatch-guards-private.json").unlink()
        with self.assertRaises(EvidenceUnavailable):
            verify_recovery_qualification(self.root)

    def test_event_bytes_must_match_the_saved_hash(self):
        path = self.root / "actual-recovery-run-private" / "events-private.jsonl"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(EvidenceInvalid, "event_log_hash_mismatch"):
            verify_recovery_qualification(self.root)


if __name__ == "__main__":
    unittest.main()
