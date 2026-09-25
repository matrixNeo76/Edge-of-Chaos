"""Tests for tools/build_papers.py on fixtures (no LaTeX installation needed)."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.build_papers import (
    build_report,
    find_control_characters,
    main,
    parse_log,
    split_overfull,
    zenodo_size,
)

LOG = r"""This is pdfTeX, Version 3.141592653-2.6-1.40.26 (MiKTeX 24.1)
LaTeX Warning: Citation `kleiner2024' on page 3 undefined on input line 168.
LaTeX Warning: Reference `sec:limits' on page 5 undefined on input line 210.
LaTeX Warning: Citation `kleiner2024' on page 4 undefined on input line 170.
Overfull \hbox (6.92761pt too wide) in paragraph at lines 215--216
Overfull \hbox (2.1pt too wide) in paragraph at lines 300--301
Overfull \hbox (52.60684pt too wide) in paragraph at lines 508--509
Overfull \hbox (21.78319pt too wide) in alignment at lines 96--96
Output written on P0_Distilled_v0.1.pdf (17 pages, 367956 bytes).
"""


class TestControlCharacters(unittest.TestCase):

    def test_detects_the_tab_left_by_a_stray_sed(self):
        # A sed replacement once turned "\citep" into a TAB followed by "itep"
        text = "line one\nThe theorem is published \titep{kleiner2024}.\n"
        self.assertEqual(find_control_characters(text), [(2, 26, "U+0009")])

    def test_clean_text_and_newlines(self):
        self.assertEqual(find_control_characters("a\r\nb\nc"), [])
        self.assertEqual(find_control_characters("x\x7fy"), [(1, 2, "U+007F")])


class TestLogParsing(unittest.TestCase):

    def test_extracts_outcome_citations_references_and_overfull(self):
        info = parse_log(LOG)
        self.assertEqual((info["pages"], info["bytes"]), (17, 367956))
        self.assertEqual(info["undefined_citations"], ["kleiner2024"])
        self.assertEqual(info["undefined_references"], ["sec:limits"])
        self.assertEqual(info["errors"], [])
        self.assertEqual([o["lines"] for o in info["overfull"]], ["215--216", "508--509", "96--96"])

    def test_errors_and_missing_output(self):
        info = parse_log("! Undefined control sequence.\nl.12 \\foo\n")
        self.assertEqual(info["errors"], ["Undefined control sequence."])
        self.assertIsNone(info["pages"])

    def test_baseline_separates_known_from_new_overfull(self):
        info = parse_log(LOG)
        known, new = split_overfull(info["overfull"], ["215--216", "96--96"])
        self.assertEqual([o["lines"] for o in known], ["215--216", "96--96"])
        self.assertEqual([o["lines"] for o in new], ["508--509"])

    def test_zenodo_size_is_decimal(self):
        # Zenodo showed 355.9 kB for a file that Windows showed as 348 KB
        self.assertEqual(zenodo_size(355858), "355.9 kB")


class TestEndToEndWithoutBuild(unittest.TestCase):

    def test_no_build_mode_reports_md5_and_problems(self):
        with TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / "Paper.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
            (docs / "Paper.pdf").write_bytes(b"%PDF-1.5 fake")
            (docs / "Paper.log").write_text(LOG, encoding="latin-1")
            report_path = docs / "report.md"
            status = main(["--docs-dir", str(docs), "--papers", "Paper", "--no-build",
                           "--report", str(report_path)])
            self.assertEqual(status, 1)  # undefined citation and reference, new overfull
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("undefined citations: ['kleiner2024']", report)
            self.assertIn("`", report)

            # Recording the overfull boxes in the baseline leaves only the undefined entries
            status = main(["--docs-dir", str(docs), "--papers", "Paper", "--no-build", "--update-baseline"])
            baseline = json.loads((docs / ".build_baseline.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline["Paper"], ["215--216", "508--509", "96--96"])

    def test_report_lists_every_paper(self):
        row = {"paper": "P", "pages": 3, "bytes": 1000, "zenodo_size": "1.0 kB", "md5": "abc",
               "control_characters": [], "errors": [], "undefined_citations": [],
               "undefined_references": [], "new_overfull": [], "epoch": 1, "ok": True}
        report = build_report([row])
        self.assertIn("| P | 3 | 1000 | 1.0 kB | `abc` | ok |", report)
        self.assertIn("SOURCE_DATE_EPOCH", report)


if __name__ == "__main__":
    unittest.main()
