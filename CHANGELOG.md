# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/) as far as applicable to
continuously evolving research software.

## [Unreleased]

### Added
- Multilingual READMEs: `README.md` (English, now the default), `README.it.md`
  (Italian), `README.zh.md` (Chinese), cross-linked at the top of each.

### Changed
- Translated the entire codebase and repository documentation to English
  (previously Italian): filenames, docstrings, comments, CLI output strings,
  argparse help text, and CLI subcommand names
  (`metrologia`→`metrology`, `demarcazione`→`demarcation`, `tutti`→`all`).
- Renamed `valenza_metrologia.py` → `thermodynamic_valence.py`,
  `valenza_metrologia.rs` → `thermodynamic_valence.rs`,
  `dashboard_valenza.py` → `valence_dashboard.py`,
  `dashboard_valenza.png` → `valence_dashboard.png`,
  `test_valenza_metrologia.py` → `test_thermodynamic_valence.py`.
- Renamed the Rust package/binary/PyO3 module accordingly in `Cargo.toml`
  (`valenza_metrologia` → `thermodynamic_valence`,
  `valenza_metrologia_rust` → `thermodynamic_valence_rust`).
- Renamed the result dictionary keys `d_kl_allostasica`→`d_kl_allostatic` and
  `psi_valenza`→`psi_valence` across all Python/Rust implementations and their
  consumers, for consistency with the English codebase.

### Removed
- `hardware_driver.py` (v1): dead code, never imported by any script in the
  repository — fully superseded by `hardware_driver_v2.py`.

### Fixed
- Terminology typo "sentienza" → "senzienza" (correct Italian) in `README.it.md`
  and (previously) `AGENTS.md`.
- Broken README references to files excluded from the public repository
  (`docs_v0.2/...`, `report_campagna_rumore_p0.pdf`).

## [0.1.0] - 2026-09-22

### Added
- Python metrology digital twin (`valenza_metrologia.py`, later renamed) and its
  Rust counterpart (`valenza_metrologia.rs`, `lib.rs` via PyO3).
- Operational demarcation tests (`demarcation_tests.py`): edge of chaos, spectral
  causal degeneracy, finite-size scaling.
- Mock hardware drivers for Keithley DMM / PicoScope (`hardware_driver.py`,
  `hardware_driver_v2.py`).
- 4-quadrant visualization dashboard (`dashboard_valenza.py`, later renamed).
- Test suite (`test_valenza_metrologia.py`, `test_hardware_session.py`).
- Containerization (`Dockerfile`, `docker-compose.yml`) and installers
  (`install.sh`, `install.ps1`).
- Single CLI entry point (`paper0_cli.py`) and standalone PyInstaller build
  (`build_exe.ps1`), as an alternative to Docker for lab use.
- Dual MIT/Apache-2.0 license, `CITATION.cff`, packaging documentation.

### Fixed
- Broken import in `test_hardware_session.py` (renamed `hardware_driver-v2.py` →
  `hardware_driver_v2.py`).
- Ambiguous Rust type in `valenza_metrologia.rs`/`lib.rs` (`x_val` without an
  annotation).
- `Cargo.toml` did not wire `lib.rs` into the PyO3 build (missing `[lib]` +
  `pyo3` dependency).
- Missing dependencies (`matplotlib`, `seaborn`) in the installation scripts.
- Hardcoded `/workspace/...` paths in `dashboard_valenza.py` and
  `test_valenza_metrologia.py`, replaced with relative/`cwd`-based paths.
- 1/f noise generator in `hardware_driver_v2.py` that amplified the DC
  component, producing degenerate signals (zero mean/NaN).

### Known, unresolved
- `test_hardware_session.py::test_noise_calibration_edge_of_chaos` fails
  deterministically due to a tolerance threshold that does not isolate the 1/f
  noise from the mock signal's deterministic sinusoidal carrier — see
  `docs_v0.2/04_ENVIRONMENT_STATUS_AND_FIXES.md`, Bug 8.
