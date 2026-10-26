"""Actual BW tools/COW grammar/OS, scripted proposals only; no model training."""
from pathlib import Path
from contextlib import contextmanager
import json
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sss.artifact_assessment import ArtifactAssessmentCase
from sss.practice_oracle import AffineClampFoldCase
from sss.workflow_assessment import SENTINEL,workflow_question,observe_capture
from sss_integration.bw_verified_practice_cpu import BAD,GOOD,ROWS,captured_pair


class WorkflowAssessmentTests(unittest.TestCase):
    def test_exception_retires_actual_http_service_model_and_original_lease(self):
        from test_thinking_grammar import ThinkingTokenizer
        from serve.test_cow_grammar_canonical_flow import GrammarCPUBackend,_render,_encode
        from sss_integration.workflow_evaluate import native_server
        tokenizer=ThinkingTokenizer();closed=[];released=[]
        profile=dict(model_contract_id='a'*64,execution_profile_id='b'*64,model_weights_sha256='c'*64,
            model_path='/not-loaded-scripted-model',execution=dict(GPU=[0],
                resume_contract='identical-native-operators-v1',generated_operator='normal-verifier-decode',
                selected_token_protocol='consumed-selected-receipt-v1',sampling_protocol='full-vocab-min-p-u53-v2',
                native_request_protocol='consumed-greedy-ack-v1',prefill_chunk=16,capacity=131072,eos_tokens=[256]))
        class Scripted(GrammarCPUBackend):
            def close(self):closed.append(True);super().close()
        components=dict(tokenizer=tokenizer,render=_render,
            encode_rendered=lambda messages,rendered,add_generation_prompt:_encode(tokenizer,messages,rendered,add_generation_prompt),
            append_initial_user_suffix=lambda canonical,controller,content:tuple(tokenizer.encode('\nuser:'+content+'\nassistant:',parse_special=False)),
            append_user_suffix=lambda canonical,controller,content:tuple(tokenizer.encode('\nuser:'+content+'\nassistant:',parse_special=False)),
            initial_root_mode=lambda canonical,controller:'context_only' if controller=={'status':'idle'} else 'unsupported',
            renderer_id='d'*64)
        @contextmanager
        def scripted_lease(*args,**kwargs):
            try:yield {}
            finally:released.append(True)
        panel=SimpleNamespace(identity='e'*64,pcc=Path('/scripted-runtime'),config=dict(gpu_index=0,
            gpu_uuid='GPU-scripted',context_tokens=131072,batch_tokens=16,stop_token_ids=[256],
            minimum_free_mib=1,maximum_initial_utilization=100,
            storage=dict(cache_bytes=64<<20,staging_bytes=1<<20,minimum_free_bytes=1<<20)))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with (patch('sss_integration.workflow_evaluate.cow_gpu_admission',scripted_lease),
                  patch('context_time_travel.llama_dense_backend.LlamaDenseBackend',lambda *a,**k:Scripted(profile,tokenizer)),
                  patch('serve.cow_http.model_text_components',lambda *a,**k:components)):
                with self.assertRaisesRegex(RuntimeError,'injected body failure'):
                    with native_server(panel,profile,root) as connection:
                        raise RuntimeError('injected body failure')
            self.assertTrue(closed);self.assertEqual(released,[True])
            self.assertEqual(json.loads((root/'server-private.json').read_bytes()),dict(status='RETIRED',connection=connection))
            port=int(connection['endpoint_url'].rsplit(':',1)[1])
            with self.assertRaises(OSError):socket.create_connection(('127.0.0.1',port),timeout=1)

    def test_real_failed_and_finished_workflow_capture_and_no_dispatch_replay(self):
        self._capture_replay('gbnf')

    def test_lark_failed_and_finished_capture_and_no_dispatch_replay(self):
        self._capture_replay('lark')

    def _capture_replay(self,grammar_syntax):
        from branchwrite.coding_cli import read_launch
        from branchwrite.lesson_capture import capture_assessment,capture_failure
        case=ArtifactAssessmentCase(AffineClampFoldCase.install('workflow-cpu-01','assessment.workflow-cpu',ROWS),
            BAD,'code.repair.affine','composition')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with captured_pair(root/'bw',task_override=workflow_question(case),project_sentinel=SENTINEL,extra_check_file=True,grammar_syntax=grammar_syntax) as pair:
                failed=capture_assessment(pair['failed_state'],root/'failed-archive')
                fixed=capture_assessment(pair['corrected_state'],root/'fixed-archive')
                failed_launch=read_launch(pair['failed_state']);fixed_launch=read_launch(pair['corrected_state'])
                left,left_source=observe_capture(case,failed,failed_launch)
                right,right_source=observe_capture(case,fixed,fixed_launch)
                self.assertFalse(left['finished']);self.assertEqual(left_source,BAD)
                self.assertTrue(right['finished']);self.assertTrue(right['read_edit_check_finish'])
                self.assertEqual(right_source,GOOD);self.assertGreater(right['native_receipts'],0)
                self.assertIn('create_text_file',right['tools'])
                self.assertIn('set_mode',right['tools'])
                self.assertEqual(fixed.file_bytes('check_notes.py'),b'# Owned helper; independent artifact grading remains separate.\n')
                pair['project'].rename(root/'retired-project')
            with patch('subprocess.Popen',side_effect=AssertionError('no dispatch')):
                self.assertEqual(observe_capture(case,fixed,fixed_launch),(right,GOOD))
            # A failure archive is not a standalone assessment, even when valid.
            with self.assertRaisesRegex(ValueError,'standalone'):
                observe_capture(case,pair['failure'],failed_launch)
            # A passing host workflow does not establish semantic correctness.
            self.assertFalse(left['host_verified']);self.assertTrue(right['host_verified'])


if __name__=='__main__':unittest.main()
