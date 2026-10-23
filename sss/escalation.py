"""Independent difficulty coordinates and pure recommendations; no job authority."""
from dataclasses import dataclass,asdict
from .records import digest

@dataclass(frozen=True)
class Difficulty:
    composition_depth:int=1
    context_tokens:int=2048
    environment_complexity:int=0
    autonomy:int=0
    def __post_init__(self):
        if any(type(v) is not int for v in asdict(self).values()):raise ValueError('Integer difficulty coordinates required')
        if not 1<=self.composition_depth<=1024 or not 1<=self.context_tokens<=1048576 or not 0<=self.environment_complexity<=4 or not 0<=self.autonomy<=3:raise ValueError('Difficulty outside declared curriculum')
    @property
    def identity(self):return digest(asdict(self))
    def advance(self,axis,value):
        if axis not in asdict(self) or value<=getattr(self,axis):raise ValueError('Choose one increasing coordinate')
        return Difficulty(**dict(asdict(self),**{axis:value}))

def recommendation(graph,skill,profile,cell,assessment,qualified_prerequisites,*,supported_cells):
    readiness=graph.readiness(skill,qualified_prerequisites)
    expected=dict(graph_id=graph.identity,skill_id=skill,profile_id=profile,band=cell.identity)
    if any(assessment.get(k)!=v for k,v in expected.items()):raise ValueError('Assessment belongs to another skill, profile or difficulty cell')
    qualified=assessment.get('status')=='qualified' and assessment.get('qualified') is True
    if not readiness['ready']:action='prerequisites'
    elif cell.identity not in supported_cells:action='coverage_unavailable'
    elif qualified:action='eligible_for_one_axis_probe'
    elif assessment.get('status')=='regressed':action='retention_repair'
    elif assessment.get('status') in ('unavailable','insufficient_evidence'):action='resolve_evidence_gap'
    else:action='practice_current_cell'
    return dict(**expected,action=action,automatically_qualified_next_cell=False,weights_updated=False,execution_authorized=False)
