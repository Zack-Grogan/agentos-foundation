from pathlib import Path
import tempfile
import unittest
from scripts.new_workspace import create


class ScaffoldTests(unittest.TestCase):
    def test_clean_copy_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = create(Path(tmp) / "new", "My studio", "research")
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertFalse((target / ".agentos").exists())
            self.assertFalse((target / ".git").exists())
            self.assertIn("My studio", (target / "workspace-profile.json").read_text())
            with self.assertRaises(ValueError):
                create(target, "New", "operations")

    def test_manifest_omits_unrelated_files_and_update_plan_preserves_edits(self):
        from scripts.update_plan import plan

        root = Path(__file__).resolve().parents[1]
        sentinel = root / "unrelated-private-fixture.txt"
        if sentinel.exists():
            self.fail("Unexpected preexisting test sentinel")
        sentinel.write_text("Do not export unrelated files.")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                target = create(Path(tmp) / "new", "Customized", "operations")
                self.assertFalse((target / sentinel.name).exists())
                file = target / "README.md"
                file.write_text(file.read_text() + "\nLocal customization.\n")
                report = plan(target, root)
                self.assertEqual(
                    next(x for x in report["changes"] if x["path"] == "README.md")[
                        "status"
                    ],
                    "local-customization",
                )
                self.assertIn("Local customization.", file.read_text())
        finally:
            sentinel.unlink()
