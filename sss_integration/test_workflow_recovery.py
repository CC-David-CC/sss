"""Actual HTTP/store/ledger recovery, with an explicitly scripted CPU backend."""
from pathlib import Path
from contextlib import contextmanager
import json,os,subprocess,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch

from sss.adapters.cow_learning import process_identity
from sss.artifact_assessment import ArtifactAssessmentCase
from sss.practice_oracle import AffineClampFoldCase
from sss_integration.bw_verified_practice_cpu import BAD,ROWS
from sss_integration.workflow_recovery import storage_admission,require_retired,resume_case

PROFILE=dict(model_contract_id='a'*64,execution_profile_id='b'*64,model_weights_sha256='c'*64,
    model_path='/explicit-scripted-CPU-fixture',execution=dict(GPU=[0],
        resume_contract='identical-native-operators-v1',generated_operator='normal-verifier-decode',
        selected_token_protocol='consumed-selected-receipt-v1',sampling_protocol='full-vocab-min-p-u53-v2',
        native_request_protocol='consumed-greedy-ack-v1',prefill_chunk=16,capacity=131072,eos_tokens=[256]))

def fixture(mode=None):
    from test_thinking_grammar import ThinkingTokenizer
    from serve.test_cow_grammar_canonical_flow import GrammarCPUBackend,_render,_encode
    tok=ThinkingTokenizer()
    action=json.dumps(dict(tool='read_file',arguments=dict(path='task.py')),separators=(',',':')).encode()
    class Scripted(GrammarCPUBackend):
        def __init__(self,*args,**kwargs):super().__init__(PROFILE,tok);self.cursor=0
        def chosen(self):return action[self.cursor]if self.cursor<len(action)else 256
        def logits(self,lease):return tuple(1000. if i==self.chosen()else -1000. for i in range(self.vocab_size))
        def sample_legal(self,lease,mask,*args,**kwargs):
            token=self.chosen();assert mask[token>>3]&(1<<(token&7));return token
        def consume_generated(self,lease,ids):
            super().consume_generated(lease,ids)
            for token in ids:self.cursor=0 if token==256 else self.cursor+1
    suffix=lambda canonical,controller,content:tuple(tok.encode('\nuser:'+content+'\nassistant:',parse_special=False))
    components=dict(tokenizer=tok,render=_render,
        encode_rendered=lambda messages,rendered,add_generation_prompt:_encode(tok,messages,rendered,add_generation_prompt),
        append_initial_user_suffix=suffix,append_user_suffix=suffix,
        initial_root_mode=lambda canonical,controller:'context_only'if controller=={'status':'idle'}else'unsupported',renderer_id='d'*64)
    case=ArtifactAssessmentCase(AffineClampFoldCase.install('owned-recovery-fixture','owned.recovery',ROWS),BAD,'code.repair.affine','composition')
    class Panel:
        identity='e'*64;pcc=Path('/explicit-scripted-runtime');cases=[case]
        config=dict(gpu_index=0,gpu_uuid='GPU-scripted',context_tokens=131072,batch_tokens=16,
            stop_token_ids=[256],minimum_free_mib=1,maximum_initial_utilization=100,
            maximum_tokens=256,maximum_requests=2,maximum_steps=128,grammar_syntax='lark',
            storage=dict(cache_bytes=64<<20,staging_bytes=1<<20,minimum_free_bytes=1<<20))
        def verify(self):pass
        def profile(self,candidate):return PROFILE
    @contextmanager
    def cpu_lease(*args,**kwargs):yield {}
    if mode and mode.endswith('-exhaust'):Panel.config.update(maximum_tokens=16,maximum_requests=1)
    return Panel(),Scripted,components,cpu_lease

def make_failed_child(root,mode):
    from sss_integration.workflow_evaluate import run
    from branchwrite.cow_client import HTTPTransport,OperationIndeterminate
    panel,backend,components,lease=fixture(mode);root=Path(root)
    (root/'profile.json').write_text(json.dumps(PROFILE));(root/'candidate.json').write_text('null')
    original=HTTPTransport.request;dropped=[]
    def request(self,method,path,*args,**kwargs):
        if method=='POST'and path=='/cow/text/ask'and not dropped:
            dropped.append(True)
            if mode in('after','crash'):original(self,method,path,*args,**kwargs)
            if mode=='crash':os._exit(17)  # No finally block or terminal server receipt.
            raise OperationIndeterminate('injected '+mode+' generation send')
        return original(self,method,path,*args,**kwargs)
    with (patch('sss_integration.workflow_evaluate.BWWorkflowEvaluator',lambda path:panel),
          patch('sss_integration.workflow_evaluate.cow_gpu_admission',lease),
          patch('context_time_travel.llama_dense_backend.LlamaDenseBackend',backend),
          patch('serve.cow_http.model_text_components',lambda *a,**k:components),
          patch.object(HTTPTransport,'request',request)):
        try:run(root/'unused-owner-config',root/'profile.json',root/'candidate.json',root/'evaluation',expected_evaluator_id=panel.identity)
        except OperationIndeterminate:
            assert dropped;return
        raise AssertionError('Fault was not exercised')

class WorkflowRecoveryTests(unittest.TestCase):
    def test_filesystem_guard_refuses_before_model_admission(self):
        with tempfile.TemporaryDirectory()as tmp:
            with patch('shutil.disk_usage',return_value=SimpleNamespace(free=99)):
                with self.assertRaisesRegex(ValueError,'filesystem admission refused'):
                    storage_admission(tmp,cache_bytes=60,staging_bytes=30,minimum_free_bytes=10)
            with patch('shutil.disk_usage',return_value=SimpleNamespace(free=100)):
                self.assertEqual(storage_admission(tmp,cache_bytes=60,staging_bytes=30,minimum_free_bytes=10)['required_free_bytes'],100)
            for value in (True,-1,0):
                with self.assertRaises(ValueError):storage_admission(tmp,cache_bytes=value,staging_bytes=30,minimum_free_bytes=10)

    def test_native_workflow_refuses_low_filesystem_before_gpu_lease(self):
        from sss_integration.workflow_evaluate import native_server
        panel,_,_,_=fixture()
        with tempfile.TemporaryDirectory()as tmp:
            with (patch('shutil.disk_usage',return_value=SimpleNamespace(free=1)),
                  patch('sss_integration.workflow_evaluate.cow_gpu_admission',side_effect=AssertionError('GPU must not be admitted'))):
                with self.assertRaisesRegex(ValueError,'filesystem admission refused'):
                    with native_server(panel,PROFILE,Path(tmp)):pass

    def test_live_original_producer_refused(self):
        with self.assertRaisesRegex(ValueError,'still present'):require_retired([process_identity(os.getpid())])
        with self.assertRaises(ValueError):require_retired([])

    def exercise(self,mode,replay,refused=False,allow_crashed_server=False):
        from contextlib import nullcontext
        retained=os.environ.get('SSS_RECOVERY_TEST_EVIDENCE')
        context=nullcontext(tempfile.mkdtemp(prefix='recovery-'+mode+'-',dir=retained)) if retained else tempfile.TemporaryDirectory()
        with context as tmp:
            if retained:print('RETAINED_FIXTURE',tmp,flush=True)
            root=Path(tmp);cmd=[sys.executable,'-m',__name__,'--fixture',str(root),mode]
            child=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            identity=process_identity(child.pid);out,err=child.communicate(timeout=30)
            self.assertEqual(child.returncode,17 if mode=='crash'else 0,err)
            panel,backend,components,lease=fixture(mode);before=[]
            class Counted(backend):
                def consume_generated(self,lease,ids):before.extend(ids);return super().consume_generated(lease,ids)
            with (patch('sss.adapters.cow_evaluation.cow_gpu_admission',lease),
                  patch('context_time_travel.llama_dense_backend.LlamaDenseBackend',Counted),
                  patch('serve.cow_http.model_text_components',lambda *a,**k:components)):
                # One extra interpreter step only; no fresh task or tool replay.
                if refused:
                    from branchwrite.model_dispatch import ModelReconciliationRequired
                    originals={p.name:p.read_bytes()for p in(root/'evaluation/0000/state/cow-operations').glob('*.json')}
                    expected=ValueError if mode=='crash'else ModelReconciliationRequired
                    with self.assertRaises(expected):
                        resume_case(panel,PROFILE,None,root/'evaluation',0,root/'recovery',
                            producer_identities=[identity],additional_steps=1,allow_original_replay=False,
                            storage=panel.config['storage'])
                    self.assertEqual(before,[])
                    self.assertEqual(originals,{p.name:p.read_bytes()for p in(root/'evaluation/0000/state/cow-operations').glob('*.json')})
                    return
                result=resume_case(panel,PROFILE,None,root/'evaluation',0,root/'recovery',
                    producer_identities=[identity],additional_steps=128 if mode.endswith('-exhaust')else 1,allow_original_replay=replay,
                    allow_crashed_server=allow_crashed_server,
                    storage=dict(cache_bytes=64<<20,staging_bytes=1<<20,minimum_free_bytes=1<<20))
            self.assertFalse(result['finished']);self.assertFalse(result['passed'])
            self.assertGreater(result['completed_operations_preserved'],0)
            self.assertEqual(result['original_operation_replayed'],mode.startswith('before'))
            self.assertEqual(bool(before),mode.startswith('before'))
            if mode.endswith('-exhaust'):
                self.assertEqual(result['workflow']['status'],'model_budget_exhausted')
                self.assertFalse(result['workflow']['training_eligible'])
                self.assertTrue((root/'recovery/budget/budget.json').exists())
                self.assertFalse((root/'recovery/capture').exists())
            if mode=='crash':
                self.assertFalse((root/'evaluation/server-private.json').exists())
                proof=json.loads((root/'recovery/crashed-server-retirement-private.json').read_bytes())
                self.assertTrue(proof['original_terminal_receipt_missing'])
                self.assertTrue(proof['endpoint_bind_probe_succeeded'])

    def test_durable_response_recovered_without_new_forward_work(self):self.exercise('after',False)
    def test_unsettled_send_replayed_only_by_explicit_original_id(self):self.exercise('before',True)
    def test_unknown_send_is_not_replayed_without_explicit_selection(self):self.exercise('before',False,refused=True)

    def test_crashed_server_recovers_original_completion_only_with_explicit_adoption(self):
        self.exercise('crash',False,allow_crashed_server=True)

    def test_crashed_server_is_refused_without_explicit_adoption(self):
        self.exercise('crash',False,refused=True)

    def test_explicit_recovery_can_settle_exhausted_model_budget_without_a_lesson(self):
        self.exercise('before-exhaust',True)

    def test_crashed_server_adoption_refuses_live_endpoint_before_gpu_lease(self):
        import socket
        from sss_integration.workflow_recovery import reopened_server
        panel,_,_,_=fixture()
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
        identity=process_identity(child.pid);child.terminate();child.wait(timeout=5)
        with tempfile.TemporaryDirectory()as tmp,socket.socket()as occupied:
            root=Path(tmp);recovery=root/'recovery';recovery.mkdir()
            occupied.bind(('127.0.0.1',0));occupied.listen()
            connection=dict(model_contract_id=PROFILE['model_contract_id'],execution_profile_id=PROFILE['execution_profile_id'],
                eos_tokens=PROFILE['execution']['eos_tokens'],endpoint_url='http://127.0.0.1:'+str(occupied.getsockname()[1]),
                endpoint_pin='explicit-scripted-owned-endpoint')
            (root/'server-ready-private.json').write_text(json.dumps(dict(connection=connection)))
            with patch('sss.adapters.cow_evaluation.cow_gpu_admission',side_effect=AssertionError('No GPU lease before endpoint proof')):
                with self.assertRaisesRegex(ValueError,'endpoint.*in use'):
                    with reopened_server(panel,PROFILE,root,recovery,storage=panel.config['storage'],
                            allow_crashed_server=True,producer_identities=[identity]):pass
            self.assertFalse((recovery/'crashed-server-retirement-private.json').exists())

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--fixture':make_failed_child(sys.argv[2],sys.argv[3])
    else:unittest.main()
