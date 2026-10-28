"""Real native LoRA AdamW via both clients; tiny CPU mechanics, not learning."""
from pathlib import Path
import argparse, json, os, subprocess, sys, threading, time


def run(pcc_root, bw_root, executable, output):
    pcc=Path(pcc_root).resolve(strict=True);bw=Path(bw_root).resolve(strict=True)
    sys.path[:0]=[str(pcc),str(pcc/'experimental/branching_context/src'),str(bw)]
    import numpy as np
    from serve.cow_http import make_server
    from tools.pcc_lessons import LessonService, NativeRunner
    from tools.pcc_optimizer_profiles import identity
    from tools.pcc_native_training import sha256, execute_native
    from tools.gguf_reader import GGUFFile
    from experimental.native_training.make_llama_fixture import make_fixture
    from experimental.native_training.test_optimizer_training import state_arrays
    from sss.records import digest
    root=Path(output).absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    model=make_fixture(root/'base.gguf',dtype='f32',layers=1);base=sha256(model)
    def write(path,value):
        with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    def tensors(path):
        info=GGUFFile(path)
        return {t.name:np.fromfile(path,dtype={'F16':'<f2','F32':'<f4'}[t.type_name],
            count=t.elements,offset=info.data_start+t.offset) for t in info.tensors}
    fresh=dict(schema=2,title='Owned tiny LoRA AdamW fresh',mode='lora',rank=2,
        optimizer='adamw',learning_rate=.001,optimizer_settings=dict(schema=1),
        state_policy='fresh',training_budget_seconds=None)
    resume=dict(fresh,title='Owned tiny LoRA AdamW resume',state_policy='resume')
    fresh_id=identity(fresh);resume_id=identity(resume)
    conditions=[]
    for client_name in ('bw','cow'):
        directory=root/client_name;directory.mkdir(mode=0o700)
        config=dict(model=str(model),base_sha256=base,executable=str(executable),devices=['CPU'],gpu_uuids=[],
            device_budget_bytes={'CPU':4<<30},reserve_bytes=128<<20,host_reserve_bytes=128<<20,
            sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',timeout_seconds=60,
            optimizer_profiles={fresh_id:fresh,resume_id:resume})
        runner=NativeRunner(config)
        service=LessonService(directory/'service','a'*64,lambda text:[int(c) for c in text],runner,
            max_tokens=512,max_steps=8,sequence_profile='dense-llama-short-v1')
        key='cpu-lora-'+os.urandom(16).hex()
        server=make_server(object(),api_key=key,training_service=service)
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            url='http://127.0.0.1:'+str(server.server_port)
            connection=dict(endpoint_url=url,endpoint_pin=digest(dict(url=url)),model_contract_id='a'*64,
                execution_profile_id='b'*64,eos_tokens=[0])
            connection_file=directory/'connection-private.json';write(connection_file,connection)
            env={**os.environ,'PYTHONPATH':os.pathsep.join([str(bw),str(pcc),str(pcc/'experimental/branching_context/src'),
                str(Path(__file__).resolve().parents[1])]),'BW_COW_API_KEY':key,'COW_API_KEY':key,'CUDA_VISIBLE_DEVICES':''}
            if client_name=='bw':
                cli=[sys.executable,'-m','branchwrite','lesson','--connection',str(connection_file),'--state-dir',str(directory/'journal')]
            else:
                cli=[sys.executable,'-m','tools.cow_cli','--url',url,'--state-dir',str(directory/'journal'),'lesson']
            def command(args,name,expect=0):
                done=subprocess.run([*cli,*args],capture_output=True,text=True,env=env,timeout=30)
                (directory/(name+'.stdout')).write_text(done.stdout);(directory/(name+'.stderr')).write_text(done.stderr)
                assert done.returncode==expect,(name,done.returncode,done.stderr,done.stdout)
                return json.loads(done.stdout) if expect==0 else None
            def wait(op):
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    value=service.job(op)
                    if value['state'] not in ('queued','running'):
                        assert value['state']=='complete',value;return value
                    time.sleep(.02)
                raise TimeoutError('Original registered LoRA CPU job has not settled')
            def candidate(op):return service._read(service.root/'operations'/(op+'.json'))['candidate']
            profiles=command(['optimizers'],'discovery')['profiles']
            assert {p['id'] for p in profiles}=={fresh_id,resume_id}
            assert all(p['schema']==2 and p['mode']=='lora' and p['rank']==2 and not p['may_stop_before_all_selected_lessons'] for p in profiles)
            lesson_files=[];ids=[]
            for i,(prompt,completion) in enumerate([('01','234'),('12','345'),('23','456'),('0','1234'),('1','2345')]):
                # Independent arithmetic check for the owned teaching fixture only.
                values=[int(v) for v in prompt+completion]
                assert all(b==a+1 for a,b in zip(values,values[1:]))
                proof=digest(dict(kind='owned-consecutive-digit-fixture',values=values,passed=True))
                lesson=dict(schema=1,title='Owned mechanics '+str(i),model_contract_id='a'*64,prompt=prompt,
                    completion=completion,rationale='Host-checked synthetic mechanics fixture, not a spontaneous LLM failure or capability result',
                    scope='owned-training',evidence=dict(method='host-verified-correction-v1',failed_result_sha256='b'*64,
                    corrected_result_sha256=proof,verification_sha256=proof))
                path=directory/('lesson-'+str(i)+'.json');write(path,lesson);lesson_files.append(path)
                if i==0:
                    args=['submit',str(path),'--operation-id','single','--train-now','--mode','lora','--rank','2',
                        '--learning-rate','.001','--steps','2','--optimizer-profile-id',fresh_id]
                    accepted=command(args,'single');first=wait('single-train')
                    assert first['optimizer']=='adamw' and first['optimizer_completed_steps']==2 and first['example_cursor']==2
                    assert len(first['steps'])==2 and first['training_budget'] is None
                    assert command(args,'repeat-single')==accepted
                    ids.append(first['lesson_ids'][0])
                elif i<3:
                    ack=command(['submit',str(path),'--operation-id','lesson-'+str(i)],'submit-'+str(i));ids.append(ack['lesson_id'])
            shared=['--mode','lora','--rank','2','--learning-rate','.001']
            first_sha=candidate('single-train')['candidate_sha256']
            args=['train',ids[0],*shared,'--operation-id','resume','--parent-job-id','single-train',
                '--expected-parent-sha256',first_sha,'--batch-size','1','--steps','3','--optimizer-profile-id',resume_id]
            ack=command(args,'resume');continued=wait('resume')
            assert continued['optimizer_completed_steps']==5 and continued['example_cursor']==5
            assert continued['consumed_example_presentations']==3 and continued['expected_parent_sha256']==first_sha
            assert command(args,'repeat-resume')==ack
            examples=[service.lesson(ids[0])['example']]
            direct=dict(model=str(model),base_sha256=base,mode='lora',rank=2,devices=['CPU'],
                device_budget_bytes={'CPU':4<<30},reserve_bytes=128<<20,host_reserve_bytes=128<<20,
                sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',examples=examples,
                optimizer='adamw',optimizer_settings=dict(schema=1),optimizer_state_mode='fresh',
                learning_rate=.001,batch_size=1,steps=5,deadline_seconds=60)
            uninterrupted=execute_native(executable,direct,directory/'uninterrupted',timeout=75)
            current=candidate('resume');a=tensors(current['candidate_path']);b=tensors(uninterrupted['candidate_path'])
            assert a.keys()==b.keys() and all(np.array_equal(a[k],b[k]) for k in a)
            _,a=state_arrays(current['optimizer_state_path']);_,b=state_arrays(uninterrupted['optimizer_state_path'])
            assert a.keys()==b.keys() and all(np.array_equal(a[k],b[k]) for k in a)
            # New lesson block uses learned hat and deliberately fresh moments.
            args=['train',*ids,*shared,'--operation-id','batch','--parent-job-id','resume',
                '--expected-parent-sha256',current['candidate_sha256'],'--batch-size','2','--steps','2','--optimizer-profile-id',fresh_id]
            ack=command(args,'batch');batch=wait('batch');batch_candidate=candidate('batch')
            assert batch['optimizer_completed_steps']==2 and batch['example_cursor']==3
            assert [s['examples'] for s in batch['steps']]==[2,1] and batch['consumed_lesson_ids_this_job']==ids
            assert batch_candidate['receipt']['optimizer_checkpoint']['candidate_sha256']==batch_candidate['candidate_sha256']
            # Compare to an independently submitted native request with the exact inherited hat.
            direct.update(initial_adapter=current['candidate_path'],initial_adapter_sha256=current['candidate_sha256'],
                examples=[service.lesson(i)['example'] for i in ids],batch_size=2,steps=2)
            straight_batch=execute_native(executable,direct,directory/'uninterrupted-batch',timeout=75)
            a=tensors(batch_candidate['candidate_path']);b=tensors(straight_batch['candidate_path'])
            assert a.keys()==b.keys() and all(np.array_equal(a[k],b[k]) for k in a)
            _,a=state_arrays(batch_candidate['optimizer_state_path']);_,b=state_arrays(straight_batch['optimizer_state_path'])
            assert a.keys()==b.keys() and all(np.array_equal(a[k],b[k]) for k in a)
            assert command(args,'repeat-batch')==ack
            # Pending selection is frozen before a later lesson arrives.
            fourth=command(['submit',str(lesson_files[3]),'--operation-id','fourth'],'fourth')['lesson_id']
            args=['train','--pending',*shared,'--operation-id','pending','--batch-size','2','--optimizer-profile-id',fresh_id]
            ack=command(args,'pending');pending=wait('pending');assert pending['lesson_ids']==[fourth]
            fifth=command(['submit',str(lesson_files[4]),'--operation-id','fifth'],'fifth')['lesson_id']
            assert command(args,'repeat-pending')==ack and service.job('pending')['lesson_ids']==[fourth]
            assert next(v for v in service.lessons()['lessons'] if v['lesson_id']==fifth)['pending']
            # Refused before queue: incompatible mode/rank/pin, new ordered data resume, changed policy rate.
            request=dict(operation_id='bad',lesson_ids=ids,mode='lora',rank=2,batch_size=2,steps=2,learning_rate=.001,
                parent_job_id='batch',optimizer_profile_id=resume_id)
            negative=0
            for changes in [dict(lesson_ids=ids[::-1]),dict(lesson_ids=[fourth]),dict(mode='full'),dict(rank=4),
                    dict(learning_rate=.002),dict(expected_parent_sha256='0'*64),dict(parent_job_id=None)]:
                bad=dict(request,**changes);bad['operation_id']='bad-'+str(negative)
                try:service.submit('/cow/training/jobs',bad)
                except ValueError:pass
                else:raise AssertionError('Incompatible registered LoRA resume admitted')
                assert not (service.root/'operations'/(bad['operation_id']+'.json')).exists()
                assert not (service.root/'runs'/bad['operation_id']).exists();negative+=1
            wrong=['train',ids[0],*shared,'--operation-id','bad-cli','--parent-job-id','resume','--rank','4',
                '--optimizer-profile-id',resume_id]
            command(wrong,'bad-client-rank',2)
            assert not (service.root/'operations/bad-cli.json').exists()
            # Reusing an accepted operation with altered updates cannot train again.
            command(['train',ids[0],*shared,'--operation-id','resume','--parent-job-id','single-train',
                '--expected-parent-sha256',first_sha,'--batch-size','1','--steps','4','--optimizer-profile-id',resume_id],
                'changed-operation',2)
            assert len(list((service.root/'runs').iterdir()))==4
            conditions.append(dict(client=client_name,status='PASS',actual_service_native_jobs=4,
                uninterrupted_native_controls=2,registered_lora_adamw=True,single_example_explicit_steps=2,
                resumed_global_steps=5,resumed_cursor=5,weights_and_all_moments_bit_exact=True,
                new_block_retains_hat_and_resets_moments=True,final_partial_batch=[2,1],
                pending_selection_frozen=True,operation_retries_not_retrained=True,
                refused_before_queue=negative+1,promoted=False))
        finally:
            server.shutdown();server.server_close();thread.join();service.close()
    assert sha256(model)==base
    value=dict(schema=1,status='PASS',scope='Real tiny CPU LoRA AdamW through both actual CLIs and authenticated PCC service; no model learning or GPU qualification',
        conditions=conditions,base_unchanged=True,executable_sha256=sha256(executable),gpu_used=False,promoted=False)
    write(root/'result.json',value);print(json.dumps(value));return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root','bw-root','executable','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.pcc_root,args.bw_root,args.executable,args.output)
