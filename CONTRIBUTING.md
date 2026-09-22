# Contributing to Edge-of-Chaos

Thanks for your interest in this project. Edge-of-Chaos is the digital-twin metrology
platform supporting the P0_Distilled research programme (see [README.md](README.md)
and [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)). It is research software, not a
finished product — contributions are welcome, but please read this before opening an
issue or a pull request.

## Scope

This repository contains **only the software** (Python/Rust digital twin, hardware
drivers, tests, packaging). The scientific manuscripts and preregistered protocol are
handled separately (see the paper's own Declarations section on data/code
availability). Contributions here should be about the *code*: correctness, tests,
packaging, documentation of the implementation — not about the scientific claims of
the research programme itself (for that, see the paper's own channels).

## How to contribute

1. **Bug reports**: open an issue describing the command you ran, the expected vs.
   actual output, and your environment (OS, Python version, Rust version if relevant).
2. **Pull requests**: fork, create a branch, make your change, and make sure the
   existing test suites pass:
   ```bash
   python -m unittest test_valenza_metrologia -v
   python -m unittest test_hardware_session -v
   cargo check --all-targets
   ```
3. **Development setup**: see [install.sh](install.sh) / [install.ps1](install.ps1)
   for a scripted setup, or [requirements-dev.txt](requirements-dev.txt) for the
   pinned dependency versions this project was last verified against.

## Code style

- Python: no enforced formatter yet: match the existing style of the file you're
  editing (docstrings in Italian are the existing convention for this codebase — keep
  it consistent within a file rather than mixing languages mid-file).
- Rust: standard `rustfmt` conventions.
- Comments explain *why*, not *what* — avoid restating what the code already makes
  obvious from naming.

## Known limitations to be aware of

Before proposing a fix, check
[docs_v0.2/03_CODE_ARCHITECTURE_MAP.md](docs_v0.2/03_CODE_ARCHITECTURE_MAP.md) (if
present in your checkout) or the project's own issue tracker — several scripts are
intentionally simplified digital-twin prototypes, not the final preregistered
experimental implementation (see the paper's Declarations section).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating, you agree to abide by its terms.
