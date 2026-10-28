"""Deterministic independent-case partitions and checked complete-result merges.

This module assigns no GPU, starts no worker and grants no tool authority.
An incomplete shard can never become a complete evaluation by itself.
"""
import re
from ..records import digest
from ..paired import compare_frozen_evaluations, measured_candidate_binding, POLICY

GATES = ('independent', 'composition', 'transfer_recovery')


def _hash(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def plan(evaluation_id, cases, count):
    if (not _hash(evaluation_id) or type(cases) is not list or not cases
            or any(type(row) is not dict or set(row) != {'id', 'skill_id', 'gate'}
                or not _hash(row.get('id')) or type(row.get('skill_id')) is not str
                or not row['skill_id'] or row.get('gate') not in GATES for row in cases)
            or len({row['id'] for row in cases}) != len(cases)
            or type(count) is not int or not 1 <= count <= min(64, len(cases))):
        raise ValueError('Pinned unique cases and a bounded nonempty shard count required')
    value = dict(schema=1, evaluation_id=evaluation_id, case_contracts=[dict(row) for row in cases],
                 case_ids=[row['id'] for row in cases], count=count,
                 assignments=[list(range(index, len(cases), count)) for index in range(count)])
    return dict(**value, plan_id=digest(value))


def indices(partition, index):
    expected = plan(partition['evaluation_id'], partition['case_contracts'], partition['count'])
    if partition != expected or type(index) is not int or not 0 <= index < expected['count']:
        raise ValueError('Pinned shard plan and selected shard index required')
    return list(expected['assignments'][index])


def binding(partition, index):
    indices(partition, index)
    return dict(plan_id=partition['plan_id'], index=index, count=partition['count'],
                total_cases=len(partition['case_ids']))


def groups(outcomes):
    result = {}
    for row in outcomes:
        key = row['skill_id'], row['gate']
        entry = result.setdefault(key, dict(skill_id=key[0], gate=key[1], cases=0, passed=0, finished=0))
        entry['cases'] += 1; entry['passed'] += row['passed']; entry['finished'] += row['finished']
    return [result[key] for key in sorted(result, key=lambda key: (key[0], GATES.index(key[1])))]


def merge(partition, documents):
    """Require every assigned outcome exactly once, with matching model/runtime."""
    indices(partition, 0)
    if (partition['count'] < 2 or type(documents) is not list
            or len(documents) != partition['count']):
        raise ValueError('All independent shard results required; no partial promotion')
    observed = {}; by_case = {}; model = runtime = candidate = None; calls = work = setup_calls = setup_work = 0
    contracts = {row['id']: row for row in partition['case_contracts']}
    for doc in documents:
        shard = doc.get('shard', {})
        index = shard.get('index')
        assigned = indices(partition, index)
        if (doc.get('status') != 'SHARD_COMPLETE' or shard != binding(partition, index)
                or index in observed or doc.get('evaluation_id') != partition['evaluation_id']
                or doc.get('weights_updated') is not False or doc.get('promoted') is not False
                or not _hash(doc.get('model_sha256')) or not _hash(doc.get('runtime_id'))):
            raise ValueError('Complete unique shards with pinned immutable identities required')
        composite=measured_candidate_binding(doc)
        if model is None: model, runtime, candidate = doc['model_sha256'], doc['runtime_id'], composite
        if doc['model_sha256'] != model or doc['runtime_id'] != runtime:
            raise ValueError('Shard model or numerical runtime differs')
        if composite!=candidate:
            raise ValueError('Shard composite candidate differs; equal base weights do not identify a LoRA hat')
        rows = doc.get('outcomes')
        if type(rows) is not list or len(rows) != len(assigned):
            raise ValueError('Shard outcome coverage differs')
        assigned_ids = {partition['case_ids'][position] for position in assigned}
        local = set()
        for row in rows:
            if (type(row) is not dict or row.get('id') not in assigned_ids or row['id'] in local
                    or row['id'] in by_case or type(row.get('skill_id')) is not str or not row['skill_id']
                    or row.get('gate') not in GATES
                    or any(row.get(k) != contracts[row['id']][k] for k in ('skill_id', 'gate'))
                    or any(type(row.get(k)) is not bool for k in ('passed', 'finished'))):
                raise ValueError('Foreign, duplicate or malformed shard outcome')
            local.add(row['id']); by_case[row['id']] = dict(row)
        if local != assigned_ids:
            raise ValueError('Missing assigned outcomes')
        for key in ('cases', 'passed', 'finished', 'model_calls', 'prefill_tokens'):
            if type(doc.get(key)) is not int or doc[key] < 0:
                raise ValueError('Explicit nonnegative integer aggregates required')
        if (doc['cases'] != len(rows) or any(doc[k] != sum(row[k] for row in rows) for k in ('passed', 'finished'))
                or doc.get('groups') != groups(rows)):
            raise ValueError('Shard aggregate or per-skill counts differ')
        calls += doc['model_calls']; work += doc['prefill_tokens']; observed[index] = digest(doc)
        for key in ('setup_model_calls','setup_prefill_tokens'):
            if type(doc.get(key,0)) is not int or not 0<=doc.get(key,0)<=doc['model_calls' if key=='setup_model_calls' else 'prefill_tokens']:
                raise ValueError('Invalid shared-prefix setup work')
        setup_calls+=doc.get('setup_model_calls',0);setup_work+=doc.get('setup_prefill_tokens',0)
    if set(observed) != set(range(partition['count'])) or set(by_case) != set(partition['case_ids']):
        raise ValueError('Full frozen evaluation coverage required')
    outcomes = [by_case[key] for key in partition['case_ids']]
    result = dict(schema=1, status='COMPLETE', scope='Checked merge of independent frozen evaluation cases; no model promotion',
        evaluation_id=partition['evaluation_id'], model_sha256=model, runtime_id=runtime,
        cases=len(outcomes), passed=sum(row['passed'] for row in outcomes),
        finished=sum(row['finished'] for row in outcomes), groups=groups(outcomes),
        model_calls=calls, prefill_tokens=work, outcomes=outcomes, weights_updated=False, promoted=False,
        setup_model_calls=setup_calls,setup_prefill_tokens=setup_work,**candidate,
        merged_shards=dict(plan_id=partition['plan_id'], count=partition['count'],
                           result_ids=[observed[index] for index in range(partition['count'])]))
    compare_frozen_evaluations(result, result, POLICY)
    return result
