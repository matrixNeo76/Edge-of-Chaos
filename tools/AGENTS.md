# AGENTS.md — tools/

Rules for the corpus and repository tools, in addition to the root [AGENTS.md](../AGENTS.md).
What each tool does and when to run it: [README.md](README.md).

- **Report, never edit a paper.** No tool writes to a `.tex` file; corrections go through the
  author's approval of the exact texts.
- **Standard library only** at run time (the tests may use pytest and hypothesis). No credentials,
  no personal data in requests.
- **Exit code 1 on errors**, a Markdown report with `--report`, so that every tool can run in CI
  and inside `tools/round.py`.
- **Tests without network or LaTeX:** fixtures and simulated HTTP responses
  (`tools/tests/`). Every new check comes with a test of what it accepts and what it rejects.
- **Types:** `uv run mypy` must pass for `tools/`.
- **Configuration in TOML next to the tool** (`corpus_facts.toml`, `citation_accepted.toml`,
  `zenodo_records.toml`, `public_guard.toml`). Change a fact or an accepted discrepancy only with
  its reason, never to silence a real finding.
- Paths of the private folders (`docs/`, `docs_v0.2/`) are arguments or defaults, never
  assumptions: the public repository does not contain them.
