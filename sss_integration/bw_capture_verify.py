"""Independently re-check a BW-captured failure/correction with S³.

This adapter reads existing immutable BW captures. It does not create a BW task,
edit an archive, approve training, or dispatch a model update.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile

from sss.adapters.code_check import run_check
from sss.adapters.linux_sandbox import EnvironmentUnavailable, LinuxSandbox
from sss import records as sss_records
from sss.records import digest
from sss.suites.code_foundations import cases

_HEX = re.compile(r'[a-f0-9]{64}\Z')
_MAX_SOURCE_BYTES = 64 * 1024


class VerificationRefused(ValueError):
    """The captures or requested registered check do not match."""


class VerificationUnavailable(RuntimeError):
    """Required BW code or an isolated Linux check environment is unavailable."""


def _bw_capture_api():
    try:
        return importlib.import_module('branchwrite.lesson_capture')
    except ImportError as exc:
        raise VerificationUnavailable('matching BW source must be on PYTHONPATH') from exc


def _case(case_id):
    matches = [case for case in cases() if case.id == case_id]
    if len(matches) != 1:
        raise VerificationRefused('case_id_not_in_sss_registry')
    case = matches[0]
    if len(case.before) != 1:
        raise VerificationRefused('registered_case_must_name_one_source_file')
    return case


def _source_name(case):
    name = next(iter(case.before))
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute()
            or any(part in ('', '.', '..') for part in relative.parts)
            or '\\' in name or '\x00' in name):
        raise VerificationRefused('registered_source_path_is_not_relative')
    return name


def _capture_pair(failure_dir, correction_dir, failure_id, correction_id):
    if not all(type(value) is str and _HEX.fullmatch(value)
               for value in (failure_id, correction_id)):
        raise VerificationRefused('owner_pinned_capture_ids_must_be_sha256')
    api = _bw_capture_api()
    try:
        failure = api.read_capture(failure_dir, expected_capture_id=failure_id)
        correction = api.read_capture(correction_dir, expected_capture_id=correction_id)
    except api.CaptureRefused as exc:
        raise VerificationRefused('bw_capture_integrity_check_failed') from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise VerificationRefused('bw_capture_integrity_check_failed') from exc
    fm, cm = failure.manifest, correction.manifest
    if fm.get('kind') != 'failure' or cm.get('kind') != 'correction':
        raise VerificationRefused('failure_and_correction_capture_kinds_required')
    if cm.get('failure_capture_id') != failure.capture_id:
        raise VerificationRefused('correction_does_not_link_the_supplied_failure')
    if (fm.get('independently_verified') is not False
            or cm.get('independently_verified') is not False
            or fm.get('training_approved') is not False
            or cm.get('training_approved') is not False):
        raise VerificationRefused('bw_capture_must_remain_unverified_and_unapproved')
    if fm.get('evidence', {}).get('task_id') != cm.get('evidence', {}).get('task_id'):
        raise VerificationRefused('failure_and_correction_task_ids_differ')
    for key in ('model_contract_id', 'execution_profile_id'):
        if fm.get(key) != cm.get(key):
            raise VerificationRefused('failure_and_correction_model_bindings_differ')
    return failure, correction


def _materialize(capture, source_name, workspace):
    try:
        raw = capture.file_bytes(source_name)
    except (OSError, ValueError, KeyError) as exc:
        raise VerificationRefused('registered_source_missing_from_capture') from exc
    if type(raw) is not bytes or len(raw) > _MAX_SOURCE_BYTES:
        raise VerificationRefused('registered_source_exceeds_size_bound')
    target = workspace.joinpath(*PurePosixPath(source_name).parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _receipt(*, status, failure, correction, case, source_name, source_hashes,
             checks, reason_codes=()):
    oracle_implementation = {
        'code_check.py': Path(run_check.__code__.co_filename),
        'linux_sandbox.py': Path(LinuxSandbox.run.__code__.co_filename),
        'code_foundations.py': Path(cases.__code__.co_filename),
        'records.py': Path(sss_records.__file__),
    }
    implementation_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in oracle_implementation.items()
    }
    receipt = dict(
        schema=1,
        method='sss-independent-bw-capture-oracle-v1',
        status=status,
        failure_capture_id=failure.capture_id,
        correction_capture_id=correction.capture_id,
        task_id_sha256=hashlib.sha256(
            str(failure.manifest['evidence']['task_id']).encode('utf-8')).hexdigest(),
        model_contract_id=failure.manifest['model_contract_id'],
        execution_profile_id=failure.manifest['execution_profile_id'],
        case_id=case.id,
        skill_ids=list(case.skills),
        source_name=source_name,
        source_sha256=source_hashes,
        checker_id=digest(case.check_program),
        checker_implementation_sha256=digest(implementation_hashes),
        oracle_implementation_sha256=implementation_hashes,
        checks=checks,
        reason_codes=list(reason_codes),
        independently_verified=(status == 'verified'),
        training_approved=False,
        lesson_created=False,
    )
    receipt['receipt_sha256'] = digest(receipt)
    return receipt


def verify_bw_capture_pair(*, failure_dir, correction_dir, failure_capture_id,
                           correction_capture_id, case_id):
    """Return a sanitized receipt after S³ checks the exact captured source bytes.

    A ``verified`` receipt means the original source fails and the captured
    correction passes the registered S³ oracle. It does not approve that source
    as a practice lesson or authorize training.
    """
    failure, correction = _capture_pair(
        failure_dir, correction_dir, failure_capture_id, correction_capture_id)
    case = _case(case_id)
    source_name = _source_name(case)
    source_hashes = {}
    checks = []
    try:
        with tempfile.TemporaryDirectory(prefix='sss-bw-oracle-') as temporary:
            root = Path(temporary)
            for label, capture in (('failure', failure), ('correction', correction)):
                workspace = root / label
                workspace.mkdir(mode=0o700)
                source_hashes[label] = _materialize(capture, source_name, workspace)
                observation = run_check(case, LinuxSandbox(workspace))
                checks.append(dict(
                    capture_id=capture.capture_id,
                    role=label,
                    passed=observation.get('passed') is True,
                    settled=observation.get('settled') is True,
                    checker_evidence_sha256=observation.get('evidence_sha256'),
                    source_sha256=source_hashes[label],
                ))
    except EnvironmentUnavailable as exc:
        return _receipt(status='unavailable', failure=failure, correction=correction,
                        case=case, source_name=source_name, source_hashes=source_hashes,
                        checks=checks, reason_codes=['linux_sandbox_unavailable'])
    except OSError as exc:
        return _receipt(status='unavailable', failure=failure, correction=correction,
                        case=case, source_name=source_name, source_hashes=source_hashes,
                        checks=checks, reason_codes=['host_check_io_unavailable'])
    expected = [('failure', False), ('correction', True)]
    actual = [(row['role'], row['passed']) for row in checks]
    if any(not row['settled'] for row in checks):
        return _receipt(status='unavailable', failure=failure, correction=correction,
                        case=case, source_name=source_name, source_hashes=source_hashes,
                        checks=checks, reason_codes=['oracle_did_not_settle'])
    if actual != expected:
        reasons = []
        if len(checks) != 2 or actual[:1] != [('failure', False)]:
            reasons.append('captured_failure_did_not_fail_sss_oracle')
        if len(checks) != 2 or actual[-1:] != [('correction', True)]:
            reasons.append('captured_correction_did_not_pass_sss_oracle')
        return _receipt(status='mismatch', failure=failure, correction=correction,
                        case=case, source_name=source_name, source_hashes=source_hashes,
                        checks=checks, reason_codes=reasons)
    return _receipt(status='verified', failure=failure, correction=correction,
                    case=case, source_name=source_name, source_hashes=source_hashes,
                    checks=checks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--failure', type=Path, required=True)
    parser.add_argument('--failure-capture-id', required=True)
    parser.add_argument('--correction', type=Path, required=True)
    parser.add_argument('--correction-capture-id', required=True)
    parser.add_argument('--case', required=True, help='Registered S³ code case id')
    args = parser.parse_args(argv)
    try:
        receipt = verify_bw_capture_pair(
            failure_dir=args.failure,
            correction_dir=args.correction,
            failure_capture_id=args.failure_capture_id,
            correction_capture_id=args.correction_capture_id,
            case_id=args.case,
        )
    except VerificationUnavailable:
        print(json.dumps(dict(schema=1, status='unavailable',
                              reason_codes=['bw_capture_reader_unavailable'],
                              training_approved=False, lesson_created=False), sort_keys=True))
        return 2
    except VerificationRefused:
        print(json.dumps(dict(schema=1, status='refused',
                              reason_codes=['capture_or_case_binding_failed'],
                              training_approved=False, lesson_created=False), sort_keys=True))
        return 3
    print(json.dumps(receipt, sort_keys=True, separators=(',', ':')))
    return {'verified': 0, 'mismatch': 1, 'unavailable': 2}[receipt['status']]


if __name__ == '__main__':
    raise SystemExit(main())
