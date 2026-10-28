"""Reduce complete frozen direct-hat results to shareable learning evidence.

Input: baseline/{result,settlement}.json and update-NNN/{result,settlement}.json,
with optional original mechanics and execution-control receipts. No question,
answer, raw outcome, artifact path, model or optimizer bytes are exported.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sss import paired


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def report(directory,*,presentations_per_update=27):
    if type(presentations_per_update) is not int or presentations_per_update<1:
        raise ValueError('Explicit positive practice presentations per update required')
    directory=Path(directory)
    baseline=load(directory/'baseline/result.json')
    if baseline.get('candidate_adapters')!=[]:
        raise ValueError('Explicit base-only reference required')
    if load(directory/'baseline/settlement.json')['status']!='COMPLETE':
        raise ValueError('Settled complete baseline required')
    points=[];previous=baseline;previous_update=0;datasets=set()
    for folder in sorted(directory.glob('update-*')):
        update=int(folder.name.split('-')[1]);candidate=load(folder/'result.json')
        settlement=load(folder/'settlement.json')
        if update<=0 or settlement['status']!='COMPLETE' or len(candidate.get('candidate_adapters',[]))!=1:
            raise ValueError('Complete settled direct-hat assessment required')
        assessment=paired.compare_frozen_evaluations(baseline,candidate,paired.POLICY)
        point=dict(update=update,presentations=update*presentations_per_update,
            passed=candidate['passed'],finished=candidate['finished'],
            **{k:assessment[k] for k in ('answer_gains','answer_losses','completion_gains','completion_losses','groups',
               'assessment_id','candidate_evidence_id','baseline_evidence_id','candidate_model_contract_id','candidate_adapters')},
            frozen_development_gate_status=assessment['status'],promoted=False,
            evaluation_wall_seconds=settlement['execution_wall_seconds'],
            allocated_evaluation_gpu_seconds=settlement['allocated_seconds'],
            consumed_forward_tokens=candidate['prefill_tokens'],native_forward_calls=candidate['model_calls'],
            result_sha256=sha(folder/'result.json'))
        if update==previous_update+1:
            delta=paired.compare_frozen_evaluations(previous,candidate,paired.POLICY)
            point['previous_update_delta']=dict(previous_update=previous_update,
                **{k:delta[k] for k in ('answer_gains','answer_losses','completion_gains','completion_losses','assessment_id')})
        mechanics=folder/'mechanics-private.json'
        if mechanics.exists():
            owner=load(mechanics);version=owner['candidate'];receipt=version['receipt']
            step=receipt['steps'][0];gradients=step['gradients']
            if (version['mode']!='lora' or version['optimizer_completed_steps']!=update
                    or receipt['example_cursor']!=point['presentations']
                    or version['candidate_sha256']!=candidate['candidate_adapters'][0]['sha256']
                    or any(not math.isfinite(g['l2']) for g in gradients)):
                raise ValueError('Native mechanics do not match this measured adapter and practice cursor')
            datasets.add(receipt['optimizer_checkpoint']['dataset_sha256'])
            point['mechanics']=dict(native_optimizer=receipt['optimizer'],finite_gradient_groups=len(gradients),
                nonzero_gradient_groups=sum(g['l2']>0 for g in gradients),batch_loss_before=step['before'],batch_loss_after=step['after'],
                owner_reload_loss_error=owner['reload_loss_error'],
                allocated_native_update_and_reload_seconds=owner['allocated_native_seconds'],
                optimizer_completed_steps=version['optimizer_completed_steps'],evidence_sha256=sha(mechanics))
        points.append(point);previous=candidate;previous_update=update
    if not points or len(datasets)>1:
        raise ValueError('Nonempty comparable curve with one fixed practice stream required')
    value=dict(schema=1,status='PARTIAL_CURVE',scope='Repeated development observations of directly attached LoRA; no merged-deployment or sealed qualification',
        evaluation_id=baseline['evaluation_id'],runtime_id=baseline['runtime_id'],cases=baseline['cases'],
        baseline=dict(passed=baseline['passed'],finished=baseline['finished'],base_model_sha256=baseline['model_sha256'],
            candidate_model_contract_id=baseline['candidate_model_contract_id'],consumed_forward_tokens=baseline['prefill_tokens']),
        points=points,pairing_implementation_sha256=sha(Path(paired.__file__)),
        report_implementation_sha256=sha(Path(__file__)),presentations_per_update=presentations_per_update,
        practice_dataset_sha256=next(iter(datasets)) if datasets else None,
        promoted=False,weights_published=False,merge_gate_waived=False,
        retention='Owner-managed; this report neither deletes nor promotes candidates',
        limitations=['Repeated development data, not sealed acceptance','Shared-GPU wall times include contention and host work',
                     'Different predeclared settings are not a universal optimizer ranking','Original failed merged-weight gate is retained'])
    for filename,key in [('baseline-controls.json','baseline_controls'),('trained-bridge.json','trained_runtime_bridge'),('input-overlap.json','input_overlap')]:
        path=directory/filename
        if path.exists():
            record=load(path)
            if record['status']!='COMPLETE':raise ValueError('Incomplete optional control receipt')
            if key=='trained_runtime_bridge' and (record['new_runtime_id']!=baseline['runtime_id'] or record['cases']!=baseline['cases']):
                raise ValueError('Trained bridge covers another runtime or case count')
            if key=='input_overlap' and (record['evaluation_id']!=baseline['evaluation_id'] or record['development_cases']!=baseline['cases']):
                raise ValueError('Overlap audit covers another evaluation')
            value[key]=record
    if 'input_overlap' in value and datasets and value['input_overlap']['dataset_sha256'] not in datasets:
        raise ValueError('Overlap audit covers another practice stream')
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--presentations-per-update',type=int,default=27)
    a=parser.parse_args();value=report(a.input,presentations_per_update=a.presentations_per_update)
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=value['status'],points=len(value['points']),latest_update=value['points'][-1]['update'])))


if __name__=='__main__':main()
