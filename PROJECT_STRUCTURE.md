# Project Structure — Edge-of-Chaos (P0_Distilled v0.1)

Generated: 2026-09-22, updated after renaming the Italian-named scripts to English
and adding `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`. Excludes regenerable build artifacts
(`venv_build/`, `target/`, `dist/`, `build/`, `dist_wheel/`, `output/`,
`__pycache__/`, `.ruff_cache/`, `paper0.spec`) — see [.gitignore](.gitignore).

```
Edge-of-Chaos/
│
├── docs/                              [3.5 MB]  MANUSCRIPTS AND SUBMISSION MATERIAL (not in the public repo)
│   ├── P0_Distilled_v0.1.tex/.pdf               Distilled v0.1 paper (root of the repo)
│   ├── P0_Distilled.tex                         Previous version of the distilled paper
│   ├── P1_Main.tex/.pdf                         Paper 1 — main Lakatosian programme (v16.2)
│   ├── P2_SelfAgency.tex/.pdf                   Paper 2 — minimal self-agency protocol (v2.0)
│   ├── P3_Critique.tex/.pdf                     Paper 3 — external critical assessment (v2.0)
│   ├── C1_Philosophy.tex/.pdf                   Companion 1 — philosophical argument for Postulate 2
│   ├── C2_PowerAnalysis.tex/.pdf                Companion 2 — Monte Carlo power analysis
│   ├── AR_Response.tex/.pdf                     Author's response to 4 rounds of review ⚠️ confidential
│   ├── ES_Summary.tex/.pdf                      Executive summary
│   ├── COVER_LETTER.md, cover_letter_editor.pdf Journal submission material
│   ├── DECLARATIONS.md, SIGNIFICANCE_STATEMENT.md, SUGGESTED_REVIEWERS.md
│   ├── LAY_SUMMARY.md                           Plain-language summary (195 words)
│   ├── SUBMISSION_CHECKLIST.md, SUBMISSION_GUIDE.md, SUGGERIMENTI.txt
│   ├── EMAILS_TO_EXPERTS.md, ONLINE_PRESENCE_SETUP.md
│   ├── P0_Piano_Acquisti_e_BOM_Laboratorio.md   Lab procurement plan / bill of materials
│   ├── lista_strumentazione_hardware_lab.pdf
│   ├── report_campagna_rumore_p0.pdf            Report on the percolative noise simulation campaign
│   ├── articolo_medium_p0_distilled*.pdf        Popular-science articles (Medium)
│   ├── document_relationships.txt               ASCII diagram of the dependencies between documents
│   └── README.md                                Corpus index, suggested reading order
│
├── docs_v0.2/                         [156 KB]  AI-ORIENTED DISTILLED DOCUMENTATION (derived, unofficial, not in the public repo)
│   ├── README.md                                Index
│   ├── 01_PROGRAMME_OVERVIEW.md                 Summary of the Lakatosian programme (from P0_Distilled)
│   ├── 02_MATH_GLOSSARY.md                      Symbol/equation glossary
│   ├── 03_CODE_ARCHITECTURE_MAP.md              Script ↔ paper-section map, implementation fidelity
│   ├── 04_ENVIRONMENT_STATUS_AND_FIXES.md       Python+Rust environment audit, verified bugs and fixes
│   ├── 05_PACKAGING_PYINSTALLER.md              Standalone packaging (PyInstaller) vs Docker
│   ├── 06_ZENODO_PREPARATION.md                 What to separate for a Zenodo deposit
│   ├── 07_KNOWLEDGE_GRAPH.md + graph.json       Knowledge graph (nodes/relations), Markdown + JSON for LLMs
│   ├── 08_P1_MAIN_SYNTHESIS.md                  Synthesis of P1_Main (extended/definitive version)
│   ├── 09_P2_SELFAGENCY_SYNTHESIS.md            Synthesis of P2_SelfAgency (self-agency extension)
│   ├── 10_P3_CRITIQUE_SYNTHESIS.md              Synthesis of P3_Critique (external critical assessment)
│   ├── 11_C1_PHILOSOPHY_SYNTHESIS.md            Synthesis of C1_Philosophy (argument for Postulate 2)
│   ├── 12_C2_POWERANALYSIS_SYNTHESIS.md         Synthesis of C2_PowerAnalysis (Monte Carlo power analysis)
│   └── 13_AR_RESPONSE_SYNTHESIS.md              ⚠️ Confidential — review history, never public
│
├── media/                             [383 MB]  PROMOTIONAL MULTIMEDIA MATERIAL (not in the public repo)
│   ├── Decodificare_il_Paper_0.mp4
│   ├── Il_Protocollo_del_Paper_0.mp4
│   ├── La_Sentienza_Neuromorfica.mp4
│   ├── Beyond_Digital_AI.mp4
│   ├── Coscienza_Artificiale.mp4
│   ├── How_dead_matter_becomes_sentient.m4a      ⚠️ 104 MB, exceeds GitHub's hard limit (100 MB/file)
│   ├── Architettura_della_Self-Agency.png
│   ├── Il_Mistero_del_Rumore_1_f.png
│   ├── Operational_Framework_for_Interoceptive_Sentience.png
│   ├── Orchestrating_Memristive_Chaos.pptx
│   └── Continuous_Sentience_Physics.pptx
│
├── (root)                                        CODE — DIGITAL TWIN AND METROLOGY
│   ├── thermodynamic_valence.py                 Python metrology engine (SDE, k-NN D_KL, Psi(t))
│   ├── thermodynamic_valence.rs                 Same engine, pure Rust (zero-dependency binary)
│   ├── lib.rs                                   Native Python extension via PyO3
│   ├── Cargo.toml / Cargo.lock                  Cargo config (bin + lib PyO3)
│   ├── demo_pyo3_integration.py                 Demo of the Rust→Python binding
│   │
│   ├── demarcation.py                           The 3 operational demarcation conditions (P0 section 3)
│   ├── necessary_conditions.py                  Criteria for 3 necessary conditions (P1 section 3, App. B, D)
│   ├── synthetic_systems.py                     Synthetic systems with a known answer (tests, demos)
│   ├── demarcation_tests.py                     Compatibility module (re-exports the two modules above)
│   ├── valence_dashboard.py                     4-quadrant graphical dashboard (matplotlib/seaborn)
│   ├── valence_dashboard.png                    Example visual artifact (checked in, not generated)
│   │
│   ├── hardware_driver_v2.py                    Hardware driver (mock, Keithley/PicoScope, preregistered lab parameters)
│   │
│   ├── test_thermodynamic_valence.py            Unit tests for the metrology engine
│   ├── test_demarcation.py                      Tests of the demarcation conditions
│   ├── test_necessary_conditions.py             Tests of the necessary-condition criteria
│   ├── test_hardware_session.py                 Unit tests for the hardware session
│   │
│   ├── paper0_cli.py                            Single subcommand entry point (for packaging)
│   │
│   ├── install.sh / install.ps1                 Automated environment setup (venv + pip + maturin)
│   ├── build_exe.ps1                            Standalone executable build (PyInstaller, no Docker)
│   ├── Dockerfile / docker-compose.yml          Containerization for reproducibility
│   │
│   ├── requirements.txt / requirements-dev.txt  Pinned Python dependencies (runtime / build)
│   ├── references.bib                           BibTeX bibliography (45 citations)
│   │
│   ├── AGENTS.md                                Instructions for AI assistants (cross-tool standard)
│   ├── CLAUDE.md / GEMINI.md                    Stubs pointing to AGENTS.md
│   ├── README.md / README.it.md / README.zh.md  Repository guide (EN default, IT, ZH)
│   ├── PROJECT_STRUCTURE.md                     This file
│   ├── CHANGELOG.md                             Software version history
│   ├── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
│   ├── LICENSE / LICENSE-MIT / LICENSE-APACHE   Dual license MIT/Apache-2.0
│   ├── CITATION.cff                             Software citation metadata
│   ├── .github/                                 Issue/PR templates
│   └── .gitignore / .gitattributes
```

## Note on sizes for a possible Zenodo deposit

| Component | Size | Consideration |
|---|---|---|
| Code (root, excluding artifacts) | ~190 KB | Negligible |
| `docs/` (manuscripts) | 3.5 MB | Negligible, but excluded from the public repo (active journal submission) |
| `docs_v0.2/` | 156 KB | To be decided whether to include (contains a synthesis of not-yet-public content — see below) |
| `media/` | **383 MB** | Dominant — a single file (104 MB) exceeds GitHub's hard limit. Excluded from the public repo |

See [docs_v0.2/06_ZENODO_PREPARATION.md](docs_v0.2/06_ZENODO_PREPARATION.md) for the
full recommendation on what to include in a Zenodo deposit/public repository and what
to keep separate.
