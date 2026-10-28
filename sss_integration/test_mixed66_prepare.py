import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sss_integration.mixed66_prepare import check_overlap, protected_panel


class Mixed66PreparationTests(unittest.TestCase):
    def test_overlap_stops_before_preparation(self):
        with self.assertRaisesRegex(ValueError, 'collision'):
            check_overlap(['practice', 'protected'], {'heldout': ['protected']})
        self.assertEqual(check_overlap(['practice'], {'heldout': ['protected']})['heldout']['exact_prompt_collisions'], 0)

    def test_panel_requires_matching_content_and_count(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'panel.json'
            raw = json.dumps([{'prompt': 'private'}]).encode()
            path.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            self.assertEqual(protected_panel(path, sha, 1, 'external64')[0], ['private'])
            with self.assertRaisesRegex(ValueError, 'identity'):
                protected_panel(path, '0' * 64, 1, 'external64')
            with self.assertRaisesRegex(ValueError, 'size'):
                protected_panel(path, sha, 64, 'external64')
            with self.assertRaises(FileNotFoundError):
                protected_panel(path.parent / 'missing', sha, 1, 'external64')


if __name__ == '__main__':
    unittest.main()
