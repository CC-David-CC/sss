"""Optional owner-installed PCC learning policy; S3 owns scores and decisions."""
import copy
from pathlib import Path
from sss.records import digest, file_sha256
from sss.learning import next_skill_block
from sss.paired import compare_frozen_evaluations, POLICY
from sss.assessment_growth import plan as growth_plan, PURPOSES


class LearningPolicy:
    """PCC owns durable rounds; this adapter supplies no workflow runtime."""
    def __init__(self,evaluator,training,*,title,max_rounds,assessment_purpose="adaptive_learning",minimum_skill_cases=96):
        if assessment_purpose not in PURPOSES or type(minimum_skill_cases) is not int or not 3<=minimum_skill_cases<=1000000:
            raise ValueError('Explicit assessment purpose and bounded skill coverage required')
        self.assessment=dict(purpose=assessment_purpose,minimum_skill_cases=minimum_skill_cases)
        self.evaluator=evaluator
        self.training=copy.deepcopy(training);self.title=title;self.max_rounds=max_rounds
        self.sources={str(Path(__file__).resolve()):file_sha256(__file__),
            str(Path(next_skill_block.__code__.co_filename).resolve()):file_sha256(next_skill_block.__code__.co_filename),
            str(Path(compare_frozen_evaluations.__code__.co_filename).resolve()):file_sha256(compare_frozen_evaluations.__code__.co_filename),
            str(Path(growth_plan.__code__.co_filename).resolve()):file_sha256(growth_plan.__code__.co_filename)}
        self.adapter=digest(dict(evaluator=evaluator.binding(),sources=self.sources))

    def describe(self):
        return dict(schema=1,title=self.title,adapter_id=self.adapter,
            training=copy.deepcopy(self.training),max_rounds=self.max_rounds,assessment=copy.deepcopy(self.assessment))

    def verify(self):
        for path,expected in self.sources.items():
            if file_sha256(path)!=expected:raise ValueError('Learning analysis source changed')
        if self.adapter!=digest(dict(evaluator=self.evaluator.binding(),sources=self.sources)):
            raise ValueError('Learning evaluator binding changed')
        self.evaluator.verify()

    def evaluate(self,candidate,path,worker_fd):return self.evaluator(candidate,path,worker_fd)

    def recover_evaluation(self,candidate,path):
        recover=getattr(self.evaluator,'recover',None)
        return recover(candidate,path) if callable(recover) else None

    def validate_evaluation(self,value,candidate):
        compare_frozen_evaluations(value,value,POLICY)
        self.evaluator.validate(value,candidate)

    def validate_lessons(self,lessons,previous_report):
        self.evaluator.validate_lessons(lessons,previous_report)

    def analyze(self,baseline,parent,candidate):
        proposal=next_skill_block(baseline,parent,candidate)
        return dict(working_parent='parent' if proposal['working_decision']=='RETAIN_PARENT' else 'candidate',report=proposal,
            assessment=growth_plan(candidate,**self.assessment))
