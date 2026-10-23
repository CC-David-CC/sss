"""Explicit model/context/target policies. Profiles never acquire resources."""
from dataclasses import asdict, dataclass
from .records import digest

@dataclass(frozen=True)
class ContextPolicy:
    maximum: int=131072
    compact_at: int=98304
    target: int=32768
    def __post_init__(self):
        if any(type(v) is not int for v in (self.maximum,self.compact_at,self.target)) or not 0<self.target<self.compact_at<self.maximum:
            raise ValueError('Require target < compaction trigger < total context maximum')
    def check(self, current, output_reserve, anticipated_input=0):
        if any(type(v) is not int or v<0 for v in (current,output_reserve,anticipated_input)):
            raise ValueError('Token counts must be explicit nonnegative integers')
        projected=current+anticipated_input+output_reserve
        return dict(projected_tokens=projected,admitted=projected<=self.maximum,
                    compact_required=current+anticipated_input>=self.compact_at or projected>self.maximum)

@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    model_revision: str
    tokenizer_id: str
    template_id: str
    harness_id: str
    harness_revision: str
    thinking: str='off'
    tool_mode: str='direct'
    retrieval: str='self'
    context: ContextPolicy=ContextPolicy()
    def __post_init__(self):
        for value in (self.model_id,self.model_revision,self.tokenizer_id,self.template_id,self.harness_id,self.harness_revision):
            if type(value) is not str or not value or len(value)>1024:raise ValueError('Explicit pinned model and harness identities required')
        if self.thinking not in ('on','off'):raise ValueError('Explicit supported thinking mode required')
        if self.tool_mode not in ('direct','assisted'):raise ValueError('Unknown tool mode')
        if self.retrieval not in ('self','assisted'):raise ValueError('Unknown retrieval mode')
        if not isinstance(self.context,ContextPolicy):raise ValueError('Expected ContextPolicy')
    @property
    def identity(self):return digest(asdict(self))

TARGET_POLICIES=('verified_thinking_actions_answer','actions_answer')

def target_segments(segments, policy=TARGET_POLICIES[0]):
    if policy not in TARGET_POLICIES:raise ValueError('Unknown target policy')
    result=[]
    for segment in segments:
        if segment['role'] not in ('system','user','assistant','tool'):raise ValueError('Unknown role')
        if segment['kind'] not in ('instruction','question','observation','thinking','action','answer','summary'):
            raise ValueError('Unknown segment kind')
        assistant=segment['role']=='assistant'
        if segment['kind'] in ('thinking','action','answer','summary') and not assistant:
            raise ValueError('Assistant segment has another role')
        selected=assistant and segment['kind'] in ('thinking','action','answer','summary')
        if segment['kind']=='thinking' and policy=='actions_answer':selected=False
        if selected and segment.get('verified') is not True:raise ValueError('Unverified assistant segment cannot be a target')
        result.append(selected)
    if not any(result):raise ValueError('No approved training targets')
    return result
