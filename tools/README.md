# Tools for the corpus and the repository

Checks that catch the recurring errors of the revision rounds: inconsistencies between papers,
unverified or wrong citations, build problems, mismatches between local files and published
records, and version drift. None of them edits a paper: they report, and every correction to a
`.tex` file goes through the author's approval.

All tools use the Python standard library only, carry no personal data in their requests, and
need no credentials. Run them from the repository root.

| Tool | What it checks | Typical command |
|---|---|---|
| `build_papers.py` | Backs up, compiles (3 pdflatex passes), checks control characters, LaTeX errors, undefined citations/references and new overfull boxes; writes pages, sizes (decimal kB, as Zenodo shows them) and MD5. Builds are reproducible (`SOURCE_DATE_EPOCH`). | `python -m tools.build_papers --docs-dir docs --backup-suffix _pre_round4` |
| `corpus_lint.py` | Citations not in the bibliography, revision numbers that disagree, shared facts outside their allowed values (`corpus_facts.toml`), theory-to-code map of `PERSONA.md`; warnings for uncited entries, American spellings, avoid-list expressions. | `python -m tools.corpus_lint --docs-dir docs --facts tools/corpus_facts.toml --persona PERSONA.md` |
| `verify_citations.py` | DOIs and arXiv IDs against Crossref and DataCite: title, year, first author. Cached; reviewed discrepancies accepted with a reason in `citation_accepted.toml`. | `python -m tools.verify_citations --docs-dir docs --bib references.bib --cache <cache.json> --accepted tools/citation_accepted.toml` |
| `zenodo_check.py` | Latest version of each record in `zenodo_records.toml`: file and MD5 against the local copy, version note, community, related identifiers, software version. | `python -m tools.zenodo_check --config tools/zenodo_records.toml --docs-dir docs` |
| `check_versions.py` | Same release version in `Cargo.toml`, `Cargo.lock`, `CITATION.cff`, `.zenodo.json`, with a released `CHANGELOG.md` section. Runs in CI. | `python -m tools.check_versions` |

Each tool accepts `--report <file.md>` (except `check_versions`) and exits with 1 when it finds
errors, so it can run in CI. Tests: `python -m pytest -q tools/tests` (fixtures and simulated HTTP
responses; no network, no LaTeX).

## In a revision round

1. Before writing the spec: `corpus_lint` and `verify_citations`; their findings enter the spec.
2. After applying the approved texts: `build_papers` (backup, build, checks, MD5 table).
3. After the new versions are published: update `zenodo_records.toml` and run `zenodo_check`.

## Configuration files

- `corpus_facts.toml`: facts shared across papers (counts, numbering) and their allowed values.
  Change a fact only when the programme changes, never to silence an inconsistency.
- `citation_accepted.toml`: discrepancies checked by a person, with the reason.
- `zenodo_records.toml`: concept record IDs, file names and expected version notes.
