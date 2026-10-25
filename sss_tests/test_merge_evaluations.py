import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from sss.records import digest
from sss.foundations import Exercise
from sss.studies.evaluation_shards import plan, indices, binding, groups
from sss_integration.merge_evaluations import merge_directories


def write(path, value): path.write_text(json.dumps(value))


def fixture(base):
    cases = []
    for index in range(4):
        e = Exercise(skill_id='math.add', kind='expression', split='development', family_id='fixture',
                     trial_id=str(index), gate='independent', payload={'expression': ['add', index, 1]}, prompt='fixture')
        cases.append(dict(exercise=asdict(e), exercise_id=e.identity, prefix_tokens=[3, 4]))
    data = dict(schema=1, cases=cases); data['evaluation_id'] = digest(data)
    path = base/'cases.json'; write(path, data)
    import hashlib
    cases_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    partition = plan(data['evaluation_id'], [dict(id=r['exercise_id'], skill_id='math.add', gate='independent') for r in cases], 2)
    from sss.studies import evaluation_shards
    runtime = dict(scope='synthetic CPU fixture',
        case_partition_implementation_sha256=hashlib.sha256(Path(evaluation_shards.__file__).read_bytes()).hexdigest())
    runtime_id = digest(runtime)
    roots = []
    for index in range(2):
        root = base/('shard-'+str(index)); root.mkdir(); roots.append(root)
        rows = []
        for position in indices(partition, index):
            outcome = dict(id=cases[position]['exercise_id'], skill_id='math.add', gate='independent', passed=True, finished=True)
            rows.append(outcome)
            write(root/f'{position:04d}-private.json', dict(outcome, index=position, model_sha256='b'*64,
                runtime_id=runtime_id, evaluation_id=data['evaluation_id'], seconds=1.,
                completion=dict(text='fixture', sampled_token_ids=[7, 1], stop_reason='eos', stop_token_id=1,
                                model_calls=2, prefill_tokens=4)))
        summary = dict(schema=1, status='SHARD_COMPLETE', shard=binding(partition, index), outcomes=rows, groups=groups(rows),
            cases=2, passed=2, finished=2, model_calls=4, prefill_tokens=8, model_sha256='b'*64,
            runtime_id=runtime_id, evaluation_id=data['evaluation_id'], weights_updated=False, promoted=False)
        write(root/'result.json', summary)
        write(root/'intent.json', dict(shard=summary['shard'], cases_sha256=cases_sha, case_count=2,
            partition=partition, assigned_indices=indices(partition,index),
            model_sha256='b'*64, runtime_id=runtime_id, evaluation_id=data['evaluation_id'],
            weights_updated=False, gpu_uuid='GPU-fixture-'+str(index), runtime=runtime))
        write(root/'settlement.json', dict(status='SHARD_COMPLETE', weights_updated=False,
            allocated_seconds=1., execution_wall_seconds=2.))
    return path, data['evaluation_id'], roots


class MergeDirectoryTests(unittest.TestCase):
    def test_real_files_merge_global_indices_without_changing_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); cases, identity, roots = fixture(base)
            before = {str(f): f.read_bytes() for root in roots for f in root.iterdir()}
            result = merge_directories(cases, identity, roots, base/'merged', coordinator_wall_seconds=3.)
            self.assertEqual(result['cases'], 4)
            self.assertEqual(len(list((base/'merged').glob('*-private.json'))), 4)
            self.assertEqual(before, {str(f): f.read_bytes() for root in roots for f in root.iterdir()})
            settlement = json.loads((base/'merged/settlement.json').read_text())
            self.assertEqual(settlement['physical_gpus'], 2)
            self.assertEqual(settlement['allocated_seconds'], 2.)

    def test_bad_or_missing_raw_record_never_publishes_complete_marker(self):
        for defect in ['missing', 'boolean', 'tokens', 'identity']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                base = Path(temp); cases, identity, roots = fixture(base); raw = roots[1]/'0001-private.json'
                if defect == 'missing': raw.unlink()
                else:
                    value = json.loads(raw.read_text())
                    if defect == 'boolean': value['passed'] = 1
                    if defect == 'tokens': value['completion']['sampled_token_ids'] = []
                    if defect == 'identity': value['model_sha256'] = 'd'*64
                    write(raw, value)
                with self.assertRaises(ValueError):
                    merge_directories(cases, identity, roots, base/'merged', coordinator_wall_seconds=3.)
                self.assertFalse((base/'merged/result.json').exists())

    def test_impossible_wall_interval_or_tampered_intent_is_rejected(self):
        for defect in ['time', 'intent']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                base = Path(temp); cases, identity, roots = fixture(base)
                if defect == 'intent':
                    p = roots[0]/'intent.json'; value = json.loads(p.read_text()); value['runtime']['scope'] = 'changed'; write(p, value)
                with self.assertRaises(ValueError):
                    merge_directories(cases, identity, roots, base/'merged', coordinator_wall_seconds=1. if defect == 'time' else 3.)

    def test_output_alias_cannot_write_into_a_source_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); cases, identity, roots = fixture(base)
            alias = base/'alias'; alias.symlink_to(roots[0], target_is_directory=True)
            with self.assertRaises(ValueError):
                merge_directories(cases, identity, roots, alias/'merged', coordinator_wall_seconds=3.)
            self.assertFalse((roots[0]/'merged').exists())


if __name__ == '__main__': unittest.main()
