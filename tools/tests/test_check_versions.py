"""Tests for tools/check_versions.py on the repository and on fixtures."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.check_versions import check

REPO = Path(__file__).resolve().parents[2]


def make_repo(directory, cargo="0.4.0", lock="0.4.0", citation="0.4.0", zenodo="v0.4.0", changelog="0.4.0"):
    (directory / "Cargo.toml").write_text(f'[package]\nname = "thermodynamic_valence"\nversion = "{cargo}"\n', encoding="utf-8")
    (directory / "Cargo.lock").write_text(f'[[package]]\nname = "thermodynamic_valence"\nversion = "{lock}"\n', encoding="utf-8")
    (directory / "CITATION.cff").write_text(f"cff-version: 1.2.0\nversion: {citation}\n", encoding="utf-8")
    (directory / ".zenodo.json").write_text(json.dumps({"notes": f"{zenodo} fixes things."}), encoding="utf-8")
    (directory / "CHANGELOG.md").write_text(f"# Changelog\n\n## [Unreleased]\n\n## [{changelog}] - 2026-09-25\n", encoding="utf-8")


class TestCheckVersions(unittest.TestCase):

    def test_repository_is_consistent(self):
        _, problems = check(REPO)
        self.assertEqual(problems, [])

    def test_consistent_fixture(self):
        with TemporaryDirectory() as tmp:
            make_repo(Path(tmp))
            self.assertEqual(check(Path(tmp)), ("0.4.0", []))

    def test_mismatches_are_reported(self):
        with TemporaryDirectory() as tmp:
            make_repo(Path(tmp), lock="0.3.0", zenodo="v0.3.0", changelog="0.3.0")
            _, problems = check(Path(tmp))
            self.assertEqual(len(problems), 2)
            self.assertIn("Cargo.lock=0.3.0", problems[0])
            self.assertIn("no released section for 0.4.0", problems[1])


if __name__ == "__main__":
    unittest.main()
