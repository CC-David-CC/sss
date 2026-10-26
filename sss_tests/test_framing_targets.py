import copy
import tempfile
from pathlib import Path
import unittest
from sss.profiles import target_segments as legacy_target_segments,TARGET_POLICIES
from sss.lesson_targets import target_segments
from sss.episodes import training_tokens,EpisodeArchive


class FramingTargets(unittest.TestCase):
    def rows(self):
        return [dict(role='user',kind='question',rendered='Q:',scope='practice',verified=False),
                dict(role='assistant',kind='answer',rendered='A!',scope='practice',verified=True),
                dict(role='assistant',kind='framing',rendered='\n',scope='practice',verified=False)]

    def test_complete_template_framing_is_context_only_under_both_policies(self):
        for policy in TARGET_POLICIES:
            rows=self.rows();self.assertEqual(target_segments(rows,policy),[False,True,False])
            result=training_tokens(rows,tokenize=lambda text:list(text.encode()),policy=policy)
            self.assertEqual(result['targets'],list(b':A!\n'))
            self.assertEqual(result['loss_mask'],[False,True,True,False])

    def test_framing_cannot_be_role_spoofed_or_labelled_verified(self):
        for role,verified in [('user',False),('tool',False),('assistant',True),('assistant',None)]:
            rows=self.rows();rows[-1].update(role=role,verified=verified)
            for policy in TARGET_POLICIES:
                with self.assertRaises(ValueError):target_segments(rows,policy)
        with tempfile.TemporaryDirectory() as td:
            archive=EpisodeArchive(Path(td)/'episode',create=True,metadata=dict(origin='synthetic'))
            with self.assertRaises(ValueError):archive.append('assistant','framing','\n',verified=True)
            with self.assertRaises(ValueError):archive.append('user','framing','\n',verified=False)

    def test_ordinary_answer_verification_is_not_weakened(self):
        rows=self.rows();rows[1]['verified']=False
        for policy in TARGET_POLICIES:
            with self.assertRaises(ValueError):target_segments(rows,policy)

    def test_legacy_profile_contract_is_unchanged_and_delegated(self):
        for policy in TARGET_POLICIES:
            with self.assertRaises(ValueError):legacy_target_segments(self.rows(),policy)
            ordinary=self.rows()[:-1]
            self.assertEqual(target_segments(ordinary,policy),legacy_target_segments(ordinary,policy))
            with self.assertRaises(ValueError):target_segments([self.rows()[-1]],policy)
            with self.assertRaises(ValueError):target_segments(self.rows(),'unknown-policy')


if __name__=='__main__':unittest.main()
