import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from sss.adapters.cow_evaluation import validate_profile, token_completion, runtime_binding, shared_input_prefix


class CowEvaluationTests(unittest.TestCase):
    def test_common_input_prefix_is_exact_detached_and_never_includes_a_question_suffix(self):
        inputs = [[1, 2, 3], [1, 2, 4, 5], [1, 2]]
        prefix = shared_input_prefix(inputs)
        self.assertEqual(prefix, [1, 2])
        prefix.append(9)
        self.assertEqual(inputs[0], [1, 2, 3])
        self.assertEqual(shared_input_prefix([[1], [2]]), [])
        with self.assertRaises(ValueError): shared_input_prefix([[True], [1]])
        with self.assertRaises(ValueError): shared_input_prefix([[]])

    def profile(self):
        return dict(model_path='/tmp/model.gguf', model_weights_sha256='a'*64,
                    execution=dict(capacity=512, prefill_chunk=512,
                                   eos_tokens=[1, 9], GPU=[4], device_binding='cuda-single-device-v1'))

    def validate(self, profile):
        validate_profile(profile, model='/tmp/model.gguf', model_sha256='a'*64,
                         gpu_uuid='GPU-test', context_tokens=512, batch_tokens=512,
                         stop_token_ids=[1, 9], hardware_row=['4', 'GPU-test', '30000', '0'])

    def test_exact_policy_and_physical_gpu(self):
        self.validate(self.profile())
        for key, value in [('capacity', 1024), ('prefill_chunk', 128),
                           ('eos_tokens', [1]), ('GPU', [3])]:
            profile = self.profile(); profile['execution'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate(profile)
        profile = self.profile(); profile['model_weights_sha256'] = 'b'*64
        with self.assertRaises(ValueError): self.validate(profile)

    def test_preserves_sampled_eos_multiline_and_cow_receipt(self):
        receipt = dict(tokens=[2, 3, 9], stop_reason='eos', stop_token_id=9,
                       counters=dict(consumed_tokens=8, forward_calls=4), snapshot='s-final')
        session = SimpleNamespace(profile=self.profile(), complete=Mock(return_value=receipt))
        tok = SimpleNamespace(decode=Mock(return_value='first\nsecond'))
        result = token_completion(session, tok, [4, 5, 6, 7, 8], maximum=16,
                                  stop_token_ids=[1, 9], stream='case-1')
        session.complete.assert_called_once_with([4, 5, 6, 7, 8], maximum=16, stream='case-1')
        tok.decode.assert_called_once_with([2, 3])
        self.assertEqual(result['text'], 'first\nsecond')
        self.assertEqual(result['sampled_token_ids'], [2, 3, 9])
        self.assertIs(result['cow_receipt'], receipt)

    def test_does_not_strip_length_cutoff_or_retry_failure(self):
        receipt = dict(tokens=[2, 3], stop_reason='length', stop_token_id=None,
                       counters=dict(consumed_tokens=7, forward_calls=3))
        session = SimpleNamespace(profile=self.profile(), complete=Mock(return_value=receipt))
        tok = SimpleNamespace(decode=Mock(return_value='unfinished'))
        token_completion(session, tok, [4], maximum=2, stop_token_ids=[1, 9], stream='case-2')
        tok.decode.assert_called_once_with([2, 3])
        session.complete = Mock(side_effect=RuntimeError('native boundary failed'))
        with self.assertRaises(RuntimeError):
            token_completion(session, tok, [4], maximum=2, stop_token_ids=[1, 9], stream='case-3')
        self.assertEqual(session.complete.call_count, 1)

    def test_refuses_changed_stops_before_execution(self):
        session = SimpleNamespace(profile=self.profile(), complete=Mock())
        with self.assertRaises(ValueError):
            token_completion(session, None, [4], maximum=2, stop_token_ids=[1], stream='case-4')
        session.complete.assert_not_called()

    def test_runtime_can_compare_candidates_but_preserves_math_changes(self):
        first = self.profile()
        first.update(backend='llama-dense-llama.cpp', native_build={'sha256': {'bridge': 'x'}})
        first['execution']['environment'] = {'CUDA_VISIBLE_DEVICES': '4', 'NVIDIA_TF32_OVERRIDE': '0'}
        import copy
        second = copy.deepcopy(first)
        second.update(model_path='/tmp/next.gguf', model_weights_sha256='b'*64)
        second['execution'].update(GPU=[5], environment={'CUDA_VISIBLE_DEVICES': '5', 'NVIDIA_TF32_OVERRIDE': '0'})
        self.assertEqual(runtime_binding(first), runtime_binding(second))
        second['execution']['environment']['NVIDIA_TF32_OVERRIDE'] = '1'
        self.assertNotEqual(runtime_binding(first), runtime_binding(second))


if __name__ == '__main__': unittest.main()
