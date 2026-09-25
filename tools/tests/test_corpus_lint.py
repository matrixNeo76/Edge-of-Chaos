"""Tests for tools/corpus_lint.py on small fixtures."""

import tomllib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.corpus_lint import (
    check_citations,
    check_persona_map,
    check_revisions,
    check_style,
    lint,
    parse_persona_map,
    split_bibliography,
    strip_comments,
)

REPO = Path(__file__).resolve().parents[2]
FACTS = tomllib.loads((REPO / "tools" / "corpus_facts.toml").read_text(encoding="utf-8"))["fact"]

PAPER = r"""\documentclass{article}
\lhead{\small v2.0, rev.~5}
\date{Version 2.0, revision 5 --- September 2026}
\begin{document}
As shown by \citet{kleiner2024} and \citep[see][p.~3]{seth2025, birch2024}. % \citep{commented}
The programme has six negative controls and two new negative controls (Controls~8--9).
The twelve objections examined in \S2--\S13 are reclassified; the ten objections examined in v1.0 were fewer.
The parsimony argument favors illusionism. Crucially, the organisation holds.
\begin{thebibliography}{9}
\bibitem[Kleiner \& Ludwig(2024)]{kleiner2024} Kleiner, J. The organization of consciousness.
\bibitem[Seth(2025)]{seth2025} Seth, A. K.
\bibitem[Unused(2020)]{unused2020} Nobody.
\end{thebibliography}
\end{document}
"""


def write_paper(directory, name, text):
    (directory / f"{name}.tex").write_text(text, encoding="utf-8")


class TestParsing(unittest.TestCase):

    def test_comments_are_removed_but_escaped_percent_kept(self):
        self.assertEqual(strip_comments("50\\% of cases % a comment\nnext"), "50\\% of cases \nnext")

    def test_citations_undefined_and_unused(self):
        body, bibliography = split_bibliography(strip_comments(PAPER))
        undefined, unused = check_citations(body, bibliography)
        self.assertEqual([key for _, key in undefined], ["birch2024"])
        self.assertEqual(unused, ["unused2020"])

    def test_revisions_agree_or_disagree(self):
        self.assertEqual(check_revisions(PAPER), {})
        clash = PAPER.replace("rev.~5", "rev.~4")
        self.assertEqual(check_revisions(clash), {"header": 4, "date": 5, "body (highest)": 5})

    def test_style_ignores_the_bibliography(self):
        body, _ = split_bibliography(PAPER)
        american, avoid, distilled = check_style(body)
        self.assertEqual([word for _, word in american], ["favors"])  # "organization" is in a cited title
        self.assertEqual([phrase for _, phrase in avoid], ["Crucially"])
        self.assertEqual(distilled, [])
        self.assertEqual(check_style("the reference horizon T_ref")[1], [])  # technical use allowed


class TestFacts(unittest.TestCase):

    def run_lint(self, text, name="P3_Critique"):
        with TemporaryDirectory() as tmp:
            write_paper(Path(tmp), name, text)
            return lint(Path(tmp), [name], FACTS)

    def test_consistent_paper_has_only_the_expected_findings(self):
        errors, warnings = self.run_lint(PAPER)
        self.assertEqual(errors, ["P3_Critique:5: citation 'birch2024' is not in the bibliography"])
        self.assertIn("P3_Critique: bibliography entry 'unused2020' is never cited", warnings)

    def test_drifting_counts_are_errors(self):
        drifted = (PAPER.replace("six negative controls", "seven negative controls")
                        .replace("Controls~8--9", "Controls~6--7")
                        .replace("twelve objections examined in", "eleven objections examined in"))
        errors, _ = self.run_lint(drifted)
        joined = "\n".join(errors)
        self.assertIn("negative controls of Paper I: 'seven negative controls'", joined)
        self.assertIn("numbers of the Paper II controls", joined)
        self.assertIn("questions examined by the critical assessment: 'eleven objections examined in", joined)

    def test_history_sentence_is_not_a_count(self):
        errors, _ = self.run_lint(PAPER)
        self.assertFalse(any("ten objections" in e for e in errors))


class TestPersonaMap(unittest.TestCase):

    def test_repository_map_resolves(self):
        entries = parse_persona_map((REPO / "PERSONA.md").read_text(encoding="utf-8"))
        self.assertIn("demarcation.causal_non_separability", entries)
        self.assertEqual(check_persona_map(entries, REPO), [])

    def test_missing_entries_are_reported(self):
        entries = ["demarcation.no_such_function", "no_such_file.py", "calculate_thermodynamic_valence",
                   "thermodynamic_valence.py/.rs", "missing_module.py/.rs"]
        self.assertEqual(check_persona_map(entries, REPO),
                         ["demarcation.no_such_function", "no_such_file.py", "missing_module.py/.rs"])


if __name__ == "__main__":
    unittest.main()
