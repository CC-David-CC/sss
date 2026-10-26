"""CPU machinery through actual BW/COW/OS and the real GGUF tokenizer/template.

Proposals are scripted. No model forward pass, backprop or learning is claimed.
"""
import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sss.records import digest, canonical
from sss.adapters.bw_verified_practice import PCCArtifactRenderer, PracticeExportRefused
from sss.adapters.bw_action_practice import PCCActionRenderer, export_action_correction, read_action_export


@unittest.skipUnless(os.environ.get('SSS_BW_ACTION_MODEL'), 'set SSS_BW_ACTION_MODEL to the local qualified MiniCPM GGUF')
class BWActionPracticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from serve.cow_http import model_text_components
        from sss_integration.bw_verified_practice_cpu import captured_pair
        cls.tmp=tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        cls.components=model_text_components(Path(os.environ['SSS_BW_ACTION_MODEL']),
            dict(enable_thinking=False),model_contract_id='a'*64)
        cls.tokenizer_id=PCCArtifactRenderer.tokenizer_identity(cls.components)
        cls.renderer=PCCActionRenderer(cls.components,model_contract_id='a'*64,
            tokenizer_sha256=cls.tokenizer_id,maximum_tokens=16384,stop_token_ids=[1,130073])
        check = ('python3 -B -c \'from task import solve; '
                 'assert solve([-4,0,2,9],3,-2,-5,8)=={"values":[-5,-2,4,8],"total":5}; '
                 'assert solve([],1,2,0,9)=={"values":[],"total":0}\'')
        with captured_pair(cls.root/'bw',check_command=check,
                           finish_answer='The saved repair passed the behavior check.') as pair:
            cls.owner=pair['owner']; cls.correction=pair['correction'].capture_id; cls.failure=pair['failure'].capture_id
            cls.exported=export_action_correction(cls.owner,pair['correction'].directory,
                correction_capture_id=cls.correction,failure_capture_id=cls.failure,
                renderer=cls.renderer,output=cls.root/'export')
        (cls.root/'bw').rename(cls.root/'hidden-original-bw')

    def reread(self, **overrides):
        values=dict(owner=self.owner,expected_export_id=self.exported.export_id,correction_capture_id=self.correction,
            failure_capture_id=self.failure,renderer=self.renderer)
        values.update(overrides)
        return read_action_export(self.root/'export',**values)

    def test_original_turns_become_four_append_exact_action_through_eos_lessons(self):
        value=self.reread()
        self.assertEqual(len(value.lessons),4)
        from tools.pcc_lesson_segments import tokenize_segments
        selected=[]
        for lesson,tokens in zip(value.lessons,value.tokens):
            self.assertEqual(tokens,tokenize_segments(lesson,lambda text:self.renderer.tokenizer.encode(text,parse_special=True),16384))
            ids=[t for t,on in zip(tokens['targets'],tokens['loss_mask']) if on]
            self.assertEqual(ids[-1],130073)
            selected.append(json.loads(self.renderer.tokenizer.decode(ids[:-1]))['tool'])
            self.assertEqual(sum(s['kind'] in ('action','answer') for s in lesson['segments']),1)
            self.assertFalse(any(s['verified'] for s in lesson['segments'] if s['role']!='assistant'))
            self.assertLessEqual(len(ids),256)
        self.assertEqual(selected,['read_file','replace','run_check','finish'])
        self.assertLess(len(value.tokens[0]['tokens']),len(value.tokens[-1]['tokens']))
        self.assertTrue((self.root/'export/finished-training-examples/example.txt').is_file())
        self.assertFalse(value.binding()['training_approved']);self.assertFalse(value.binding()['owner_registered'])

    def test_reread_is_original_evidence_only(self):
        from sss.adapters import bw_action_practice
        before={p:p.read_bytes() for p in (self.root/'export').rglob('*') if p.is_file()}
        with patch.object(bw_action_practice,'observe',side_effect=AssertionError('no oracle re-execution')):
            self.reread()
        self.assertEqual(before,{p:p.read_bytes() for p in (self.root/'export').rglob('*') if p.is_file()})

    def test_wrong_owner_export_and_capture_pins_refuse(self):
        for overrides in [dict(expected_export_id='0'*64),dict(correction_capture_id='0'*64),
                          dict(owner=replace(self.owner,model_contract_id='b'*64))]:
            with self.assertRaises(PracticeExportRefused):self.reread(**overrides)

    def test_context_overflow_refuses_before_copy_or_oracle_without_truncation(self):
        from branchwrite.lesson_actions import captured_action_turns
        tiny=PCCActionRenderer(self.components,model_contract_id='a'*64,tokenizer_sha256=self.tokenizer_id,
            maximum_tokens=512,stop_token_ids=[1,130073])
        turns=captured_action_turns(self.root/'export/capture',expected_capture_id=self.correction)
        with self.assertRaisesRegex(ValueError,'exceed|budget'):
            tiny.render(turns,target_policy='actions_answer')

    def test_protected_feedback_refused_before_export_or_oracle(self):
        protected=replace(self.owner,protected_texts=('HOST TOOL CONTEXT',))
        out=self.root/'must-not-exist'
        with self.assertRaisesRegex(PracticeExportRefused,'protected'):
            export_action_correction(protected,self.root/'export/capture',correction_capture_id=self.correction,
                failure_capture_id=self.failure,renderer=self.renderer,output=out)
        self.assertFalse(out.exists())

    def test_rehashed_changed_action_target_cannot_manufacture_a_verified_lesson(self):
        import shutil
        other=self.root/'tampered-export';shutil.copytree(self.root/'export',other)
        p=other/'export-private.json';value=json.loads(p.read_bytes())
        value['lessons'][0]['segments'][-1]['rendered']='made-up answer'
        value['export_id']=digest({k:v for k,v in value.items() if k!='export_id'})
        p.chmod(0o600);p.write_bytes(canonical(value))
        with self.assertRaisesRegex(PracticeExportRefused,'proof, lessons, tokens or masks'):
            read_action_export(other,owner=self.owner,expected_export_id=value['export_id'],correction_capture_id=self.correction,
                failure_capture_id=self.failure,renderer=self.renderer)

    def test_owner_installs_all_four_exact_turns_through_existing_lesson_registry(self):
        from sss.adapters.verified_practice_registry import InstalledBWPractice
        registrations=[]
        for index, identity in enumerate(self.exported.lesson_ids):
            registrations.append(dict(owner=self.owner.descriptor(),renderer=self.renderer.binding(),
                export_directory=str(self.root/'export'),export_id=self.exported.export_id,lesson_id=identity,
                correction_capture_id=self.correction,failure_capture_id=self.failure,turn_index=index))
        config=dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=registrations)
        path=self.root/'registry.json';path.write_bytes(canonical(config));path.chmod(0o600)
        registry=InstalledBWPractice(path,components=self.components,model_contract_id='a'*64)
        records=[dict(lesson_id=digest(lesson),lesson=lesson) for lesson in self.exported.lessons]
        registry.validate_lessons(records)
        self.assertEqual(len(registry.lessons()),4)
        changed=copy.deepcopy(records);changed[0]['lesson']['segments'][-1]['rendered']='unapproved teaching'
        with self.assertRaises(ValueError):registry.validate_lessons(changed)
        config['registrations'].append(copy.deepcopy(registrations[0]));path.write_bytes(canonical(config))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            InstalledBWPractice(path,components=self.components,model_contract_id='a'*64)

    def test_action_selector_bool_and_unpinned_runtime_refuse_before_proof_loading(self):
        from sss.adapters.verified_practice_registry import InstalledBWPractice
        row=dict(owner=self.owner.descriptor(),renderer=self.renderer.binding(),
            export_directory=str(self.root/'export'),export_id=self.exported.export_id,lesson_id=self.exported.lesson_ids[0],
            correction_capture_id=self.correction,failure_capture_id=self.failure,turn_index=True)
        path=self.root/'invalid-registry.json'
        for value in (row,dict(row,turn_index=0,renderer=dict(row['renderer'],pcc_sources_sha256={}))):
            path.write_bytes(canonical(dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=[value])));path.chmod(0o600)
            with patch('sss.adapters.verified_practice_registry._load_registration',side_effect=AssertionError('preflight first')):
                with self.assertRaises(ValueError):InstalledBWPractice(path,components=self.components,model_contract_id='a'*64)


if __name__=='__main__':unittest.main()
