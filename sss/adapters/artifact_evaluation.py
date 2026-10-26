"""Optional real COW artifact panel with BW's independent execution checker.

PCC still owns the model, GPU lease, consumed requests and original worker.
This panel reuses the existing CowLearningEvaluator dispatch/recovery methods.
It measures protected development cases and never supplies training lessons.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

from sss.artifact_assessment import installed_cases,artifact_question
from sss.adapters.cow_learning import CowLearningEvaluator,write_once
from sss.adapters.cow_evaluation import candidate_binding,runtime_binding,shared_input_prefix
from sss.paired import compare_frozen_evaluations,POLICY
from sss.records import canonical,digest,file_sha256


class CowArtifactEvaluator(CowLearningEvaluator):
    panel_kind='sss.cow-artifact-evaluator.v1'
    child_module='sss_integration.artifact_evaluate'
    finished_means='native EOS; independently checked artifact correctness reported separately'

    def _configuration_fields(self):
        return set()

    def _validate_configuration(self,config):
        pass

    def _extra_source_paths(self):
        return []

    def __init__(self,configuration):
        self.configuration=Path(configuration).absolute()
        if self.configuration.is_symlink() or not self.configuration.is_file():
            raise ValueError('Original owner configuration must be a regular file')
        raw=self.configuration.read_bytes();config=json.loads(raw)
        configuration_sha256=hashlib.sha256(raw).hexdigest()
        required={'schema','pcc_root','bw_root','cow_profile','runtime_proof','cases',
            'gpu_index','gpu_uuid','maximum_tokens','minimum_free_mib',
            'maximum_initial_utilization','timeout_seconds'}
        required |= self._configuration_fields()
        if (type(config) is not dict or set(config)!=required or type(config['schema']) is not int
                or config['schema']!=1):raise ValueError('Closed owner artifact evaluator configuration required')
        for key in ('pcc_root','bw_root','cow_profile','runtime_proof','cases'):
            if type(config[key]) is not str or not Path(config[key]).is_absolute():
                raise ValueError('Absolute installed runtime/input paths required')
        for key in ('gpu_index','maximum_tokens','minimum_free_mib','maximum_initial_utilization','timeout_seconds'):
            if type(config[key]) is not int:raise ValueError('Explicit integer artifact evaluation limits required')
        if (config['gpu_index']<0 or not 1<=config['maximum_tokens']<=4096
                or config['minimum_free_mib']<1 or not 0<=config['maximum_initial_utilization']<=100
                or not 1<=config['timeout_seconds']<=14400 or type(config['gpu_uuid']) is not str
                or not config['gpu_uuid'].startswith('GPU-')):
            raise ValueError('Bounded explicit owner limits and physical GPU required')
        self._validate_configuration(config)
        self.pcc=Path(config['pcc_root']).resolve(strict=True)
        self.bw=Path(config['bw_root']).resolve(strict=True)
        self.sss=Path(__file__).resolve().parents[2]
        self.template=json.loads(Path(config['cow_profile']).read_bytes())
        if self.template.get('adapter') is not None or self.template['execution'].get('adapter') is not None:
            raise ValueError('An unattached original COW base profile is required')
        self.model=Path(self.template['model_path']).resolve(strict=True)
        self.base=self.template['model_weights_sha256'];self.model_contract=self.template['model_contract_id']
        self.config=copy.deepcopy(config)
        self.config.update(context_tokens=self.template['execution']['capacity'],
            batch_tokens=self.template['execution']['prefill_chunk'],
            stop_token_ids=self.template['execution']['eos_tokens'])
        if (type(self.config['context_tokens']) is not int or not 1<=self.config['context_tokens']<=131072
                or type(self.config['batch_tokens']) is not int
                or not 1<=self.config['batch_tokens']<=self.config['context_tokens']):
            raise ValueError('Bounded explicit native context and batch required')
        from tools.pcc_cow_profile import bind_dense_profile
        # Parent and execution child may live in separate qualified PCC trees.
        # Their profile binder must nevertheless be the identical implementation.
        if file_sha256(bind_dense_profile.__code__.co_filename)!=file_sha256(self.pcc/'tools/pcc_cow_profile.py'):
            raise ValueError('Installed PCC profile binding differs from execution runtime')
        from serve.cow_http import model_text_components
        self.host_pcc=Path(model_text_components.__code__.co_filename).resolve(strict=True).parents[1]
        from sss.adapters.bw_verified_practice import PCCArtifactRenderer
        components=model_text_components(self.model,dict(enable_thinking=False),model_contract_id=self.model_contract)
        from sss.adapters.runtime_sources import rendering_sources
        rendering_paths=rendering_sources(components,model_text_components)
        self.decoder=components['tokenizer'];self.encoder=components['render'].__self__
        self.renderer=PCCArtifactRenderer(components,model_contract_id=self.model_contract,
            tokenizer_sha256=PCCArtifactRenderer.tokenizer_identity(components),
            maximum_tokens=self.config['context_tokens'],stop_token_ids=self.config['stop_token_ids'])
        cases_raw=Path(config['cases']).read_bytes()
        self.cases=installed_cases(json.loads(cases_raw))
        self.case_index={case.identity:(case.skill_id,case.gate) for case in self.cases}
        self._prepare_inputs()
        build_path=Path(config['runtime_proof']);self.build=json.loads(build_path.read_bytes())
        if (type(self.build.get('sha256')) is not dict
                or self.template['bridge_library'] not in self.build['sha256']):
            raise ValueError('Existing qualified native bridge proof required')
        files=[self.configuration,Path(config['cow_profile']),build_path,Path(config['cases']),
            Path(__file__),self.sss/'sss/artifact_assessment.py',
            self.sss/(self.child_module.replace('.','/')+'.py'),
            self.sss/'sss/adapters/cow_evaluation.py',self.sss/'sss/adapters/cow_learning.py',
            self.sss/'sss/adapters/bw_verified_practice.py',self.sss/'sss/adapters/bw_practice_oracle.py',
            self.sss/'sss/practice_oracle.py',self.sss/'sss/adapters/code_check.py',
            self.sss/'sss/paired.py',self.sss/'sss/records.py',
            *sorted((self.bw/'branchwrite').glob('*.py')),*self._extra_source_paths(),
            self.sss/'sss/adapters/runtime_sources.py',*rendering_paths]
        self.pins={str(p):file_sha256(p) for p in files};self.pins.update(self.build['sha256'])
        self.pins[str(self.configuration)]=configuration_sha256
        self.pins[str(Path(config['cases']))]=hashlib.sha256(cases_raw).hexdigest()
        self._binding=dict(schema=1,kind=self.panel_kind,
            model_contract_id=self.model_contract,evaluation_id=self.evaluation_id,
            configuration=copy.deepcopy(config),sources_and_inputs_sha256=copy.deepcopy(self.pins),
            renderer=self.renderer.binding(),checked_practice_lesson_ids=[],
            finished_means=self.finished_means,
            shared_prefix_tokens=len(self.prefix),no_implicit_retry=True)
        self.identity=digest(self._binding);self.verify()

    def _prepare_inputs(self):
        from serve.server import Service
        from sss.adapters.bw_verified_practice import SYSTEM
        self.prefixes=[Service.encode_prompt(self.encoder,[dict(role='system',content=SYSTEM),
            dict(role='user',content=artifact_question(case))],None,
            dict(enable_thinking=False,add_generation_prompt=True)) for case in self.cases]
        if any(len(p)+self.config['maximum_tokens']>self.config['context_tokens'] for p in self.prefixes):
            raise ValueError('Original artifact assessment and full output allowance must fit context')
        self.prefix=shared_input_prefix(self.prefixes)
        if not self.prefix:raise ValueError('Artifact panel needs a real shared input prefix')
        self.evaluation_id=digest(dict(kind='sss.artifact-assessment.v1',
            cases=[c.descriptor() for c in self.cases],prefixes=self.prefixes))

    def verify(self):
        from tools.pcc_cow_evaluation import verify_sources
        if file_sha256(self.model)!=self.base:raise ValueError('Original artifact base changed')
        for path,expected in self.pins.items():
            if file_sha256(path)!=expected:raise ValueError('Installed artifact source/input changed: '+path)
        if digest(self._binding)!=self.identity:raise ValueError('Original artifact evaluator binding changed')
        self.renderer.verify();verify_sources(self.template,self.pcc)

    def validate_lessons(self,records,previous_report):
        raise ValueError('Protected artifact assessment supplies no practice lessons')

    def expected_runtime(self,profile):
        return dict(kind='sss.cow-artifact-runtime.v1',sources_and_inputs_sha256=self.pins,
            cow_runtime=runtime_binding(profile),maximum_tokens=self.config['maximum_tokens'],
            input_prefixes_sha256=digest(self.prefixes),checker='fixed BW isolated affine-clamp-fold oracle',
            output_representation='canonical-final-artifact-v1',finished='native-eos',greedy=True)

    def _command(self,directory,profile):
        return [sys.executable,'-m',self.child_module,
            '--owner-config',str(self.configuration),'--expected-evaluator-id',self.identity,
            '--profile',str(directory/'candidate-profile.json'),
            '--candidate',str(directory/'candidate-selection-private.json'),'--output',str(directory/'evaluation')]

    def _environment(self):
        return dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,[self.sss,self.host_pcc,self.pcc,
            self.pcc/'experimental/branching_context/src',self.bw])),PYTHONDONTWRITEBYTECODE='1')

    def __call__(self,candidate,directory,worker_fd):
        write_once(Path(directory)/'candidate-selection-private.json',copy.deepcopy(candidate))
        return super().__call__(candidate,directory,worker_fd)

    def _summary(self,value,candidate):
        compare_frozen_evaluations(value,value,POLICY)
        profile=self.profile(candidate)
        if (value['evaluation_id']!=self.evaluation_id
                or value['runtime_id']!=digest(self.expected_runtime(profile))
                or value['model_sha256']!=profile['model_weights_sha256']
                or any(canonical(value.get(k))!=canonical(v) for k,v in candidate_binding(profile).items())
                or {r['id']:(r['skill_id'],r['gate']) for r in value['outcomes']}!=self.case_index):
            raise ValueError('Artifact measurement identity/runtime/coverage changed')

    def validate(self,value,candidate):
        if type(value) is not dict or type(value.get('evidence_directory')) is not str:
            raise ValueError('Actual original artifact evidence directory required')
        recovered=self.recover(candidate,Path(value['evidence_directory']))
        if canonical(recovered)!=canonical(value):raise ValueError('Original artifact evidence differs')

    def _evidence(self,candidate,directory):
        from sss.adapters.bw_verified_practice import _extract,_oracle,PracticeExportRefused
        directory=Path(directory).absolute();self.verify();profile=self.profile(candidate)
        read=lambda p:json.loads(p.read_bytes())
        expected=dict(schema=1,evaluator_id=self.identity,profile=profile,
            command=self._command(directory,profile),no_implicit_retry=True)
        if (canonical(read(directory/'adapter-intent-private.json'))!=canonical(expected)
                or canonical(read(directory/'candidate-profile.json'))!=canonical(profile)
                or canonical(read(directory/'candidate-selection-private.json'))!=canonical(candidate)):
            raise ValueError('Original artifact dispatch changed')
        root=directory/'evaluation';value=read(root/'result.json');settled=read(root/'settlement.json')
        if canonical(read(root/'intent-private.json'))!=canonical(dict(evaluator_id=self.identity,
                profile=profile,prefixes_sha256=digest(self.prefixes),candidate=candidate,training=False)):
            raise ValueError('Original artifact child intent changed')
        self._summary(value,candidate)
        if (value.get('evidence_directory')!=str(directory) or settled!=dict(schema=1,status='COMPLETE',
                completed_cases=len(self.cases),result_sha256=file_sha256(root/'result.json'),
                weights_updated=False,promoted=False)):
            raise ValueError('Original artifact settlement changed')
        for index,(case,prefix,row) in enumerate(zip(self.cases,self.prefixes,value['outcomes'])):
            observed=read(root/('%04d-private.json'%index));completion=observed['completion']
            tokens=completion['sampled_token_ids'];stops=self.config['stop_token_ids']
            stopped=completion['stop_reason']=='eos'
            if (not tokens or len(tokens)>self.config['maximum_tokens']
                    or any(type(t) is not int or t<0 for t in tokens)
                    or any(t in stops for t in tokens[:-1]) or stopped!=(tokens[-1] in stops)
                    or completion['stop_token_id']!=(tokens[-1] if stopped else None)
                    or completion['cow_receipt']['tokens']!=tokens
                    or completion['text']!=self.decoder.decode(tokens[:-1] if stopped else tokens)
                    or observed['prefix_sha256']!=digest(prefix)
                    or observed['outcome']!=row or row['finished']!=stopped
                    or (row['id'],row['skill_id'],row['gate'])!=(case.identity,case.skill_id,case.gate)):
                raise ValueError('Original artifact token/input/stopping evidence changed')
            oracle=root/('oracle-%04d'%index)
            try:source=_extract(completion['text'],case.source_mode)
            except (ValueError,UnicodeError):
                if observed['artifact_parse']!='invalid' or row['passed'] or oracle.exists():
                    raise ValueError('Malformed artifact did not retain its original refusal')
                continue
            status=read(oracle/'result-private.json')['status']
            proof=_oracle(case.case,source,oracle,status)
            if observed['artifact_parse']!='valid' or row['passed']!=(proof['status']=='pass'):
                raise ValueError('Original isolated artifact grade differs')
        self.verify();return value
