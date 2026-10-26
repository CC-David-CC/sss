"""Membership/configuration unit controls; no forged proof is a real lesson approval."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sss.adapters.verified_practice_registry import InstalledBWPractice
from sss.records import digest


def lesson():
    return dict(schema=2,model_contract_id='a'*64,scope='owned-training',segments=['controlled unit fixture'])


def row():
    return dict(owner=dict(kind='bw-artifact-practice-v1'),
        renderer=dict(schema=1,kind='pcc-final-artifact-through-eos-renderer-v1',model_contract_id='a'*64,renderer_sha256='e'*64,tokenizer_sha256='f'*64,maximum_tokens=512,stop_token_ids=[1,2],representation='final-artifact-v1',adapter_sha256='1'*64,system_sha256='2'*64),
        export_directory='/private/owned-export',export_id='b'*64,lesson_id=digest(lesson()),
        failure_capture_id='c'*64,correction_capture_id='d'*64)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'registry.json'
        self.config=dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=[row()])
        self.write()
        # Fault injection is deliberately limited to the installed proof loader.
        # Real archive/oracle/tokenizer authority is exercised by optional tests.
        self.loader=patch('sss.adapters.verified_practice_registry._load_registration',
            side_effect=lambda r,c,m:(dict(export_id=r['export_id'],proof='controlled'),lesson()))
        self.loader_mock=self.loader.start();self.addCleanup(self.loader.stop)

    def write(self):
        self.path.write_text(json.dumps(self.config));self.path.chmod(0o600)

    def install(self):
        return InstalledBWPractice(self.path,components={},model_contract_id='a'*64)

    def test_exact_membership_and_detached_results(self):
        installed=self.install();record=dict(lesson_id=digest(lesson()),lesson=lesson())
        installed.validate_lessons([record])
        bound=installed.binding();bound['checked_practice_lesson_ids'].clear()
        self.assertEqual(len(installed.binding()['checked_practice_lesson_ids']),1)
        exported=installed.lessons();exported[0]['scope']='development'
        installed.validate_lessons([record])
        changed=copy.deepcopy(record);changed['lesson']['segments']=['unverified replacement']
        with self.assertRaises(ValueError):installed.validate_lessons([changed])

    def test_partial_invalid_batch_and_duplicates_never_admitted(self):
        installed=self.install();record=dict(lesson_id=digest(lesson()),lesson=lesson())
        with self.assertRaises(ValueError):installed.validate_lessons([record,dict(lesson_id='f'*64,lesson=lesson())])
        with self.assertRaises(ValueError):installed.validate_lessons([record,record])
        for value in ([],{},None):
            with self.assertRaises(ValueError):installed.validate_lessons(value)
        installed.validate_lessons([record])
        with self.assertRaises(ValueError):installed.validate_lessons([dict(lesson_id=digest(None),lesson=None)])

    def test_changed_registry_or_proof_requires_new_policy(self):
        installed=self.install();self.config['registrations'][0]['export_id']='e'*64;self.write()
        with self.assertRaisesRegex(ValueError,'registry'):installed.verify()
        self.config['registrations'][0]['export_id']='b'*64;self.write()
        with patch('sss.adapters.verified_practice_registry._load_registration',return_value=(dict(proof='changed'),lesson())):
            with self.assertRaisesRegex(ValueError,'proof'):installed.verify()

    def test_duplicate_approval_refused(self):
        self.config['registrations'] *= 2;self.write()
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.install()

    def test_untrusted_provider_or_paths_refused_before_loader(self):
        for change in ('kind','path','key','schema'):
            self.config=dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=[row()])
            if change=='kind':self.config['registrations'][0]['owner']['kind']='student.module'
            elif change=='path':self.config['registrations'][0]['export_directory']='relative'
            elif change=='key':self.config['registrations'][0]['executable']='student.py'
            else:self.config['schema']=True
            self.write();self.loader_mock.reset_mock()
            with self.assertRaises(ValueError):self.install()
            self.loader_mock.assert_not_called()

    def test_private_immutable_owned_configuration_required(self):
        self.path.chmod(0o644)
        with self.assertRaises(ValueError):self.install()
        self.path.chmod(0o600);link=self.path.parent/'linked.json';link.symlink_to(self.path)
        with self.assertRaises(ValueError):InstalledBWPractice(link,components={},model_contract_id='a'*64)
        hard=self.path.parent/'hard.json';hard.hardlink_to(self.path)
        with self.assertRaises(ValueError):self.install()

    def test_replaced_final_path_is_refused_at_descriptor_boundary(self):
        original_open=os.open
        other=self.path.parent/'other.json';other.write_text(json.dumps(self.config));other.chmod(0o644)
        saved=self.path.parent/'registry.saved';triggered=[]
        def swapped(name,flags,*args,**kwargs):
            if name=='registry.json' and 'dir_fd' in kwargs:
                triggered.append(flags)
                self.path.rename(saved);self.path.symlink_to(other)
                try:return original_open(name,flags,*args,**kwargs)
                finally:self.path.unlink();saved.rename(self.path)
            return original_open(name,flags,*args,**kwargs)
        with patch('sss.adapters.verified_practice_registry.os.open',side_effect=swapped):
            with self.assertRaises(ValueError):self.install()
        self.assertTrue(triggered)
        self.assertTrue(triggered[0]&os.O_NOFOLLOW)
        self.loader_mock.assert_not_called()

    def test_duplicate_json_fields_and_nonfinite_config_refuse(self):
        for text in ('{"schema":1,"schema":1}', '{"x":NaN}', '{"x":1e999}'):
            self.path.write_text(text);self.path.chmod(0o600);self.loader_mock.reset_mock()
            with self.assertRaises(ValueError):self.install()
            self.loader_mock.assert_not_called()

    def test_proof_loader_failure_does_not_install_partial_membership(self):
        with patch('sss.adapters.verified_practice_registry._load_registration',side_effect=ValueError('original source changed')):
            with self.assertRaises(ValueError):self.install()


if __name__=='__main__':unittest.main()
