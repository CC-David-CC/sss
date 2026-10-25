"""Optional S³ adapter to PCC/COW's existing BW execution path."""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import subprocess
import sys


def shared_input_prefix(prefixes):
    """Exact common rendered input only; no answer or lesson information."""
    if (type(prefixes) is not list or not prefixes
            or any(type(row) is not list or not row
                or any(type(token) is not int or token < 0 for token in row) for row in prefixes)):
        raise ValueError('Explicit nonempty rendered token prefixes required')
    shared = list(prefixes[0])
    for row in prefixes[1:]:
        length = 0
        for left, right in zip(shared, row):
            if left != right: break
            length += 1
        del shared[length:]
        if not shared: break
    return shared


def runtime_binding(profile):
    """Identify execution independently of candidate weights and GPU placement.

    The full, model-bound COW profile is retained in the evaluation intent.
    Equal-runtime curves can then compare different candidates without erasing
    the exact per-request model, execution-profile and physical GPU identities.
    """
    execution = {k: v for k, v in profile['execution'].items() if k not in ('GPU', 'environment')}
    execution['environment'] = {k: v for k, v in profile['execution']['environment'].items()
                                if k != 'CUDA_VISIBLE_DEVICES'}
    return dict(backend=profile['backend'], native_build=profile['native_build'],
                execution=execution, worker_layout='one-pinned-physical-GPU-per-process')


def validate_profile(profile, *, model, model_sha256, gpu_uuid, context_tokens,
                     batch_tokens, stop_token_ids, hardware_row):
    e = profile['execution']
    if (Path(profile['model_path']).resolve() != Path(model).resolve()
            or profile['model_weights_sha256'] != model_sha256
            or e['capacity'] != context_tokens or e['prefill_chunk'] != batch_tokens
            or e['eos_tokens'] != sorted(set(stop_token_ids))
            or e.get('device_binding') != 'cuda-single-device-v1'
            or e['GPU'] != [int(hardware_row[0])]
            or hardware_row[1] != gpu_uuid):
        raise ValueError('COW profile does not match the exact evaluation model, GPU or policy')


@contextmanager
def cow_session(pcc_root, profile, model, model_sha256, gpu_uuid, directory, *,
                context_tokens, batch_tokens, stop_token_ids,
                minimum_free_mib, maximum_initial_utilization, on_admission=None):
    """Use the existing COW GPU lock and request owner, with explicit headroom."""
    if (type(minimum_free_mib) is not int or minimum_free_mib < 1
            or type(maximum_initial_utilization) is not int
            or not 0 <= maximum_initial_utilization <= 100):
        raise ValueError('Explicit COW admission limits required')
    sys.path[:0] = [str(Path(pcc_root).resolve()),
                   str(Path(pcc_root).resolve()/'experimental/branching_context/src')]
    from tools.cow_server import gpu_locks
    from tools.pcc_cow_evaluation import CowEvaluationSession
    def observe():
        raw = subprocess.check_output(['nvidia-smi',
            '--query-gpu=index,uuid,memory.free,utilization.gpu',
            '--format=csv,noheader,nounits'], text=True, timeout=30)
        rows = [tuple(v.strip() for v in line.split(',')) for line in raw.splitlines()]
        selected = [row for row in rows if row[1] == gpu_uuid]
        if len(selected) != 1:
            raise ValueError('Pinned COW GPU is unavailable')
        return selected[0]
    row = observe()
    validate_profile(profile, model=model, model_sha256=model_sha256,
                     gpu_uuid=gpu_uuid, context_tokens=context_tokens,
                     batch_tokens=batch_tokens, stop_token_ids=stop_token_ids, hardware_row=row)
    with gpu_locks(Path.home()/'.local/state/context-cow', [int(row[0])]):
        row = observe()
        if int(row[2]) < minimum_free_mib or int(row[3]) > maximum_initial_utilization:
            raise RuntimeError('COW GPU lacks the admitted headroom')
        admission = dict(gpu_uuid=gpu_uuid, free_mib=int(row[2]),
                utilization=int(row[3]), context_tokens=context_tokens, batch_tokens=batch_tokens,
                minimum_free_mib=minimum_free_mib, maximum_initial_utilization=maximum_initial_utilization)
        if on_admission is not None: on_admission(admission)
        previous = {k: os.environ.get(k) for k in profile['execution']['environment']}
        os.environ.update(profile['execution']['environment'])
        session = None
        try:
            session = CowEvaluationSession(profile, Path(directory)/'cow-store', pcc_root)
            session.pcc_admission = admission
            yield session
        finally:
            try:
                if session is not None: session.close()
            finally:
                for k, value in previous.items():
                    if value is None: os.environ.pop(k, None)
                    else: os.environ[k] = value


def token_completion(session, tok, prefix, *, maximum, stop_token_ids, stream):
    """S³ maps an original COW receipt to its existing grading record."""
    if list(sorted(set(stop_token_ids))) != session.profile['execution']['eos_tokens']:
        raise ValueError('Scoring stop tokens differ from COW')
    receipt = session.complete(prefix, maximum=maximum, stream=stream)
    tokens = receipt['tokens']
    text_tokens = tokens[:-1] if receipt['stop_reason'] == 'eos' else tokens
    return dict(text=tok.decode(text_tokens), sampled_token_ids=tokens,
                stop_reason=receipt['stop_reason'], stop_token_id=receipt['stop_token_id'],
                prefill_tokens=receipt['counters']['consumed_tokens'],
                model_calls=receipt['counters']['forward_calls'], cow_receipt=receipt)
