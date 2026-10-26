"""Real BW/COW/OS teacher capture, independent oracle and student rendering.

No model inference/training. Owner-declared scripted origin remains explicit.
"""
import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from sss.records import canonical,digest
from sss.adapters.bw_action_practice import (
    BWActionTeacherTransfer,PCCActionRenderer,export_action_correction,read_action_export)
from sss.adapters.bw_verified_practice import PCCArtifactRenderer,PracticeExportRefused
from sss.adapters.verified_practice_registry import InstalledBWPractice


@unittest.skipUnless(os.environ.get('SSS_BW_ACTION_MODEL'),'local real GGUF metadata required')
class TeacherTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from serve.cow_http import model_text_components
        from sss_integration.bw_verified_practice_cpu import captured_pair
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        cls.student='d'*64  # Explicit test contract; never a serving-model claim.
        cls.components=model_text_components(Path(os.environ['SSS_BW_ACTION_MODEL']),
            dict(enable_thinking=False),model_contract_id=cls.student)
        cls.renderer=PCCActionRenderer(cls.components,model_contract_id=cls.student,
            tokenizer_sha256=PCCArtifactRenderer.tokenizer_identity(cls.components),maximum_tokens=16384,
            stop_token_ids=[1,130073])
        check=('python3 -B -c \'from task import solve; '
               'assert solve([-4,0,2,9],3,-2,-5,8)=={"values":[-5,-2,4,8],"total":5}\'')
        with captured_pair(cls.root/'bw',check_command=check) as pair:
            cls.owner=pair['owner'];cls.failure=pair['failure'].capture_id;cls.correction=pair['correction'].capture_id
            cls.transfer=BWActionTeacherTransfer(digest(cls.owner.binding()),cls.owner.model_contract_id,
                cls.student,cls.failure,cls.correction,'owner-scripted','sss-cpu-scripted-control')
            cls.exported=export_action_correction(cls.owner,pair['correction'].directory,
                correction_capture_id=cls.correction,failure_capture_id=cls.failure,renderer=cls.renderer,
                output=cls.root/'export',teacher_transfer=cls.transfer)
        (cls.root/'bw').rename(cls.root/'original-bw-unavailable')

    def reread(self,**changes):
        kwargs=dict(owner=self.owner,expected_export_id=self.exported.export_id,
            correction_capture_id=self.correction,failure_capture_id=self.failure,renderer=self.renderer,
            teacher_transfer=self.transfer)
        kwargs.update(changes)
        return read_action_export(self.root/'export',**kwargs)

    def config(self):
        return dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=[dict(
            owner=self.owner.descriptor(),renderer=self.renderer.binding(),export_directory=str(self.root/'export'),
            export_id=self.exported.export_id,lesson_id=identity,turn_index=i,
            correction_capture_id=self.correction,failure_capture_id=self.failure,
            teacher_transfer=self.transfer.descriptor()) for i,identity in enumerate(self.exported.lesson_ids)])

    def install(self,config,name):
        path=self.root/name;path.write_bytes(canonical(config));path.chmod(0o600)
        return InstalledBWPractice(path,components=self.components,model_contract_id=self.student)

    def test_original_source_preserved_and_only_student_actions_supervised(self):
        value=self.reread();record=json.loads((self.root/'export/export-private.json').read_bytes())
        self.assertEqual(record['schema'],2)
        self.assertEqual(record['owner']['model_contract_id'],'a'*64)
        self.assertEqual(record['renderer']['model_contract_id'],self.student)
        self.assertEqual(record['teacher_transfer'],self.transfer.descriptor())
        self.assertFalse(record['proof']['source_backend_relabelled'])
        self.assertEqual(record['teacher_transfer']['teacher_kind'],'owner-scripted')
        tools=[]
        for lesson,tokens in zip(value.lessons,value.tokens):
            self.assertEqual(lesson['model_contract_id'],self.student)
            selected=[v for v,on in zip(tokens['targets'],tokens['loss_mask']) if on]
            self.assertEqual(selected[-1],130073)
            tools.append(json.loads(self.renderer.tokenizer.decode(selected[:-1]))['tool'])
            self.assertEqual(sum(s['verified'] for s in lesson['segments']),1)
        self.assertEqual(tools,['read_file','replace','run_check','finish'])
        self.assertFalse(value.binding()['training_approved'])
        self.assertFalse(value.binding()['owner_registered'])

    def test_no_implicit_transfer_or_fake_target_contract(self):
        for changes in (dict(teacher_transfer=None),dict(teacher_transfer={}),
                        dict(owner=replace(self.owner,model_contract_id=self.student))):
            with self.assertRaises(ValueError):self.reread(**changes)

    def test_every_transfer_pin_and_origin_is_rechecked(self):
        for field in ('source_owner_sha256','source_model_contract_id','student_model_contract_id',
                      'failure_capture_id','correction_capture_id'):
            with self.subTest(field=field),self.assertRaises(ValueError):
                self.reread(teacher_transfer=replace(self.transfer,**{field:'0'*64}))
        for field,value in (('teacher_kind','agent'),('teacher_identifier','changed-declaration')):
            with self.subTest(field=field),self.assertRaises(ValueError):
                self.reread(teacher_transfer=replace(self.transfer,**{field:value}))

    def test_closed_transfer_descriptor(self):
        original=self.transfer.descriptor()
        self.assertEqual(BWActionTeacherTransfer.from_descriptor(original),self.transfer)
        for value in (dict(original,schema=True),dict(original,approve_training=True),
                      dict(original,teacher_kind='model-proven'),dict(original,teacher_identifier=''),
                      dict(original,teacher_identifier='x\n'),dict(original,student_model_contract_id='a'*64)):
            with self.assertRaises(ValueError):BWActionTeacherTransfer.from_descriptor(value)

    def test_student_registry_installs_exact_four_lessons(self):
        registry=self.install(self.config(),'registry.json')
        records=[dict(lesson_id=digest(v),lesson=v) for v in self.exported.lessons]
        registry.validate_lessons(records)
        self.assertEqual(len(registry.lessons()),4)
        self.assertTrue(all(r['teacher_transfer']==self.transfer.descriptor()
            for r in registry.binding()['registrations']))
        changed=copy.deepcopy(records);changed[0]['lesson']['model_contract_id']='a'*64
        with self.assertRaises(ValueError):registry.validate_lessons(changed)
        config=self.config();config['registrations'][0].pop('teacher_transfer')
        with self.assertRaises(ValueError):self.install(config,'registry-no-transfer.json')
        config=self.config();config['registrations'][0]['teacher_transfer']['correction_capture_id']='0'*64
        with self.assertRaises(ValueError):self.install(config,'registry-wrong-capture.json')

    def test_protected_material_cannot_be_smuggled_through_transfer(self):
        owner=replace(self.owner,protected_texts=('HOST TOOL CONTEXT',))
        transfer=replace(self.transfer,source_owner_sha256=digest(owner.binding()))
        destination=self.root/'protected-must-not-exist'
        with self.assertRaisesRegex(ValueError,'protected'):
            export_action_correction(owner,self.root/'export/capture',correction_capture_id=self.correction,
                failure_capture_id=self.failure,renderer=self.renderer,output=destination,teacher_transfer=transfer)
        self.assertFalse(destination.exists())

    def test_readback_never_replays_tools_or_oracle(self):
        with patch('sss.adapters.bw_action_practice.observe',side_effect=AssertionError('no tool replay')):
            self.reread()

    def test_owner_cli_exports_and_audits_original_captures_for_student(self):
        owner_path=self.root/'cli-owner.json';owner_path.write_bytes(canonical(self.owner.descriptor()));owner_path.chmod(0o600)
        transfer_path=self.root/'cli-transfer.json';transfer_path.write_bytes(canonical(self.transfer.descriptor()));transfer_path.chmod(0o600)
        output=self.root/'cli-export'
        common=['--owner',str(owner_path),'--teacher-transfer',str(transfer_path),
            '--model',os.environ['SSS_BW_ACTION_MODEL'],'--correction-capture-id',self.correction,
            '--failure-capture-id',self.failure,'--directory',str(output),'--maximum-tokens','16384',
            '--stop-token-ids','1','130073']
        cmd=[sys.executable,'-m','sss.adapters.bw_action_practice']
        exported=json.loads(subprocess.check_output(cmd+['export',*common,'--correction-capture',str(self.root/'export/capture')],text=True))
        audited=json.loads(subprocess.check_output(cmd+['audit',*common,'--export-id',exported['export_id']],text=True))
        self.assertEqual(exported['export_id'],audited['export_id'])
        self.assertEqual(audited['examples'],4)
        self.assertEqual(audited['model_forward_calls'],0)
        self.assertEqual(audited['training_updates'],0)
        self.assertFalse(audited['training_approved'])


if __name__=='__main__':unittest.main()
