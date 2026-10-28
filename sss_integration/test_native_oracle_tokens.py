"""Optional NumPy token-protocol checks; no native/model execution."""
import io,struct,unittest
from types import SimpleNamespace
from unittest.mock import patch
from sss.adapters import native_oracle

def logits(values):return struct.pack('<'+'f'*len(values),*values)
class TokenProtocolTests(unittest.TestCase):
 def test_exact_prefix_eos_and_multiline_response_are_preserved(self):
  proc=SimpleNamespace(stdin=io.BytesIO());tok=SimpleNamespace(tokens=list(range(5)),decode=lambda ids:'A\n' if ids==[0] else 'bad')
  frames=[struct.pack('<iQi',5,2,1),logits([9,0,0,0,0]),struct.pack('<iQi',5,3,2),logits([0,0,0,0,9])]
  prefix=[2,3]
  with patch.object(native_oracle,'receive',side_effect=frames):result=native_oracle.token_completion(proc,tok,prefix,maximum=4,context_tokens=128,batch_tokens=128,stop_token_ids=[4])
  self.assertEqual(prefix,[2,3]);self.assertEqual(result['text'],'A\n');self.assertEqual(result['sampled_token_ids'],[0,4]);self.assertEqual(result['stop_reason'],'eos');self.assertEqual(result['prefill_tokens'],5)
  self.assertEqual(proc.stdin.getvalue(),b'F 128 2 2 3\nF 128 3 2 3 0\n')
 def test_bad_work_receipt_and_nonfinite_logits_are_infrastructure_errors(self):
  tok=SimpleNamespace(tokens=list(range(5)),decode=lambda ids:'')
  for frames in [[struct.pack('<iQi',5,1,0)],[struct.pack('<iQi',5,2,1),logits([float('nan'),0,0,0,0])]]:
   with patch.object(native_oracle,'receive',side_effect=frames),self.assertRaises(ValueError):native_oracle.token_completion(SimpleNamespace(stdin=io.BytesIO()),tok,[2,3],maximum=4,context_tokens=128,batch_tokens=128,stop_token_ids=[4])
 def test_context_refusal_precedes_any_model_request(self):
  proc=SimpleNamespace(stdin=io.BytesIO());tok=SimpleNamespace(tokens=list(range(5)),decode=lambda ids:'')
  with self.assertRaises(ValueError):native_oracle.token_completion(proc,tok,[2]*126,maximum=4,context_tokens=128,batch_tokens=128,stop_token_ids=[4])
  self.assertEqual(proc.stdin.getvalue(),b'')

if __name__=='__main__':unittest.main()
