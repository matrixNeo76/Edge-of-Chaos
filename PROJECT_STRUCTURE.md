# Project Structure — Edge-of-Chaos

Map of the public repository. Regenerable build outputs (`target/`, `build/`, `dist/`,
`dist_wheel/`, `output/`, virtual environments, caches) are excluded; see [.gitignore](.gitignore).

The scientific manuscripts and the working notes of the author are kept in folders that are not
part of the public repository (`docs/`, `docs_v0.2/`, `media/`). The published papers are on
Zenodo, in the community
[edge-of-chaos-programme](https://zenodo.org/communities/edge-of-chaos-programme); see
[README.md](README.md#-related-publications) for their DOIs.

```
Edge-of-Chaos/
│
├── thermodynamic_valence.py      Python metrology engine (SDE digital twin, k-NN D_KL, declared proxy of Psi(t))
├── thermodynamic_valence.rs      Same formulas in Rust (std-only binary); same numbers for the same inputs
├── lib.rs                        Native Python extension (PyO3) exposing the Rust engine
├── Cargo.toml / Cargo.lock       Cargo configuration (binary + PyO3 library)
├── demo_pyo3_integration.py      Demonstration of the Rust -> Python binding
│
├── demarcation.py                The three operational demarcation conditions (P0 section 3)
├── necessary_conditions.py       Criteria for three of the necessary conditions (P1 section 3, App. B, D)
├── synthetic_systems.py          Synthetic systems with a known answer (tests, demonstrations)
├── demarcation_tests.py          Compatibility module (re-exports the two modules above)
├── valence_dashboard.py          Four-panel graphical dashboard (matplotlib/seaborn)
├── valence_dashboard.png         Example output (checked in, not generated)
├── hardware_driver_v2.py         Hardware drivers (mocks only: Keithley, PicoScope; preregistered parameters)
├── paper0_cli.py                 Single command-line entry point
│
├── test_*.py                     Tests (pytest); test_engine_parity.py needs the native module
├── notebooks/demo.ipynb          Demonstration notebook (runs on Binder)
├── tools/                        Corpus and repository checks (see tools/README.md)
│
├── install.sh / install.ps1      Environment setup (venv + pip + maturin)
├── build_exe.ps1                 Standalone executable build (PyInstaller)
├── Dockerfile / docker-compose.yml  Container build that runs the test suites
├── requirements.txt / requirements-dev.txt  Python dependencies (runtime / build)
├── references.bib                BibTeX bibliography of the software and the corpus
│
├── AGENTS.md                     Instructions for AI assistants (agents.md convention)
├── CLAUDE.md / GEMINI.md         Stubs pointing to AGENTS.md
├── PERSONA.md                    Identity, voice and content rules for texts of the corpus
├── README.md / README.it.md / README.zh.md  Repository guide (EN, IT, ZH)
├── PROJECT_STRUCTURE.md          This file
├── CHANGELOG.md                  Software version history
├── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
├── LICENSE / LICENSE-MIT / LICENSE-APACHE  Dual licence MIT / Apache-2.0
├── CITATION.cff / .zenodo.json   Citation metadata (GitHub) and Zenodo deposit metadata
├── .coderabbit.yaml              Automated review configuration
└── .github/                      CI workflow, Dependabot, issue and PR templates
```
