# AGENTS.md — Instructions for AI assistants

This file follows the [agents.md](https://agents.md/) convention. `CLAUDE.md` and `GEMINI.md`
point here, so that the instructions live in one place. `tools/AGENTS.md` adds the rules for the
corpus and repository tools; the nearest file applies.

Before writing or revising texts of the corpus, read `PERSONA.md` (identity, voice, content
rules). If present, `docs_v0.2/WORKFLOW.md` describes the author's internal workflow and takes
precedence for anything private (revision rounds, Zenodo, outreach, local toolchain).

## What this repository is

**Edge-of-Chaos** is the software of a research programme on necessary physical conditions for
primary interoceptive sentience in continuous neuromorphic substrates: a Python digital twin and
metrology platform, with a native Rust engine exposed through PyO3. The repository contains only
the software; the papers are on Zenodo (DOIs in [README.md](README.md)), and their sources live in
folders that are not part of the public repository (`docs/`, `docs_v0.2/`, `media/`, if present in
your checkout). Map of the files: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Setup

```bash
uv sync                                   # Python environment from pyproject.toml + uv.lock (3.11-3.14)
uv sync --group build                     # + maturin and PyInstaller
uv run maturin build --release --locked --out dist_wheel && uv pip install dist_wheel/*.whl
```

Rust stable with rustfmt and clippy (`rust-toolchain.toml`). pip users: `pip install -r
requirements-dev.txt` (same ranges as `pyproject.toml`).

## Commands

```bash
uv run ruff check .                       # lint (rules in pyproject.toml)
uv run pytest -q                          # code tests + tools/ tests; the parity test needs the native module
uv run mypy                               # types of tools/
uv run python -m tools.public_guard       # no internal names in public files
uv run python -m tools.check_versions     # release version and citation metadata agree
cargo fmt --check && cargo clippy --all-targets --locked -- -D warnings
cargo test --release --locked
python paper0_cli.py metrology|dashboard|demarcation|conditions|hardware|test
```

Corpus tools (need `docs/`; see [tools/README.md](tools/README.md)):

```bash
python -m tools.round pre                 # before a revision spec: corpus_lint + verify_citations
python -m tools.round build --backup-suffix _pre_roundN   # after approved texts: backup, build, MD5
python -m tools.round post                # after publishing: zenodo_check + knowledge-graph status
```

## Definition of done

- **Code change**: ruff, pytest, mypy and the public guard pass; for Rust, fmt, clippy, tests and
  the Python/Rust parity test pass; formulas and deviations from the papers are stated in the
  docstrings; `CHANGELOG.md` updated.
- **Corpus change**: never without the author's approval of the exact texts; then
  `tools.round build`, visual check of the PDFs, MD5 table for the Zenodo upload.
- **Release**: `check_versions` passes, tag and GitHub release, Zenodo record checked with
  `zenodo_check`.

## Commits and pull requests

- Conventional Commits in English (`fix:`, `feat:`, `build:`, `ci:`, `docs:`, `chore:`), with the
  reason in the body. One topic per branch and pull request.
- A pull request needs green CI; CodeRabbit reviews it in Italian.
- Never push to `main`, merge, tag, release or publish without the author's explicit confirmation.

## Code conventions

- Docstrings and comments in English; comments explain the *why*, not the *what*.
- Python: Ruff decides lint; no formatter is enforced, so follow the style of the file.
- Rust: rustfmt and clippy; warnings are errors in CI.
- Tests use cases whose answer is known in advance and fixed seeds (`numpy.random.default_rng`).
- Dependencies are declared in `pyproject.toml`; keep `requirements*.txt` in step
  (`tools/tests/test_dependency_sync.py`).

## Before changing anything

- Several scripts are **simplified digital-twin prototypes**, not the preregistered
  implementation of the experimental protocol. Do not assume a function implements a paper's
  equation without checking its docstring.
- `thermodynamic_valence.py`, `thermodynamic_valence.rs` and `lib.rs` implement the **same
  practical proxy** of Psi(t) (a log-ratio of the raw dissipative components plus a KL-divergence
  penalty), which is **not algebraically equivalent** to the formal Psi(t) of Paper I, Appendix F
  (entropy-production rates normalised by a hardware-calibrated `S_crit_dot`). The difference is
  disclosed in the code and in the papers. It is not a bug to "fix" by making the code match the
  paper without discussing it with the author.

## Rigorous Scientific Determinism for Paper Analysis

This applies whenever you read, summarize, critique, or extract claims from any paper of the
corpus, including the Laudan variant in `docs/laudan_variant/` (if present).

- **Never hallucinate or extrapolate a physical/hardware metric.** This covers
  lithography/fabrication process details, memristor device parameters, energy-per-spike figures
  (pJ/fJ), entropy-production rates, benchmark numbers, time constants, and any other
  quantitative claim presented as an empirical or literature value. If a value is not explicit in
  the text you're reading, write **"Value not present in text"**: do not infer it from a
  similar-sounding paper, round a nearby number, or fill the gap with a plausible estimate.
- **Verify every citation and DOI externally before treating it as real.** A well-formatted
  citation is not evidence that it exists: this corpus has had real citations formatted as if
  fabricated (missing authors, e.g. the original "Nano Letters (2024)" entry) and citations that
  turned out to be unverifiable after a real search (e.g. "CAT (2026)", "CDF (2025)" in an early
  draft, removed after a web search found nothing). Only an actual search tells; `tools.verify_citations`
  checks DOIs and arXiv IDs against Crossref and DataCite. A confident "not found" is only as good
  as the search that produced it.
- **Keep digital-twin/simulation claims and physical-substrate claims strictly separate.** Never
  present a simulation output, a code-computed value or a model assumption as a measurement on
  real hardware, and never present a paper's physical-substrate claim as validated by the digital
  twin unless the text says so explicitly. No experiment on a physical substrate has been carried
  out.
- **Use a fixed extraction schema when cataloguing claims from a manuscript:**

  | Claim | Location in source | Status |
  |---|---|---|
  | *(the value/claim as stated)* | *(see below)* | Confirmed in text / Value not present in text / Externally verified / Unverifiable |

  Use `file:line` when working from the `.tex`/`.md` source; from a compiled PDF use `file:page`
  or a section reference, never an invented line number.

## Boundaries

**Never, without the author's explicit request:**

- modify, rename or delete anything in `docs/`, `docs_v0.2/` or `media/`;
- copy content of `docs_v0.2/` or `docs/` into public files: some of it is confidential
  (`docs_v0.2/WORKFLOW.md` lists which);
- use the internal name of the entry-point paper, the author's employer or personal data in
  public files (`tools/public_guard.py` enforces it);
- change the licence terms (`LICENSE*`, `CITATION.cff`, `.zenodo.json`).

**Ask first:** new dependencies, changes to CI or Dependabot, anything that sends data outside
the repository (emails, uploads, publications).
