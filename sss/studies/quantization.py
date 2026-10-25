"""Measured storage-precision comparisons, independent of an inference engine.

Input assessments contain actual frozen case outcomes. Missing formats stay
unmeasured. A net score cannot hide individual answers lost to quantization.
"""
import re
from ..paired import compare_frozen_evaluations, POLICY
from ..records import digest


def quantization_report(assessments, formats):
    """Compare each precision with its family's F32 and its untrained peer.

    Assessments are {family, format, bytes, result}; result is the existing
    complete frozen-evaluation document, including Boolean case outcomes.
    This reports observations only and neither changes acceptance nor promotes.
    """
    if (type(formats) is not list or not formats or 'F32' not in formats
            or any(type(f) is not str or re.fullmatch('[A-Za-z0-9_]+', f) is None for f in formats)
            or len(set(formats)) != len(formats)):
        raise ValueError('Unique explicit formats including F32 required')
    measured = {}
    for row in assessments:
        key = row['family'], row['format']
        if key[0] not in ('original', 'trained') or key[1] not in formats or key in measured:
            raise ValueError('Unknown or duplicate measured variant')
        if type(row['bytes']) is not int or row['bytes'] <= 0:
            raise ValueError('Measured positive model size required')
        # Existing comparison validates completeness, hashes, exact case identity,
        # skill/gate identity, Boolean outcomes, counts and immutable evaluation.
        compare_frozen_evaluations(row['result'], row['result'], POLICY)
        measured[key] = row
    if not measured:
        raise ValueError('At least one measured assessment required')
    anchor = next(iter(measured.values()))['result']
    for row in measured.values():
        compare_frozen_evaluations(anchor, row['result'], POLICY)

    def paired(left, right):
        value = compare_frozen_evaluations(left, right, POLICY)
        return {k: value[k] for k in ('baseline_model_sha256', 'candidate_model_sha256',
                'baseline_evidence_id', 'candidate_evidence_id', 'answer_gains',
                'answer_losses', 'completion_gains', 'completion_losses', 'groups')}

    rows = []
    for fmt in formats:
        for family in ('original', 'trained'):
            data = measured.get((family, fmt))
            if data is None:
                rows.append(dict(family=family, format=fmt, status='UNMEASURED'))
                continue
            result = data['result']
            row = dict(family=family, format=fmt, status='COMPLETE', bytes=data['bytes'],
                       model_sha256=result['model_sha256'], evidence_id=digest(result),
                       cases=result['cases'], passed=result['passed'], finished=result['finished'])
            own = measured.get((family, 'F32'))
            if own is not None:
                row['versus_own_F32'] = paired(own['result'], result)
            original = measured.get(('original', fmt))
            if family == 'trained' and original is not None:
                row['versus_original_same_format'] = paired(original['result'], result)
            rows.append(row)
    report = dict(schema=1, status='COMPLETE' if len(measured) == 2*len(formats) else 'IN_PROGRESS',
                  scope='Frozen development behavior by stored precision; not broad capability or promotion',
                  evaluation_id=anchor['evaluation_id'], runtime_id=anchor['runtime_id'],
                  declared_formats=formats, measured_variants=len(measured), expected_variants=2*len(formats),
                  rows=rows, weights_updated=False, weights_published=False, promoted=False)
    report['report_id'] = digest(report)
    return report
