"""Frozen artifact-repair assessment definitions; no execution or lesson intake."""
import copy
from dataclasses import dataclass
import re

from sss.practice_oracle import AffineClampFoldCase
from sss.records import canonical, digest


@dataclass(frozen=True)
class ArtifactAssessmentCase:
    case: AffineClampFoldCase
    baseline_source: bytes
    skill_id: str
    gate: str
    source_mode: int = 0o644

    def __post_init__(self):
        if type(self.case) is not AffineClampFoldCase:
            raise ValueError('Closed installed artifact checker required')
        self.case.__post_init__()
        if (type(self.baseline_source) is not bytes or not 0<len(self.baseline_source)<=32768
                or type(self.skill_id) is not str
                or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',self.skill_id) is None
                or self.gate not in ('independent','composition','transfer_recovery')
                or type(self.source_mode) is not int or self.source_mode not in (0o600,0o644)):
            raise ValueError('Bounded original source, skill, mastery gate and mode required')
        self.baseline_source.decode('utf-8',errors='strict')

    def descriptor(self):
        self.__post_init__()
        return dict(schema=1,kind='sss.artifact-assessment-case.v1',split_role='development',
            case=dict(case_id=self.case.case_id,split_id=self.case.split_id,rows=self.case.rows),
            baseline_source=self.baseline_source.decode('utf-8'),source_mode=self.source_mode,
            skill_id=self.skill_id,gate=self.gate)

    @classmethod
    def from_descriptor(cls,value):
        fields={'schema','kind','split_role','case','baseline_source','source_mode','skill_id','gate'}
        if (type(value) is not dict or set(value)!=fields or type(value['schema']) is not int
                or value['schema']!=1 or value['kind']!='sss.artifact-assessment-case.v1'
                or value['split_role']!='development' or type(value['baseline_source']) is not str
                or type(value['case']) is not dict
                or set(value['case'])!={'case_id','split_id','rows'}):
            raise ValueError('Closed development assessment descriptor required')
        c=value['case']
        return cls(AffineClampFoldCase.install(c['case_id'],c['split_id'],c['rows']),
            value['baseline_source'].encode('utf-8',errors='strict'),value['skill_id'],value['gate'],value['source_mode'])

    @property
    def identity(self):return digest(self.descriptor())


def installed_cases(value):
    if type(value) is not list or not 1<=len(value)<=4096:
        raise ValueError('Explicit bounded frozen artifact cases required')
    result=[ArtifactAssessmentCase.from_descriptor(copy.deepcopy(row)) for row in value]
    if (len({c.identity for c in result})!=len(result)
            or len({c.case.case_id for c in result})!=len(result)):
        raise ValueError('Duplicate frozen assessment case')
    # Hidden oracle variations alone are not independent model questions.
    prompts={(c.baseline_source,c.source_mode) for c in result}
    if len(prompts)!=len(result):
        raise ValueError('Identical visible task is not multiple independent assessment cases')
    return result


def artifact_question(case):
    case.__post_init__()
    from sss.adapters.bw_verified_practice import TASK
    baseline=canonical(dict(path='task.py',mode=case.source_mode,
                            source=case.baseline_source.decode('utf-8'))).decode('utf-8')
    return (TASK+'\n\nReturn only canonical final-artifact-v1 JSON with exactly '
        'path="task.py", mode='+str(case.source_mode)+' and source containing the complete '
        'corrected UTF-8 file. Preserve its final newline. No Markdown fences or explanation.'
        '\n\nOriginal artifact:\n'+baseline)
