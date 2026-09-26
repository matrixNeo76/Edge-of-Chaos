"""Tests for tools/verify_citations.py with simulated Crossref and DataCite responses (no network)."""

import http.client
import json
import unittest
import urllib.error

from tools.verify_citations import (
    compare,
    extract_bib_entries,
    extract_bibitems,
    identifier_of,
    normalise,
    report,
    verify,
)

TEX = r"""\begin{thebibliography}{9}
\bibitem[Kleiner \& Ludwig(2024)]{kleiner2024}
Kleiner, J., \& Ludwig, T. (2024). The case for neurons: a no-go theorem for consciousness on a chip. \emph{Neuroscience of Consciousness}, 2024(1), niae037. doi:10.1093/nc/niae037

\bibitem[Butlin et al.(2023)]{butlin2023}
Butlin, P., et al. (2023). Consciousness in artificial intelligence: insights from the science of consciousness. arXiv:2308.08708.

\bibitem[Lakatos(1970)]{lakatos1970}
Lakatos, I. (1970). Falsification and the methodology of scientific research programmes.
\end{thebibliography}
"""

BIB = """@article{Doerig2019,
  author = {Doerig, Adrien and Schurger, Aaron},
  title = {The unfolding argument},
  year = {2019},
  doi = {10.1016/j.concog.2019.04.002}
}
"""

CROSSREF = {"message": {"title": ["The case for neurons: a no-go theorem for consciousness on a chip"],
                        "issued": {"date-parts": [[2024, 11]]}, "author": [{"family": "Kleiner"}],
                        "volume": "2024"}}
DATACITE_ARXIV = {"data": {"attributes": {
    "titles": [{"title": "Consciousness in Artificial Intelligence: Insights from the Science of Consciousness"}],
    "publicationYear": 2023, "creators": [{"familyName": "Butlin", "name": "Butlin, Patrick"}]}}}
DATACITE_ZENODO = {"data": {"attributes": {
    "titles": [{"title": "Necessary Physical Conditions for Primary Interoceptive Sentience"}],
    "publicationYear": 2026, "creators": [{"name": "Iavarone, Francesco"}]}}}


def fake_get(url, timeout=30):
    if "crossref" in url and "niae037" in url:
        return json.dumps(CROSSREF)
    if "datacite" in url and "arXiv.2308.08708" in url:
        return json.dumps(DATACITE_ARXIV)
    if "datacite" in url and "zenodo" in url:
        return json.dumps(DATACITE_ZENODO)
    raise urllib.error.HTTPError(url, 404, "Not Found", None, None)


class TestExtraction(unittest.TestCase):

    def test_bibitems_and_identifiers(self):
        entries = dict(extract_bibitems(TEX))
        self.assertEqual(list(entries), ["kleiner2024", "butlin2023", "lakatos1970"])
        self.assertEqual(identifier_of(entries["kleiner2024"]), ("doi", "10.1093/nc/niae037"))
        self.assertEqual(identifier_of(entries["butlin2023"]), ("arxiv", "2308.08708"))
        self.assertEqual(identifier_of(entries["lakatos1970"]), (None, None))

    def test_bibtex_entries(self):
        (key, text), = extract_bib_entries(BIB)
        self.assertEqual(key, "Doerig2019")
        self.assertEqual(identifier_of(text), ("doi", "10.1016/j.concog.2019.04.002"))

    def test_normalise_removes_latex_accents_and_markup(self):
        self.assertEqual(normalise(r"Chollat-Namy \& Mont\'evil, \emph{Organisms}"),
                         ["chollatnamy", "montevil", "organisms"])

    def test_normalise_handles_crossref_markup_and_unicode_dashes(self):
        # Two false discrepancies of the first real run
        self.assertEqual(normalise("Computing Around <i>kT</i>"), ["computing", "around", "kt"])
        self.assertEqual(normalise(r"around $kT$"), ["around", "kt"])
        self.assertEqual(normalise("Memristor, Hodgkin\u2013Huxley"), ["memristor", "hodgkin", "huxley"])
        self.assertEqual(normalise("Hodgkin--Huxley"), ["hodgkin", "huxley"])
        # A non-breaking hyphen in a DataCite title matches an ASCII hyphen in the entry
        self.assertEqual(normalise("dual\u2011aspect monist"), normalise("dual-aspect monist"))


class TestComparison(unittest.TestCase):

    def test_matching_entry_is_verified(self):
        record = {"title": "The case for neurons", "years": [2024], "first_author": "Kleiner", "volume": None}
        self.assertEqual(compare("Kleiner, J. (2024). The case for neurons.", record), [])

    def test_each_kind_of_discrepancy(self):
        record = {"title": "A completely different paper title", "years": [2021], "first_author": "Smith", "volume": None}
        problems = compare("Kleiner, J. (2024). The case for neurons.", record)
        self.assertEqual(len(problems), 3)
        self.assertTrue(problems[0].startswith("title differs"))


class TestVerify(unittest.TestCase):

    def test_statuses_and_cache(self):
        entries = [("P0", key, text) for key, text in extract_bibitems(TEX)]
        entries.append(("refs.bib", "Doerig2019", extract_bib_entries(BIB)[0][1]))
        entries.append(("P0", "iavarone2026a", "Iavarone, F. (2026). Necessary physical conditions for primary "
                                               "interoceptive sentience. Zenodo. doi:10.5281/zenodo.22896026"))
        cache = {}
        results = {r["key"]: r["status"] for r in verify(entries, cache, get=fake_get, pause=0)}
        # arXiv through DataCite; the Zenodo DOI is unknown to Crossref (404) and found on DataCite
        self.assertEqual(results, {"kleiner2024": "verified", "butlin2023": "verified",
                                   "lakatos1970": "no identifier", "Doerig2019": "not found",
                                   "iavarone2026a": "verified"})
        self.assertIn("doi:10.1093/nc/niae037", cache)

        # A second run uses the cache and makes no request
        def no_network(url, timeout=30):
            raise AssertionError("network used despite the cache")
        again = verify(entries[:2], cache, get=no_network, pause=0)
        self.assertEqual([r["status"] for r in again], ["verified", "verified"])

    def test_hyphenated_and_joined_spellings_match(self):
        record = {"title": "Non-equilibrium brain dynamics as a signature of consciousness", "years": [2021],
                  "first_author": "Perl", "volume": None}
        self.assertEqual(compare("Sanz Perl, Y. (2021). Nonequilibrium brain dynamics as a signature of "
                                 "consciousness.", record), [])

    def test_umlaut_transliterated_as_e_matches(self):
        record = {"title": "Rationally warranted promise", "years": [2025], "first_author": "Duerr", "volume": None}
        self.assertEqual(compare("D\\\"urr, P. M., \\& Fischer, E. (2025). Rationally warranted promise.", record), [])
        self.assertEqual(compare("Dürr, P. M. (2025). Rationally warranted promise.", record), [])

    def test_year_inside_an_identifier_does_not_count(self):
        # The record says 2019; the entry says 2018 and its DOI contains 2019
        record = {"title": "The unfolding argument", "years": [2019], "first_author": "Doerig", "volume": None}
        entry = "Doerig, A. (2018). The unfolding argument. doi:10.1016/j.concog.2019.04.002"
        self.assertEqual(len(compare(entry, record)), 1)
        self.assertTrue(compare(entry, record)[0].startswith("year differs"))
        self.assertEqual(compare(entry.replace("(2018)", "(2019)"), record), [])

    def test_accepted_discrepancies_only_for_their_fields(self):
        title = "The case for neurons: a no-go theorem for consciousness on a chip"
        entry = [("P0", "kleiner2024", f"Kleiner, J. (2023). {title}. doi:10.1093/nc/niae037")]
        (plain,) = verify(entry, {}, get=fake_get, pause=0)
        self.assertEqual(plain["status"], "discrepancy")  # year only
        accepted = {("kleiner2024", "doi:10.1093/nc/niae037"): ({"year"}, "online-first year, checked")}
        (result,) = verify(entry, {}, get=fake_get, pause=0, accepted=accepted)
        self.assertEqual(result["status"], "accepted")
        self.assertIn("checked", result["details"])
        # A different mismatch in the same entry is still reported
        wrong_author = [("P0", "kleiner2024", f"Smith, J. (2023). {title}. doi:10.1093/nc/niae037")]
        (result,) = verify(wrong_author, {}, get=fake_get, pause=0, accepted=accepted)
        self.assertEqual(result["status"], "discrepancy")

    def test_network_errors_are_not_reported_as_missing(self):
        for error in (urllib.error.URLError("no network"), ConnectionResetError("reset"),
                      http.client.IncompleteRead(b"partial")):
            def offline(url, timeout=30, error=error):
                raise error
            with self.subTest(type(error).__name__):
                (result,) = verify([("P0", "k", "doi:10.1000/abc")], {}, get=offline, pause=0)
                self.assertEqual(result["status"], "unverifiable now")

    def test_report_puts_problems_first(self):
        text = report([{"source": "P0", "key": "a", "status": "verified", "details": ""},
                       {"source": "P0", "key": "b", "status": "discrepancy", "details": "year differs"}])
        self.assertLess(text.index("| b |"), text.index("| a |"))


if __name__ == "__main__":
    unittest.main()
