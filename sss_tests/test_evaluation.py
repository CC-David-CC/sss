import tempfile,unittest
from pathlib import Path
from sss.evaluation import freeze,evaluate
from sss.profiles import ModelProfile
from sss.foundations import reference

class EvaluationTests(unittest.TestCase):
    def profile(self):return ModelProfile('fixture','v1','bytes','owned','reference','v1')
    def test_perfect_small_probe_cannot_claim_qualification(self):
        with tempfile.TemporaryDirectory() as root:
            frozen=freeze(Path(root)/'run',self.profile(),['math.add.carry'])
            answers={e.prompt:reference(e) for e in frozen[2].values()}
            def model(messages,tools,intent):
                intent.write_text('owned reference call')
                return dict(content=answers[messages[-1]['content']]),{}
            result=evaluate(frozen,model)
            self.assertFalse(result['assessments'][0]['qualified'])
            self.assertEqual(result['assessments'][0]['gates']['independent']['passed'],3)
            with self.assertRaises(FileExistsError):evaluate(frozen,model)
    def test_uncertain_endpoint_is_not_retried(self):
        with tempfile.TemporaryDirectory() as root:
            frozen=freeze(Path(root)/'run',self.profile(),['math.place_value']);calls=[]
            def model(messages,tools,intent):calls.append(messages);raise TimeoutError('owned injected uncertainty')
            result=evaluate(frozen,model)
            self.assertEqual(len(calls),9)
            self.assertEqual(result['assessments'][0]['status'],'unavailable')
