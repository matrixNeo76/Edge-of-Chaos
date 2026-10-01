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

    def test_version_in_zenodo_notes_must_end(self):
        with TemporaryDirectory() as tmp:
            make_repo(Path(tmp), zenodo="v0.4.01")
            _, problems = check(Path(tmp))
            self.assertIn(".zenodo.json (notes)=0.4.01", problems[0])  # read in full, so it disagrees


class TestCitationMetadata(unittest.TestCase):

    def write_metadata(self, directory, zenodo_title="Edge-of-Chaos", zenodo_licence="MIT", zenodo_orcid="0000-0001"):
        make_repo(directory)
        (directory / "Cargo.toml").write_text(
            '[package]\nname = "thermodynamic_valence"\nversion = "0.4.0"\nlicense = "MIT OR Apache-2.0"\n', encoding="utf-8")
        (directory / "CITATION.cff").write_text(
            "cff-version: 1.2.0\ntitle: Edge-of-Chaos\nauthors:\n  - family-names: Doe\n"
            '    orcid: "https://orcid.org/0000-0001"\nversion: 0.4.0\nlicense:\n  - MIT\n  - Apache-2.0\n',
            encoding="utf-8")
        (directory / ".zenodo.json").write_text(json.dumps({
            "title": zenodo_title, "license": zenodo_licence, "notes": "v0.4.0 fixes things.",
            "creators": [{"name": "Doe", "orcid": zenodo_orcid}]}), encoding="utf-8")

    def test_agreeing_metadata(self):
        with TemporaryDirectory() as tmp:
            self.write_metadata(Path(tmp))
            self.assertEqual(check(Path(tmp)), ("0.4.0", []))

    def test_each_disagreement_is_reported(self):
        with TemporaryDirectory() as tmp:
            self.write_metadata(Path(tmp), zenodo_title="Other", zenodo_licence="GPL-3.0", zenodo_orcid="0000-0002")
            _, problems = check(Path(tmp))
            self.assertEqual(len(problems), 3)
            self.assertIn("title differs", problems[0])
            self.assertIn("ORCIDs differ", problems[1])
            self.assertIn("GPL-3.0 is not one of", problems[2])


if __name__ == "__main__":
    unittest.main()
