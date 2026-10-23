from pathlib import Path
import argparse,json,math,time
from tools.pcc_lessons import LessonService,NativeRunner
from tools.pcc_native_training import sha256
from tools.strata_tokenizer import Tokenizer
from sss.records import digest
from sss.suites.legacy_ceiling import cases,check
from sss.adapters.native_oracle import receive,oracle_process,completion

def evaluate_records(root,label,rows,adapter,args,runner_config,tokenizer,phase,*,resuming=False):
    records=[];phase('fresh-native-evaluation',checkpoint=label,resuming=resuming)
    suffix='-resumed-oracle.log' if resuming else '-oracle.log'
    with oracle_process(args.oracle,runner_config['model'],args.evaluation_gpu_uuid,root/(label+suffix),adapter) as proc:
        for index,row in enumerate(rows):
            generated=completion(proc,tokenizer,row['prompt']);verdict=check(row,generated)
            records.append(dict(id=row['id'],split=row['split'],completion=generated,verdict=verdict))
            if index%16==15:phase('fresh-native-evaluation',checkpoint=label,cases=index+1,total=len(rows),resuming=resuming)
    (root/(label+'-private.json')).write_text(json.dumps(records,indent=2)+'\n')
    return records

def finish_study(root,manifest,results,runner_config,anchor_id,blind,evaluate,phase):
    unchanged=sha256(runner_config['model'])==manifest['base_sha256']
    if not unchanged:raise ValueError('Original model changed during quality study')
    eligible=[r for r in results if r['learning_pass']]
    selected=max(eligible,key=lambda r:(r['held_out_passed'],-r['examples'])) if eligible else results[-1]
    operation=selected['job_id']
    if operation!='quality-through-'+str(selected['examples']):raise ValueError('Checkpoint job identity differs')
    record=json.loads((root/'lesson-store/operations'/(operation+'.json')).read_bytes())
    if (record['state']!='complete' or record['request']['operation_id']!=operation
            or record['acceptance']['request_sha256']!=digest([record['path'],record['request']])):
        raise ValueError('Completed candidate lacks its original operation binding')
    candidate=record['candidate']
    if candidate['candidate_sha256']!=selected['candidate_sha256'] or sha256(candidate['candidate_path'])!=selected['candidate_sha256']:
        raise ValueError('Selected completed candidate identity differs')
    def final_records(label,adapter=None):
        path=root/(label+'-private.json')
        if not path.exists():return evaluate(label,adapter,selected=blind)
        records=json.loads(path.read_bytes());by_id={r['id']:r for r in records}
        if len(records)!=len(blind) or set(by_id)!={r['id'] for r in blind}:raise ValueError('Saved blind evaluation has different cases')
        for row in blind:
            value=by_id[row['id']]
            if value['split']!='blind_test' or value['verdict']!=check(row,value['completion']):raise ValueError('Saved blind verdict differs')
        return records
    original_blind=final_records('blind-original')
    candidate_blind=final_records('blind-selected',candidate['candidate_path'])
    baseline_blind_passed=sum(r['verdict']['passed'] for r in original_blind)
    blind_passed=sum(r['verdict']['passed'] for r in candidate_blind)
    blind_gate=blind_passed/len(blind)>=.9 and blind_passed>=baseline_blind_passed
    passed=bool(eligible) and blind_gate
    result=dict(status='BOUNDED_LEARNING_PASS' if passed else 'NO_QUALIFIED_GAIN',promoted=False,
        base_unchanged=unchanged,manifest=manifest,original_failure_id=anchor_id,checkpoints=results,
        selected_candidate_sha256=selected['candidate_sha256'],selected_examples=selected['examples'],
        blind=dict(baseline_passed=baseline_blind_passed,candidate_passed=blind_passed,total=len(blind),passed=blind_gate),
        qualification='generated return-expression benchmark only; not general BW task competence or sustained load')
    (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');phase('complete',status=result['status']);return 0 if passed else 3

def resume_final_evaluation(root,args,config,phase):
    """Read completed candidates and frozen data. Cannot submit training jobs."""
    if (root/'result.json').exists():raise ValueError('Study already completed; inspect its result instead of evaluating again')
    manifest=json.loads((root/'manifest.json').read_bytes());data=json.loads((root/'data-private.json').read_bytes())
    results=json.loads((root/'checkpoints.json').read_bytes());runner=config['runner']
    if ([r['examples'] for r in results]!=manifest['checkpoints']
            or runner['base_sha256']!=manifest['base_sha256'] or sha256(args.oracle)!=manifest['oracle_sha256']):
        raise ValueError('Resume requires every completed checkpoint and the original model/oracle identities')
    for key,field in [('training','training_sha256'),('evaluation','evaluation_sha256'),('blind','blind_sha256')]:
        if digest(data[key])!=manifest[field]:raise ValueError('Frozen study data differs')
    # Recompute every selection/preservation gate from preserved observations;
    # no new candidate can be selected by editing the aggregate checkpoint file.
    baseline=json.loads((root/'baseline-private.json').read_bytes())
    baseline_by_id={r['id']:r for r in baseline};held=[r for r in baseline if r['split']=='held_out']
    cases_by_id={r['id']:r for r in data['training']+data['evaluation']}
    def validate_observations(records):
        for value in records:
            case=cases_by_id[value['id']]
            if value['split']!=case['split'] or value['verdict']!=check(case,value['completion']):raise ValueError('Preserved semantic verdict differs')
    validate_observations(baseline)
    controls=[r for r in baseline if r['split']=='preservation' and r['verdict']['passed']]
    baseline_held=sum(r['verdict']['passed'] for r in held);required_gain=max(1,math.ceil((len(held)-baseline_held)*.25))
    anchor=json.loads((root/'training-order-private.json').read_bytes())[0]
    if baseline_by_id[anchor['id']]['verdict']['passed']:raise ValueError('Original failure is not a preserved failure')
    for row in results:
        observed=json.loads((root/('after-'+str(row['examples'])+'-private.json')).read_bytes());now={r['id']:r for r in observed}
        if set(now)!=set(baseline_by_id) or len(observed)!=len(baseline):raise ValueError('Saved checkpoint case identities differ')
        validate_observations(observed)
        held_pass=sum(now[r['id']]['verdict']['passed'] for r in held)
        gates=dict(repairs=now[anchor['id']]['verdict']['passed'],held_out=(held_pass/len(held)>=.9 and held_pass>=baseline_held+required_gain),
            preservation=(len(controls)>=8 and all(now[r['id']]['verdict']['passed'] for r in controls)))
        if row['gates']!=gates or row['learning_pass']!=all(gates.values()) or row['held_out_passed']!=held_pass:
            raise ValueError('Saved checkpoint gates differ from original observations')
    tokenizer=Tokenizer.from_gguf(runner['model'])
    def evaluate(label,adapter=None,selected=None):
        return evaluate_records(root,label,selected,adapter,args,runner,tokenizer,phase,resuming=True)
    return finish_study(root,manifest,results,runner,anchor['id'],data['blind'],evaluate,phase)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-config',type=Path,required=True)
    parser.add_argument('--oracle',type=Path,required=True)
    parser.add_argument('--evaluation-gpu-uuid',required=True)
    parser.add_argument('--workdir',type=Path,required=True)
    parser.add_argument('--resume-final-evaluation',action='store_true',help='Read a completed checkpoint series and evaluate only the remaining frozen blind cases; never train')
    parser.add_argument('--examples',type=int,default=1000)
    parser.add_argument('--checkpoints',default='1,32,256,1000')
    parser.add_argument('--rank',type=int,default=8);parser.add_argument('--batch-size',type=int,default=8)
    parser.add_argument('--learning-rate',type=float,default=.001)
    args=parser.parse_args(argv);root=args.workdir.absolute()
    if args.resume_final_evaluation:
        if not root.is_dir():parser.error('Resume requires the existing private study directory')
    else:root.mkdir(mode=0o700,parents=True,exist_ok=False)
    service=None
    def phase(name,**extra):
        value=dict(phase=name,time=time.time(),**extra);temporary=root/'phase.tmp';temporary.write_text(json.dumps(value)+'\n');temporary.replace(root/'phase.json')
        print(json.dumps(value),flush=True)
    try:
        config=json.loads(args.training_config.read_bytes());runner_config=config['runner']
        if args.resume_final_evaluation:return resume_final_evaluation(root,args,config,phase)
        checkpoints=[int(v) for v in args.checkpoints.split(',')]
        if not 1<=args.examples<=1000 or checkpoints!=sorted(set(checkpoints)) or checkpoints[-1]!=args.examples or checkpoints[0]<1:
            raise ValueError('Declare increasing checkpoints ending at the requested owned-example count')
        if args.batch_size<1:raise ValueError('Positive batch size required')
        phase('freeze-data-and-policy')
        tokenizer=Tokenizer.from_gguf(runner_config['model']);pool=cases(count=2000)
        training=[];evaluation=[r for r in pool if r['split'] in ('held_out','preservation')];blind=[r for r in pool if r['split']=='blind_test']
        for row in pool:
            if row['split']!='train':continue
            prefix=tokenizer.encode(row['prompt']);full=tokenizer.encode(row['prompt']+row['completion'])
            if (full[:len(prefix)]==prefix and 2<=len(full)-1<=config['max_tokens'] and len(training)<args.examples):training.append(row)
        if len(training)!=args.examples or not all(check(r,r['completion'])['passed'] for r in training+evaluation+blind):
            raise ValueError('Owned labels failed independent checks or admitted token bounds')
        probes=training[:64];observed=probes+evaluation
        policy=dict(repair='initial training-pool failure must pass',held_out_minimum_accuracy=.90,
            held_out_minimum_repaired_error_fraction=.25,preservation='all baseline-passing controls must remain passing',
            preservation_minimum_baseline_controls=8,
            candidate_selection='eligible checkpoints: most held-out passes, then fewer examples; otherwise final candidate for diagnosis only',
            blind_final='untouched until selection; at least90% and no fewer passes than original model',
            generation='greedy return-expression completion, newline stop,24-token cap; fresh full-prefill oracle',
            no_automatic_promotion=True)
        manifest=dict(policy=policy,training_sha256=digest(training),evaluation_sha256=digest(evaluation),blind_sha256=digest(blind),
            training_count=len(training),evaluation_count=len(evaluation),checkpoints=checkpoints,
            native_executable_sha256=sha256(runner_config['executable']),oracle_sha256=sha256(args.oracle),
            base_sha256=runner_config['base_sha256'],rank=args.rank,batch_size=args.batch_size,learning_rate=args.learning_rate)
        (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (root/'data-private.json').write_text(json.dumps(dict(training=training,evaluation=evaluation,blind=blind),indent=2)+'\n')
        def evaluate(label,adapter=None,selected=None):
            return evaluate_records(root,label,observed if selected is None else selected,adapter,args,runner_config,tokenizer,phase)
        baseline=evaluate('baseline')
        failures=[r for r in baseline if r['split']=='train' and not r['verdict']['passed']]
        if not failures:
            phase('baseline-no-observed-training-failure');(root/'result.json').write_text(json.dumps(dict(status='NO_OBSERVED_TRAINING_FAILURE',trained=False,promoted=False))+'\n')
            return 4
        anchor=next(r for r in training if r['id']==failures[0]['id'])
        training=[anchor]+[r for r in training if r['id']!=anchor['id']]
        (root/'training-order-private.json').write_text(json.dumps(training,indent=2)+'\n')
        contract=digest(dict(owner_benchmark='signed-ceiling-v1',base_sha256=runner_config['base_sha256']))
        service=LessonService(root/'lesson-store',contract,tokenizer.encode,NativeRunner(runner_config),max_tokens=config['max_tokens'],max_steps=config['max_steps'])
        phase('admit-independently-checked-training-variations',count=len(training))
        ids=[];failure_hash=digest(failures[0]);checker_hash=sha256(Path(check.__code__.co_filename))
        for index,row in enumerate(training):
            lesson=dict(schema=1,title='Signed ceiling division variation '+str(index),model_contract_id=contract,
                prompt=row['prompt'],completion=row['completion'],scope='owned-training',
                rationale='Owned variation of a captured native completion failure; exact signed-integer checks validate the correction. Evaluation cases are excluded.',
                evidence=dict(method='host-verified-correction-v1',failed_result_sha256=failure_hash,
                    corrected_result_sha256=digest(dict(prompt=row['prompt'],completion=row['completion'])),
                    verification_sha256=digest(dict(case=row['id'],checker_sha256=checker_hash,verdict=check(row,row['completion'])))))
            ids.append(service.submit('/cow/training/lessons',dict(operation_id='lesson-'+row['id'],lesson=lesson))['lesson_id'])
        base_by_id={r['id']:r for r in baseline};held=[r for r in baseline if r['split']=='held_out'];controls=[r for r in baseline if r['split']=='preservation' and r['verdict']['passed']]
        baseline_held=sum(r['verdict']['passed'] for r in held);required_gain=max(1,math.ceil((len(held)-baseline_held)*.25))
        results=[];prior=None;start=0
        for count in checkpoints:
            selected=ids[start:count];batch=min(args.batch_size,len(selected));steps=(len(selected)+batch-1)//batch;operation='quality-through-'+str(count)
            request=dict(operation_id=operation,lesson_ids=selected,mode='lora',batch_size=batch,steps=steps,learning_rate=args.learning_rate,rank=args.rank,parent_job_id=prior)
            phase('native-standard-lora-update',through_examples=count,new_examples=len(selected),steps=steps)
            service.submit('/cow/training/jobs',request)
            deadline=time.monotonic()+3700
            while True:
                job=service.job(operation)
                if job['state'] not in ('queued','running'):break
                if time.monotonic()>deadline:raise TimeoutError('Native update has no terminal proof; reconcile its original run')
                time.sleep(3)
            if job['state']!='complete':raise RuntimeError('Native quality update failed; preserve original job evidence')
            candidate=service._read(service.root/'operations'/(operation+'.json'))['candidate']
            records=evaluate('after-'+str(count),candidate['candidate_path']);now={r['id']:r for r in records}
            held_pass=sum(now[r['id']]['verdict']['passed'] for r in held)
            gates=dict(repairs=now[anchor['id']]['verdict']['passed'],held_out=(held_pass/len(held)>=.9 and held_pass>=baseline_held+required_gain),
                preservation=(len(controls)>=8 and all(now[r['id']]['verdict']['passed'] for r in controls)))
            row=dict(examples=count,job_id=operation,candidate_sha256=candidate['candidate_sha256'],held_out_passed=held_pass,held_out_total=len(held),
                baseline_held_out_passed=baseline_held,preserved=sum(now[r['id']]['verdict']['passed'] for r in controls),preservation_baseline_passed=len(controls),
                original_failure_repaired=gates['repairs'],gates=gates,learning_pass=all(gates.values()),promoted=False)
            results.append(row);(root/'checkpoints.json').write_text(json.dumps(results,indent=2)+'\n');phase('checkpoint-evaluated',**row)
            prior=operation;start=count
        return finish_study(root,manifest,results,runner_config,anchor['id'],blind,evaluate,phase)
    except BaseException as error:
        phase('failed',error=type(error).__name__+': '+str(error));raise
    finally:
        if service is not None:service.close()

if __name__=='__main__':raise SystemExit(main())
