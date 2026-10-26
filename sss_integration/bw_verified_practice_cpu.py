"""Joined CPU machinery proof: genuine task.py BW correction, no model inference.

The real BW interpreter/tools and PCC HTTP/grammar/store execute. A deterministic
byte backend scripts proposals; MiniCPM's real GGUF is used for metadata/rendering
and tokenization only, never a forward pass or native model load.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import os
import threading

from sss.practice_oracle import AffineClampFoldCase
from sss.adapters.bw_verified_practice import BWArtifactPractice,PCCArtifactRenderer,export_correction,read_export

BAD = b'def solve(values, scale, offset, low, high):\n    return {"values": [], "total": 0}\n'
GOOD = (b'def solve(values, scale, offset, low, high):\n'
        b'    result = []\n'
        b'    for value in values:\n'
        b'        result.append(min(high, max(low, scale * value + offset)))\n'
        b'    return {"values": result, "total": sum(result)}\n')
ROWS = [dict(values=[-4,0,2,9],scale=3,offset=-2,low=-5,high=8),
        dict(values=[],scale=-2,offset=7,low=-1,high=3),
        dict(values=[-3,1,1,5],scale=-2,offset=1,low=-4,high=6)]


@contextmanager
def captured_pair(root, *, task_override=None, corrected_source=GOOD, project_sentinel=None, model_contract_id='a'*64, baseline_source=BAD, extra_check_file=False):
    from branchwrite.coding_cli import build_launch,save_launch,run_saved
    from branchwrite.lesson_capture import capture_failure,capture_correction
    from test_thinking_grammar import ThinkingTokenizer
    from serve.test_cow_grammar_canonical_flow import GrammarCPUBackend,_render,_encode
    from context_time_travel.real import BranchingModel
    from context_time_travel.coordinator import ContextCoordinator
    from context_time_travel.pools import PoolConfig
    from serve.cow_adapter import CowAdapter
    from serve.cow_text_adapter import CowTextAdapter
    from serve.cow_grammar_disk import DurableGrammarCatalog
    from serve.cow_http import make_server
    root=Path(root);root.mkdir(mode=0o700,parents=True,exist_ok=False)
    project=root/'project';project.mkdir(mode=0o700);(project/'task.py').write_bytes(baseline_source);(project/'task.py').chmod(0o644)
    if project_sentinel is not None:
        (project/'preserve-input.txt').write_bytes(project_sentinel);(project/'preserve-input.txt').chmod(0o644)
    owner=BWArtifactPractice(AffineClampFoldCase.install('owned-affine-join-01','practice.join-01',ROWS),
        model_contract_id,hashlib.sha256(baseline_source).hexdigest())
    actions=[];tokenizer=ThinkingTokenizer()
    profile=dict(model_contract_id=owner.model_contract_id,execution_profile_id='b'*64,model_weights_sha256='c'*64,
        execution=dict(GPU=[0],resume_contract='identical-native-operators-v1',generated_operator='normal-verifier-decode',
            selected_token_protocol='consumed-selected-receipt-v1',sampling_protocol='full-vocab-min-p-u53-v2',
            native_request_protocol='consumed-greedy-ack-v1',prefill_chunk=16,capacity=131072,eos_tokens=[256]))
    class Scripted(GrammarCPUBackend):
        def __init__(self,p,t):super().__init__(p,t);self.index=self.cursor=0
        def selected(self):
            raw=json.dumps(actions[min(self.index,len(actions)-1)],separators=(',',':')).encode()
            return raw[self.cursor] if self.cursor<len(raw) else 256
        def logits(self,lease):
            chosen=self.selected() if actions else 256
            return tuple(1000. if i==chosen else -1000. for i in range(self.vocab_size))
        def sample_legal(self,lease,mask,*args,**kwargs):
            value=self.selected()
            if not mask[value>>3] & (1<<(value&7)):raise AssertionError('script violates real production grammar')
            return value
        def consume_generated(self,lease,ids):
            super().consume_generated(lease,ids)
            for value in ids:
                if value==256:self.index+=1;self.cursor=0
                else:self.cursor+=1
    coordinator=ContextCoordinator(root/'cow-store',PoolConfig(gpus=(0,),ram_bytes=64*1024**2,disk_bytes=256*1024**2,min_available_bytes=0),
        lambda gpu:BranchingModel(root/'cow-store',Scripted(profile,tokenizer),profile))
    server=None;thread=None;catalog=None
    old_key=os.environ.get('BW_COW_API_KEY');os.environ['BW_COW_API_KEY']='owned-joined-cpu'
    try:
        coordinator.ready(5);adapter=CowAdapter(coordinator)
        suffix=lambda canonical,controller,content:tuple(tokenizer.encode('\nuser:'+content+'\nassistant:',parse_special=False))
        text=CowTextAdapter(adapter,tokenizer,_render,lambda messages,rendered,add_generation_prompt:_encode(tokenizer,messages,rendered,add_generation_prompt),
            append_initial_user_suffix=suffix,append_user_suffix=suffix,
            initial_root_mode=lambda canonical,controller:'context_only' if controller=={'status':'idle'} else 'unsupported',renderer_id='d'*64)
        catalog=DurableGrammarCatalog(root/'grammars',tokenizer,[256])
        server=make_server(adapter,api_key='owned-joined-cpu',text_adapter=text,grammar_catalog=catalog,
            connection_info=dict(model_contract_id=owner.model_contract_id,execution_profile_id='b'*64,eos_tokens=[256]))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        connection=dict(endpoint_url='http://127.0.0.1:'+str(server.server_port),endpoint_pin='owned-scripted-cpu',
            model_contract_id=owner.model_contract_id,execution_profile_id='b'*64,eos_tokens=[256])
        def run(name,fix):
            backend=coordinator._workers[0]['model'].backend;backend.index=backend.cursor=0
            actions[:]=[dict(tool='read_file',arguments=dict(path='task.py'))]
            if fix:
                actions.extend([dict(tool='replace',arguments=dict(path='task.py',before=baseline_source.decode(),after=corrected_source.decode())),
                    dict(tool='run_check',arguments=dict(name='syntax',command='python3 -B -c \'import ast; ast.parse(open("task.py").read())\'')),
                    dict(tool='finish',arguments=dict(answer='Scripted host correction; independent grading remains separate'))])
            if fix and extra_check_file:
                actions.insert(2,dict(tool='create_text_file',arguments=dict(path='check_notes.py',line_ending='LF',
                    final_newline=True,lines=['# Owned helper; independent artifact grading remains separate.'])))
                actions.insert(3,dict(tool='set_mode',arguments=dict(path='check_notes.py',mode='0644')))
            state=root/name;launch=build_launch(project,task_override or owner.task_prompt,connection,
                branch=name,project_files=True,thinking_mode='off',instruction_style='compact-finish-request',shell_timeout=3)
            if fix and extra_check_file:
                launch['config']['grant']['read_paths']=['check_notes.py']
                launch['config']['grant']['mode_paths']=['check_notes.py']
                launch['config']['grant']['mode_mask']=0o777
            save_launch(state,launch);returned=[]
            _,result=run_saved(state,max_steps=1024,progress=lambda event:returned.append(event) if event=='tool_returned' else None,
                control=None if fix else lambda:len(returned)>=1)
            return state,result
        failed,failed_result=run('failed',False)
        failure=capture_failure(failed,root/'failure-capture')
        corrected,corrected_result=run('corrected',True)
        if failed_result['verified'] or not corrected_result['verified']:raise AssertionError('actual scripted BW host boundaries disagree')
        correction=capture_correction(corrected,root/'correction-capture',failure.directory)
        yield dict(owner=owner,failure=failure,correction=correction,failed_state=failed,corrected_state=corrected,
            project=project,source_failed=baseline_source,source_corrected=corrected_source,
            scope='Scripted CPU machinery through actual BW/COW/OS; not model-generated proposals or model learning')
    finally:
        if server is not None:server.shutdown();server.server_close()
        if thread is not None:thread.join(5)
        if catalog is not None:catalog.close()
        coordinator.close()
        if old_key is None:os.environ.pop('BW_COW_API_KEY',None)
        else:os.environ['BW_COW_API_KEY']=old_key


def actual_renderer(model,model_contract_id='a'*64,*,maximum_tokens=4096):
    from serve.cow_http import model_text_components
    components=model_text_components(Path(model),dict(enable_thinking=False),model_contract_id=model_contract_id)
    return PCCArtifactRenderer(components,model_contract_id=model_contract_id,
        tokenizer_sha256=PCCArtifactRenderer.tokenizer_identity(components),maximum_tokens=maximum_tokens,stop_token_ids=[1,130073])


def run(root,model):
    root=Path(root);root.mkdir(mode=0o700,parents=True,exist_ok=False)
    renderer=actual_renderer(model)
    with captured_pair(root/'bw') as pair:
        exported=export_correction(pair['owner'],pair['correction'].directory,
            correction_capture_id=pair['correction'].capture_id,failure_capture_id=pair['failure'].capture_id,
            renderer=renderer,output=root/'export')
        identity=exported.export_id;owner=pair['owner'];left=pair['failure'].capture_id;right=pair['correction'].capture_id
    # Server retired and original operational paths become unavailable.
    (root/'bw').rename(root/'hidden-original-bw')
    read_export(root/'export',owner=owner,expected_export_id=identity,correction_capture_id=right,failure_capture_id=left,renderer=renderer)
    result=dict(schema=1,status='PASS',export_id=identity,lesson_id=exported.lesson_id,
        model_forward_passes=0,gpu_used=False,training_approved=False,owner_registered=False,
        scope='Joined capture/oracle/real-template-tokenizer machinery only; scripted proposals and no learning')
    (root/'result-private.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.output,args.model)))
