import json
from pathlib import Path
import tempfile
import unittest
from sss.episodes import *

class EpisodeTests(unittest.TestCase):
    def make(self,root):
        a=EpisodeArchive(Path(root)/'archive',create=True,metadata=dict(origin='synthetic'))
        question=a.append('user','question','Why is the service slow after lunch?',topic='service-latency',question_id='morning')
        a.append('tool','observation','Queue depth was 37 at 13:00.',verified=True,topic='service-latency',refs=[question])
        return a
    def test_causal_compaction_future_has_no_influence(self):
        with tempfile.TemporaryDirectory() as root:
            a=self.make(root);note=compact_reference(a,1,count=len,budget=800,unit='test-characters')
            a.append('user','question','A later question mentions workers.',question_id='later')
            self.assertEqual(note,compact_reference(a,1,count=len,budget=800,unit='test-characters'))
            self.assertTrue(verify_note(a,note))
            self.assertEqual(note['open_question_count'],1)
    def test_hash_tampering_and_future_references(self):
        with tempfile.TemporaryDirectory() as root:
            a=self.make(root)
            with self.assertRaises(ValueError):a.append('assistant','answer','guess',refs=['f'*64])
            p=a.path/'events/00000001.json';p.chmod(0o600)
            row=json.loads(p.read_bytes());row['text']='forged';p.write_text(json.dumps(row))
            with self.assertRaises(ValueError):EpisodeArchive(a.path)
    def test_retrieval_and_exact_claims(self):
        with tempfile.TemporaryDirectory() as root:
            a=self.make(root);result=a.search('queue depth')
            self.assertEqual(a.read(result[0]['id'])['text'],'Queue depth was 37 at 13:00.')
            note=compact_reference(a,1,count=len,budget=2048,unit='test-characters')
            note['entries'][0]['quote']='invented';note['note_id']=digest({k:v for k,v in note.items() if k!='note_id'})
            with self.assertRaises(ValueError):verify_note(a,note)
    def test_masks_exactly_track_thinking_and_observations(self):
        spans=[dict(role='user',kind='question',verified=False,scope='practice',rendered='Q:'),dict(role='assistant',kind='thinking',verified=True,scope='practice',rendered='think'),dict(role='tool',kind='observation',verified=False,scope='practice',rendered='OBS'),dict(role='assistant',kind='answer',verified=True,scope='practice',rendered='A')]
        encode=lambda s:list(s.encode())
        joint=training_tokens(spans,tokenize=encode);answer=training_tokens(spans,tokenize=encode,policy='actions_answer')
        self.assertEqual(sum(joint['loss_mask']),6);self.assertEqual(sum(answer['loss_mask']),1)
        self.assertEqual(joint['tokens'],answer['tokens'])
        with self.assertRaises(ValueError):training_tokens(spans,tokenize=encode,maximum=3)
        spans[0]['scope']='qualification'
        with self.assertRaises(ValueError):training_tokens(spans,tokenize=encode)
    def test_public_artifact_and_training_are_different(self):
        with tempfile.TemporaryDirectory() as root:
            a=self.make(root);a.append('assistant','answer','Measured queue depth is 37; cause is not established.',verified=True,resolves='morning')
            result=export_text(a,Path(root)/'finished.txt',public=True)
            self.assertFalse(result['trained']);self.assertTrue(Path(root,'finished.txt').exists())
            a.append('user','question','hidden test',scope='qualification')
            with self.assertRaises(ValueError):export_text(a,Path(root)/'bad.txt',public=True)
    def test_token_boundary_mismatch_is_not_silently_masked(self):
        spans=[dict(role='user',kind='question',verified=False,scope='practice',rendered='a'),dict(role='assistant',kind='answer',verified=True,scope='practice',rendered='b')]
        with self.assertRaises(ValueError):training_tokens(spans,tokenize=lambda s: [1] if s=='a' else [2,3])
