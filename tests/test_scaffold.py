from pathlib import Path
import tempfile
import unittest
from scripts.new_workspace import create

class ScaffoldTests(unittest.TestCase):
    def test_clean_copy_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = create(Path(tmp)/'new', 'My studio', 'research')
            self.assertTrue((target/'AGENTS.md').is_file())
            self.assertFalse((target/'.agentos').exists())
            self.assertFalse((target/'.git').exists())
            self.assertIn('My studio', (target/'workspace-profile.json').read_text())
            with self.assertRaises(ValueError):
                create(target, 'New', 'operations')
