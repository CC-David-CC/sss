import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sss_integration.foundation_panel_run import run


class FoundationPanelRunTests(unittest.TestCase):
    def test_tampered_panel_fails_before_starting_a_server(self):
        with tempfile.TemporaryDirectory() as directory:
            panel=Path(directory)/'panel.json'
            panel.write_text(json.dumps({'evaluation_id':'wrong','cases':[]}))
            with patch('sss_integration.foundation_panel_run.subprocess.Popen') as popen:
                with self.assertRaisesRegex(ValueError,'panel identity'):
                    run(argparse.Namespace(panel=panel))
                popen.assert_not_called()


if __name__=='__main__':
    unittest.main()
