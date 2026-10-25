"""Assess a proposed check against independently graded program variants.

Pure reduction of host observations. This grants no execution or lesson approval.
"""
import re
from ..records import digest


def assess(reference, mutants):
    if type(mutants) is not list or not mutants or len(mutants)>64:
        raise ValueError('One reference and a bounded nonempty mutant set required')
    rows=[reference,*mutants]
    fields={'schema','kind','case_id','program_sha256','command_sha256','checker_id',
            'checker_implementation_sha256','oracle_passed','oracle_evidence_sha256',
            'tool_disposition','tool_exit_code','namespace_retired','source_unchanged',
            'bw_ledger_sha256','bw_outcome_sha256','bw_interpreter_id','bw_implementation_sha256'}
    for row in rows:
        if (type(row) is not dict or set(row)!=fields or type(row['schema']) is not int or row['schema']!=1
                or row['kind']!='sss.bw-check-observation.v1' or type(row['case_id']) is not str
                or not row['case_id'] or len(row['case_id'])>128
                or any(type(row[key]) is not bool for key in ('oracle_passed','namespace_retired','source_unchanged'))
                or any(type(row[key]) is not str or re.fullmatch('[a-f0-9]{64}',row[key]) is None
                       for key in fields if key.endswith('_sha256') or key in ('checker_id','bw_interpreter_id'))
                or row['tool_disposition'] not in ('exited','timeout','output_limit','spawn_error')
                or (row['tool_exit_code'] is not None and type(row['tool_exit_code']) is not int)):
            raise ValueError('Complete bounded host check observations required')
    if (len({row['program_sha256'] for row in rows})!=len(rows)
            or any(any(row[key]!=reference[key] for key in ('case_id','command_sha256','checker_id',
                'checker_implementation_sha256','bw_implementation_sha256')) for row in mutants)):
        raise ValueError('Distinct programs with one case, command, checker and BW implementation required')
    def settled(row):
        return (row['tool_disposition']=='exited' and row['namespace_retired'] and row['source_unchanged']
                and type(row['tool_exit_code']) is int)
    available=all(settled(row) for row in rows)
    valid_variants=reference['oracle_passed'] and all(not row['oracle_passed'] for row in mutants)
    evaluated=[row for row in mutants if settled(row) and not row['oracle_passed']]
    detected=sum(row['tool_exit_code']!=0 for row in evaluated)
    status=('UNAVAILABLE' if not available else 'INVALID_VARIANT_SET' if not valid_variants
            else 'REFERENCE_CHECK_FAILED' if reference['tool_exit_code']!=0
            else 'DETECTS_DECLARED_MUTANTS' if detected==len(mutants) else 'MISSES_DECLARED_MUTANTS')
    value=dict(schema=1,kind='sss.check-sensitivity.v1',status=status,case_id=reference['case_id'],
        command_sha256=reference['command_sha256'],checker_id=reference['checker_id'],
        mutant_count=len(mutants),detected_mutants=detected,missed_mutants=len(evaluated)-detected,
        unavailable_mutants=sum(not settled(row) for row in mutants),
        invalid_mutants=sum(row['oracle_passed'] for row in mutants),
        reference_check_passed=settled(reference) and reference['tool_exit_code']==0,
        evidence_ids=[digest(row) for row in rows],
        scope='Only these independently graded program variants; no broad test-quality or model-skill qualification',
        training_approved=False,promoted=False)
    value['assessment_id']=digest(value)
    return value
