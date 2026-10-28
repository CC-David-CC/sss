"""Closed owner factory joining real assessments and exact mixed practice.

PCC owns jobs, workers and training. BW owns effects. This installs the existing
S³ panels/providers; a student request selects installed identities only.
"""
import copy
import hashlib
from pathlib import Path
import re

from sss.adapters.owner_configuration import read_private_json
from sss.adapters.learning_panels import LearningPanelEvaluator,PanelLearningPolicy
from sss.records import canonical,digest,file_sha256

KIND='sss.learning-stack.v1'
NAME=re.compile(r'[a-z][a-z0-9_-]{0,63}\Z')
POLICY_FIELDS={'title','training','max_rounds','assessment_purpose','minimum_skill_cases'}
PANEL_KINDS={'cow-artifact':'target','bw-workflow':'workflow','cow-foundations':'retention'}


def _name(value):return type(value)is str and NAME.fullmatch(value)is not None


def _configuration(value):
    fields={'schema','kind','panels','practice','practice_mix','policies'}
    if (type(value)is not dict or set(value)!=fields or type(value['schema'])is not int
            or value['schema']!=1 or value['kind']!=KIND):
        raise ValueError('Closed owner learning-stack configuration required')
    for name,minimum,maximum in [('panels',3,32),('practice',2,32),('policies',1,8)]:
        if type(value[name])is not list or not minimum<=len(value[name])<=maximum:
            raise ValueError('Bounded explicit learning-stack entries required')
    names=set()
    for row in value['panels']:
        if (type(row)is not dict or set(row)!={'panel_id','role','kind','configuration'}
                or not _name(row['panel_id']) or row['panel_id']in names
                or type(row['kind'])is not str or row['kind']not in PANEL_KINDS
                or row['role']!=PANEL_KINDS[row['kind']]
                or type(row['configuration'])is not str or not Path(row['configuration']).is_absolute()):
            raise ValueError('Exact known panel kind, role, name and owner configuration required')
        names.add(row['panel_id'])
    if {r['role']for r in value['panels']}!={'target','workflow','retention'}:
        raise ValueError('Real target, workflow and retention roles are all required')
    providers=set()
    for row in value['practice']:
        if type(row)is not dict or not _name(row.get('provider_id'))or row['provider_id']in providers:
            raise ValueError('Unique installed practice provider required')
        providers.add(row['provider_id'])
        kind=row.get('kind')
        if kind=='bw-verified':
            if (set(row)!={'provider_id','role','kind','configuration'}or row['role']!='target'
                    or type(row['configuration'])is not str or not Path(row['configuration']).is_absolute()):
                raise ValueError('Exact owner-approved BW target practice registry required')
        elif kind=='foundation-practice':
            if (set(row)!={'provider_id','role','kind','panel_id'}or row['role']!='review'
                    or row['panel_id']not in names
                    or next(r['kind']for r in value['panels']if r['panel_id']==row['panel_id'])!='cow-foundations'):
                raise ValueError('Foundation review must name an installed foundations panel')
        else:raise ValueError('Unknown practice provider; modules and client-supplied checkers are unsupported')
    if {r['role']for r in value['practice']}!={'target','review'}:
        raise ValueError('Target practice and mixed review must both be installed')
    mix=value['practice_mix']
    if (type(mix)is not dict or set(mix)!={'minimum_target_lessons','minimum_review_lessons'}
            or any(type(n)is not int or not 0<=n<=4096 for n in mix.values())or not any(mix.values())):
        raise ValueError('Explicit bounded target/review lesson minima required')
    for row in value['policies']:
        if (type(row)is not dict or set(row)!=POLICY_FIELDS
                or row['assessment_purpose']not in ('machinery','adaptive_learning')
                or type(row['training'])is not dict
                or type(row['training'].get('batch_size'))is not int
                or row['training']['batch_size']<sum(mix.values())):
            raise ValueError('Explicit learning recipe, feasible practice mix and assessment purpose required')
    return value


class FoundationPractice:
    """Read only the verified practice partition of an installed COW panel."""
    def __init__(self,evaluator):
        self.evaluator=evaluator
        self._bound=copy.deepcopy(evaluator.binding())
        self._lessons=copy.deepcopy(evaluator.allowed_lessons)
        self._binding=dict(schema=1,kind='sss.foundation-review-provider.v1',
            model_contract_id=evaluator.model_contract,evaluator=self._bound,
            checked_practice_lesson_ids=sorted(self._lessons),implementation_sha256=file_sha256(__file__))
        self.verify()

    def binding(self):return copy.deepcopy(self._binding)

    def verify(self):
        self.evaluator.verify()
        if (canonical(self.evaluator.binding())!=canonical(self._bound)
                or self.evaluator.allowed_lessons!=self._lessons
                or file_sha256(__file__)!=self._binding['implementation_sha256']):
            raise ValueError('Installed foundation review source/membership changed')

    def lessons(self):
        self.verify();return [copy.deepcopy(self._lessons[k])for k in sorted(self._lessons)]

    def validate_lessons(self,records,previous_report=None):
        self.verify();self.evaluator.validate_lessons(records,previous_report)


class InstalledLearningPanels(LearningPanelEvaluator):
    def __init__(self,panels,providers,*,model_contract_id,documents,roles,mix):
        self._documents=copy.deepcopy(documents);self._practice_roles=copy.deepcopy(roles)
        self._mix=copy.deepcopy(mix)
        pins={path:sha for path,sha in documents.items()}
        pins[str(Path(__file__).resolve())]=file_sha256(__file__)
        reader=Path(read_private_json.__code__.co_filename).resolve();pins[str(reader)]=file_sha256(reader)
        super().__init__(panels,providers,model_contract_id=model_contract_id,installation_files=pins)

    def verify(self):
        for name,expected in self._documents.items():
            _,raw,_=read_private_json(name)
            if hashlib.sha256(raw).hexdigest()!=expected:
                raise ValueError('Owner learning-stack configuration changed; install a new policy')
        super().verify()

    def validate_lessons(self,records,previous_report):
        super().validate_lessons(records,previous_report)
        counts={'target':0,'review':0}
        for record in records:counts[self._practice_roles[self._owners[record['lesson_id']]]]+=1
        if any(counts[role]<self._mix['minimum_'+role+'_lessons']for role in counts):
            raise ValueError('Selected practice omits the owner-required target/review mix')


class StackLearningPolicy(PanelLearningPolicy):
    def validate_lessons(self,records,previous_report):
        super().validate_lessons(records,previous_report)
        # Existing native training walks this dataset. Include every selected
        # example in the first batch rather than approving unused review rows.
        if len(records)>self.training['batch_size']:
            raise ValueError('Each selected lesson must fit in the native training batch')


def configured_learning_stack(path,native,serving_profile,tokenizer):
    documents={}
    def read(name):
        selected,raw,value=read_private_json(name)
        documents[str(selected)]=hashlib.sha256(raw).hexdigest()
        return value
    config=_configuration(read(path))
    # Only the owner can install these concrete adapter kinds. Validate the
    # whole schema before importing optional BW/PCC components or opening models.
    from sss.adapters.cow_learning import CowLearningEvaluator
    from sss.adapters.artifact_evaluation import CowArtifactEvaluator
    from sss.adapters.workflow_evaluation import BWWorkflowEvaluator
    from sss.adapters.verified_practice_registry import InstalledBWPractice
    from serve.cow_http import model_text_components
    model=Path(native.config['model']).resolve(strict=True)
    if (Path(serving_profile['model_path']).resolve(strict=True)!=model
            or serving_profile['model_weights_sha256']!=native.config['base_sha256']):
        raise ValueError('Training and serving must name this exact immutable base')
    panels=[];by_name={}
    for row in config['panels']:
        installed=read(row['configuration'])
        if row['kind']=='cow-foundations':
            panel=CowLearningEvaluator(installed,native,serving_profile,tokenizer)
        else:
            cls=CowArtifactEvaluator if row['kind']=='cow-artifact'else BWWorkflowEvaluator
            panel=cls(row['configuration'])
        if panel.base!=native.config['base_sha256']or panel.model!=model:
            raise ValueError('Every panel must assess the exact training base and its candidates')
        panels.append((row['panel_id'],row['role'],panel));by_name[row['panel_id']]=panel
    components=model_text_components(model,dict(enable_thinking=False),
        model_contract_id=serving_profile['model_contract_id'],tokenizer=tokenizer)
    providers=[];roles={}
    protected={hashlib.sha256(case.baseline_source).hexdigest()
        for _,_,panel in panels for case in getattr(panel,'cases',[])}
    for row in config['practice']:
        if row['kind']=='bw-verified':
            read(row['configuration'])
            provider=InstalledBWPractice(row['configuration'],components=components,
                model_contract_id=serving_profile['model_contract_id'])
            # Hidden-oracle variants do not make the identical visible repair a
            # new practice task. Reject exact source overlap before installation.
            for registration in provider.binding()['registrations']:
                if registration['owner']['baseline_source_sha256']in protected:
                    raise ValueError('Protected assessment source cannot become practice')
        else:provider=FoundationPractice(by_name[row['panel_id']])
        providers.append((row['provider_id'],provider));roles[row['provider_id']]=row['role']
    evaluator=InstalledLearningPanels(panels,providers,model_contract_id=serving_profile['model_contract_id'],
        documents=documents,roles=roles,mix=config['practice_mix'])
    policies={}
    for row in config['policies']:
        policy=StackLearningPolicy(evaluator,**copy.deepcopy(row));identity=digest(policy.describe())
        if identity in policies:raise ValueError('Duplicate installed learning policy')
        policies[identity]=policy
    return policies
