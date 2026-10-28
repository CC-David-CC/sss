"""Joined owner machinery: genuine BW actions are scripted, never model inference."""
from dataclasses import replace
import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sss.records import canonical,digest
from sss.practice_oracle import AffineClampFoldCase
from sss.adapters import bw_verified_practice as joined
from sss.adapters.bw_verified_practice import BWArtifactPractice,PracticeExportRefused,export_correction,read_export


MODEL=os.environ.get('PCC_MINICPM_GGUF')
class GenuineJoinedExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MODEL or not Path(MODEL).is_file():
            raise RuntimeError('Set PCC_MINICPM_GGUF to the owner GGUF for this explicit optional CPU integration test')
        from sss_integration.bw_verified_practice_cpu import captured_pair,actual_renderer
        cls.temp=tempfile.TemporaryDirectory(prefix='sss-joined-owner-');cls.root=Path(cls.temp.name);cls.renderer=actual_renderer(MODEL)
        with captured_pair(cls.root/'original') as pair:
            cls.owner=pair['owner'];cls.correction_id=pair['correction'].capture_id;cls.failure_id=pair['failure'].capture_id
            cls.bad=pair['source_failed'];cls.good=pair['source_corrected']
            cls.exports={policy:export_correction(cls.owner,pair['correction'].directory,correction_capture_id=cls.correction_id,
                failure_capture_id=cls.failure_id,renderer=cls.renderer,output=cls.root/policy,target_policy=policy)
                for policy in ('actions_answer','verified_thinking_actions_answer')}
        (cls.root/'original').rename(cls.root/'hidden-original')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def read(self,directory=None,*,owner=None,renderer=None,expected_export_id=None,**pins):
        exported=self.exports['actions_answer']
        return read_export(directory or exported.directory,owner=owner or self.owner,renderer=renderer or self.renderer,
            expected_export_id=expected_export_id or exported.export_id,
            correction_capture_id=pins.get('correction_capture_id',self.correction_id),failure_capture_id=pins.get('failure_capture_id',self.failure_id))

    def mutant(self,name,modify):
        path=self.root/('tampered-'+name);shutil.copytree(self.exports['actions_answer'].directory,path)
        record=json.loads((path/'export-private.json').read_bytes());modify(path,record)
        record['files']=[r for r in joined._inventory(path) if r['path']!='export-private.json']
        record['export_id']=digest({k:v for k,v in record.items() if k!='export_id'})
        file=path/'export-private.json';file.chmod(0o600);file.write_bytes(canonical(record));file.chmod(0o400)
        return path,record['export_id']

    def test_genuine_artifacts_and_independent_failed_passed_executions(self):
        from branchwrite.lesson_capture import read_capture
        exported=self.exports['actions_answer'];directory=exported.directory
        corrected=read_capture(directory/'capture',expected_capture_id=self.correction_id)
        failed=read_capture(directory/'capture/failure',expected_capture_id=self.failure_id)
        self.assertEqual(corrected.file_bytes('task.py'),self.good);self.assertEqual(failed.file_bytes('task.py'),self.bad)
        self.assertEqual(failed.manifest['evidence']['checks'],[])
        for label,status in [('failed-oracle','fail'),('corrected-oracle','pass')]:
            value=json.loads((directory/label/'result-private.json').read_bytes())
            self.assertIs(value['execution_attempted'],True);self.assertEqual(value['status'],status)
            self.assertFalse(value['lesson_approved']);self.assertEqual(value['observation']['isolation']['namespace_members_after'],[])
        self.assertFalse(exported.binding()['training_approved']);self.assertFalse(exported.binding()['owner_registered'])
        self.assertEqual(exported.proof['sources']['pcc_lesson_segments'],joined._sources()['pcc_lesson_segments'])

    def test_exact_taught_artifact_through_eos_and_masked_tail_both_policies(self):
        left,right=self.exports.values()
        for key in ('tokens','targets','loss_mask'):self.assertEqual(left.tokens[key],right.tokens[key])
        for exported in (left,right):
            targets=[t for t,m in zip(exported.tokens['targets'],exported.tokens['loss_mask']) if m]
            self.assertEqual(targets[-1],130073);envelope=self.renderer.tokenizer.decode(targets[:-1])
            self.assertEqual(joined._extract(envelope,self.owner.source_mode),self.good)
            self.assertTrue(json.loads(envelope)['source'].endswith('\n'));self.assertFalse(exported.tokens['loss_mask'][-1])
            framing=exported.lesson['segments'][-1]
            self.assertEqual((framing['role'],framing['kind'],framing['verified']),('assistant','framing',False))
            self.assertFalse(any(s['kind']=='thinking' for s in exported.lesson['segments']))

    def test_real_pcc_lesson_admission_idempotent_without_training(self):
        from tools.pcc_lessons import LessonService
        tokenize=lambda text:self.renderer.tokenizer.encode(text,parse_special=True)
        with tempfile.TemporaryDirectory() as root:
            runner=lambda *args:(_ for _ in ()).throw(AssertionError('must never train'))
            service=LessonService(root,self.owner.model_contract_id,tokenize,runner,max_tokens=4096,rendered_tokenize=tokenize)
            try:
                for index,exported in enumerate(self.exports.values()):
                    request=dict(operation_id='verified-artifact-'+str(index),lesson=exported.lesson)
                    receipt=service.submit('/cow/training/lessons',request)
                    self.assertEqual(receipt,service.submit('/cow/training/lessons',request))
                    actual=service.lesson(receipt['lesson_id'])['example']
                    for key in ('tokens','targets','loss_mask'):self.assertEqual(actual[key],exported.tokens[key])
            finally:service.close()

    def test_offline_reader_no_rerun_and_detached_handle(self):
        with patch.object(joined,'observe',side_effect=AssertionError('offline reader must not execute')):exported=self.read()
        altered=exported.lesson;altered['segments'][1]['rendered']='unrelated';self.assertNotEqual(altered,exported.lesson)
        self.assertFalse((self.root/'original').exists());self.assertEqual(exported.export_id,self.exports['actions_answer'].export_id)
        text=(exported.directory/'finished-training-examples/example.txt').read_text()
        self.assertIn('no model weight update is implied',text);self.assertIn(self.owner.task_prompt,text)

    def test_owner_and_capture_pins_refuse(self):
        for changes in [dict(model_contract_id='d'*64),dict(baseline_source_sha256='e'*64),dict(source_mode=0o600)]:
            with self.subTest(changes=changes),self.assertRaises(PracticeExportRefused):self.read(owner=replace(self.owner,**changes))
        for pins in [dict(failure_capture_id='f'*64),dict(correction_capture_id='f'*64)]:
            with self.subTest(pins=pins),self.assertRaises(PracticeExportRefused):self.read(**pins)

    def test_protected_material_refuses_before_export(self):
        for owner in [replace(self.owner,protected_texts=('result.append',)),
                      replace(self.owner,protected_source_sha256s=(hashlib.sha256(self.good).hexdigest(),))]:
            with self.subTest(owner=owner.binding()),self.assertRaises(PracticeExportRefused):
                export_correction(owner,self.exports['actions_answer'].directory/'capture',correction_capture_id=self.correction_id,
                    failure_capture_id=self.failure_id,renderer=self.renderer,output=self.root/('protected-'+digest(owner.binding())))

    def test_wrong_actual_task_refuses(self):
        from sss_integration.bw_verified_practice_cpu import captured_pair
        with captured_pair(self.root/'wrong-task',task_override='Different task; syntax is not owner correctness') as pair:
            with self.assertRaisesRegex(PracticeExportRefused,'captured task'):
                export_correction(self.owner,pair['correction'].directory,correction_capture_id=pair['correction'].capture_id,
                    failure_capture_id=pair['failure'].capture_id,renderer=self.renderer,output=self.root/'wrong-task-export')
        self.assertFalse((self.root/'wrong-task-export/export-private.json').exists())

    def test_mutated_renderer_state_and_overflow_refuse(self):
        for name,value in [('maximum',2),('stops',(1,)),('model','f'*64),('tokenizer_id','f'*64)]:
            old=getattr(self.renderer,name)
            try:
                setattr(self.renderer,name,value)
                with self.subTest(name=name),self.assertRaises(PracticeExportRefused):self.renderer.verify()
            finally:setattr(self.renderer,name,old)
        from sss_integration.bw_verified_practice_cpu import actual_renderer
        short=actual_renderer(MODEL,maximum_tokens=32)
        with self.assertRaises(ValueError):
            export_correction(self.owner,self.exports['actions_answer'].directory/'capture',correction_capture_id=self.correction_id,
                failure_capture_id=self.failure_id,renderer=short,output=self.root/'overflow')
        self.assertFalse((self.root/'overflow/export-private.json').exists())

    def test_available_oracle_without_failed_contrast_cannot_export(self):
        empty=AffineClampFoldCase.install('owned-empty-contrast','practice.empty',
            [dict(values=[],scale=1,offset=0,low=-1,high=1)])
        owner=replace(self.owner,case=empty)
        with self.assertRaisesRegex(PracticeExportRefused,'contrast'):
            export_correction(owner,self.exports['actions_answer'].directory/'capture',correction_capture_id=self.correction_id,
                failure_capture_id=self.failure_id,renderer=self.renderer,output=self.root/'no-contrast')
        self.assertFalse((self.root/'no-contrast/export-private.json').exists())

    def test_oracle_infrastructure_unavailable_never_writes_completed_export(self):
        with patch('branchwrite.terminal.execute_command',side_effect=OSError('synthetic infrastructure refusal')):
            with self.assertRaisesRegex(PracticeExportRefused,'unavailable'):
                export_correction(self.owner,self.exports['actions_answer'].directory/'capture',correction_capture_id=self.correction_id,
                    failure_capture_id=self.failure_id,renderer=self.renderer,output=self.root/'oracle-unavailable')
        self.assertFalse((self.root/'oracle-unavailable/export-private.json').exists())
        receipt=json.loads((self.root/'oracle-unavailable/failed-oracle/result-private.json').read_bytes())
        self.assertEqual(receipt['status'],'unavailable')

    def test_actual_bw_syntax_pass_and_finish_not_independent_correctness(self):
        from sss_integration.bw_verified_practice_cpu import captured_pair
        with captured_pair(self.root/'bad-correction',corrected_source=self.bad+b'\n') as pair:
            self.assertTrue(pair['correction'].manifest['evidence']['recorded_workflow_verified'])
            with self.assertRaisesRegex(PracticeExportRefused,'contrast'):
                export_correction(self.owner,pair['correction'].directory,correction_capture_id=pair['correction'].capture_id,
                    failure_capture_id=pair['failure'].capture_id,renderer=self.renderer,output=self.root/'bad-correction-export')
        self.assertFalse((self.root/'bad-correction-export/export-private.json').exists())

    def test_reader_rederives_content_roles_masks_not_recomputed_flags(self):
        changes=[('unrelated',lambda p,r:r['lesson']['segments'][1].update(rendered='unrelated answer')),
                 ('newline',lambda p,r:r['lesson']['segments'][1].update(rendered=r['lesson']['segments'][1]['rendered'].replace('\\n',''))),
                 ('role',lambda p,r:r['lesson']['segments'][1].update(role='user')),
                 ('thinking',lambda p,r:r['lesson']['segments'][1].update(kind='thinking')),
                 ('mask',lambda p,r:r['tokens']['loss_mask'].__setitem__(-1,True)),
                 ('finished-text',lambda p,r:((p/'finished-training-examples/example.txt').chmod(0o600),
                    (p/'finished-training-examples/example.txt').write_text('unrelated teaching record'))),
                 ('extra-key',lambda p,r:r.update(invented_approval=True)),
                 ('source-pin',lambda p,r:r['proof']['sources'].update(pcc_lesson_segments='f'*64))]
        for name,modify in changes:
            path,identity=self.mutant(name,modify)
            with self.subTest(name=name),self.assertRaises(PracticeExportRefused):self.read(path,expected_export_id=identity)

    def test_original_oracle_raw_outputs_types_inputs_projection_and_retirement_rechecked(self):
        def change_result(path,record,mutate):
            file=path/'corrected-oracle/result-private.json';result=json.loads(file.read_bytes());mutate(path,result)
            result['evidence_sha256']=digest({k:v for k,v in result.items() if k!='evidence_sha256'});file.write_bytes(canonical(result))
        def output(path,result,change):
            value=json.loads(result['observation']['stdout']);change(value);raw=canonical(value)
            (path/'corrected-oracle/stdout.bin').write_bytes(raw)
            result['observation'].update(stdout=raw.decode(),stdout_sha256=hashlib.sha256(raw).hexdigest())
        for name,mutate in [('raw-grade',lambda p,r:output(p,r,lambda v:v.update(results=[]))),
                            ('exact-type',lambda p,r:output(p,r,lambda v:v['results'][0].update(total=True))),
                            ('input-preservation',lambda p,r:output(p,r,lambda v:v['inputs_after'][0]['values'].append(99))),
                            ('projection',lambda p,r:r['observation']['details']['inputs'][0].update(sha256='f'*64)),
                            ('argv',lambda p,r:r['observation']['details']['argv'].__setitem__(-1,'[]')),
                            ('unretired',lambda p,r:r['observation']['isolation'].update(namespace_members_after=[42])),
                            ('checker',lambda p,r:r.update(checker_implementation_sha256='f'*64)),
                            ('bw-source',lambda p,r:r.update(bw_implementation_sha256='f'*64)),
                            ('unavailable',lambda p,r:r.update(status='unavailable'))]:
            path,identity=self.mutant(name,lambda p,r:change_result(p,r,mutate))
            with self.subTest(name=name),self.assertRaises(PracticeExportRefused):self.read(path,expected_export_id=identity)

    def test_missing_failed_bytes_extra_files_links_and_modes_refuse(self):
        path,identity=self.mutant('missing-failure',lambda p,r:(p/'capture/failure/objects'/hashlib.sha256(self.bad).hexdigest()).unlink())
        with self.assertRaises((OSError,ValueError)):self.read(path,expected_export_id=identity)
        for name,mutate in [('extra',lambda p:(p/'unregistered.txt').write_text('unapproved')),
                            ('link',lambda p:(p/'linked').symlink_to('export-private.json')),
                            ('mode',lambda p:(p/'capture/objects'/hashlib.sha256(self.good).hexdigest()).chmod(0o600))]:
            path=self.root/('unregistered-'+name);shutil.copytree(self.exports['actions_answer'].directory,path);mutate(path)
            with self.subTest(name=name),self.assertRaises(PracticeExportRefused):self.read(path)


if __name__=='__main__':unittest.main()
