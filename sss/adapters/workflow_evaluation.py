"""Optional actual BW/COW workflow panel for the public learning-panel protocol."""
from pathlib import Path
import json

from sss.adapters.artifact_evaluation import CowArtifactEvaluator
from sss.adapters.cow_evaluation import runtime_binding
from sss.workflow_assessment import RECIPE,make_launch,original_project,observe_capture
from sss.records import canonical,digest,file_sha256


class BWWorkflowEvaluator(CowArtifactEvaluator):
    panel_kind='sss.bw-workflow-evaluator.v1'
    child_module='sss_integration.workflow_evaluate'
    finished_means='actual BW read/edit/current passing check/explicit finish, preserved input; artifact correctness separate'

    def _configuration_fields(self):
        return {'maximum_steps','maximum_requests'}

    def _validate_configuration(self,config):
        if (type(config['maximum_steps']) is not int or not 1<=config['maximum_steps']<=1024
                or type(config['maximum_requests']) is not int or not 1<=config['maximum_requests']<=32):
            raise ValueError('Explicit bounded BW interpreter and per-action request limits required')

    def _extra_source_paths(self):
        return [Path(__file__),self.sss/'sss/workflow_assessment.py',
            *sorted(p for root in (self.bw/'examples',self.bw/'branchwrite/_examples')
                if root.exists() for p in root.rglob('*')
                if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')]

    def _prepare_inputs(self):
        # BW/PCC construct actual bootstrap/tool-result context dynamically. Do
        # not claim that the artifact-only JSON prefix is a workflow prefix.
        self.prefix=();self.prefixes=[]
        self.evaluation_id=digest(dict(kind='sss.bw-workflow-assessment.v1',
            cases=[c.descriptor() for c in self.cases],recipe=RECIPE))

    def expected_runtime(self,profile):
        return dict(kind='sss.bw-workflow-runtime.v1',sources_and_inputs_sha256=self.pins,
            cow_runtime=runtime_binding(profile),recipe=RECIPE,
            maximum_steps=self.config['maximum_steps'],maximum_tokens=self.config['maximum_tokens'],
            maximum_requests_per_action=self.config['maximum_requests'],
            checker='fixed BW isolated affine-clamp-fold oracle',finished=self.finished_means,greedy=True)

    def _evidence(self,candidate,directory):
        from branchwrite.lesson_capture import read_capture
        from sss.adapters.bw_verified_practice import _oracle
        directory=Path(directory).absolute();self.verify();profile=self.profile(candidate)
        read=lambda p:json.loads(p.read_bytes())
        expected=dict(schema=1,evaluator_id=self.identity,profile=profile,
            command=self._command(directory,profile),no_implicit_retry=True)
        if (canonical(read(directory/'adapter-intent-private.json'))!=canonical(expected)
                or canonical(read(directory/'candidate-profile.json'))!=canonical(profile)
                or canonical(read(directory/'candidate-selection-private.json'))!=canonical(candidate)):
            raise ValueError('Original workflow dispatch changed')
        root=directory/'evaluation';value=read(root/'result.json');settled=read(root/'settlement.json')
        if canonical(read(root/'intent-private.json'))!=canonical(dict(evaluator_id=self.identity,
                profile=profile,candidate=candidate,training=False)):
            raise ValueError('Original workflow child intent changed')
        self._summary(value,candidate)
        if (value.get('evidence_directory')!=str(directory) or settled!=dict(schema=1,status='COMPLETE',
                completed_cases=len(self.cases),result_sha256=file_sha256(root/'result.json'),
                weights_updated=False,promoted=False)):
            raise ValueError('Original workflow settlement changed')
        server=read(root/'server-private.json');connection=server['connection']
        if (server['status']!='RETIRED' or connection['model_contract_id']!=profile['model_contract_id']
                or connection['execution_profile_id']!=profile['execution_profile_id']
                or connection['eos_tokens']!=profile['execution']['eos_tokens']
                or not connection['endpoint_url'].startswith('http://127.0.0.1:')):
            raise ValueError('Original workflow server/profile did not retire')
        for index,(case,row) in enumerate(zip(self.cases,value['outcomes'])):
            folder=root/('%04d'%index);observed=read(folder/'observation-private.json')
            original_project(case,folder/'project')
            expected_launch=make_launch(case,folder/'project',connection,self.config)
            capture=read_capture(folder/'capture',expected_capture_id=observed['workflow']['capture_id'])
            workflow,source=observe_capture(case,capture,expected_launch)
            if canonical(workflow)!=canonical(observed['workflow']):
                raise ValueError('Original workflow ledger observation changed')
            proof=_oracle(case.case,source,folder/'oracle',observed['oracle_status'])
            expected_row=dict(id=case.identity,skill_id=case.skill_id,gate=case.gate,
                passed=workflow['finished'] and proof['status']=='pass',finished=workflow['finished'])
            if canonical(observed['outcome'])!=canonical(expected_row) or canonical(row)!=canonical(expected_row):
                raise ValueError('Original workflow/independent artifact score changed')
        self.verify();return value
