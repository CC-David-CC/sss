"""Validate aggregate measured learning curves without a model or plotting stack."""
import math,re
from .records import digest

def measured_curves(protocol,document):
    identity=protocol.get('protocol_id')
    if identity!=digest({k:v for k,v in protocol.items() if k!='protocol_id'}) or document.get('protocol_id')!=identity:
        raise ValueError('Curve protocol identity differs')
    cases=protocol['cases_per_evaluation'];batch=protocol['batch_size']
    reference=document['reference_passed'];finished=document['reference_finished']
    if any(type(v) is not int or not 0<=v<=cases for v in [reference,finished]):
        raise ValueError('Explicit measured reference counts required')
    result={arm['id']:[] for arm in protocol['arms']};seen=set()
    for point in document['points']:
        name=point['arm'];update=point['update']
        if name not in result or type(update) is not int or update not in protocol['checkpoint_updates'] or (name,update) in seen:
            raise ValueError('Unknown or duplicate measured curve point')
        seen.add((name,update))
        if type(point['presentations']) is not int or point['presentations']!=update*batch:
            raise ValueError('Update and practice exposure differ')
        gains=point['original_answers_gained'];losses=point['original_answers_lost']
        if type(gains) is not int or not 0<=gains<=cases-reference or type(losses) is not int or not 0<=losses<=reference:
            raise ValueError('Original-answer gain/loss counts outside bounds')
        if type(point['passed']) is not int or point['passed']!=reference+gains-losses:
            raise ValueError('Net score does not reconcile original answers gained/lost')
        if type(point['finished']) is not int or not 0<=point['finished']<=cases:
            raise ValueError('Explicit response completion count required')
        if type(point['model_sha256']) is not str or re.fullmatch('[a-f0-9]{64}',point['model_sha256']) is None:
            raise ValueError('Measured model identity required')
        if update==0 and (gains or losses or point['finished']!=finished or point['model_sha256']!=protocol['reference']['unchanged_original_F32_sha256']):
            raise ValueError('Update zero must be the actual unchanged reference')
        for value in point.get('native_cumulative_timing',{}).values():
            if type(value) not in (int,float) or not math.isfinite(value) or value<0:
                raise ValueError('Finite nonnegative measured native timing required')
        result[name].append(point)
    for name,points in result.items():
        points.sort(key=lambda p:p['update'])
        if [p['update'] for p in points]!=list(range(len(points))):
            raise ValueError('Missing measured checkpoints cannot be interpolated')
        if document.get('status')=='COMPLETE' and [p['update'] for p in points]!=protocol['checkpoint_updates']:
            raise ValueError('Complete claim requires every declared checkpoint in every arm')
    return result
