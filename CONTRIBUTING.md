# Contributing to Edge-of-Chaos

Thanks for your interest in this project. Edge-of-Chaos is the digital-twin metrology
platform supporting the research programme on primary interoceptive sentience (see [README.md](README.md)
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
   checks pass (the same ones CI runs):
   ```bash
   uv sync                       # environment from pyproject.toml and uv.lock
   uv run ruff check .
   uv run pytest -q              # code tests and tools/ tests
   uv run python -m tools.public_guard
   cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test --release
   ```
   Optional: `uvx pre-commit install` runs the fast checks before every commit.
3. **Development setup**: `uv sync` (recommended), or `pip install -r requirements-dev.txt`
   for pip users; [install.sh](install.sh) / [install.ps1](install.ps1) script the pip
   setup and build the native module with maturin. Dependencies are declared once in
   `pyproject.toml`; `requirements*.txt` keep the same ranges.
4. **Commits**: Conventional Commits in English (`fix:`, `feat:`, `build:`, `ci:`, `docs:`,
   `chore:`), with the reason in the body; add an entry to `CHANGELOG.md`.

## Code style

- Python: lint with Ruff (rules in `pyproject.toml`); no formatter is enforced, so match
  the style of the file you are editing. Docstrings and comments are in English.
- Rust: `rustfmt` and `clippy` (warnings are errors in CI).
- Tests use cases whose answer is known in advance and fixed seeds.
- Comments explain *why*, not *what* — avoid restating what the code already makes
  obvious from naming.

## Known limitations to be aware of

Before proposing a fix, check
the docstrings of the module and the project's issue tracker — several scripts are
intentionally simplified digital-twin prototypes, not the final preregistered
experimental implementation (see the paper's Declarations section).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating, you agree to abide by its terms.
