"""Joined owner machinery: genuine BW actions are scripted, never model inference."""
from dataclasses import replace
import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sss.records import canonical,digest
from sss.practice_oracle import AffineClampFoldCase
from sss.adapters import bw_verified_practice as joined
from sss.adapters.bw_verified_practice import BWArtifactPractice,PracticeExportRefused,export_correction,read_export


class OwnerContract(unittest.TestCase):
    def owner(self):
        return BWArtifactPractice(AffineClampFoldCase.install('new-owned-case','practice.new',
            [dict(values=[1,-2],scale=3,offset=-1,low=-3,high=5)]),'a'*64,'b'*64)

    def test_closed_detached_descriptor_roundtrip(self):
        owner=self.owner();descriptor=owner.descriptor()
        self.assertEqual(BWArtifactPractice.from_descriptor(descriptor),owner)
        descriptor['case']['rows'][0]['values'].append(99)
        self.assertNotEqual(BWArtifactPractice.from_descriptor(descriptor).binding(),owner.binding())
        for field,value in [('schema',True),('kind','arbitrary-module:factory'),('module','os')]:
            altered=owner.descriptor();altered[field]=value
            with self.subTest(field=field),self.assertRaises(PracticeExportRefused):BWArtifactPractice.from_descriptor(altered)

    def test_protected_cases_nonpractice_and_unsupported_modes_refuse(self):
        owner=self.owner()
        for changes in [dict(split_role='heldout'),dict(protected_case_ids=(owner.case.case_id,)),
                        dict(protected_case_ids=(owner.case.split_id,)),dict(source_mode=True),dict(source_mode=0o755)]:
            with self.subTest(changes=changes),self.assertRaises(PracticeExportRefused):replace(owner,**changes)

    def test_plain_task_spec_without_hidden_rows_or_identifiers(self):
        owner=self.owner()
        for hidden in (owner.case.case_id,owner.case.split_id,owner.case.inputs_json.decode(),owner.baseline_source_sha256):
            self.assertNotIn(hidden,owner.task_prompt)
        self.assertIn('solve(values, scale, offset, low, high)',owner.task_prompt)
        self.assertIn('2,048 nodes',owner.task_prompt)

    def test_exact_artifact_envelope_preserves_final_newline(self):
        source=b'def solve(values, scale, offset, low, high):\n    return {}\n'
        encoded=joined._artifact(source,0o644);self.assertEqual(joined._extract(encoded,0o644),source)
        for change in (dict(path='./task.py'),dict(mode=True),dict(extra='unrelated')):
            value=json.loads(encoded);value.update(change)
            with self.subTest(change=change),self.assertRaises(PracticeExportRefused):joined._extract(canonical(value).decode(),0o644)
        with self.assertRaises(UnicodeError):joined._artifact(b'\xff',0o644)

    def test_render_text_preserves_prior_export_bytes_and_exclusive_writer(self):
        from sss.episodes import EpisodeArchive,render_text,export_text
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);archive=EpisodeArchive(root/'archive',create=True,metadata=dict(origin='synthetic'))
            archive.append('user','question','Owned question',scope='practice')
            archive.append('assistant','answer','Owned verified artifact',scope='practice',verified=True)
            # Exact previous byte assembly, retained as a compatibility assertion.
            text=['Skills cubed: completed teaching record','Artifact complete; no model weight update is implied.','Archive head: '+archive.head,'']
            for row in archive.records():
                text += [f"[{row['seq']} | {row['role']} | {row['kind']} | verified={row['verified']} | id={row['id']}]",row['text'],'']
            self.assertEqual(render_text(archive,public=True),'\n'.join(text).encode())
            exported=export_text(archive,root/'example.txt',public=True)
            self.assertEqual((root/'example.txt').read_bytes(),render_text(archive,public=True));self.assertFalse(exported['trained'])
            with self.assertRaises(FileExistsError):export_text(archive,root/'example.txt',public=True)


if __name__=='__main__':unittest.main()
