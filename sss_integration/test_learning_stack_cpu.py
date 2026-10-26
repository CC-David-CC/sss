"""Install real panel/render/capture bindings; prohibit inference and native training.

Actual BW executes a synthetic scripted teacher correction and independent
oracle. MiniCPM supplies real metadata/template/tokenization. This validates
installation and public lesson admission only, not model learning or scores.
"""
from dataclasses import asdict
from contextlib import closing
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

try:
    from tools.pcc_lessons import LessonService,NativeRunner
    from tools.pcc_optimizer_profiles import identity
    from tools.pcc_cow_profile import bind_dense_profile
    from tools.gguf_reader import GGUFFile
    from tools.strata_tokenizer import Tokenizer
    from serve.cow_http import model_text_components
    from serve.server import Service
    import branchwrite
except ModuleNotFoundError:
    raise unittest.SkipTest('Optional BW/PCC installation required')

from sss.adapters.bw_verified_practice import export_correction
from sss.adapters.cow_learning import configured_policies
from sss.adapters.foundation_training import build_pack,SYSTEM
from sss.adapters.pcc_foundation_render import PCCFoundationRenderer
from sss.foundations import Exercise
from sss.records import digest,file_sha256
from sss_integration.bw_verified_practice_cpu import captured_pair,actual_renderer


class NoTrainingRunner(NativeRunner):
    launches=0
    def __call__(self,*args):
        self.launches+=1;raise AssertionError('CPU installation test must not train')


class InstalledLearningStackCPUTests(unittest.TestCase):
    def test_actual_installed_factory_and_public_mixed_lesson_admission(self):
        required=['SSS_STACK_CPU_MODEL','SSS_STACK_CPU_PROFILE','SSS_STACK_EXECUTION_ROOT',
                  'SSS_STACK_RUNTIME_PROOF','SSS_STACK_ORACLE','SSS_STACK_BW_ROOT']
        if not all(os.environ.get(k)for k in required):self.skipTest('Explicit qualified owner inputs required')
        output=os.environ.get('SSS_STACK_CPU_OUTPUT')
        if output:
            root=Path(output).absolute();root.mkdir(mode=0o700,exist_ok=False)
        else:
            tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
        model=Path(os.environ['SSS_STACK_CPU_MODEL']).resolve(strict=True)
        profile=json.loads(Path(os.environ['SSS_STACK_CPU_PROFILE']).read_bytes())
        model_sha=file_sha256(model)
        self.assertEqual(profile['model_weights_sha256'],model_sha)
        contract=profile['model_contract_id'];execution=Path(os.environ['SSS_STACK_EXECUTION_ROOT']).resolve(strict=True)
        from tools import pcc_lessons
        host=Path(pcc_lessons.__file__).resolve().parents[1]
        self.assertNotEqual(host,execution,'This control intentionally qualifies separate API/execution source pins')
        tokenizer=Tokenizer.from_gguf(model)
        components=model_text_components(model,dict(enable_thinking=False),model_contract_id=contract,tokenizer=tokenizer)
        renderer=actual_renderer(model,contract,maximum_tokens=512)
        owned_baseline=(b'def solve(values, scale, offset, low, high):\n'
            b'    return {"values": values, "total": sum(values)}\n')
        with captured_pair(root/'bw',model_contract_id=contract,baseline_source=owned_baseline)as pair:
            exported=export_correction(pair['owner'],pair['correction'].directory,
                correction_capture_id=pair['correction'].capture_id,failure_capture_id=pair['failure'].capture_id,
                renderer=renderer,output=root/'export')
            registration=dict(owner=pair['owner'].descriptor(),renderer=renderer.binding(),
                export_directory=str(exported.directory),export_id=exported.export_id,lesson_id=exported.lesson_id,
                failure_capture_id=pair['failure'].capture_id,correction_capture_id=pair['correction'].capture_id)
        (root/'bw').rename(root/'retired-original-bw')
        write(root/'approved.json',dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=[registration]))
        # Separate genuine development definitions and verified practice data;
        # no evaluator will run during this installation-only test.
        template_cases=json.loads(Path(os.environ['SSS_STACK_CPU_CASES']).read_bytes())
        write(root/'artifact-cases.json',template_cases)
        def profile_for(name,capacity):
            value=copy.deepcopy(profile);value['execution']['capacity']=capacity
            value=bind_dense_profile(value,model_path=model,model_sha256=model_sha,
                gpu_index=0,gpu_uuid=profile['hardware']['gpu_uuid'])
            write(root/name,value);return value
        profile_for('target-profile.json',1024);profile_for('workflow-profile.json',32768)
        profile_for('review-profile.json',512)
        common=dict(schema=1,pcc_root=str(execution),bw_root=os.environ['SSS_STACK_BW_ROOT'],
            cow_profile=str(root/'target-profile.json'),runtime_proof=os.environ['SSS_STACK_RUNTIME_PROOF'],
            cases=str(root/'artifact-cases.json'),gpu_index=0,gpu_uuid=profile['hardware']['gpu_uuid'],
            maximum_tokens=256,minimum_free_mib=1,maximum_initial_utilization=100,timeout_seconds=900)
        write(root/'target.json',common)
        workflow=dict(common,cow_profile=str(root/'workflow-profile.json'),maximum_steps=512,maximum_requests=8)
        write(root/'workflow.json',workflow)
        pack=build_pack(['math.add.no_carry'],seed=2026102601,practice_per_gate=2,checks_per_gate=1,
            generation_profile='without-replacement-v1')
        write(root/'practice-pack.json',pack)
        foundation=PCCFoundationRenderer(components)
        metadata=GGUFFile(model).metadata
        tokenizer_id=digest(dict(metadata={k:v for k,v in metadata.items()if k.startswith('tokenizer.')},
            source_sha256=file_sha256(execution/'tools/strata_tokenizer.py')))
        cases=[]
        for raw in pack['exercises']:
            if raw['split']!='development':continue
            e=Exercise(**raw)
            prefix=Service.encode_prompt(foundation.encoder,[dict(role='system',content=SYSTEM),
                dict(role='user',content=e.prompt)],None,dict(enable_thinking=False,add_generation_prompt=True))
            cases.append(dict(exercise=asdict(e),exercise_id=e.identity,prefix_tokens=list(prefix)))
        data=dict(schema=1,split='development',pack_id=pack['pack_id'],model_contract_id=contract,
            tokenizer_sha256=tokenizer_id,renderer_sha256=foundation.renderer_sha256,cases=cases)
        data['evaluation_id']=digest(data);write(root/'review-cases.json',data)
        review=dict(pcc_root=str(execution),cow_profile=str(root/'review-profile.json'),
            cases=str(root/'review-cases.json'),evaluation_id=data['evaluation_id'],practice_pack=str(root/'practice-pack.json'),
            oracle=os.environ['SSS_STACK_ORACLE'],runtime_proof=os.environ['SSS_STACK_RUNTIME_PROOF'],
            gpu_index=0,gpu_uuid=profile['hardware']['gpu_uuid'],context_tokens=512,batch_tokens=512,
            maximum_tokens=64,stop_token_ids=profile['execution']['eos_tokens'],minimum_free_mib=1,
            maximum_initial_utilization=100,timeout_seconds=900)
        write(root/'retention.json',review)
        optimizer=dict(schema=2,title='CPU installation only; never dispatched',mode='full',rank=None,
            optimizer='adamw',learning_rate=1e-4,optimizer_settings=dict(schema=1),state_policy='fresh',training_budget_seconds=None)
        recipe=dict(mode='full',rank=2,batch_size=2,steps=1,learning_rate=1e-4,optimizer_profile_id=identity(optimizer))
        runner=NoTrainingRunner(dict(model=str(model),base_sha256=model_sha,executable='/not-invoked-by-test',
            devices=['CPU'],gpu_uuids=[],device_budget_bytes={'CPU':32<<30},reserve_bytes=128<<20,
            host_reserve_bytes=128<<20,sequence_profile='dense-llama-short-v1',memory_profile='allocator-v1',
            timeout_seconds=60,optimizer_profiles={identity(optimizer):optimizer}))
        config=dict(schema=1,kind='sss.learning-stack.v1',
            panels=[dict(panel_id=name,role=name,kind=kind,configuration=str(root/(name+'.json')))
                for name,kind in [('target','cow-artifact'),('workflow','bw-workflow'),('retention','cow-foundations')]],
            practice=[dict(provider_id='verified-code',role='target',kind='bw-verified',configuration=str(root/'approved.json')),
                dict(provider_id='mixed-review',role='review',kind='foundation-practice',panel_id='retention')],
            practice_mix=dict(minimum_target_lessons=1,minimum_review_lessons=1),
            policies=[dict(title='CPU installed bindings; no learning claim',training=recipe,max_rounds=2,
                assessment_purpose='machinery',minimum_skill_cases=3)])
        write(root/'stack.json',config)
        policies=configured_policies(root/'stack.json',runner,profile,tokenizer)
        policy_id,policy=next(iter(policies.items()));policy.verify()
        self.assertEqual({p['role']for p in policy.evaluator.binding()['panels']},{'target','workflow','retention'})
        self.assertIn(str(host/'tools/pcc_lessons.py'),policy.evaluator._panels[-1][2].pins)
        values=policy.evaluator.lessons();code=next(v for v in values if digest(v)==exported.lesson_id)
        review_lesson=next(v for v in values if digest(v)!=exported.lesson_id)
        with closing(LessonService(root/'service',contract,tokenizer.encode,runner,max_tokens=512,max_steps=2,
                sequence_profile='dense-llama-short-v1',rendered_tokenize=lambda text:tokenizer.encode(text,parse_special=True),
                learning_policies=policies))as service:
            records=[]
            for index,value in enumerate([code,review_lesson]):
                receipt=service.submit('/cow/training/lessons',dict(operation_id='install-'+str(index),lesson=value))
                records.append(service.lesson(receipt['lesson_id']))
            policy.validate_lessons(records,None)
            with self.assertRaisesRegex(ValueError,'target/review mix'):policy.validate_lessons(records[:1],None)
        self.assertEqual(runner.launches,0)
        write(root/'result-private.json',dict(schema=1,status='PASS',policy_id=policy_id,
            admitted_exact_lessons=2,actual_panel_bindings=3,development_review_cases=len(cases),
            native_or_model_calls=0,weights_updated=False,scores_exercised=False,
            scope='Real archive/oracle/renderer/configuration/lesson-admission installation; scripted teacher, no model learning'))


if __name__=='__main__':unittest.main()
