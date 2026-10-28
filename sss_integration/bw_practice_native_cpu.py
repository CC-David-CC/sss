"""One native CPU update from a verified BW failure-derived S³ practice lesson.

Controlled fixture only. This proves the path and exact target mask, not model
quality or generalization. Requires matching BW/PCC checkouts and a PCC native
CPU executable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pcc-root', type=Path, required=True)
parser.add_argument('--bw-root', type=Path, required=True)
parser.add_argument('--native-executable', type=Path, required=True)
parser.add_argument('--workdir', type=Path, required=True)
args = parser.parse_args()
pcc = args.pcc_root.resolve(strict=True)
bw = args.bw_root.resolve(strict=True)
sys.path[:0] = [str(bw), str(pcc)]

from experimental.native_training.make_cpu_fixture import make_fixture
from tools.pcc_lessons import LessonService, NativeRunner
from sss.adapters.bw_fixtures import task
from sss_integration.bw_capture_verify import (
    admit_bw_practice_lesson, build_practice_lesson_from_capture_pair,
)
from branchwrite.lesson_capture import capture_correction, capture_failure
from branchwrite.lesson_cli import digest

root = args.workdir.absolute()
root.mkdir(mode=0o700, parents=True, exist_ok=False)
model = make_fixture(root / 'tiny-byte-fixture.gguf', context_length=1024)
binary = args.native_executable.resolve(strict=True)
base_sha256 = hashlib.sha256(model.read_bytes()).hexdigest()
contract = hashlib.sha256(b'pcc-byte-fixture-v1' + model.read_bytes()).hexdigest()
tokenizer = lambda text: list(text.encode('utf-8'))
runner = NativeRunner(dict(
    model=str(model), base_sha256=base_sha256, executable=str(binary),
    devices=['CPU'], gpu_uuids=[], device_budget_bytes={'CPU': 1024**3},
    reserve_bytes=16 * 1024**2,
))
service = LessonService(root / 'service', contract, tokenizer, runner,
                        max_tokens=512, max_steps=1,
                        rendered_tokenize=tokenizer)

def render(rows):
    return [dict(role=row['role'], kind=row['kind'],
                 rendered=('U:' if row['role'] == 'user' else 'A:') + row['content'],
                 verified=row['verified'], scope=row['scope']) for row in rows]

try:
    connection = dict(endpoint_url='http://127.0.0.1:1', endpoint_pin='fixture-only',
                      model_contract_id=contract,
                      execution_profile_id=digest({'cpu': 'fixture'}), eos_tokens=[256])
    failed = task(root / 'failed-work', connection, corrected=False,
                  factor=2, name='double')
    captures = root / 'captures'
    captures.mkdir(mode=0o700)
    failure = capture_failure(failed, captures / 'failure')
    repaired = task(root / 'corrected-work', connection, corrected=True,
                    factor=2, name='double', include_failed_check=True)
    correction = capture_correction(repaired, captures / 'correction',
                                    captures / 'failure')
    prepared = build_practice_lesson_from_capture_pair(
        failure_dir=captures / 'failure', correction_dir=captures / 'correction',
        failure_capture_id=failure.capture_id,
        correction_capture_id=correction.capture_id,
        case_id='python.double', practice_case_id='python.triple.practice',
        skill_id='code.python.debug', archive_path=root / 'practice-archive',
        model_contract_id=contract, renderer_sha256=digest('native-cpu-renderer-v1'),
        tokenizer_sha256=digest('utf8-byte-tokenizer-v1'), render=render,
        tokenize=tokenizer, maximum=512)
    admission = admit_bw_practice_lesson(service, 'bw-practice-native-lesson', prepared)
    request = dict(operation_id='bw-practice-native-update',
                   lesson_ids=[admission['lesson_id']], mode='full', batch_size=1,
                   steps=1, learning_rate=0.001, rank=1, parent_job_id=None)
    acceptance = service.submit('/cow/training/jobs', request)
    deadline = time.monotonic() + 180
    while True:
        job = service.job(acceptance['job_id'])
        if job['state'] not in ('queued', 'running'):
            if job['state'] != 'complete':
                raise RuntimeError('Native update did not complete: ' + repr(job))
            break
        if time.monotonic() > deadline:
            raise TimeoutError('Native CPU update exceeded 180 seconds')
        time.sleep(0.1)
    private_request = json.loads((root / 'service' / 'runs' /
                                  acceptance['job_id'] / 'request-private.json').read_text())
    expected = prepared['expected_example']
    actual = private_request['examples'][0]
    if any(actual.get(key) != expected.get(key)
           for key in ('tokens', 'targets', 'loss_mask')):
        raise RuntimeError('Native request differs from the S³ checked lesson')
    if job.get('promoted') is not False:
        raise RuntimeError('Controlled candidate must not be promoted')
    if hashlib.sha256(model.read_bytes()).hexdigest() != base_sha256:
        raise RuntimeError('Immutable base fixture changed')
    result = dict(
        status='PASS', scope='controlled BW capture → S³ practice → PCC admission → native CPU update',
        model_quality_claim=False, spontaneous_failure=False, gpu_used=False,
        source_case='python.double', practice_case='python.triple.practice',
        skill_id='code.python.debug', failure_capture_id=failure.capture_id,
        correction_capture_id=correction.capture_id,
        capture_receipt_sha256=prepared['capture_receipt']['receipt_sha256'],
        lesson_id=admission['lesson_id'], job_id=acceptance['job_id'],
        supervised_tokens=sum(expected['loss_mask']),
        native_loss_mask_matches_sss=True, weights_updated=True,
        promoted=False, base_unchanged=True, base_sha256=base_sha256,
        candidate_sha256=hashlib.sha256(
            (root / 'service' / 'runs' / acceptance['job_id'] /
             'candidate.gguf').read_bytes()).hexdigest(),
        loss_before=job['steps'][0]['before'], loss_after=job['steps'][0]['after'],
    )
    (root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
finally:
    service.close()
