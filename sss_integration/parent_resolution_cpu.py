"""Actual PCC/BW CLI parent guards with controlled S3 semantic scores.

Native weights really change. The injected scores test decisions, not learning.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, subprocess, sys, threading, time


def run(pcc_root,bw_root,executable,output):
    pcc=Path(pcc_root).resolve(strict=True);bw=Path(bw_root).resolve(strict=True)
    sys.path[:0]=[str(pcc),str(pcc/'experimental/branching_context/src'),str(bw)]
    from serve.cow_http import make_server
    from tools.pcc_lessons import LessonService,NativeRunner
    from tools.pcc_cow_profile import bind_dense_profile,bind_dense_adapter
    from tools.pcc_native_training import sha256
    from experimental.native_training.make_llama_fixture import make_fixture
    from sss.learning import next_skill_block
    from sss.records import digest
    from sss_integration.resolve_parent import resolve_proposal
    root=Path(output).absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    model=make_fixture(root/'base.gguf',dtype='f32',layers=1);base=sha256(model)
    def write(path,value):
        with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    profile=dict(backend='llama-dense-llama.cpp',native_build=dict(sha256={},lora_binding='llama-adapter-per-lease-v1'),
        hardware=dict(gpu_uuid='GPU-identity-fixture'),execution=dict(state_format='llama-dense-frontier-v1',kv_dtype='FP32',
        device_binding='cuda-single-device-v1',environment=dict(CUDA_VISIBLE_DEVICES='0'),GPU=[0]))
    profile_file=root/'identity-only-profile.json';write(profile_file,profile)
    results=[]
    for mode in ('full','lora'):
        directory=root/mode;directory.mkdir(mode=0o700)
        runner=NativeRunner(dict(model=str(model),base_sha256=base,executable=str(executable),devices=['CPU'],
            gpu_uuids=[],device_budget_bytes={'CPU':4<<30},reserve_bytes=128<<20,host_reserve_bytes=128<<20,
            sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',timeout_seconds=60))
        service=LessonService(directory/'service','a'*64,lambda text:[int(c) for c in text],runner,max_tokens=512,max_steps=8,sequence_profile='dense-llama-short-v1')
        key='cpu-parent-'+os.urandom(16).hex()
        server=make_server(object(),api_key=key,training_service=service)
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            url='http://127.0.0.1:'+str(server.server_port)
            connection=dict(endpoint_url=url,endpoint_pin=digest(dict(url=url)),model_contract_id='a'*64,execution_profile_id='b'*64,eos_tokens=[0])
            connection_file=directory/'connection-private.json';write(connection_file,connection)
            env={**os.environ,'PYTHONPATH':os.pathsep.join([str(bw),str(pcc),str(pcc/'experimental/branching_context/src'),str(Path(__file__).resolve().parents[1])]),'BW_COW_API_KEY':key,'COW_API_KEY':key,'CUDA_VISIBLE_DEVICES':''}
            def command(args,name,expect=0):
                done=subprocess.run(args,capture_output=True,text=True,env=env,timeout=30)
                (directory/(name+'.stdout')).write_text(done.stdout);(directory/(name+'.stderr')).write_text(done.stderr)
                assert done.returncode==expect,(name,done.returncode,done.stderr)
                return json.loads(done.stdout) if expect==0 else None
            def wait(identity):
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    value=service.job(identity)
                    if value['state'] not in ('queued','running'):
                        assert value['state']=='complete',value;return value
                    time.sleep(.02)
                raise TimeoutError('Original CPU job did not settle')
            # Generated digit continuation has an actual independent host check.
            assert all(b==a+1 for a,b in zip([0,1,2,3],[1,2,3,4]))
            check=dict(kind='owned-digit-continuation-fixture',prompt='01',completion='234',passed=True,synthetic_mechanics=True)
            write(directory/'teaching-check-private.json',check)
            lesson=dict(schema=1,title='Owned digit mechanics fixture',model_contract_id='a'*64,prompt='01',completion='234',
                rationale='Generated consecutive-digit fixture for native transport tests; no spontaneous model failure or capability claim',scope='owned-training',
                evidence=dict(method='host-verified-correction-v1',failed_result_sha256=digest(dict(synthetic_failure=True,passed=False)),
                corrected_result_sha256=digest(check),verification_sha256=digest(check)))
            accepted=service.submit('/cow/training/lessons',dict(operation_id='lesson',lesson=lesson));lesson_id=accepted['lesson_id']
            request=dict(operation_id='first',lesson_ids=[lesson_id],mode=mode,batch_size=1,steps=1,learning_rate=.001,rank=2,parent_job_id=None)
            service.submit('/cow/training/jobs',request);first=wait('first');first_sha=first['candidate']['sha256']
            bwcli=[sys.executable,'-m','branchwrite','lesson','--connection',str(connection_file),'--state-dir',str(directory/'bw-journal')]
            shared=['train',lesson_id,'--mode',mode,'--rank','2','--learning-rate','.001','--batch-size','1']
            good=[*bwcli,*shared,'--operation-id','from-bw','--parent-job-id','first','--expected-parent-sha256',first_sha]
            bad=[*bwcli,*shared,'--operation-id','bad-bw','--parent-job-id','first','--expected-parent-sha256','0'*64]
            command(bad,'bad-bw',2)
            assert not (service.root/'operations/bad-bw.json').exists() and not (service.root/'runs/bad-bw').exists()
            ack=command(good,'good-bw');second=wait('from-bw')
            assert second['expected_parent_sha256']==first_sha
            assert command(good,'repeat-bw')==ack
            assert len(list((service.root/'runs').iterdir()))==2
            changed=good[:-1]+['0'*64];command(changed,'changed-bw-operation',2)
            first_record=service._read(service.root/'operations/first.json')['candidate']
            second_record=service._read(service.root/'operations/from-bw.json')['candidate']
            def evidence(candidate,outcomes):
                path=Path(candidate['candidate_path']) if candidate and mode=='full' else model
                weights=sha256(path);bound=bind_dense_profile(profile,model_path=path,model_sha256=weights,gpu_index=0,gpu_uuid='GPU-identity-fixture');adapters=[]
                if candidate and mode=='lora':
                    bound=bind_dense_adapter(bound,adapter_path=candidate['candidate_path'],adapter_sha256=candidate['candidate_sha256'])
                    adapters=[dict(sha256=candidate['candidate_sha256'],scale=1.)]
                rows=[dict(id='owned-'+str(i),skill_id='fixture.sequence',gate='independent',passed=p,finished=f) for i,(p,f) in enumerate(outcomes)]
                return dict(status='COMPLETE',evaluation_id='c'*64,runtime_id='d'*64,model_sha256=weights,cases=len(rows),
                    passed=sum(x['passed'] for x in rows),finished=sum(x['finished'] for x in rows),outcomes=rows,
                    candidate_model_contract_id=bound['model_contract_id'],candidate_adapters=adapters,weights_updated=False,promoted=False)
            original=evidence(None,[(True,True),(False,False),(False,False),(False,False)])
            parent=evidence(first_record,[(True,True),(True,True),(False,False),(False,False)])
            candidate=evidence(second_record,[(False,True),(True,True),(True,True),(True,True)])
            proposal=next_skill_block(original,parent,candidate);assert proposal['working_decision']=='KEEP_AND_REPAIR' and proposal['strict_preservation_status']=='REJECTED'
            files={}
            for name,value in [('baseline',original),('parent',parent),('candidate',candidate),('proposal',proposal)]:
                files[name]=directory/(name+'-controlled.json');write(files[name],value)
            version=Path(second_record['candidate_path']).parent/'versions'/(second_record['candidate_sha256']+'.json')
            kwargs=dict(artifact_roots=[root],state_policy='fresh',base_model=model if mode=='lora' else None)
            resolution=resolve_proposal(pcc,files['proposal'],files['baseline'],files['parent'],files['candidate'],version,profile_file,**kwargs)
            expected=resolution['pcc_resolution']['candidate_sha256'];assert expected==second['candidate']['sha256']
            receipt_file=directory/'resolved-parent-private.json'
            resolve_command=[sys.executable,'-m','sss_integration.resolve_parent','--pcc-root',str(pcc),
                '--proposal',str(files['proposal']),'--baseline',str(files['baseline']),'--parent',str(files['parent']),
                '--candidate',str(files['candidate']),'--version',str(version),'--profile',str(profile_file),
                '--artifact-root',str(root),'--state-policy','fresh','--output',str(receipt_file)]
            if mode=='lora':resolve_command+=['--base-model',str(model)]
            actual=command(resolve_command,'resolve-cli')
            assert actual['resolution_id']==resolution['resolution_id'] and not actual['dispatched']
            before=receipt_file.read_bytes();command(resolve_command,'resolve-cli-existing',2)
            assert receipt_file.read_bytes()==before and receipt_file.stat().st_mode&0o777==0o600
            altered=copy.deepcopy(proposal);altered['next_parent']=altered['parent'];altered['proposal_id']=digest({k:v for k,v in altered.items() if k!='proposal_id'})
            wrong=directory/'altered-proposal.json';write(wrong,altered)
            try:resolve_proposal(pcc,wrong,files['baseline'],files['parent'],files['candidate'],version,profile_file,**kwargs)
            except ValueError:pass
            else:raise AssertionError('Changed proposal selected another parent')
            cowcli=[sys.executable,'-m','tools.cow_cli','--url',url,'--state-dir',str(directory/'cow-journal'),'lesson']
            good=[*cowcli,*shared,'--operation-id','from-cow','--parent-job-id','from-bw','--expected-parent-sha256',expected]
            ack=command(good,'good-cow');third=wait('from-cow');assert third['expected_parent_sha256']==expected
            assert command(good,'repeat-cow')==ack
            bad=[*cowcli,*shared,'--operation-id','bad-cow','--parent-job-id','from-bw','--expected-parent-sha256',first_sha]
            command(bad,'bad-cow',2)
            assert not (service.root/'operations/bad-cow.json').exists() and len(list((service.root/'runs').iterdir()))==3
            # Guard must not be accepted without a named parent, nor on a lesson-only submission.
            for index,payload in enumerate([dict(request,operation_id='bad-api-no-parent',expected_parent_sha256=first_sha),
                                            dict(request,operation_id='bad-api-format',parent_job_id='first',expected_parent_sha256=True)]):
                try:service.submit('/cow/training/jobs',payload)
                except ValueError:pass
                else:raise AssertionError('Invalid parent pin accepted')
            results.append(dict(mode=mode,status='PASS',actual_native_jobs=3,both_cli_guards_enforced=True,
                wrong_parent_refused_before_queue=True,operation_retry_not_retrained=True,recomputed_proposal_resolved=True,
                actual_resolver_cli_private_and_exclusive=True,forged_proposal_refused=True,controlled_scores=True,promoted=False))
        finally:
            server.shutdown();server.server_close();thread.join();service.close()
    assert sha256(model)==base
    value=dict(schema=1,status='PASS',scope='Real CPU native/PCC HTTP/BW and COW CLI binding mechanics with explicitly injected S3 semantic scores; no learning or GPU qualification',
        conditions=results,base_unchanged=True,executable_sha256=sha256(executable),gpu_used=False,promoted=False)
    write(root/'result.json',value);print(json.dumps(value));return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root','bw-root','executable','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.pcc_root,args.bw_root,args.executable,args.output)
