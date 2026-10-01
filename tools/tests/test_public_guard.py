import tempfile
import unittest
from pathlib import Path

from tools.public_guard import load_rules, scan

CONFIG = """
[[rule]]
name = "internal name"
pattern = 'P0[_ ]Distilled'
reason = "use the title"
allowed = ["tools/*"]
"""


class PublicGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "guard.toml").write_text(CONFIG, encoding="utf-8")
        self.rules = load_rules(self.root / "guard.toml")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return rel

    def test_finds_a_forbidden_name_with_its_line(self):
        rel = self.write("README.md", "intro\nthe P0_Distilled paper\n")
        findings = scan(self.root, [rel], self.rules)
        self.assertEqual([(f[0], f[1], f[2]) for f in findings], [("README.md", 2, "internal name")])

    def test_match_is_case_insensitive(self):
        rel = self.write("notes.md", "p0 distilled\n")
        self.assertEqual(len(scan(self.root, [rel], self.rules)), 1)

    def test_allowed_paths_are_skipped(self):
        rel = self.write("tools/build.py", "SOURCE = 'P0_Distilled_v0.1.tex'\n")
        self.assertEqual(scan(self.root, [rel], self.rules), [])

    def test_binary_and_missing_files_are_skipped(self):
        (self.root / "image.png").write_bytes(b"\x89PNG\xff\xfe P0_Distilled")
        self.assertEqual(scan(self.root, ["image.png", "missing.md"], self.rules), [])

    def test_repository_config_loads(self):
        config = Path(__file__).resolve().parents[1] / "public_guard.toml"
        names = [rule[0] for rule in load_rules(config)]
        self.assertIn("internal name of the entry-point paper", names)


if __name__ == "__main__":
    unittest.main()
