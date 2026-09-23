# AGENTS.md — Quick guide for AI assistants

This file follows the [agents.md](https://agents.md/) convention, read by several
agentic tools (Codex CLI, Cursor, aider, and others). For Claude Code and Gemini CLI
see `CLAUDE.md` / `GEMINI.md`, which point back here to avoid duplicating and
drifting the instructions apart.

## What this repository is

**Edge-of-Chaos** is the software platform (Python digital twin + native Rust
extension via PyO3) supporting the research programme *P0_Distilled v0.1* on
primary interoceptive sentience in continuous neuromorphic substrates. The
repository contains **only the software**: the scientific manuscripts live in
`docs/` (if present in your checkout — not part of the public repository, see
below). The canonical corpus in `docs/` uses a Lakatosian research-programme
framing (hard core / protective belt / progressiveness criteria); a parallel,
experimental reframing using Laudan's research-traditions framework
(revisable core assumption / problem-solving effectiveness / pursuit versus
acceptance) exists in `docs/laudan_variant/` (if present) — see that folder's
own `README.md` for its status and how it relates to the canonical corpus.
Neither supersedes the other unless the author says so.

**Before doing anything**, read [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for the
repository map, and if present `docs_v0.2/` for deeper context (scientific
programme, math glossary, code↔paper map, environment status, knowledge graph in
`docs_v0.2/graph.json`).

## Main commands

```bash
# Tests
python -m unittest test_thermodynamic_valence -v
python -m unittest test_hardware_session -v

# Rust
cargo check --all-targets
cargo run --release --bin thermodynamic_valence

# Native PyO3 extension (requires maturin)
maturin build --release --out dist_wheel
pip install dist_wheel/*.whl

# Single CLI (for packaging / quick use)
python paper0_cli.py metrology|dashboard|demarcation|hardware|test

# Standalone executable build (no Docker)
./build_exe.ps1

# Compile the LaTeX papers in docs/ to PDF (MiKTeX installed locally — see below)
pdflatex -interaction=nonstopmode -halt-on-error docs/P1_Main.tex
pdflatex -interaction=nonstopmode -halt-on-error docs/P1_Main.tex  # second pass for refs/TOC
```

## Local LaTeX toolchain (MiKTeX)

MiKTeX is installed locally on this machine (`winget install MiKTeX.MiKTeX`),
with on-the-fly package auto-install enabled
(`initexmf --set-config-value "[MPM]AutoInstall=1"`), so `pdflatex`/`xelatex`/
`lualatex` are available without manual package management. Its `bin\x64` is on
the user PATH; if a shell doesn't see it yet (stale environment in a long-lived
session), use the full path:
`C:\Users\<user>\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe`.

**Before recompiling any paper in `docs/`:** those PDFs are the versions
published on Zenodo with live DOIs — back up the current PDF first (e.g. into
`docs/_pdf_backup_pre_v2/`) before overwriting it, and remember that publishing
a corrected PDF to Zenodo requires a "New version" upload there, not just a
local recompile — see `docs_v0.2/14_DISSEMINATION_OUTREACH_MAP.md` and
`docs_v0.2/15_OUTREACH_DRAFTS.md` if present for the surrounding context.
Compile twice (pdflatex reruns) to resolve cross-references/TOC/bookmarks, and
clean up `.aux`/`.log`/`.out` afterwards — they're build artifacts, not
sources.

## Code conventions

- Docstrings and comments are in English across the codebase — keep the language
  consistent within a file, do not mix.
- No enforced Python formatter: follow the style of the file you are editing.
- Rust: standard `rustfmt` conventions.
- Comments explain the *why*, not the *what* — do not restate what variable names
  already make obvious.

## What to know before changing anything

- Several scripts are **simplified digital-twin prototypes**, not the final,
  preregistered implementation of the paper's experimental protocol (see
  `docs_v0.2/03_CODE_ARCHITECTURE_MAP.md` if present in your checkout). Do not
  assume a function faithfully implements the paper's equation without checking.
- `test_hardware_session.py::test_noise_calibration_edge_of_chaos` is a **known,
  unresolved failure** due to a tolerance threshold that is too tight — it is not a
  regression you introduced, see `docs_v0.2/04_ENVIRONMENT_STATUS_AND_FIXES.md`.
- `thermodynamic_valence.py`, `thermodynamic_valence.rs`, and `lib.rs` all
  implement the **same practical proxy** of Psi(t) — a log-ratio of the raw
  dissipative components plus a KL-divergence penalty — which is **not
  algebraically equivalent** to the formal Psi(t) defined in `P1_Main.tex`
  Appendix F (normalized entropy-production rates against a hardware-calibrated
  `S_crit_dot`). This is documented explicitly in-line in all three code files
  and in P1_Main/ES_Summary — it is a known, disclosed simplification (the
  digital twin doesn't yet estimate `S_crit_dot`), not a bug to silently "fix"
  by making the code match the paper without discussing it with the author first.

## Rigorous Scientific Determinism for Paper Analysis

This applies whenever you read, summarize, critique, or extract claims from
any paper in `docs/` **and** `docs/laudan_variant/` — the risk below is not
specific to either; it has shown up in both.

- **Never hallucinate or extrapolate a physical/hardware metric.** This
  covers lithography/fabrication process details, memristor device
  parameters, energy-per-spike figures (pJ/fJ), entropy-production rates,
  benchmark numbers, time constants, and any other quantitative claim
  presented as an empirical or literature value. If a value is not explicit
  in the text you're reading, write **"Value not present in text"** — do not
  infer it from a similar-sounding paper, round a nearby number, or fill the
  gap with a plausible-sounding estimate.
- **Verify every citation and DOI externally before treating it as real.**
  A citation that is well-formatted (author, year, venue) is not evidence
  that it exists — this corpus has both real citations that were formatted
  as if fabricated (missing authors, e.g. the original "Nano Letters (2024)"
  entry) and citations that turned out to be genuinely unverifiable after a
  real search (e.g. "CAT (2026)", "CDF (2025)" in the original P0 draft,
  removed after a web search found nothing). Formatting quality tells you
  nothing about whether the source exists; only an actual search does. See
  `docs_v0.2/16_REVIEW_OF_EXTERNAL_ANALYSES.md` (if present) for a worked
  example of this verification process, including a case where the
  verifier's own search missed a real number because the search pattern was
  too narrow — a reminder that a confident "not found" is only as good as
  the search that produced it.
- **Keep digital-twin/simulation claims and physical-substrate claims
  strictly separate.** The software in this repository is a simplified
  digital-twin prototype (see above) — never present a simulation output,
  a code-computed value, or a model assumption as if it were a measurement
  on real hardware, and never present a paper's physical-substrate claim as
  already validated by the digital twin unless the text says so explicitly.
- **Use a fixed extraction schema when cataloguing claims from a manuscript.**
  For each numeric or empirical claim, record it as:

  | Claim | Location in source | Status |
  |---|---|---|
  | *(the value/claim as stated)* | *(see below)* | Confirmed in text / Value not present in text / Externally verified / Unverifiable |

  For **"Location in source"**: use `file:line` when working from the
  `.tex`/`.md` source. When working directly from a compiled **PDF**, use
  `file:page` or a section/paragraph reference instead — never invent a line
  number for a binary file you haven't extracted text from with a tool that
  actually reports one.

## What NOT to touch without explicitly asking

- **`docs/`** (if present): scientific manuscripts managed separately for journal
  submission, OSF, and Zenodo/ORCID. Do not modify, rename, or delete anything in
  there.
- **`docs_v0.2/13_AR_RESPONSE_SYNTHESIS.md`** (if present): confidential, reveals
  peer-review history — never include it in public output or a public repository.
- **`media/`**: heavy promotional material, kept out of the public repository due to
  size — do not re-include it in a commit/push without an explicit decision.
- Licenses (`LICENSE*`) and `CITATION.cff`: do not change the license terms without
  asking the author.

## Tests before opening a PR

See the checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).
