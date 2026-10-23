from pathlib import Path
import tempfile
import unittest
from sss.curriculum import foundation_graph
from sss.reporting import report_html,write_report
from sss.foundation_cli import example_archive
from sss.episodes import EpisodeArchive,export_text

class ReportingTests(unittest.TestCase):
    def test_self_contained_unmeasured_report(self):
        graph=foundation_graph();text=report_html(graph)
        self.assertIn(graph.identity,text)
        self.assertNotIn('<script src=',text)
        self.assertIn('unmeasured',text)
        with self.assertRaises(ValueError):report_html(graph,[dict(graph_id='other')])
    def test_reference_example_is_real_checked_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            a=example_archive(Path(root)/'example','math.linear_system')
            loaded=EpisodeArchive(a.path)
            self.assertEqual(loaded.head,a.head)
            result=export_text(loaded,Path(root)/'conversation.txt',public=True)
            self.assertFalse(result['trained'])
            self.assertIn('assistant | thinking',Path(root,'conversation.txt').read_text())
    def test_report_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'report.html';write_report(foundation_graph(),path)
            with self.assertRaises(FileExistsError):write_report(foundation_graph(),path)
