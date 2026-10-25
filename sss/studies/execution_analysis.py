"""Read-only CPU analysis of completed evaluations, parallel across artifacts.

Workers return observations. One caller merges and writes the report. No GPU,
model loading, grading change, training, retry or workflow authority lives here.
"""
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
import json
import math
import statistics
import time

from ..records import digest
from ..paired import compare_frozen_evaluations, POLICY


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Finite nonnegative execution measurement required')
    return value


def _analyze_one(item):
    label, directory = item
    directory = Path(directory)
    raw = (directory/'result.json').read_bytes()
    result = json.loads(raw)
    compare_frozen_evaluations(result, result, POLICY)
    settlement = json.loads((directory/'settlement.json').read_text())
    if settlement['status'] != 'COMPLETE':
        raise ValueError('Completed assessment and settlement required')
    expected = {row['id']: row for row in result['outcomes']}
    seen = set()
    indices = set()
    seconds = []
    request_seconds = []
    generation_seconds = []
    groups = {}
    consumed_tokens = calls = export_bytes = import_bytes = 0
    for path in sorted(directory.glob('*-private.json')):
        row = json.loads(path.read_bytes())
        index = row['index']
        if (type(index) is not int or not 0 <= index < result['cases'] or index in indices
                or path.name != f'{index:04d}-private.json'
                or row['id'] not in expected or row['id'] in seen
                or any(row[k] != result[k] for k in ('model_sha256', 'runtime_id', 'evaluation_id'))
                or any(type(row[k]) is not bool for k in ('passed', 'finished'))
                or any(row[k] != expected[row['id']][k] for k in ('skill_id', 'gate', 'passed', 'finished'))):
            raise ValueError('Private execution record differs from the completed assessment')
        seen.add(row['id']); indices.add(index)
        elapsed = _number(row['seconds']); seconds.append(elapsed)
        group = groups.setdefault((row['skill_id'], row['gate']), dict(cases=0, seconds=0.))
        group['cases'] += 1; group['seconds'] += elapsed
        completion = row['completion']
        consumed_tokens += _number(completion['prefill_tokens'])
        calls += _number(completion['model_calls'])
        receipt = completion.get('cow_receipt')
        if receipt is not None:
            request = _number(receipt['request_seconds'])
            generation = _number(receipt['generation_seconds'])
            if generation > request or request > elapsed + 1e-6:
                raise ValueError('Nested execution intervals disagree')
            request_seconds.append(request); generation_seconds.append(generation)
            export_bytes += _number(receipt['counters']['checkpoint_export_bytes'])
            import_bytes += _number(receipt['counters']['checkpoint_import_bytes'])
    if seen != expected.keys() or len(indices) != result['cases']:
        raise ValueError('Missing or duplicated response evidence')
    if (directory/'result.json').read_bytes() != raw:
        raise ValueError('Assessment changed during CPU analysis')
    ordered = sorted(seconds)
    return dict(assessment=label, evidence_id=digest(result), evaluation_id=result['evaluation_id'],
        runtime_id=result['runtime_id'], model_sha256=result['model_sha256'], cases=len(seconds),
        passed=result['passed'], finished=result['finished'], case_seconds=sum(seconds),
        case_distribution=dict(minimum=ordered[0], median=statistics.median(ordered),
            p95=ordered[math.ceil(.95*len(ordered))-1], maximum=ordered[-1]),
        allocated_seconds=_number(settlement['allocated_seconds']),
        execution_wall_seconds=_number(settlement['execution_wall_seconds']),
        cow_cases=len(request_seconds), cow_request_seconds=sum(request_seconds),
        cow_generation_seconds=sum(generation_seconds), checkpoint_export_bytes=export_bytes,
        checkpoint_import_bytes=import_bytes, forward_tokens=consumed_tokens, forward_calls=calls,
        groups=[dict(skill_id=k[0], gate=k[1], **v) for k, v in sorted(groups.items())])


def analyze_assessments(assessments, *, workers=1):
    if (type(assessments) is not dict or not 1 <= len(assessments) <= 256
            or any(type(k) is not str or not k or len(k) > 128 for k in assessments)
            or type(workers) is not int or not 1 <= workers <= 32):
        raise ValueError('Named independent assessments and bounded worker count required')
    items = sorted(assessments.items())
    workers = min(workers, len(items))
    started = time.monotonic()
    if workers == 1:
        rows = [_analyze_one(item) for item in items]
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=get_context('spawn')) as pool:
            rows = list(pool.map(_analyze_one, items, chunksize=1))
    # Deterministic content identity is separate from CPU placement and elapsed
    # analysis time, so serial/parallel reports can be checked byte-for-byte.
    content = dict(schema=1, scope='Completed evaluation execution analysis; no GPU or new grading',
                   assessments=rows, interval_note='Generation is inside request, inside case; do not add nested times',
                   weights_updated=False, promoted=False)
    return dict(**content, report_id=digest(content), analysis=dict(workers=workers,
        wall_seconds=time.monotonic()-started, method='Independent CPU processes; deterministic merge by assessment label'))
