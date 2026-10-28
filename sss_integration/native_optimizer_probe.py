"""Probe complete ordinary-Llama gradients under an explicit owned GPU lease.

No optimizer update, candidate export or model promotion is permitted here.
"""
from pathlib import Path
import argparse
import fcntl
import json
import math
import os
import subprocess
import sys
import time

from sss_integration.native_optimizer_step import digest, sha, write


def run(a):
    if not (a.gpu_index >= 0 and a.device_budget_gib > a.reserve_gib >= 1
            and a.host_reserve_gib >= 1 and 1 <= a.timeout_seconds <= 3600
            and 0 <= a.maximum_initial_utilization <= 100):
        raise ValueError('Explicit bounded owner resources required')
    pcc = a.pcc_root.resolve(strict=True)
    sys.path.insert(0, str(pcc))
    from tools.pcc_native_training import validate_examples
    from tools.gguf_reader import GGUFFile
    selection = json.loads(a.selection.read_text())
    identity_field = 'practice_id' if selection.get('purpose') == 'mixed_66_curriculum_practice' else 'pilot_id'
    if selection.get(identity_field) != digest({k: v for k, v in selection.items() if k != identity_field}):
        raise ValueError('Checked practice selection identity differs')
    if selection.get('protected_cases_exported') is not False or selection.get('target_policy') != 'actions_answer':
        raise ValueError('Unexpected split/target policy')
    sequence_profile = ('dense-llama-action-8k-v1' if identity_field == 'practice_id'
                        else 'dense-llama-short-v1')
    examples = validate_examples(selection['examples'], sequence_profile=sequence_profile)
    if [e['id'] for e in examples] != [r['lesson_id'] for r in selection['selection']]:
        raise ValueError('Selected examples differ from admitted lessons')
    model = a.model.resolve(strict=True)
    if sha(model) != selection['model_sha256']:
        raise ValueError('Pinned original model differs')
    expected = {t.name for t in GGUFFile(model).tensors}
    if not expected:
        raise ValueError('Complete parameter layout required')
    example = max(examples, key=lambda e: len(e['tokens']))
    root = a.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    request = dict(model=str(model), base_sha256=selection['model_sha256'], mode='full',
                   devices=['CUDA0'], sequence_profile=sequence_profile, memory_profile='allocator-v1',
                   device_budget_bytes={'CUDA0': a.device_budget_gib << 30}, reserve_bytes=a.reserve_gib << 30,
                   host_reserve_bytes=a.host_reserve_gib << 30, examples=[example], gradient_probe_only=True,
                   learning_rate=1e-6, batch_size=1, steps=1, deadline_seconds=a.timeout_seconds,
                   candidate=str(root / 'never-written.gguf'))
    write(root / 'intent.json', dict(selection_id=selection[identity_field], sequence_profile=sequence_profile, model_sha256=selection['model_sha256'],
                                    selection_sha256=sha(a.selection), executable_sha256=sha(a.native_executable),
                                    source_sha256=sha(__file__), expected_parameter_tensors=len(expected),
                                    weights_updated=False))
    write(root / 'request-private.json', request)
    lock = Path.home() / '.local/state/context-cow' / ('gpu-' + str(a.gpu_index) + '.lock')
    lock.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    start = time.monotonic()
    status = 'FAILED'
    child = None
    with lock.open('a') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.free,utilization.gpu',
                                        '--format=csv,noheader,nounits'], text=True).splitlines()
        physical = [r.split(',') for r in rows if int(r.split(',')[0]) == a.gpu_index]
        if len(physical) != 1 or int(physical[0][2]) < a.device_budget_gib * 1024 or int(physical[0][3]) > a.maximum_initial_utilization:
            raise RuntimeError('Fresh GPU admission refused')
        row = physical[0]
        write(root / 'admission.json', dict(physical_gpu=a.gpu_index, gpu_uuid=row[1].strip(),
                                           free_mib=int(row[2]), utilization=int(row[3]), lease=str(lock)))
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=row[1].strip(), CUDA_DEVICE_ORDER='PCI_BUS_ID',
                   GGML_CUDA_F32_ACTIVATIONS='1', NVIDIA_TF32_OVERRIDE='0')
        try:
            with (root / 'stdout-private.json').open('x') as out, (root / 'stderr-private.log').open('x') as err:
                child = subprocess.Popen([str(a.native_executable), '--probe-gradients', str(root / 'request-private.json')],
                                         stdout=out, stderr=err, env=env, pass_fds=(lease.fileno(),), start_new_session=True)
                write(root / 'child.json', dict(pid=child.pid,
                      start_ticks=Path('/proc', str(child.pid), 'stat').read_text().split()[21]))
                if child.wait(timeout=a.timeout_seconds + 20):
                    raise RuntimeError('Native gradient probe failed; inspect original output')
            receipt = json.loads((root / 'stdout-private.json').read_text())
            gradients = receipt['gradients']
            if receipt.get('status') != 'GRADIENT_PROBE_PASS' or receipt.get('weights_updated') is not False or receipt.get('candidate_written') is not False:
                raise ValueError('Native no-update probe contract failed')
            if len(gradients) != len(expected) or {g['name'] for g in gradients} != expected or not all(math.isfinite(g['l2']) and g['l2'] > 0 for g in gradients):
                raise ValueError('Complete finite/nonzero parameter-gradient coverage failed')
            if Path(request['candidate']).exists():
                raise ValueError('Gradient-only probe wrote a candidate')
            result = dict(status='PASS', scope='Actual-model complete ordinary backprop gradients; no update',
                          pilot_id=selection[identity_field], selection_id_kind=identity_field,
                          sequence_profile=sequence_profile, model_sha256=selection['model_sha256'],
                          executable_sha256=sha(a.native_executable), tokens=len(example['tokens']),
                          selected_targets=sum(example['loss_mask']), parameter_tensors=len(expected),
                          finite_gradient_tensors=len(gradients), nonzero_gradient_tensors=len(gradients),
                          loss=receipt['loss'], weights_updated=False, promoted=False)
            write(root / 'result.json', result)
            status = 'PASS'
            print(json.dumps(result), flush=True)
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            write(root / 'settlement.json', dict(status=status, allocated_seconds=time.monotonic() - start,
                                                physical_gpus=1, weights_updated=False))
            fcntl.flock(lease, fcntl.LOCK_UN)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root', 'selection', 'model', 'native-executable', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--gpu-index', type=int, required=True)
    p.add_argument('--device-budget-gib', type=int, required=True)
    p.add_argument('--reserve-gib', type=int, default=4)
    p.add_argument('--host-reserve-gib', type=int, default=4)
    p.add_argument('--timeout-seconds', type=int, default=300)
    p.add_argument('--maximum-initial-utilization', type=int, default=50)
    run(p.parse_args())
