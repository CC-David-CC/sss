"""Placement forecasts from observed memory; no GPU authority or execution.

An observed peak is not an upper bound. Only matching inference workloads may
reuse this forecast; PCC retains its actual admission, leases and allocations.
"""
import copy
import re
from ..records import digest

_KEYS={'phase','runtime_id','evaluation_id','layout_id','device_class','format',
       'context_tokens','batch_tokens','maximum_tokens'}
_HASH=re.compile(r'[a-f0-9]{64}\Z')
_BOOT=re.compile(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\Z')


def _descriptor(value):
    if type(value) is not dict or set(value)!=_KEYS or value['phase']!='cow-inference':
        raise ValueError('Exact COW inference workload descriptor required')
    for key in ('runtime_id','evaluation_id','layout_id'):
        if type(value[key]) is not str or not _HASH.fullmatch(value[key]):
            raise ValueError('Pinned runtime, evaluation and model layout required')
    for key in ('context_tokens','batch_tokens','maximum_tokens'):
        if type(value[key]) is not int or not 1<=value[key]<=1<<20:
            raise ValueError('Bounded actual context, batch and output limits required')
    for key in ('device_class','format'):
        if type(value[key]) is not str or not 1<=len(value[key])<=128:
            raise ValueError('Explicit device class and stored precision required')
    return copy.deepcopy(value)


def observed_memory_forecast(descriptor, process, samples, *, evidence_sha256):
    descriptor=_descriptor(descriptor)
    if (type(process) is not dict or set(process)!={'pid','start_ticks','boot_id'}
            or any(type(process[k]) is not int or process[k]<1 for k in ('pid','start_ticks'))
            or type(process['boot_id']) is not str or not _BOOT.fullmatch(process['boot_id'])):
        raise ValueError('Original process PID, start ticks and boot identity required')
    if type(evidence_sha256) is not str or not _HASH.fullmatch(evidence_sha256):
        raise ValueError('Pinned original observation evidence required')
    if type(samples) is not list or not 1<=len(samples)<=1000000:
        raise ValueError('Original nonempty bounded memory samples required')
    values=[]
    for sample in samples:
        if (type(sample) is not dict or set(sample)!={'process','used_bytes'}
                or type(sample['process']) is not dict
                or any(type(sample['process'].get(k)) is not int for k in ('pid','start_ticks'))
                or sample['process']!=process or type(sample['used_bytes']) is not int
                or sample['used_bytes']<0):
            raise ValueError('Memory sample belongs to another process or is invalid')
        values.append(sample['used_bytes'])
    peak=max(values)
    if peak==0:raise ValueError('No positive model memory observation exists')
    result=dict(schema=1,kind='sss.observed-memory-forecast.v1',status='FORECAST_ONLY',
        descriptor=descriptor,process=copy.deepcopy(process),evidence_sha256=evidence_sha256,
        sample_count=len(values),peak_observed_bytes=peak,minimum_observed_bytes=min(values),
        guaranteed_upper_bound=False,native_admission_required=True,work_authorized=False)
    result['forecast_id']=digest(result)
    return result


def placement_candidates(forecast, descriptor, inventory):
    """Prefer idle compute and smaller fitting windows; never exclude busy GPUs.

    A returned candidate is permission to consider a placement, not an admission
    receipt. The caller must still acquire PCC's existing lease and recheck it.
    """
    wanted=_descriptor(descriptor)
    if (type(forecast) is not dict or type(forecast.get('schema')) is not int or forecast['schema']!=1
            or forecast.get('kind')!='sss.observed-memory-forecast.v1'
            or forecast.get('status')!='FORECAST_ONLY' or forecast.get('descriptor')!=wanted
            or forecast.get('guaranteed_upper_bound') is not False
            or forecast.get('native_admission_required') is not True
            or forecast.get('work_authorized') is not False
            or forecast.get('forecast_id')!=digest({k:v for k,v in forecast.items() if k!='forecast_id'})
            or type(forecast.get('peak_observed_bytes')) is not int or forecast['peak_observed_bytes']<=0):
        raise ValueError('Original forecast or requested workload differs')
    if type(inventory) is not list or len(inventory)>256:
        raise ValueError('Bounded explicit current inventory required')
    seen=set();eligible=[]
    for row in inventory:
        if (type(row) is not dict or set(row)!={'gpu_uuid','device_class','free_bytes','utilization_percent'}
                or type(row['gpu_uuid']) is not str or not row['gpu_uuid'].startswith('GPU-')
                or row['gpu_uuid'] in seen or type(row['device_class']) is not str
                or type(row['free_bytes']) is not int or row['free_bytes']<0
                or type(row['utilization_percent']) is not int or not 0<=row['utilization_percent']<=100):
            raise ValueError('Malformed, duplicate or stale inventory row')
        seen.add(row['gpu_uuid'])
        if row['device_class']==wanted['device_class'] and row['free_bytes']>=forecast['peak_observed_bytes']:
            eligible.append(copy.deepcopy(row))
    return sorted(eligible,key=lambda r:(r['utilization_percent'],r['free_bytes'],r['gpu_uuid']))
