"""
verify_citations.py
===================
Check the references of the corpus against Crossref and DataCite.

For each bibliography entry (\\bibitem in the papers, entries of a .bib file) it extracts the
DOI or arXiv ID and fetches the record: DOIs from Crossref, falling back to DataCite (which
registers Zenodo, arXiv and some journal DOIs); arXiv IDs from DataCite, through their DOI
10.48550/arXiv.<id> (the arXiv API answered HTTP 406 to every request from the development
machine). It then compares the record with the text of the entry:
- title: share of the record's title words found in the entry (>= 0.8 to pass);
- year: one of the record's years (issued, print, online) appears in the entry;
- first author: the family name appears in the entry.

Status per entry: verified / discrepancy (with details) / not found / unverifiable now
(network error) / no identifier (to verify by hand). A discrepancy is a prompt for a human
check, not a verdict: online-first and issue years, for instance, legitimately differ.

Results are cached (JSON) so that repeated runs do not query the services again. Requests carry
no personal data. Discrepancies already reviewed by a person can be listed, with the reason, in an
"accepted" TOML file (tools/citation_accepted.toml); they are then reported as "accepted".

Usage
    python -m tools.verify_citations --docs-dir docs --bib references.bib --cache docs_v0.2/.citation_cache.json \
        --accepted tools/citation_accepted.toml
"""

import argparse
import http.client
import json
import tomllib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from tools.build_papers import DEFAULT_PAPERS

USER_AGENT = "edge-of-chaos-corpus-tools/1.0 (+https://github.com/matrixNeo76/Edge-of-Chaos)"
DOI = re.compile(r"(?:doi:\s*|doi\.org/)(10\.\d{4,9}/[^\s,;}]+)", re.I)
ARXIV = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
BS = "\\"
TITLE_THRESHOLD = 0.8
STOPWORDS = {"a", "an", "the", "of", "and", "in", "on", "for", "to", "with", "as", "by", "at", "from", "is"}


def normalise(text):
    """Lower-case ASCII words, with LaTeX accents, LaTeX and HTML markup removed."""
    text = re.sub(r"<[^>]+>", " ", text)                             # <i>kT</i> in Crossref titles
    text = re.sub(r"\\[`'^\"~=.]\{?(\w)\}?", r"\1", text)          # \'e, \"{o}
    text = re.sub(r"\\[a-zA-Z]+\s*", " ", text)                     # \emph, \&
    text = text.replace("$", " ")
    text = text.replace("\u2010", "-").replace("\u2011", "-")          # Unicode hyphens (dual\u2011aspect)
    text = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", "", text)            # non-equilibrium = nonequilibrium
    # Accented letters become ASCII; any other non-ASCII character (e.g. an en dash in
    # "Hodgkin–Huxley") becomes a word separator instead of disappearing.
    text = "".join(c if ord(c) < 128 else (unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode() or " ")
                   for c in text)
    return re.findall(r"[a-z0-9]+", text.lower())


def extract_bibitems(tex_text):
    """(key, text) of each \\bibitem of a paper."""
    start = tex_text.find(BS + "begin{thebibliography}")
    if start < 0:
        return []
    section = tex_text[start:]
    parts = re.split(re.escape(BS) + r"bibitem(?:\[[^\]]*\])?\{([^}]*)\}", section)
    entries = []
    for i in range(1, len(parts), 2):
        text = parts[i + 1].split(BS + "end{thebibliography}")[0]
        entries.append((parts[i].strip(), " ".join(text.split())))
    return entries


def extract_bib_entries(bib_text):
    """(key, text) of each entry of a BibTeX file."""
    entries = []
    for match in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", bib_text, re.S):
        entries.append((match.group(1), " ".join(match.group(2).split())))
    return entries


def identifier_of(entry_text):
    doi = DOI.search(entry_text)
    if not doi:
        field = re.search(r"\bdoi\s*=\s*[{\"]\s*(10\.[^}\"]+)", entry_text, re.I)
        doi = field
    if doi:
        return "doi", doi.group(1).rstrip(".").strip()
    arxiv = ARXIV.search(entry_text) or re.search(r"\beprint\s*=\s*[{\"](\d{4}\.\d{4,5})", entry_text)
    if arxiv:
        return "arxiv", arxiv.group(1)
    return None, None


def http_get(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_crossref(doi, get=http_get):
    data = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    years = set()
    for field in ("issued", "published-print", "published-online", "published"):
        parts = (data.get(field) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            years.add(int(parts[0][0]))
    authors = data.get("author") or []
    return {"title": (data.get("title") or [""])[0], "years": sorted(years),
            "first_author": authors[0].get("family", "") if authors else "",
            "volume": data.get("volume")}


def fetch_datacite(doi, get=http_get):
    data = json.loads(get("https://api.datacite.org/dois/" + urllib.parse.quote(doi)))["data"]["attributes"]
    creators = data.get("creators") or []
    first = creators[0].get("familyName") or (creators[0].get("name", "").split(",")[0]) if creators else ""
    year = data.get("publicationYear")
    return {"title": (data.get("titles") or [{"title": ""}])[0]["title"], "years": [int(year)] if year else [],
            "first_author": first, "volume": None}


def fetch_record(kind, identifier, get=http_get):
    """Crossref first for DOIs, DataCite if Crossref does not know the DOI; DataCite for arXiv."""
    if kind == "arxiv":
        return fetch_datacite(f"10.48550/arXiv.{identifier}", get=get)
    try:
        return fetch_crossref(identifier, get=get)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        return fetch_datacite(identifier, get=get)


def strip_identifiers(entry_text):
    """The entry without DOIs, URLs and identifier fields, which often contain a year."""
    text = re.sub(r"https?://\S+", " ", entry_text)
    text = re.sub(r"\b(?:doi|eprint|url)\s*=\s*[{\"][^}\"]*[}\"]", " ", text, flags=re.I)
    text = DOI.sub(" ", text)
    text = re.sub(r"\b10\.\d{4,9}/\S+", " ", text)
    return ARXIV.sub(" ", text)


def compare(entry_text, record):
    """Problems found comparing an entry with its record (empty list: verified)."""
    problems = []
    bare = strip_identifiers(entry_text)
    entry_words = set(normalise(entry_text))
    title_words = [w for w in normalise(record["title"]) if w not in STOPWORDS]
    if title_words:
        share = sum(w in entry_words for w in title_words) / len(title_words)
        if share < TITLE_THRESHOLD:
            problems.append(f"title differs (record: \"{record['title']}\", {share:.0%} of its words in the entry)")
    # A year counts only as a whole number outside identifiers: 10.1016/j.concog.2019.04.002
    # contains 2019, but an entry dated (2018) with that DOI is still a year mismatch.
    if record["years"] and not any(re.search(rf"(?<!\d){y}(?!\d)", bare) for y in record["years"]):
        problems.append(f"year differs (record: {record['years']})")
    # Records may transliterate umlauts the German way (Dürr as "Duerr"), not only drop them.
    umlauts = re.sub(r"\\\"\{?([aouAOU])\}?", r"\1e", entry_text)
    umlauts = umlauts.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}))
    author = normalise(record["first_author"])
    if author and not set(author) <= entry_words | set(normalise(umlauts)):
        problems.append(f"first author differs (record: {record['first_author']})")
    return problems


PROBLEM_KINDS = ("title", "year", "first author")


def problem_kind(problem):
    return next(kind for kind in PROBLEM_KINDS if problem.startswith(kind))


def load_accepted(path):
    """
    {(key, identifier): (fields, reason)} from the accepted-discrepancies TOML file. An entry
    accepts only the kinds of discrepancy listed in `fields` ("title", "year", "first author").
    """
    if path is None or not path.exists():
        return {}
    items = tomllib.loads(path.read_text(encoding="utf-8")).get("accepted", [])
    accepted = {}
    for item in items:
        fields = set(item.get("fields", []))
        unknown = fields - set(PROBLEM_KINDS)
        if not fields or unknown:
            raise ValueError(f"accepted entry {item.get('key')}: 'fields' must list some of {PROBLEM_KINDS}")
        accepted[(item["key"], item["identifier"])] = (fields, item["reason"])
    return accepted


def verify(entries, cache, get=http_get, pause=1.0, accepted=None):
    """entries: (source, key, text). Returns one result per entry and updates the cache."""
    accepted = accepted or {}
    results = []
    for source, key, text in entries:
        kind, identifier = identifier_of(text)
        if not identifier:
            results.append({"source": source, "key": key, "status": "no identifier", "details": ""})
            continue
        cache_key = f"{kind}:{identifier}"
        record = cache.get(cache_key)
        if record is None:
            try:
                record = fetch_record(kind, identifier, get=get)
                cache[cache_key] = record
            except urllib.error.HTTPError as error:
                status = "not found" if error.code == 404 else "unverifiable now"
                results.append({"source": source, "key": key, "status": status, "details": f"{cache_key}: HTTP {error.code}"})
                continue
            # URLError, ConnectionResetError and timeouts are OSErrors; IncompleteRead is an
            # HTTPException raised while reading the body. None of them may stop the run.
            except (OSError, http.client.HTTPException, ValueError, KeyError) as error:
                results.append({"source": source, "key": key, "status": "unverifiable now", "details": f"{cache_key}: {error}"})
                continue
            time.sleep(pause)
        problems = compare(text, record)
        fields, reason = accepted.get((key, cache_key), (set(), ""))
        if problems and all(problem_kind(p) in fields for p in problems):
            results.append({"source": source, "key": key, "status": "accepted", "details": f"{cache_key}; {reason}"})
            continue
        results.append({"source": source, "key": key, "status": "discrepancy" if problems else "verified",
                        "details": f"{cache_key}; " + "; ".join(problems) if problems else cache_key})
    return results


def report(results):
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines = ["# Citation verification", "", ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())), "",
             "| Source | Key | Status | Details |", "|---|---|---|---|"]
    order = {"discrepancy": 0, "not found": 1, "unverifiable now": 2, "no identifier": 3, "accepted": 4, "verified": 5}
    for r in sorted(results, key=lambda r: (order[r["status"]], r["source"], r["key"])):
        lines.append(f"| {r['source']} | {r['key']} | {r['status']} | {r['details']} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify the references of the corpus against Crossref and DataCite.")
    parser.add_argument("--docs-dir", type=Path)
    parser.add_argument("--papers", nargs="+", default=DEFAULT_PAPERS)
    parser.add_argument("--bib", type=Path, nargs="*", default=[])
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--accepted", type=Path, help="TOML of reviewed, accepted discrepancies")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    entries = []
    if args.docs_dir:
        for name in args.papers:
            path = args.docs_dir / f"{name}.tex"
            if path.exists():
                entries += [(name, key, text) for key, text in extract_bibitems(path.read_text(encoding="utf-8"))]
    for bib in args.bib:
        entries += [(bib.name, key, text) for key, text in extract_bib_entries(bib.read_text(encoding="utf-8"))]

    cache = json.loads(args.cache.read_text(encoding="utf-8")) if args.cache and args.cache.exists() else {}
    try:
        results = verify(entries, cache, accepted=load_accepted(args.accepted))
    finally:  # keep what was fetched even if the run stops
        if args.cache:
            args.cache.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    text = report(results)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text)
    return 1 if any(r["status"] in ("discrepancy", "not found") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
