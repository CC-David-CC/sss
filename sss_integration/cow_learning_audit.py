"""Audit completed COW learning rounds from original evidence; never dispatch work.

Optional PCC adapter. The auditor reuses PCC record/lesson readers and S3's
registered evaluator recovery and analysis, with the existing worker lease held.
"""
from pathlib import Path
import argparse
from contextlib import contextmanager
import fcntl
import json
import math
import os
import sys
from types import SimpleNamespace
from sss.records import digest, file_sha256


@contextmanager
def idle_evidence_lease(service):
    """Block new admissions, refuse existing work, then take the worker lease.

    Both acquisitions are nonblocking: workers use the reverse lock order.
    r+b is required for exclusive NFS locks, but no file bytes are written.
    """
    paths = [service.root / name for name in ('records.lock', 'worker.lock')]
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError('Original nonsymlink record and worker locks are required')
    with paths[0].open('r+b') as records:
        try:
            fcntl.flock(records, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Original record admission is busy; audit later') from None
        for path in (service.root / 'operations').glob('*.json'):
            if service._read(path).get('state') in ('queued', 'running'):
                raise ValueError('Original queued or running work exists; audit later')
        with paths[1].open('r+b') as worker:
            try:
                fcntl.flock(worker, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Original worker is active; audit later') from None
            yield


def checked_record(service, path):
    value = service._read(path)
    if value.get('record_sha256') != digest({k: v for k, v in value.items() if k != 'record_sha256'}):
        raise ValueError('Original learning record checksum differs')
    return {k: v for k, v in value.items() if k != 'record_sha256'}


def report_summary(report):
    """Summarize only after the entire report matched fresh policy analysis.

    A panel policy wraps the ordinary proposal rather than duplicating its
    fields at the top level. Keep that distinction and every panel visible;
    never replace the report used for policy verification or parent selection.
    """
    proposal = report['aggregate'] if report.get('kind') == 'sss.panel-learning-report.v1' else report
    result = {key: proposal[key] for key in (
        'baseline_answer_delta', 'parent_answer_delta',
        'baseline_answer_losses', 'working_decision')}
    if report.get('kind') == 'sss.panel-learning-report.v1':
        result['panels'] = [dict(panel_id=p['panel_id'], role=p['role'],
            **report_summary(p['report'])) for p in report['panels']]
    return result


def audit_rounds(service, policy, run_id):
    """Read only a settled round boundary. Caller holds the existing worker lease."""
    from tools.pcc_lessons import OP, HEX
    if type(run_id) is not str or not OP.fullmatch(run_id):
        raise ValueError('An exact original learning-run ID is required')
    directory = service.root / 'learning' / run_id
    if (service.root / 'learning').is_symlink() or directory.is_symlink():
        raise ValueError('Learning evidence directory links refused')
    run_path = directory / 'run.json'
    original_run = run_path.read_bytes()
    run = checked_record(service, run_path)
    completed_rounds = run.get('completed_rounds')
    exact_boundary = type(completed_rounds) is int and completed_rounds == run.get('round')
    untrained_tail = (type(completed_rounds) is int and type(run.get('round')) is int
        and run.get('phase') == 'stopped' and run['round'] == completed_rounds + 1
        and not any(key in run for key in ('training_job_id','training_request','candidate_evaluation','pending_step_id')))
    if (run.get('run_id') != run_id or run.get('policy_id') != digest(policy.describe())
            or run.get('phase') not in ('round_complete', 'stopped')
            or run.get('pending_step_id') is not None
            or type(completed_rounds) is not int or not 1 <= completed_rounds <= policy.max_rounds
            or not (exact_boundary or untrained_tail)):
        raise ValueError('Audit requires an unchanged registered run at a completed round boundary')
    if untrained_tail:
        next_job = 'learning-job-' + digest(dict(run=run_id, round=run['round'], policy=run['policy_id']))
        if any(path.exists() for path in (service.root/'operations'/(next_job+'.json'),
                service.root/'runs'/next_job, directory/('round-%06d.json'%run['round']))):
            raise ValueError('Stopped tail has native/round artifacts; reconcile original effects first')
    policy.verify()
    pins = {str(run_path): file_sha256(run_path)}

    def read(path, *, checksum=False):
        value = checked_record(service, path) if checksum else service._read(path)
        pins[str(path)] = file_sha256(path)
        return value

    jobs = {}

    def job(identity, *, require_state=True):
        if identity in jobs:
            return jobs[identity]
        if type(identity) is not str or not OP.fullmatch(identity):
            raise ValueError('Invalid original native job identity')
        value = read(service.root / 'operations' / (identity + '.json'))
        if value['path'] != '/cow/training/jobs' or value['state'] != 'complete':
            raise ValueError('Only an original completed native job can be audited')
        candidate = value['candidate']
        if candidate['mode'] not in ('full', 'lora') or candidate.get('promoted') is not False:
            raise ValueError('Unpromoted native candidate identity required')
        roles = [('candidate_path', 'candidate_sha256')]
        state_fields = ('optimizer_state_path', 'optimizer_state_sha256')
        if any(k in candidate for k in state_fields):
            if not all(k in candidate for k in state_fields):
                raise ValueError('Partial initial optimizer state is invalid')
            roles.append(state_fields)
        elif require_state:
            raise ValueError('A registered learning round needs its original optimizer state')
        for path_key, sha_key in roles:
            path = Path(candidate[path_key])
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(service.root / 'runs'):
                raise ValueError('Original candidate/state must remain in this owned service')
            if file_sha256(path) != candidate[sha_key]:
                raise ValueError('Native candidate or optimizer-state bytes differ')
            pins[str(path)] = candidate[sha_key]
        jobs[identity] = value
        return value

    def evaluation(name, candidate, reference=None):
        saved_path = directory / (name + '-evaluation.json')
        saved = read(saved_path)
        if reference is not None and reference != dict(file=saved_path.name, sha256=digest(saved)):
            raise ValueError('Original committed evaluation reference differs')
        recovered = policy.recover_evaluation(candidate, directory / (name + '-backend'))
        if recovered is None or recovered != saved:
            raise ValueError('Complete original backend evidence must reproduce the committed evaluation')
        policy.validate_evaluation(saved, candidate)
        return saved

    creation = read(service.root / 'operations' / (run_id + '.json'))
    if (creation['path'] != '/cow/training/learning-runs' or creation['state'] != 'complete'
            or creation['request'] != run['creation_request']
            or creation['request']['policy_id'] != run['policy_id']
            or creation['request'].get('parent_job_id') != run['initial_parent_job_id']):
        raise ValueError('Original learning-run creation approval differs')
    baseline = evaluation('baseline', None, run['baseline_evaluation'])
    working_id = run['initial_parent_job_id']
    parent_operation = None if working_id is None else job(working_id, require_state=False)
    parent_candidate = None if parent_operation is None else parent_operation['candidate']
    training = policy.describe()['training']
    expected_initial = creation['request'].get('expected_parent_sha256')
    if ((parent_candidate is None and expected_initial is not None)
            or (parent_candidate is not None and
                (parent_candidate['mode'] != training['mode']
                 or (training['mode'] == 'lora' and parent_operation['request']['rank'] != training['rank'])
                 or expected_initial != parent_candidate['candidate_sha256']))):
        raise ValueError('Initial parent mode, rank or approved artifact differs')
    parent = baseline if parent_candidate is None else evaluation('initial-parent', parent_candidate)
    parent_reference = run['baseline_evaluation'] if working_id is None else dict(
        file='initial-parent-evaluation.json', sha256=digest(parent))
    rows = []
    previous_report = None
    referenced_jobs = set()
    training = policy.describe()['training']
    for number in range(1, run['completed_rounds'] + 1):
        record = read(directory / ('round-%06d.json' % number), checksum=True)
        if record['status'] != 'complete' or record['round'] != number or record['parent_job_id'] != working_id:
            raise ValueError('Original round sequence or selected parent differs')
        identity = record['candidate_job_id']
        if identity != 'learning-job-' + digest(dict(run=run_id, round=number, policy=run['policy_id'])):
            raise ValueError('Native job differs from its original derived round identity')
        if identity in referenced_jobs:
            raise ValueError('One native job cannot stand in for two learning rounds')
        referenced_jobs.add(identity)
        operation = job(identity)
        request, candidate = operation['request'], operation['candidate']
        if (request != record['training_request'] or request['parent_job_id'] != working_id
                or request['lesson_ids'] != record['lesson_ids']
                or any(request[k] != v for k, v in training.items())
                or request.get('expected_parent_sha256') !=
                   (None if parent_candidate is None else parent_candidate['candidate_sha256'])):
            raise ValueError('Native request, registered recipe, exact parent or selected lessons differ')
        lessons = []
        for lesson_id in record['lesson_ids']:
            if type(lesson_id) is not str or not HEX.fullmatch(lesson_id):
                raise ValueError('Invalid original lesson identity')
            lesson_path = service.root / 'lessons' / (lesson_id + '.json')
            lessons.append(service._lesson(lesson_id))
            pins[str(lesson_path)] = file_sha256(lesson_path)
        policy.validate_lessons(lessons, previous_report)
        from tools.pcc_native_training import (optimizer_dataset_sha256, read_optimizer_state,
            validate_optimizer_request, validate_training_budget_request, validate_training_budget_receipt)
        from tools.pcc_optimizer_profiles import select
        profile = select(service.audit_optimizer_profiles, request)
        folder = Path(candidate['candidate_path']).parent
        native_path = folder / 'request-private.json'
        native = read(native_path)
        launch = read(folder / 'launch.json')
        code = read(folder / 'command.exit')
        stdout = read(folder / 'stdout-private.json')
        original_receipt = {k:v for k,v in candidate['receipt'].items() if k not in ('request_sha256','parent_adapter_sha256')}
        examples = [row['example'] for row in lessons]
        if (type(code) is not int or code != 0
                or launch['request_sha256'] != file_sha256(native_path)
                or candidate['receipt']['request_sha256'] != launch['request_sha256']
                or stdout != original_receipt
                or candidate['receipt'].get('native') is not True
                or candidate['receipt'].get('mode') != request['mode']
                or candidate['receipt'].get('backprop_mode') != 'standard'
                or native['examples'] != examples
                or Path(native['candidate']).resolve(strict=True) != Path(candidate['candidate_path']).resolve(strict=True)
                or Path(native['optimizer_state_output']).resolve(strict=True) != Path(candidate['optimizer_state_path']).resolve(strict=True)
                or any(native[k] != request[k] for k in ('mode','rank','batch_size','steps','learning_rate'))
                or native.get('backprop_mode') != 'standard'
                or candidate['mode'] != request['mode']
                or candidate.get('optimizer_profile_id') != request['optimizer_profile_id']
                or candidate['optimizer_state_policy'] != 'fresh'
                or native.get('optimizer_state_mode') != 'fresh'
                or native.get('optimizer') != profile['optimizer']
                or native.get('optimizer_settings') != profile['optimizer_settings']
                or candidate['receipt'].get('optimizer') != profile['optimizer']):
            raise ValueError('Original native dispatch, verified lessons or optimizer recipe differs')
        validate_optimizer_request(native)
        parent_sha = None if parent_candidate is None else parent_candidate['candidate_sha256']
        expected_base = service.audit_base_sha256 if request['mode'] == 'lora' or parent_sha is None else parent_sha
        expected_model = service.audit_model_path if request['mode'] == 'lora' or parent_candidate is None else parent_candidate['candidate_path']
        if (native['base_sha256'] != expected_base
                or candidate['base_sha256'] != expected_base or launch['base_sha256'] != expected_base
                or Path(native['model']).resolve(strict=True) != Path(expected_model).resolve(strict=True)
                or not HEX.fullmatch(str(launch.get('executable_sha256')))
                or (request['mode'] == 'lora' and native.get('initial_adapter_sha256') != parent_sha)
                or (request['mode'] == 'lora' and parent_candidate is not None
                    and Path(native['initial_adapter']).resolve(strict=True) != Path(parent_candidate['candidate_path']).resolve(strict=True))
                or candidate['receipt'].get('parent_adapter_sha256') != (parent_sha if request['mode'] == 'lora' else None)
                or (request['mode'] == 'full' and native.get('initial_adapter_sha256') is not None)):
            raise ValueError('Native input weights/adapter differ from the exact selected parent')
        timed = validate_training_budget_request(native)
        if native.get('training_budget_seconds') != profile['training_budget_seconds']:
            raise ValueError('Native budget differs from the registered recipe')
        steps = candidate['receipt']['steps']
        completed = validate_training_budget_receipt(native, candidate['receipt']) if timed else training['steps']
        checkpoint = candidate['receipt']['optimizer_checkpoint']
        state = read_optimizer_state(candidate['optimizer_state_path'], candidate['optimizer_state_sha256'])
        dataset = optimizer_dataset_sha256(examples)
        if (candidate['optimizer_completed_steps'] != completed or len(steps) != completed
                or state['completed_steps'] != completed
                or checkpoint['path'] != candidate['optimizer_state_path']
                or checkpoint['sha256'] != candidate['optimizer_state_sha256']
                or checkpoint['candidate_sha256'] != candidate['candidate_sha256']
                or state['model_sha256'] != candidate['candidate_sha256']
                or state['dataset_sha256'] != dataset or checkpoint['dataset_sha256'] != dataset
                or state['config'] != checkpoint['config']):
            raise ValueError('Original optimizer state does not bind these weights and verified lessons')
        cursor = 0
        for index, row in enumerate(steps):
            count = min(training['batch_size'], len(examples) - cursor % len(examples))
            cursor += count
            if (row['step'] != index or row['examples'] != count or row['example_cursor'] != cursor
                    or not row['gradients'] or any(not math.isfinite(g['l2']) or g['l2'] < 0 for g in row['gradients'])):
                raise ValueError('Native fresh-state coverage or finite-gradient evidence differs')
        if state['example_cursor'] != cursor or candidate['receipt']['example_cursor'] != cursor:
            raise ValueError('Actual native practice cursor differs from completed batches')
        value = evaluation('candidate-%06d' % number, candidate, record['candidate_evaluation'])
        decision = policy.analyze(baseline, parent, value)
        report = read(directory / ('report-%06d.json' % number))
        if (decision['report'] != report or record['report'] != report
                or record['report_sha256'] != digest(report)
                or ('assessment' in decision and record.get('assessment') != decision['assessment'])):
            raise ValueError('Recomputed learning, forgetting or assessment proposal differs')
        next_id = identity if decision['working_parent'] == 'candidate' else working_id
        if record['working_parent_job_id'] != next_id:
            raise ValueError('Reported next working parent differs from the original decision')
        rows.append(dict(round=number, passed=value['passed'], finished=value['finished'],
            cases=value['cases'], candidate_sha256=candidate['candidate_sha256'],
            optimizer_state_sha256=candidate['optimizer_state_sha256'],
            native_updates=len(steps), presentations=candidate['receipt']['example_cursor'],
            optimizer_state_policy=candidate['optimizer_state_policy'],
            **report_summary(report), evaluation_sha256=digest(value),
            report_sha256=digest(report)))
        if decision['working_parent'] == 'candidate':
            parent, parent_candidate = value, candidate
            parent_reference = record['candidate_evaluation']
        working_id, previous_report = next_id, report
    if (run['working_parent_job_id'] != working_id or run['last_report'] != previous_report
            or run['parent_evaluation'] != parent_reference
            or (not untrained_tail and run['candidate_evaluation'] != record['candidate_evaluation'])
            or ('assessment' in decision and run.get('last_assessment') != decision['assessment'])
            or run_path.read_bytes() != original_run):
        raise ValueError('Original run changed during audit or selected another parent')
    for path, expected in pins.items():
        if file_sha256(path) != expected:
            raise ValueError('Original input changed during audit')
    policy.verify()
    return dict(schema=1, status='AUDITED_ORIGINAL_EVIDENCE',
        scope='Completed configured COW learning rounds; not broad skill mastery or release acceptance',
        policy_id=run['policy_id'], baseline=dict(passed=baseline['passed'], finished=baseline['finished'],
            cases=baseline['cases'], evaluation_sha256=digest(baseline)), rounds=rows,
        distinct_referenced_native_jobs=len(referenced_jobs),
        untrained_stopped_tail_round=run['round'] if untrained_tail else None,
        original_backend_case_records_revalidated=baseline['cases'] *
            (1 + len(rows) + int(run['initial_parent_job_id'] is not None)),
        protected_answers_exported=False, model_calls_started=0, native_jobs_started=0,
        source_records_modified=False, promoted=False,
        auditor_sha256=file_sha256(__file__))


def audit(a):
    pcc = a.pcc_root.resolve(strict=True)
    sys.path[:0] = [str(pcc), str(pcc / 'experimental/branching_context/src')]
    from tools.pcc_lessons import LessonService
    from tools.fastokens_tokenizer import load_tokenizer
    from sss.adapters.cow_learning import configured_policies
    input_pins = {path: file_sha256(path) for path in (a.training_config, a.cow_profile)}
    config = json.loads(a.training_config.read_bytes())
    profile = json.loads(a.cow_profile.read_bytes())
    root = Path(config['directory']).resolve(strict=True)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise ValueError('Audit requires the owned private training store')
    if a.output.resolve().is_relative_to(root) or a.output.exists():
        raise ValueError('Audit output must be a new file outside the original training store')
    if 'learning_config' not in config or 'skill_guard_config' in config:
        raise ValueError('Explicit configured COW learning registry required')
    from tools.pcc_optimizer_profiles import profiles
    registered = profiles(config['runner'].get('optimizer_profiles', {}),
        sequence_profile=config['runner'].get('sequence_profile', 'short-v1'),
        deadline=config['runner'].get('timeout_seconds', 3600))
    tokenizer = load_tokenizer(profile['model_path'])
    policies = configured_policies(config['learning_config'], SimpleNamespace(config=config['runner']), profile, tokenizer)
    # Read the actual PCC lesson/operation implementations without invoking its
    # constructor, executor, recovery scheduler, HTTP server or native runner.
    service = LessonService.__new__(LessonService)
    service.root, service.model = root, profile['model_contract_id']
    service.tokenize = tokenizer.encode
    service.rendered_tokenize = lambda text: tokenizer.encode(text, parse_special=True)
    service.max_tokens = config['max_tokens']
    service.sequence_profile = config['runner'].get('sequence_profile', 'short-v1')
    service.audit_optimizer_profiles = registered
    service.audit_base_sha256 = config['runner']['base_sha256']
    service.audit_model_path = config['runner']['model']
    store_contract = service._read(root / 'model.json')
    if store_contract != dict(schema=1, model_contract_id=service.model):
        raise ValueError('Original service store belongs to another model contract')
    with idle_evidence_lease(service):
        from tools.pcc_lessons import OP
        if not OP.fullmatch(a.run_id):
            raise ValueError('Invalid original run ID')
        run = checked_record(service, root / 'learning' / a.run_id / 'run.json')
        if run['policy_id'] not in policies:
            raise ValueError('Original registered policy is unavailable')
        result = audit_rounds(service, policies[run['policy_id']], a.run_id)
    for path, expected in input_pins.items():
        if file_sha256(path) != expected:
            raise ValueError('Owner audit configuration changed during verification')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps(result), flush=True)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pcc-root', type=Path, required=True)
    p.add_argument('--training-config', type=Path, required=True)
    p.add_argument('--cow-profile', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    return audit(p.parse_args(argv))


if __name__ == '__main__':main()
