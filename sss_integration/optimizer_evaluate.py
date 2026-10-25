"""One frozen direct-answer evaluation through an owned native oracle.

S3 owns grading. This command records original operations and never trains,
retries an uncertain result, changes a checker, or promotes a model.
"""
from pathlib import Path
import argparse,json,hashlib,sys,time,collections


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def run(a):
    sys.path.insert(0,str(a.pcc_root.resolve(strict=True)))
    from tools.strata_tokenizer import Tokenizer
    from tools.gguf_reader import GGUFFile
    from sss.records import digest
    from sss.evaluation import implementation_identity
    from sss.foundations import Exercise,check
    from sss.adapters.native_oracle import oracle_process,token_completion
    from sss.studies.evaluation_shards import plan as shard_plan,indices as shard_indices,binding as shard_binding
    root=a.output.resolve();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    data=json.loads(a.cases.read_text());identity=digest({k:v for k,v in data.items() if k!='evaluation_id'})
    if data.get('evaluation_id')!=identity or identity!=a.evaluation_id:raise ValueError('Pinned evaluation changed')
    if implementation_identity()!=a.checker_implementation_id:raise ValueError('Pinned checker implementation differs')
    if sha(a.model)!=a.model_sha256:raise ValueError('Pinned model artifact differs')
    if type(data.get('cases')) is not list or not data['cases']:raise ValueError('Explicit nonempty evaluation required')
    exercises=[Exercise(**row['exercise']) for row in data['cases']]
    if any(e.identity!=row['exercise_id'] for e,row in zip(exercises,data['cases'])) or len({e.identity for e in exercises})!=len(exercises):raise ValueError('Evaluation exercise identity/coverage differs')
    partition=shard_plan(identity,[dict(id=e.identity,skill_id=e.skill_id,gate=e.gate) for e in exercises],getattr(a,'shard_count',1))
    partition_source=Path(__file__).parents[1]/'sss/studies/evaluation_shards.py'
    partition_source_sha256=sha(partition_source)
    assigned=shard_indices(partition,getattr(a,'shard_index',0))
    shard=shard_binding(partition,getattr(a,'shard_index',0)) if partition['count']>1 else None
    if any(len(row['prefix_tokens'])+a.maximum_tokens>a.context_tokens for row in data['cases']):raise ValueError('Evaluation requires more context; no truncation')
    metadata=GGUFFile(a.model).metadata
    tokenizer_id=digest(dict(metadata={k:v for k,v in metadata.items() if k.startswith('tokenizer.')},source_sha256=sha(a.pcc_root/'tools/strata_tokenizer.py')))
    if tokenizer_id!=data['tokenizer_sha256']:raise ValueError('Evaluation tokenizer identity differs')
    tok=Tokenizer.from_gguf(a.model)
    build=json.loads(a.runtime_proof.read_text())
    pins=build['sha256']
    if pins.get(str(a.oracle.resolve()))!=sha(a.oracle):raise ValueError('Qualified oracle binary differs')
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Qualified runtime artifact changed: '+path)
    execution_path=getattr(a,'execution_path','fresh')
    profile=None
    common_prefix=[]
    if execution_path=='cow':
        if a.cow_profile is None:raise ValueError('Explicit pinned COW profile required')
        profile=json.loads(a.cow_profile.read_text())
        if pins.get(profile['bridge_library'])!=sha(profile['bridge_library']):
            raise ValueError('COW bridge is absent from the qualified runtime proof')
        from sss.adapters.cow_evaluation import cow_session,runtime_binding,candidate_binding,shared_input_prefix,token_completion as cow_completion
        from tools.pcc_cow_evaluation import verify_sources
        verify_sources(profile,a.pcc_root)
        if getattr(a,'cow_shared_prefix',False):
            from tools.pcc_cow_evaluation import CowEvaluationSession
            if not callable(getattr(CowEvaluationSession,'prepare_shared_prefix',None)):
                raise ValueError('This PCC snapshot does not support the shared-prefix evaluation adapter')
            common_prefix=shared_input_prefix([row['prefix_tokens'] for row in data['cases']])
            if not common_prefix:raise ValueError('These independent cases have no shared input prefix')
    elif getattr(a,'cow_profile',None) is not None:
        raise ValueError('COW profile requires explicit COW execution path')
    if getattr(a,'cow_shared_prefix',False) and profile is None:
        raise ValueError('Shared-prefix evaluation requires the explicit COW path')
    policy=dict(context_tokens=a.context_tokens,batch_tokens=a.batch_tokens,maximum_tokens=a.maximum_tokens,
        stop_token_ids=a.stop_token_ids,protocol='tokens-v1',all_logits=True,greedy=True,
        score='existing exact-foundations checker; EOS completion reported separately')
    runtime=dict(proof_sha256=sha(a.runtime_proof),runtime_artifacts=pins,adapter_sha256=sha(Path(__file__).parents[1]/'sss/adapters/native_oracle.py'),
        runner_sha256=sha(__file__),checker_implementation_id=a.checker_implementation_id,tokenizer_sha256=tokenizer_id,policy=policy,
        case_partition_implementation_sha256=partition_source_sha256)
    runtime_id=digest(runtime)
    if profile is not None:
        runtime.update(execution_path='cow-consumed-request-v1',
            cow_runtime=runtime_binding(profile),
            cow_adapter_sha256=sha(Path(__file__).parents[1]/'sss/adapters/cow_evaluation.py'))
        runtime['policy']=dict(policy,protocol='cow-consumed-request-v1',all_logits=False,
            output_boundary='All sampled tokens including EOS consumed by COW',
            counters='Actual prefix + consumed decode tokens; includes final sampled token')
        if common_prefix:
            runtime['policy'].update(shared_prefix=dict(policy='longest-common-rendered-input-v1',
                tokens=len(common_prefix),tokens_sha256=digest(common_prefix)))
        runtime_id=digest(runtime)
    intent=dict(schema=1,evaluation_id=identity,cases_sha256=sha(a.cases),split=data['split'],pack_id=data['pack_id'],model_sha256=a.model_sha256,
        model_contract_id=data['model_contract_id'],runtime_id=runtime_id,runtime=runtime,case_count=len(assigned),gpu_uuid=a.gpu_uuid,weights_updated=False)
    candidate=candidate_binding(profile) if profile is not None else {}
    if profile is not None:intent.update(cow_profile=profile,cow_profile_sha256=sha(a.cow_profile),**candidate)
    if shard is not None:intent.update(shard=shard,assigned_indices=assigned,partition=partition)
    write(root/'intent.json',intent)
    results=[];start=time.monotonic();status='FAILED';total_calls=0;total_prefill=0;admitted=False;allocation_end=None;setup=None
    def cow_admitted(receipt):
        nonlocal admitted
        admitted=True
        write(root/'admission.json',receipt)
    try:
        manager=(cow_session(a.pcc_root,profile,a.model,a.model_sha256,a.gpu_uuid,root,
                    context_tokens=a.context_tokens,batch_tokens=a.batch_tokens,stop_token_ids=a.stop_token_ids,
                    minimum_free_mib=a.minimum_free_mib,maximum_initial_utilization=a.maximum_initial_utilization,
                    on_admission=cow_admitted)
                 if profile is not None else oracle_process(a.oracle,a.model,a.gpu_uuid,root/'oracle-private.log',
                    context_tokens=a.context_tokens,batch_tokens=a.batch_tokens,minimum_free_mib=a.minimum_free_mib,
                    maximum_initial_utilization=a.maximum_initial_utilization,all_logits=True))
        with manager as proc:
            admitted=True
            if profile is None:write(root/'admission.json',proc.pcc_admission)
            pid=__import__('os').getpid() if profile is not None else proc.pid
            write(root/'native-process.json',dict(pid=pid,start_ticks=Path('/proc',str(pid),'stat').read_text().split()[21]))
            if common_prefix:
                setup=proc.prepare_shared_prefix(common_prefix)
                write(root/'shared-prefix-setup.json',setup)
                total_calls+=setup['counters']['forward_calls'];total_prefill+=setup['counters']['consumed_tokens']
            for index in assigned:
                row,exercise=data['cases'][index],exercises[index]
                case_start=time.monotonic()
                completion=(cow_completion(proc,tok,row['prefix_tokens'],maximum=a.maximum_tokens,
                                stop_token_ids=a.stop_token_ids,stream='sss-evaluation-'+str(index))
                            if profile is not None else token_completion(proc,tok,row['prefix_tokens'],maximum=a.maximum_tokens,
                                context_tokens=a.context_tokens,batch_tokens=a.batch_tokens,stop_token_ids=a.stop_token_ids))
                passed=check(exercise,completion['text']);total_calls+=completion['model_calls'];total_prefill+=completion['prefill_tokens']
                result=dict(index=index,id=exercise.identity,skill_id=exercise.skill_id,gate=exercise.gate,passed=passed,
                    finished=completion['stop_reason']=='eos',completion=completion,seconds=time.monotonic()-case_start,
                    model_sha256=a.model_sha256,runtime_id=runtime_id,evaluation_id=identity,**candidate)
                write(root/(str(index).zfill(4)+'-private.json'),result);results.append(result)
                print(json.dumps(dict(completed=len(results),total=len(assigned),passed=sum(r['passed'] for r in results),calls=total_calls)),flush=True)
        allocation_end=time.monotonic()
        if sha(a.model)!=a.model_sha256:raise ValueError('Model weights changed during evaluation')
        if sha(a.cases)!=json.loads((root/'intent.json').read_text())['cases_sha256'] or implementation_identity()!=a.checker_implementation_id:raise ValueError('Evaluation inputs/checker changed during execution')
        for path,expected in pins.items():
            if sha(path)!=expected:raise ValueError('Runtime changed during evaluation')
        if profile is not None and sha(a.cow_profile)!=intent['cow_profile_sha256']:
            raise ValueError('Pinned COW profile changed during evaluation')
        if sha(partition_source)!=partition_source_sha256:raise ValueError('Case partition implementation changed during evaluation')
        groups=[]
        for skill in sorted({e.skill_id for e in exercises}):
            for gate in ('independent','composition','transfer_recovery'):
                rows=[r for r in results if r['skill_id']==skill and r['gate']==gate]
                if rows:groups.append(dict(skill_id=skill,gate=gate,passed=sum(r['passed'] for r in rows),finished=sum(r['finished'] for r in rows),cases=len(rows)))
        summary=dict(schema=1,status='COMPLETE',scope='Frozen direct-answer behavior, no learning or model promotion',
            evaluation_id=identity,model_sha256=a.model_sha256,runtime_id=runtime_id,cases=len(results),passed=sum(r['passed'] for r in results),
            finished=sum(r['finished'] for r in results),groups=groups,model_calls=total_calls,prefill_tokens=total_prefill,
            outcomes=[{k:r[k] for k in ['id','skill_id','gate','passed','finished']} for r in results],weights_updated=False,promoted=False,**candidate)
        if setup is not None:
            summary.update(shared_prefix_setup=setup,setup_model_calls=setup['counters']['forward_calls'],
                           setup_prefill_tokens=setup['counters']['consumed_tokens'])
        if shard is not None:summary.update(status='SHARD_COMPLETE',shard=shard)
        write(root/'result.json',summary);status=summary['status'];print(json.dumps({k:v for k,v in summary.items() if k not in ['groups','outcomes']}),flush=True)
        return summary
    finally:
        write(root/'settlement.json',dict(status=status,allocated_seconds=((allocation_end or time.monotonic())-start) if admitted else 0,execution_wall_seconds=time.monotonic()-start,physical_gpus=1 if admitted else 0,completed_cases=len(results),model_calls=total_calls,prefill_tokens=total_prefill,weights_updated=False,
            setup_model_calls=setup['counters']['forward_calls'] if setup else 0,
            setup_prefill_tokens=setup['counters']['consumed_tokens'] if setup else 0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root','cases','model','oracle','runtime-proof','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('evaluation-id','checker-implementation-id','model-sha256','gpu-uuid'):p.add_argument('--'+name,required=True)
    p.add_argument('--context-tokens',type=int,required=True);p.add_argument('--batch-tokens',type=int,required=True)
    p.add_argument('--maximum-tokens',type=int,default=64);p.add_argument('--stop-token-ids',type=int,nargs='+',required=True)
    p.add_argument('--minimum-free-mib',type=int,required=True);p.add_argument('--maximum-initial-utilization',type=int,default=0)
    p.add_argument('--execution-path',choices=('fresh','cow'),default='fresh')
    p.add_argument('--cow-profile',type=Path)
    p.add_argument('--cow-shared-prefix',action='store_true')
    p.add_argument('--shard-count',type=int,default=1)
    p.add_argument('--shard-index',type=int,default=0)
    run(p.parse_args())
