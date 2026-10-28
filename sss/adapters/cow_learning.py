"""Owner-configured learning evaluation over the existing shared-prefix COW path.

This adapter freezes inputs, runs the existing evaluator in an isolated process,
and validates its original evidence. It owns neither a workflow nor a sampler.
"""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import os
import subprocess
import sys

from sss.records import canonical, digest, file_sha256
from sss.paired import compare_frozen_evaluations, POLICY


def write_once(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def process_identity(pid):
    stat = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=int(stat[19]),
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


class CowLearningEvaluator:
    def __init__(self, config, native, serving_profile, tokenizer):
        required = {'pcc_root', 'cow_profile', 'cases', 'evaluation_id', 'practice_pack',
                    'oracle', 'runtime_proof', 'gpu_index', 'gpu_uuid', 'context_tokens',
                    'batch_tokens', 'maximum_tokens', 'stop_token_ids', 'minimum_free_mib',
                    'maximum_initial_utilization', 'timeout_seconds'}
        if type(config) is not dict or set(config) != required:
            raise ValueError('Exact owner COW learning-evaluator configuration required')
        self.config = copy.deepcopy(config)
        for key in ('pcc_root', 'cow_profile', 'cases', 'practice_pack', 'oracle', 'runtime_proof'):
            if type(config[key]) is not str or not Path(config[key]).is_absolute():
                raise ValueError('Absolute owner configuration paths required')
        self.pcc = Path(config['pcc_root']).resolve(strict=True)
        self.sss = Path(__file__).resolve().parents[2]
        from tools import pcc_lessons
        self.host_pcc = Path(pcc_lessons.__file__).resolve().parents[1]
        from tools.pcc_cow_profile import bind_dense_profile
        if file_sha256(bind_dense_profile.__code__.co_filename) != file_sha256(self.pcc/'tools/pcc_cow_profile.py'):
            raise ValueError('Owner and execution PCC profile binders differ')
        for key in ('gpu_index', 'context_tokens', 'batch_tokens', 'maximum_tokens',
                    'minimum_free_mib', 'maximum_initial_utilization', 'timeout_seconds'):
            if type(config[key]) is not int:
                raise ValueError('Integer owner evaluation limits required')
        if (config['gpu_index'] < 0 or not 1 <= config['context_tokens'] <= 131072
                or not 1 <= config['batch_tokens'] <= config['context_tokens']
                or not 1 <= config['maximum_tokens'] <= 4096
                or config['minimum_free_mib'] < 1
                or not 0 <= config['maximum_initial_utilization'] <= 100
                or not 1 <= config['timeout_seconds'] <= 14400
                or type(config['gpu_uuid']) is not str
                or not config['gpu_uuid'].startswith('GPU-')
                or type(config['stop_token_ids']) is not list
                or not config['stop_token_ids']
                or any(type(t) is not int or t < 0 for t in config['stop_token_ids'])
                or config['stop_token_ids'] != sorted(set(config['stop_token_ids']))):
            raise ValueError('Explicit bounded COW placement, context, stopping and admission required')
        self.model = Path(native.config['model']).resolve(strict=True)
        self.base = native.config['base_sha256']
        self.model_contract = serving_profile['model_contract_id']
        if Path(serving_profile['model_path']).resolve(strict=True) != self.model:
            raise ValueError('Learning and serving bases differ')
        self.paths = {key: Path(config[key]).resolve(strict=True)
                      for key in ('cow_profile', 'cases', 'practice_pack', 'oracle', 'runtime_proof')}
        self.template = json.loads(self.paths['cow_profile'].read_bytes())
        if (Path(self.template['model_path']).resolve(strict=True) != self.model
                or self.template['model_weights_sha256'] != self.base
                or self.template.get('adapter') is not None):
            raise ValueError('Explicit unattached COW base profile must match native training')
        from tools.pcc_cow_evaluation import verify_sources
        verify_sources(self.template, self.pcc)
        build = json.loads(self.paths['runtime_proof'].read_bytes())
        if (type(build.get('sha256')) is not dict
                or build['sha256'].get(str(self.paths['oracle'])) != file_sha256(self.paths['oracle'])
                or self.template['bridge_library'] not in build['sha256']):
            raise ValueError('Qualified COW bridge and oracle proof required; no fresh-oracle fallback')
        self.build = build
        from tools.gguf_reader import GGUFFile
        metadata = GGUFFile(self.model).metadata
        self.tokenizer_id = digest(dict(
            metadata={k: v for k, v in metadata.items() if k.startswith('tokenizer.')},
            source_sha256=file_sha256(self.pcc / 'tools/strata_tokenizer.py')))
        from tools.strata_tokenizer import Tokenizer
        self.decoder = Tokenizer.from_gguf(self.model)
        from sss.evaluation import implementation_identity
        self.checker = implementation_identity()
        from sss.adapters.foundation_training import validate_pack, SYSTEM
        from sss.foundations import Exercise, reference, check
        from sss.adapters.pcc_foundation_render import PCCFoundationRenderer
        from serve.cow_http import model_text_components
        from serve.server import Service
        self.pack = json.loads(self.paths['practice_pack'].read_bytes())
        exercises = validate_pack(self.pack)
        self.data = json.loads(self.paths['cases'].read_bytes())
        if (self.data.get('evaluation_id') != config['evaluation_id']
                or config['evaluation_id'] != digest({k: v for k, v in self.data.items() if k != 'evaluation_id'})
                or self.data.get('split') != 'development'
                or self.data.get('pack_id') != self.pack['pack_id']
                or self.data.get('tokenizer_sha256') != self.tokenizer_id
                or self.data.get('model_contract_id') != self.model_contract
                or type(self.data.get('cases')) is not list or not self.data['cases']):
            raise ValueError('Frozen development cases and checked practice pack must match; sealed panels are not development')
        components = model_text_components(self.model, dict(enable_thinking=False),
                                          model_contract_id=self.model_contract, tokenizer=tokenizer)
        from sss.adapters.runtime_sources import rendering_sources
        rendering_paths=rendering_sources(components,model_text_components,Service.encode_prompt)
        renderer = PCCFoundationRenderer(components)
        if self.data.get('renderer_sha256') != renderer.renderer_sha256:
            raise ValueError('Frozen assessment renderer differs from actual serving renderer')
        protected = {e.identity: e for e in exercises if e.split == 'development'}
        self.case_index = {}
        for row in self.data['cases']:
            e = Exercise(**row['exercise'])
            expected_prefix = Service.encode_prompt(renderer.encoder,
                [dict(role='system', content=SYSTEM), dict(role='user', content=e.prompt)], None,
                dict(enable_thinking=False, add_generation_prompt=True))
            if (e.identity != row['exercise_id'] or e.identity not in protected
                    or e != protected[e.identity] or e.identity in self.case_index
                    or row['prefix_tokens'] != expected_prefix
                    or len(expected_prefix) + config['maximum_tokens'] > config['context_tokens']):
                raise ValueError('Assessment identity, split, exact rendering, uniqueness or context differs')
            self.case_index[e.identity] = (e.skill_id, e.gate)
        self.allowed_lessons = {}
        eval_prompts = {e.prompt for e in protected.values()}
        for e in exercises:
            if e.split != 'practice':
                continue
            answer = reference(e)
            if e.prompt in eval_prompts or not check(e, answer):
                raise ValueError('Invalid or protected practice demonstration')
            evidence = dict(exercise=asdict(e), answer=answer, passed=True,
                            origin='owned synthetic practice; not an observed model failure')
            lesson = dict(schema=2, title=e.skill_id + ' ' + e.gate,
                model_contract_id=self.model_contract, skill_id=e.skill_id,
                segments=renderer(e, answer), target_policy='actions_answer', scope='owned-training',
                evidence=dict(method='sss-verified-episode-v1', archive_sha256=digest(evidence),
                    verification_sha256=digest(dict(exercise_id=e.identity,
                        checker_id=self.pack['implementation_id'], answer=answer, passed=True)),
                    renderer_sha256=renderer.renderer_sha256, tokenizer_sha256=self.tokenizer_id))
            self.allowed_lessons[digest(lesson)] = lesson
        from sss.adapters.cow_evaluation import shared_input_prefix
        self.prefix = shared_input_prefix([r['prefix_tokens'] for r in self.data['cases']])
        if not self.prefix:
            raise ValueError('Owner learning policy requires an actual shared input prefix')
        source_paths = [Path(__file__), self.sss / 'sss_integration/optimizer_evaluate.py',
                        self.sss / 'sss/adapters/cow_evaluation.py',
                        self.sss / 'sss/adapters/foundation_training.py',
                        self.sss / 'sss/adapters/pcc_foundation_render.py',
                        self.sss / 'sss/curriculum_unique.py',
                        self.pcc / 'tools/pcc_cow_profile.py', self.pcc / 'tools/pcc_lessons.py',
                        self.pcc / 'tools/pcc_native_training.py',
                        self.host_pcc / 'tools/pcc_lessons.py', self.host_pcc / 'tools/pcc_native_training.py',
                        self.host_pcc / 'tools/pcc_cow_profile.py',
                        self.sss / 'sss/adapters/runtime_sources.py',*rendering_paths]
        if self.pack.get('generation_profile')=='without-replacement-v2':
            source_paths.append(self.sss/'sss/curriculum_unique_v2.py')
        self.pins = {str(p): file_sha256(p) for p in [*self.paths.values(), *source_paths]}
        self.pins.update(build['sha256'])
        self._binding = dict(schema=1, kind='sss.cow-learning-evaluator.v1', config=self.config,
            base_sha256=self.base, model_contract_id=self.model_contract,
            checker_implementation_id=self.checker, tokenizer_sha256=self.tokenizer_id,
            sources_and_inputs_sha256=self.pins,
            checked_practice_lesson_ids=sorted(self.allowed_lessons),
            evaluation_id=config['evaluation_id'], execution_path='cow-consumed-request-v1',
            shared_prefix_tokens=len(self.prefix), no_implicit_retry=True)
        self.identity = digest(self._binding)
        self.verify()

    def binding(self):
        return copy.deepcopy(self._binding)

    def verify(self):
        from sss.evaluation import implementation_identity
        from tools.pcc_cow_evaluation import verify_sources
        if implementation_identity() != self.checker or file_sha256(self.model) != self.base:
            raise ValueError('Original checker or base weights changed')
        for path, expected in self.pins.items():
            if file_sha256(path) != expected:
                raise ValueError('Frozen COW learning source/input changed: ' + path)
        verify_sources(self.template, self.pcc)

    def validate_lessons(self, records, previous_report):
        for record in records:
            lesson = record['lesson']
            if self.allowed_lessons.get(record['lesson_id']) != lesson:
                raise ValueError('Lesson is not this policy\'s independently checked practice')

    def profile(self, candidate):
        from tools.pcc_cow_profile import bind_dense_profile, bind_dense_adapter
        model, sha = self.model, self.base
        if candidate is not None:
            if (candidate.get('mode') not in ('full', 'lora')
                    or file_sha256(candidate['candidate_path']) != candidate['candidate_sha256']):
                raise ValueError('Native candidate mode or actual weights differ')
            if candidate['mode'] == 'full':
                model, sha = Path(candidate['candidate_path']), candidate['candidate_sha256']
        profile = bind_dense_profile(self.template, model_path=model, model_sha256=sha,
            gpu_index=self.config['gpu_index'], gpu_uuid=self.config['gpu_uuid'])
        if candidate is not None and candidate['mode'] == 'lora':
            profile = bind_dense_adapter(profile, adapter_path=candidate['candidate_path'],
                                         adapter_sha256=candidate['candidate_sha256'])
        from sss.adapters.cow_evaluation import validate_profile
        validate_profile(profile, model=model, model_sha256=sha,
            gpu_uuid=self.config['gpu_uuid'], context_tokens=self.config['context_tokens'],
            batch_tokens=self.config['batch_tokens'], stop_token_ids=self.config['stop_token_ids'],
            hardware_row=(str(self.config['gpu_index']), self.config['gpu_uuid']))
        return profile

    def expected_runtime(self, profile):
        from sss_integration.optimizer_evaluate import runtime_description
        args = SimpleNamespace(**dict(self.config, runtime_proof=self.paths['runtime_proof'],
                                      checker_implementation_id=self.checker))
        return runtime_description(args, self.build, self.tokenizer_id, profile, self.prefix)

    def validate(self, value, candidate):
        compare_frozen_evaluations(value, value, POLICY)
        from sss.adapters.cow_evaluation import candidate_binding
        profile = self.profile(candidate)
        if (value['evaluation_id'] != self.config['evaluation_id']
                or value['model_sha256'] != profile['model_weights_sha256']
                or value['runtime_id'] != digest(self.expected_runtime(profile))
                or any(value.get(k) != v for k, v in candidate_binding(profile).items())
                or {r['id']: (r['skill_id'], r['gate']) for r in value['outcomes']} != self.case_index):
            raise ValueError('COW learning result model, hat, runtime or complete case coverage differs')

    def _command(self, directory, profile):
        args = [sys.executable, '-m', 'sss_integration.optimizer_evaluate',
                '--pcc-root', str(self.pcc), '--cases', str(self.paths['cases']),
                '--evaluation-id', self.config['evaluation_id'],
                '--checker-implementation-id', self.checker,
                '--model', profile['model_path'], '--model-sha256', profile['model_weights_sha256'],
                '--oracle', str(self.paths['oracle']), '--runtime-proof', str(self.paths['runtime_proof']),
                '--output', str(directory / 'evaluation'), '--execution-path', 'cow',
                '--cow-profile', str(directory / 'candidate-profile.json'), '--cow-shared-prefix']
        for key in ('gpu_uuid', 'context_tokens', 'batch_tokens', 'maximum_tokens',
                    'minimum_free_mib', 'maximum_initial_utilization'):
            args += ['--' + key.replace('_', '-'), str(self.config[key])]
        return args + ['--stop-token-ids', *map(str, self.config['stop_token_ids'])]

    def _evidence(self, candidate, directory):
        profile = self.profile(candidate)
        intent = json.loads((directory / 'adapter-intent-private.json').read_bytes())
        if intent != dict(schema=1, evaluator_id=self.identity, profile=profile,
                          command=self._command(directory, profile), no_implicit_retry=True):
            raise ValueError('Original COW evaluation intent differs')
        if json.loads((directory / 'candidate-profile.json').read_bytes()) != profile:
            raise ValueError('Original COW candidate profile differs')
        child_intent = json.loads((directory / 'evaluation/intent.json').read_bytes())
        value = json.loads((directory / 'evaluation/result.json').read_bytes())
        settlement = json.loads((directory / 'evaluation/settlement.json').read_bytes())
        if (child_intent['runtime'] != self.expected_runtime(profile)
                or child_intent.get('cow_profile') != profile
                or child_intent['cases_sha256'] != self.pins[str(self.paths['cases'])]
                or child_intent.get('cow_profile_sha256') != file_sha256(directory / 'candidate-profile.json')
                or settlement['status'] != 'COMPLETE' or settlement['weights_updated'] is not False
                or settlement['completed_cases'] != len(self.case_index)):
            raise ValueError('Original COW intent or settlement differs')
        self.validate(value, candidate)
        from sss.foundations import Exercise, check
        outcomes = {row['id']: row for row in value['outcomes']}
        for index, case in enumerate(self.data['cases']):
            observed = json.loads((directory / 'evaluation' / ('%04d-private.json' % index)).read_bytes())
            completion = observed['completion']
            tokens = completion['sampled_token_ids']
            stopped = completion['stop_reason'] == 'eos'
            if (not tokens or len(tokens) > self.config['maximum_tokens']
                    or any(type(t) is not int or t < 0 for t in tokens)
                    or any(t in self.config['stop_token_ids'] for t in tokens[:-1])
                    or stopped != (tokens[-1] in self.config['stop_token_ids'])
                    or completion['stop_token_id'] != (tokens[-1] if stopped else None)
                    or completion['cow_receipt']['tokens'] != tokens
                    or completion['text'] != self.decoder.decode(tokens[:-1] if stopped else tokens)
                    or {k: observed[k] for k in outcomes[case['exercise_id']]} != outcomes[case['exercise_id']]
                    or observed['model_sha256'] != value['model_sha256']
                    or observed['runtime_id'] != value['runtime_id']
                    or observed['evaluation_id'] != value['evaluation_id']
                    or observed['passed'] != check(Exercise(**case['exercise']), completion['text'])
                    or observed['finished'] != stopped):
                raise ValueError('Original case tokens, decoding, stopping or independently recomputed grade differs')
        self.verify()
        return value

    def _environment(self):
        return dict(os.environ, PYTHONPATH=os.pathsep.join([
            str(self.sss), str(self.host_pcc), str(self.pcc), str(self.pcc / 'experimental/branching_context/src')]))

    def __call__(self, candidate, directory, worker_fd):
        directory = Path(directory).absolute()
        self.verify()
        os.fstat(worker_fd)
        profile = self.profile(candidate)
        command = self._command(directory, profile)
        write_once(directory / 'adapter-intent-private.json', dict(schema=1,
            evaluator_id=self.identity, profile=profile, command=command, no_implicit_retry=True))
        write_once(directory / 'candidate-profile.json', profile)
        environment = self._environment()
        with (directory / 'stdout-private.log').open('x') as out, (directory / 'stderr-private.log').open('x') as err:
            proc = subprocess.Popen(command, stdout=out, stderr=err, env=environment,
                                    cwd=self.sss, start_new_session=True, pass_fds=(worker_fd,))
            write_once(directory / 'child-process-private.json', process_identity(proc.pid))
            try:
                code = proc.wait(timeout=self.config['timeout_seconds'])
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                write_once(directory / 'child-exit-private.json', dict(status='TIMEOUT', returncode=proc.returncode))
                raise
        write_once(directory / 'child-exit-private.json', dict(status='EXITED', returncode=code))
        if code:
            raise RuntimeError('Original COW evaluator failed; inspect retained private child evidence')
        return self._evidence(candidate, directory)

    def recover(self, candidate, directory):
        directory = Path(directory).absolute()
        self.verify()
        identity_path = directory / 'child-process-private.json'
        if not identity_path.is_file():
            return None
        identity = json.loads(identity_path.read_bytes())
        try:
            live = process_identity(identity['pid'])
        except FileNotFoundError:
            live = None
        if live == identity:
            raise ValueError('Original COW evaluator process is still present; no new dispatch')
        terminal = directory / 'child-exit-private.json'
        if terminal.exists() and json.loads(terminal.read_bytes()) != dict(status='EXITED', returncode=0):
            raise ValueError('Original COW evaluator did not exit successfully')
        # A complete original child settlement may survive a lost parent's exit
        # receipt. Accept its validated evidence only after the child is gone.
        return self._evidence(candidate, directory)


def configured_policies(path, native, serving_profile, tokenizer):
    from sss.adapters.learning_policy import LearningPolicy
    config = json.loads(Path(path).read_bytes())
    if type(config) is dict and config.get('kind')=='sss.learning-stack.v1':
        from sss.adapters.learning_stack import configured_learning_stack
        return configured_learning_stack(path,native,serving_profile,tokenizer)
    if (type(config) is not dict or set(config) != {'schema', 'evaluator', 'policies'}
            or type(config['schema']) is not int or config['schema'] != 1
            or type(config['policies']) is not list or not 1 <= len(config['policies']) <= 8):
        raise ValueError('Bounded owner COW learning-policy registry required')
    evaluator = CowLearningEvaluator(config['evaluator'], native, serving_profile, tokenizer)
    result = {}
    for row in config['policies']:
        if set(row) != {'title', 'training', 'max_rounds', 'assessment_purpose', 'minimum_skill_cases'}:
            raise ValueError('Explicit learning recipe, assessment purpose and limits required')
        if row['assessment_purpose'] not in ('machinery', 'adaptive_learning'):
            raise ValueError('Fixed comparisons cannot be driven as adaptive learning runs')
        policy = LearningPolicy(evaluator, **row)
        identity = digest(policy.describe())
        if identity in result:
            raise ValueError('Duplicate owner learning policy')
        result[identity] = policy
    return result
