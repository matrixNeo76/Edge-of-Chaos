"""Tests for tools/zenodo_check.py with simulated Zenodo responses (no network)."""

import hashlib
import json
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.zenodo_check import check_record, report, run

PDF = b"%PDF-1.5 fake paper"
MD5 = hashlib.md5(PDF).hexdigest()


def record(md5=MD5, note="Version 6 (September 2026): adds related work.", community="edge-of-chaos-programme",
           related=("10.5281/zenodo.22895263",), version=None):
    return {"id": 1001, "files": [{"key": "P0.pdf", "checksum": f"md5:{md5}"}],
            "metadata": {"description": f"<p>A programme.</p><p>{note}</p>", "version": version,
                         "communities": [{"id": community}],
                         "related_identifiers": [{"identifier": r, "relation": "isSupplementTo"} for r in related]}}


SPEC = {"name": "P0", "concept": 1, "file": "P0.pdf", "version_note": "Version 6", "related": ["10.5281/zenodo.22895263"]}


class TestCheckRecord(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.docs = Path(self.tmp.name)
        (self.docs / "P0.pdf").write_bytes(PDF)

    def tearDown(self):
        self.tmp.cleanup()

    def test_consistent_record(self):
        self.assertEqual(check_record(SPEC, record(), self.docs, "edge-of-chaos-programme"), [])

    def test_each_kind_of_problem(self):
        cases = {
            "MD5 differs": record(md5="0" * 32),
            "version note 'Version 6' not in the description": record(note="Version 5 (September 2026)"),
            "not in the community": record(community="other"),
            "related identifier 10.5281/zenodo.22895263 missing": record(related=()),
        }
        for expected, rec in cases.items():
            with self.subTest(expected):
                problems = check_record(SPEC, rec, self.docs, "edge-of-chaos-programme")
                self.assertEqual(len(problems), 1)
                self.assertIn(expected, problems[0])

    def test_md5_not_compared_without_docs_dir(self):
        problems = check_record(SPEC, record(), None, "edge-of-chaos-programme")
        self.assertEqual(problems, ["MD5 not compared: --docs-dir not given"])

    def test_missing_file_and_software_version(self):
        problems = check_record({"name": "x", "file": "other.pdf"}, record(), self.docs)
        self.assertIn("file 'other.pdf' not in the latest version", problems[0])
        software = {"name": "Software", "version": "v0.4.0"}
        self.assertEqual(check_record(software, record(version="v0.4.0")), [])
        self.assertIn("expected 'v0.4.0'", check_record(software, record(version="v0.3.0"))[0])


class TestRun(unittest.TestCase):

    def test_network_errors_are_reported_per_record(self):
        def get(url, timeout=30):
            if "/1/" in url:
                return json.dumps(record())
            raise urllib.error.URLError("offline")
        config = {"community": "edge-of-chaos-programme",
                  "record": [dict(SPEC, concept=1), {"name": "P1", "concept": 2}]}
        results = run(config, get=get)
        self.assertEqual(results[0]["problems"], ["MD5 not compared: --docs-dir not given"])
        self.assertIn("cannot read the record", results[1]["problems"][0])
        text = report(results)
        self.assertIn("| P0 | 1001 | MD5 not compared", text)

    def test_unreadable_local_file_is_reported_per_record(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "P0.pdf").mkdir()  # a directory where the PDF should be: reading fails
            config = {"record": [dict(SPEC, concept=1), {"name": "Software", "concept": 1, "version": None}]}
            results = run(config, Path(tmp), get=lambda url, timeout=30: json.dumps(record()))
            self.assertIn("cannot check the record", results[0]["problems"][0])
            self.assertEqual(results[1]["problems"], [])


if __name__ == "__main__":
    unittest.main()
