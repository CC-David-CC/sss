"""Audit a private PCC/BW native-completion recovery qualification.

This optional S³ adapter validates an owner's saved qualification evidence. It
does not start a model, train, infer, recover a service, or accept a candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys


STAGES = (
    "preflight_passed",
    "before_baseline",
    "baseline_settled",
    "original_one_update_submitted",
    "actual_native_return_and_reload_proved",
    "restart_read_original",
    "needs_operator_hold",
    "bw_inspected_original_completion",
    "original_candidate_adopted",
    "candidate_pending_verified",
    "recovery_dispatch_guards_passed",
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_EVENTS_BYTES = 8 * 1024 * 1024


class EvidenceUnavailable(Exception):
    """Required evidence is missing; this is HOLD, not a model failure."""


class EvidenceInvalid(Exception):
    """Evidence exists but violates its pinned qualification contract."""


def _fail(code: str) -> None:
    raise EvidenceInvalid(code)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate_json_key")
        result[key] = value
    return result


def _parse_json(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except EvidenceInvalid:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceInvalid("invalid_json_record") from exc
    if type(value) is not dict:
        _fail("record_must_be_object")
    return value


def _read_json_with_bytes(path: Path) -> tuple[dict, bytes]:
    raw = _read_bytes(path, MAX_JSON_BYTES)
    return _parse_json(raw), raw


def _read_json(path: Path) -> dict:
    return _read_json_with_bytes(path)[0]


def _read_bytes(path: Path, limit: int) -> bytes:
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except FileNotFoundError as exc:
        raise EvidenceUnavailable("required_artifact_missing") from exc
    except OSError as exc:
        raise EvidenceInvalid("artifact_open_failed") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            _fail("invalid_artifact_file")
        chunks = []
        total = 0
        while total <= limit:
            chunk = os.read(descriptor, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        if total > limit:
            _fail("artifact_too_large")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha(value) -> bool:
    return type(value) is str and SHA256.fullmatch(value) is not None


def _expect(condition: bool, code: str) -> None:
    if not condition:
        _fail(code)


def _component(value, code: str) -> str:
    _expect(type(value) is str and SAFE_COMPONENT.fullmatch(value) is not None, code)
    return value


def _load_events(path: Path, expected_sha256) -> list[dict]:
    raw = _read_bytes(path, MAX_EVENTS_BYTES)
    # Check the exact saved bytes before parsing them. A damaged or edited log
    # should be identified as a receipt-integrity failure even when the edit
    # also makes one JSON line malformed.
    _expect(expected_sha256 == _sha(raw), "event_log_hash_mismatch")
    rows = []
    try:
        for line in raw.splitlines():
            if not line:
                _fail("blank_event_record")
            row = json.loads(line, object_pairs_hook=_pairs)
            if type(row) is not dict:
                _fail("event_must_be_object")
            rows.append(row)
    except EvidenceInvalid:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceInvalid("invalid_event_json") from exc
    return rows


def _exit_code(path: Path) -> int:
    raw = _read_bytes(path, 32)
    try:
        text = raw.decode("ascii").strip()
        if not re.fullmatch(r"-?[0-9]+", text):
            _fail("invalid_exit_receipt")
        return int(text)
    except UnicodeError as exc:
        raise EvidenceInvalid("invalid_exit_receipt") from exc


def verify_recovery_qualification(qualification_root: Path) -> dict:
    """Return a sanitized PASS receipt or raise a typed evidence exception.

    Expected root layout is the private output layout emitted by the bounded
    PCC/BW recovery qualification. Raw evidence is read locally and never
    copied into the returned receipt.
    """
    original_root = Path(qualification_root)
    if original_root.is_symlink():
        _fail("symlink_root_refused")
    try:
        root = original_root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise EvidenceUnavailable("qualification_root_missing") from exc
    except OSError as exc:
        raise EvidenceInvalid("qualification_root_invalid") from exc
    _expect(root.is_dir(), "qualification_root_not_directory")
    private = root / "actual-recovery-run-private"
    summary = _read_json(private / "qualification-summary-private.json")
    events = _load_events(
        private / "events-private.jsonl", summary.get("events_sha256")
    )
    crash, crash_bytes = _read_json_with_bytes(root / "intentional-crash-observed-private.json")
    guards, guard_bytes = _read_json_with_bytes(root / "recovery-dispatch-guards-private.json")

    _expect(type(summary.get("schema")) is int and summary.get("schema") == 1
            and summary.get("state") == "PASS",
            "qualification_summary_not_pass")
    _expect(summary.get("api_key_persisted") is False, "secret_persistence_guard_failed")
    _expect(summary.get("promoted") is False, "candidate_already_promoted")
    _expect(summary.get("recovery_guard_attempts") == [], "recovery_guard_reported_dispatch")
    _expect(summary.get("mode") == "full" and summary.get("optimizer") == "AdamW",
            "training_contract_mismatch")
    _expect(summary.get("devices") == ["CPU"] and summary.get("steps") == 1
            and summary.get("batch_size") == 1, "training_scope_mismatch")
    cpu_budget = summary.get("cpu_budget_bytes")
    _expect(type(cpu_budget) is dict and cpu_budget.get("CPU") == 4 * 1024**3,
            "cpu_budget_mismatch")
    _expect(summary.get("native_training_exit") == 0, "native_training_failed")

    pcc_commit = summary.get("pcc")
    bw_commit = summary.get("bw")
    _expect(type(pcc_commit) is str and COMMIT.fullmatch(pcc_commit) is not None,
            "pcc_source_pin_missing")
    _expect(type(bw_commit) is str and COMMIT.fullmatch(bw_commit) is not None,
            "bw_source_pin_missing")
    source = summary.get("source")
    _expect(type(source) is dict and _is_sha(source.get("driver_sha256"))
            and _is_sha(source.get("service_sha256")), "driver_source_pin_missing")

    stages = [row.get("stage") for row in events]
    _expect(tuple(stages) == STAGES, "event_stage_sequence_mismatch")
    by_stage = dict(zip(stages, events))
    job_id = _component(summary.get("job_id"), "invalid_job_identity")
    run_id = _component(summary.get("run_id"), "invalid_run_identity")
    for row in events:
        if "job_id" in row:
            _expect(row["job_id"] == job_id, "original_job_identity_changed")
        if "run_id" in row:
            _expect(row["run_id"] == run_id, "original_run_identity_changed")

    baseline = by_stage["preflight_passed"]
    _expect(baseline.get("phase") == "baseline_pending", "unexpected_initial_phase")
    settled = by_stage["baseline_settled"]
    _expect(settled.get("phase") == "choosing_lessons" and settled.get("model_calls") == 0
            and settled.get("weights_updated") is False, "baseline_was_not_control_only")
    _expect(by_stage["original_one_update_submitted"].get("training_was_sent") is True,
            "original_update_not_proven")

    candidate_sha = summary.get("candidate_sha256")
    fixture_sha = summary.get("fixture_sha256")
    _expect(_is_sha(candidate_sha), "candidate_hash_missing")
    _expect(_is_sha(fixture_sha), "fixture_hash_missing")
    _expect(candidate_sha != fixture_sha, "candidate_did_not_change")
    native_return = by_stage["actual_native_return_and_reload_proved"]
    _expect(native_return.get("candidate_sha256") == candidate_sha
            and native_return.get("job_state") == "running"
            and native_return.get("run_phase") == "training"
            and native_return.get("crash_sha256") == _sha(crash_bytes)
            and native_return.get("gate_sha256") == summary.get("completion_gate_sha256")
            and native_return.get("service_exit_code") == 73, "native_return_not_bound")
    restart = by_stage["restart_read_original"]
    _expect(restart.get("job_state") == "interrupted" and restart.get("phase") == "training",
            "interruption_not_observed")
    hold = by_stage["needs_operator_hold"]
    _expect(hold.get("phase") == "needs_operator" and hold.get("job_state") == "interrupted"
            and hold.get("reason_code") == "native_job_unresolved", "recovery_hold_not_observed")
    _expect(type(hold.get("status")) is dict and hold["status"].get("exit_code") == 0
            and hold["status"].get("timed_out") is False, "bw_hold_status_failed")
    inspection = by_stage["bw_inspected_original_completion"]
    _expect(inspection.get("state") == "eligible" and inspection.get("candidate_sha256") == candidate_sha
            and _is_sha(inspection.get("evidence_sha256")), "original_completion_not_eligible")
    adoption = by_stage["original_candidate_adopted"]
    _expect(adoption.get("candidate_sha256") == candidate_sha and adoption.get("promoted") is False,
            "original_completion_adoption_mismatch")
    pending = by_stage["candidate_pending_verified"]
    _expect(pending.get("phase") == "candidate_pending" and pending.get("job_state") == "complete"
            and pending.get("candidate_sha256") == candidate_sha and pending.get("promoted") is False,
            "candidate_pending_state_mismatch")
    _expect(type(pending.get("reconcile")) is dict and pending["reconcile"].get("exit_code") == 0,
            "original_round_reconciliation_failed")
    training_sends = sum(row.get("training_was_sent") is True for row in events)
    _expect(training_sends == 1, "recovery_dispatched_training_again")

    _expect(crash.get("schema") == 1 and crash.get("artificial_failure") is True
            and crash.get("fake_native_evidence") is False and crash.get("exit_code") == 73
            and crash.get("kind") == "private.intentional-service-crash.v1"
            and crash.get("stage") == "after actual NativeRunner return; before service job completion commit",
            "fault_injection_not_proven")
    _expect(crash.get("candidate_sha256") == candidate_sha, "fault_candidate_changed")
    _expect(guards.get("schema") == 1 and guards.get("mode") == "recovery"
            and guards.get("blocked_dispatch_attempts") == [], "recovery_dispatch_guard_failed")
    _expect(by_stage["recovery_dispatch_guards_passed"].get("blocked_dispatch_attempts") == [],
            "recovery_event_reported_dispatch")
    _expect(by_stage["recovery_dispatch_guards_passed"].get("guard_receipt_sha256") == _sha(guard_bytes),
            "recovery_guard_receipt_hash_mismatch")

    fixture = _read_bytes(root / "fixture-original-f16.gguf", 64 * 1024 * 1024)
    _expect(len(fixture) == summary.get("fixture_bytes") and _sha(fixture) == fixture_sha,
            "base_fixture_hash_mismatch")
    store = root / "store"
    run_dir = store / "runs" / job_id
    job_record = _read_json(store / "operations" / (job_id + ".json"))
    run_record = _read_json(store / "learning" / run_id / "run.json")
    round_record = _read_json(store / "learning" / run_id / "round-000001.json")
    gate_path = run_dir / "completion-gate.json"
    gate_bytes = _read_bytes(gate_path, MAX_JSON_BYTES)
    try:
        gate = json.loads(gate_bytes, object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceInvalid("invalid_completion_gate") from exc
    gate_sha = _sha(gate_bytes)
    _expect(gate_sha == summary.get("completion_gate_sha256"), "completion_gate_hash_mismatch")
    _expect(type(gate) is dict and gate.get("passed") is True and gate.get("promoted") is False,
            "completion_reload_gate_failed")
    _expect(gate.get("final_batch_examples") == 1, "completion_reload_batch_mismatch")
    error, bound = gate.get("absolute_error"), gate.get("absolute_bound")
    _expect(type(error) in (int, float) and type(bound) in (int, float)
            and math.isfinite(error) and math.isfinite(bound) and 0 <= error <= bound,
            "completion_reload_error_out_of_bound")
    _expect(_exit_code(run_dir / "command.exit") == 0, "native_exit_receipt_failed")
    _expect(_exit_code(run_dir / "completion-reload" / "command.exit") == 0,
            "reload_exit_receipt_failed")

    candidate_path = run_dir / "candidate.gguf"
    candidate_bytes = _read_bytes(candidate_path, 64 * 1024 * 1024)
    _expect(_sha(candidate_bytes) == candidate_sha, "candidate_artifact_hash_mismatch")
    _expect(job_record.get("state") == "complete", "service_job_not_complete")
    job_candidate = job_record.get("candidate")
    _expect(type(job_candidate) is dict and job_candidate.get("candidate_sha256") == candidate_sha
            and job_candidate.get("base_sha256") == fixture_sha, "job_candidate_binding_mismatch")
    _expect(run_record.get("run_id") == run_id and run_record.get("phase") == "candidate_pending"
            and run_record.get("training_job_id") == job_id, "learning_run_binding_mismatch")
    _expect(type(run_record.get("revision")) is int and run_record["revision"] >= 1,
            "learning_run_revision_missing")
    _expect(round_record.get("round") == 1, "original_round_record_missing")
    exit_receipts = list(run_dir.glob("**/command.exit"))
    _expect(len(exit_receipts) == 2, "unexpected_native_dispatch_count")

    return {
        "schema": 1,
        "kind": "pcc_bw_native_completion_recovery_machinery",
        "status": "PASS",
        "pcc_commit": pcc_commit,
        "bw_commit": bw_commit,
        "qualification_driver_sha256": source["driver_sha256"],
        "qualification_service_sha256": source["service_sha256"],
        "training": {
            "mode": "full",
            "optimizer": "AdamW",
            "device": "CPU",
            "cpu_budget_bytes": cpu_budget["CPU"],
            "steps": 1,
            "batch_size": 1,
            "native_exit_code": 0,
            "reload_exit_code": 0,
        },
        "recovery": {
            "fault_injection_exit_code": 73,
            "same_original_job_recovered": True,
            "training_dispatches": training_sends,
            "recovery_dispatch_attempts": 0,
            "final_job_state": "complete",
            "final_learning_phase": "candidate_pending",
            "promoted": False,
        },
        "artifacts": {"base_sha256": fixture_sha, "candidate_sha256": candidate_sha},
        "limits": [
            "This is a tiny synthetic CPU mechanics qualification, not MiniCPM/Wen learning evidence.",
            "A PASS verifies saved receipts and local artifacts; it does not independently attest the host or prove model quality.",
            "Candidate acceptance, retention, GPU behavior and export are outside this receipt.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification-root", type=Path, required=True,
                        help="Private directory containing the saved recovery qualification")
    parser.add_argument("--output", type=Path,
                        help="Optional new sanitized JSON receipt; existing files are refused")
    args = parser.parse_args(argv)
    try:
        result = verify_recovery_qualification(args.qualification_root)
        data = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if args.output is not None:
            target = args.output.absolute()
            if target.exists() or target.is_symlink():
                _fail("output_already_exists")
            try:
                with target.open("xb") as stream:
                    stream.write(data)
                if os.name == "posix":
                    target.chmod(0o600)
            except FileExistsError:
                _fail("output_already_exists")
            except OSError as exc:
                raise EvidenceInvalid("output_write_failed") from exc
        sys.stdout.write(data.decode("utf-8"))
        return 0
    except EvidenceUnavailable as exc:
        sys.stdout.write(json.dumps({"schema": 1, "status": "HOLD", "reason_code": str(exc)}) + "\n")
        return 2
    except EvidenceInvalid as exc:
        sys.stdout.write(json.dumps({"schema": 1, "status": "FAIL", "reason_code": str(exc)}) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
