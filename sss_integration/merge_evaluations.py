"""Merge completed evaluation shards with checked coverage and response evidence."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from sss.records import digest
from sss.foundations import Exercise
from sss.studies.evaluation_shards import plan, indices, binding, merge
from sss.studies import evaluation_shards


def _read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def merge_directories(cases, evaluation_id, directories, output, *, coordinator_wall_seconds):
    """CPU-only publication. The caller measures worker-group wall time."""
    if (type(coordinator_wall_seconds) not in (int, float)
            or not math.isfinite(coordinator_wall_seconds) or coordinator_wall_seconds < 0):
        raise ValueError('Measured nonnegative coordinator wall time required')
    data, cases_sha = _read(cases)
    source_pins={str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 str(Path(evaluation_shards.__file__).resolve()): hashlib.sha256(Path(evaluation_shards.__file__).read_bytes()).hexdigest()}
    actual = digest({k: v for k, v in data.items() if k != 'evaluation_id'})
    if data.get('evaluation_id') != evaluation_id or actual != evaluation_id:
        raise ValueError('Pinned frozen evaluation changed')
    contracts = []
    for row in data['cases']:
        exercise = Exercise(**row['exercise'])
        if exercise.identity != row['exercise_id']:
            raise ValueError('Frozen exercise identity changed')
        contracts.append(dict(id=exercise.identity, skill_id=exercise.skill_id, gate=exercise.gate))
    partition = plan(evaluation_id, contracts, len(directories))
    roots = [Path(value).resolve(strict=True) for value in directories]
    if len(set(roots)) != len(roots):
        raise ValueError('Duplicate shard directory')
    documents = []; sources = []; allocated = []; elapsed = []; gpu_uuids = set()
    for root in roots:
        result, result_sha = _read(root/'result.json')
        intent, intent_sha = _read(root/'intent.json')
        settlement, settlement_sha = _read(root/'settlement.json')
        if (settlement.get('status') != 'SHARD_COMPLETE' or settlement.get('weights_updated') is not False
                or intent.get('shard') != result.get('shard') or intent.get('cases_sha256') != cases_sha
                or intent.get('partition') != partition
                or intent.get('assigned_indices') != indices(partition, result.get('shard',{}).get('index'))
                or intent.get('weights_updated') is not False or intent.get('case_count') != result.get('cases')
                or any(intent.get(k) != result.get(k) for k in ('evaluation_id', 'model_sha256', 'runtime_id'))
                or digest(intent.get('runtime')) != result.get('runtime_id')
                or intent.get('runtime',{}).get('case_partition_implementation_sha256') != source_pins[str(Path(evaluation_shards.__file__).resolve())]):
            raise ValueError('Shard intent, settlement or runtime identity differs')
        for key, target in [('allocated_seconds', allocated), ('execution_wall_seconds', elapsed)]:
            value = settlement.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('Finite shard settlement times required')
            target.append(value)
        documents.append(result); gpu_uuids.add(intent['gpu_uuid'])
        sources.append(dict(root=root, result_sha256=result_sha, intent_sha256=intent_sha,
                            settlement_sha256=settlement_sha, result=result))
    combined = merge(partition, documents)
    if coordinator_wall_seconds + .01 < max(elapsed):
        raise ValueError('Coordinator wall interval cannot be shorter than a contained worker')
    output = Path(output).resolve()
    if any(output == source or output.is_relative_to(source) for source in roots):
        raise ValueError('Merge output must be separate from worker evidence')
    output.parent.resolve(strict=True)
    output.mkdir(mode=0o700, exist_ok=False)
    _sync_directory(output.parent)
    try:
        _write(output/'intent.json', dict(schema=1, evaluation_id=evaluation_id, cases_sha256=cases_sha,
            model_sha256=combined['model_sha256'], runtime_id=combined['runtime_id'], partition=partition,
            case_count=combined['cases'], source_pins=source_pins, weights_updated=False, scope='CPU-only checked shard merge'))
        evidence = []
        for source in sources:
            root, result = source['root'], source['result']
            index = result['shard']['index']
            assigned = indices(partition, index)
            filenames = {f'{position:04d}-private.json' for position in assigned}
            if {f.name for f in root.glob('*-private.json')} != filenames:
                raise ValueError('Shard private response file coverage differs')
            by_id = {row['id']: row for row in result['outcomes']}
            raw_calls=raw_tokens=0
            for position in assigned:
                name = f'{position:04d}-private.json'; raw = (root/name).read_bytes(); row = json.loads(raw)
                expected = by_id[partition['case_ids'][position]]
                completion = row.get('completion', {})
                if (type(row.get('index')) is not int or row['index'] != position
                        or any(type(row.get(k)) is not bool for k in ('passed', 'finished'))
                        or type(completion) is not dict or type(completion.get('text')) is not str
                        or type(completion.get('sampled_token_ids')) is not list
                        or not completion['sampled_token_ids']
                        or any(type(token) is not int or token < 0 for token in completion['sampled_token_ids'])
                        or completion.get('stop_reason') not in ('eos', 'length')
                        or any(type(completion.get(k)) is not int or completion[k]<0 for k in ('model_calls','prefill_tokens'))
                        or row.get('finished') != (completion['stop_reason'] == 'eos')
                        or any(row.get(k) != expected[k] for k in expected)
                        or any(row.get(k) != result[k] for k in ('model_sha256', 'runtime_id', 'evaluation_id'))):
                    raise ValueError('Raw shard response differs from the frozen outcome')
                raw_calls+=completion['model_calls'];raw_tokens+=completion['prefill_tokens']
                with (output/name).open('xb') as stream:
                    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                evidence.append(dict(index=position, sha256=hashlib.sha256(raw).hexdigest(), shard_index=index))
            if (raw_calls+result.get('setup_model_calls',0)!=result['model_calls']
                    or raw_tokens+result.get('setup_prefill_tokens',0)!=result['prefill_tokens']):
                raise ValueError('Shard setup and case work totals differ')
            for name, field in [('result.json', 'result_sha256'), ('intent.json', 'intent_sha256'),
                                ('settlement.json', 'settlement_sha256')]:
                if _read(root/name)[1] != source[field]:
                    raise ValueError('Shard evidence changed during merge')
        if _read(cases)[1] != cases_sha:
            raise ValueError('Frozen cases changed during merge')
        if any(hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected for path,expected in source_pins.items()):
            raise ValueError('Merge implementation changed during execution')
        _write(output/'source-evidence.json', dict(schema=1, case_files=sorted(evidence, key=lambda row: row['index']),
            shards=[dict(index=row['result']['shard']['index'], **{k: row[k] for k in
                ('result_sha256', 'intent_sha256', 'settlement_sha256')}) for row in sources]))
        _write(output/'settlement.json', dict(status='COMPLETE', allocated_seconds=sum(allocated),
            execution_wall_seconds=coordinator_wall_seconds, physical_gpus=len(gpu_uuids),
            completed_cases=combined['cases'], model_calls=combined['model_calls'], prefill_tokens=combined['prefill_tokens'],
            weights_updated=False, wall_scope='Caller-measured worker group interval; CPU merge is a subsequent phase',
            allocation_scope='Sum of the owned worker GPU allocation intervals'))
        # COMPLETE is published only after exact coverage and all private files.
        _sync_directory(output)
        _write(output/'result.json', combined)
        _sync_directory(output)
        return combined
    except BaseException as error:
        _write(output/'merge-failure.json', dict(status='FAILED', type=type(error).__name__, message=str(error),
                                               weights_updated=False, automatic_retry=False))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--evaluation-id', required=True)
    parser.add_argument('--shard', type=Path, action='append', required=True)
    parser.add_argument('--coordinator-wall-seconds', type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = merge_directories(args.cases, args.evaluation_id, args.shard, args.output,
                               coordinator_wall_seconds=args.coordinator_wall_seconds)
    print(json.dumps({k: result[k] for k in ('status', 'cases', 'passed', 'finished', 'runtime_id')}))


if __name__ == '__main__': main()
