import copy
import unittest
from sss.records import digest
from sss.studies.evaluation_shards import plan, indices, binding, groups, merge


def fixture():
    contracts = [dict(id=digest(dict(case=i)), skill_id='math.add' if i < 4 else 'state.registers',
                      gate=('independent', 'composition', 'transfer_recovery')[(i // 2) % 3]) for i in range(7)]
    partition = plan('a'*64, contracts, 3)
    docs = []
    for index in range(3):
        rows = [dict(contracts[i], passed=i % 2 == 0, finished=True) for i in indices(partition, index)]
        docs.append(dict(schema=1, status='SHARD_COMPLETE', shard=binding(partition, index),
            evaluation_id='a'*64, model_sha256='b'*64, runtime_id='c'*64, weights_updated=False, promoted=False,
            cases=len(rows), passed=sum(r['passed'] for r in rows), finished=len(rows),
            model_calls=len(rows)*2, prefill_tokens=len(rows)*10, groups=groups(rows), outcomes=rows))
    return partition, docs


class EvaluationShardTests(unittest.TestCase):
    def test_partition_covers_original_indices_once_and_keeps_order(self):
        p, _ = fixture()
        self.assertEqual(p['assignments'], [[0, 3, 6], [1, 4], [2, 5]])
        self.assertEqual(sorted(i for shard in p['assignments'] for i in shard), list(range(7)))
        altered = copy.deepcopy(p); altered['assignments'][0].append(1)
        with self.assertRaises(ValueError): indices(altered, 0)
        for index in [-1, 3, True]:
            with self.assertRaises(ValueError): indices(p, index)

    def test_merge_is_order_independent_and_preserves_all_cases(self):
        p, docs = fixture()
        left = merge(p, docs); right = merge(p, list(reversed(docs)))
        self.assertEqual(left, right)
        self.assertEqual(left['status'], 'COMPLETE')
        self.assertEqual(left['cases'], 7)
        self.assertEqual(left['passed'], 4)
        self.assertEqual([r['id'] for r in left['outcomes']], p['case_ids'])
        self.assertEqual(left['model_calls'], 14)
        self.assertEqual([row['gate'] for row in docs[0]['groups'] if row['skill_id'] == 'math.add'],
                         ['independent', 'composition'])

    def test_missing_duplicate_failed_or_unsettled_shards_cannot_complete(self):
        for defect in ['missing', 'duplicate', 'failed', 'promoted', 'wrong-plan']:
            p, docs = fixture()
            if defect == 'missing': docs.pop()
            if defect == 'duplicate': docs[2] = copy.deepcopy(docs[0])
            if defect == 'failed': docs[1]['status'] = 'FAILED'
            if defect == 'promoted': docs[1]['promoted'] = True
            if defect == 'wrong-plan': docs[1]['shard']['plan_id'] = 'd'*64
            with self.subTest(defect=defect), self.assertRaises(ValueError): merge(p, docs)

    def test_foreign_cases_changed_skill_gate_or_candidate_are_rejected(self):
        for defect in ['case', 'skill', 'gate', 'model', 'runtime', 'evaluation']:
            p, docs = fixture(); target = docs[1]
            if defect == 'case': target['outcomes'][0]['id'] = docs[0]['outcomes'][0]['id']
            if defect == 'skill': target['outcomes'][0]['skill_id'] = 'other'
            if defect == 'gate': target['outcomes'][0]['gate'] = 'transfer_recovery'
            if defect in ('model', 'runtime', 'evaluation'): target[defect+'_id' if defect != 'model' else 'model_sha256'] = 'e'*64
            with self.subTest(defect=defect), self.assertRaises(ValueError): merge(p, docs)

    def test_false_aggregates_or_bool_counts_are_rejected(self):
        for defect in ['passed', 'groups', 'model_calls']:
            p, docs = fixture()
            if defect == 'passed': docs[0]['passed'] += 1
            if defect == 'groups': docs[0]['groups'][0]['cases'] += 1
            if defect == 'model_calls': docs[0]['model_calls'] = True
            with self.subTest(defect=defect), self.assertRaises(ValueError): merge(p, docs)


if __name__ == '__main__': unittest.main()
