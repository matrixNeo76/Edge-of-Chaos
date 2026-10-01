import os
import tempfile
import unittest
from pathlib import Path

from tools import round as round_tool


class RoundTest(unittest.TestCase):
    def test_combined_report_lists_every_step_and_its_result(self):
        results = [("corpus_lint", (0, "# Corpus lint\n\nno errors", "")),
                   ("verify_citations", (1, "", "Traceback: network down"))]
        text = round_tool.combine("pre", results)
        self.assertIn("| corpus_lint | ok |", text)
        self.assertIn("| verify_citations | errors |", text)
        self.assertIn("# Corpus lint", text)
        self.assertIn("Traceback: network down", text)  # a tool without a report shows its output

    def test_repo_state_outside_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(round_tool.repo_state(tmp), "not a Git repository")

    def test_graph_status_without_a_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                code, _, note = round_tool.graph_status()
            finally:
                os.chdir(cwd)
        self.assertEqual(code, 0)
        self.assertIn("no knowledge graph", note)

    def test_refuses_to_run_without_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertEqual(round_tool.main(["pre"]), 1)
            finally:
                os.chdir(cwd)
        self.assertFalse(Path(tmp).exists())


if __name__ == "__main__":
    unittest.main()
