# Struttura del Progetto — Edge-of-Chaos (P0_Distilled v0.1)

Generato: 2026-09-22, aggiornato dopo l'aggiunta di `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`
e il riordino di `media/`. Esclude artefatti di build rigenerabili (`venv_build/`,
`target/`, `dist/`, `build/`, `dist_wheel/`, `output/`, `__pycache__/`,
`.ruff_cache/`, `paper0.spec`) — vedi [.gitignore](.gitignore).

```
Edge-of-Chaos/
│
├── docs/                              [3.5 MB]  MANOSCRITTI E MATERIALE DI SUBMISSION
│   ├── P0_Distilled_v0.1.tex/.pdf               Paper distillato v0.1 (radice del repo)
│   ├── P0_Distilled.tex                         Versione precedente del distillato
│   ├── P1_Main.tex/.pdf                         Paper 1 — programma Lakatosiano principale (v16.2)
│   ├── P2_SelfAgency.tex/.pdf                   Paper 2 — protocollo self-agency minimale (v2.0)
│   ├── P3_Critique.tex/.pdf                     Paper 3 — valutazione critica esterna (v2.0)
│   ├── C1_Philosophy.tex/.pdf                   Companion 1 — argomento filosofico per il Postulato 2
│   ├── C2_PowerAnalysis.tex/.pdf                Companion 2 — power analysis Monte Carlo
│   ├── AR_Response.tex/.pdf                     Risposta dell'autore a 4 round di revisione ⚠️ riservato
│   ├── ES_Summary.tex/.pdf                      Executive summary
│   ├── COVER_LETTER.md, cover_letter_editor.pdf Materiale di submission per rivista
│   ├── DECLARATIONS.md, SIGNIFICANCE_STATEMENT.md, SUGGESTED_REVIEWERS.md
│   ├── LAY_SUMMARY.md                           Sintesi divulgativa (195 parole)
│   ├── SUBMISSION_CHECKLIST.md, SUBMISSION_GUIDE.md, SUGGERIMENTI.txt
│   ├── EMAILS_TO_EXPERTS.md, ONLINE_PRESENCE_SETUP.md
│   ├── P0_Piano_Acquisti_e_BOM_Laboratorio.md   Piano acquisti / bill of materials laboratorio
│   ├── lista_strumentazione_hardware_lab.pdf
│   ├── report_campagna_rumore_p0.pdf            Report campagna di simulazione rumore percolativo
│   ├── articolo_medium_p0_distilled*.pdf        Articoli divulgativi (Medium)
│   ├── document_relationships.txt               Diagramma ASCII delle dipendenze tra documenti
│   └── README.md                                Indice del corpus, ordine di lettura consigliato
│
├── docs_v0.2/                         [156 KB]  DOCUMENTAZIONE DISTILLATA AI-ORIENTED (derivata, non ufficiale)
│   ├── README.md                                Indice
│   ├── 01_PROGRAMME_OVERVIEW.md                 Sintesi del programma Lakatosiano (da P0_Distilled)
│   ├── 02_MATH_GLOSSARY.md                      Glossario simboli/equazioni
│   ├── 03_CODE_ARCHITECTURE_MAP.md              Mappa script ↔ sezione del paper, fedeltà d'implementazione
│   ├── 04_ENVIRONMENT_STATUS_AND_FIXES.md       Audit ambiente Python+Rust, bug e fix verificati
│   ├── 05_PACKAGING_PYINSTALLER.md              Packaging standalone (PyInstaller) vs Docker
│   ├── 06_ZENODO_PREPARATION.md                 Cosa separare per un deposito Zenodo
│   ├── 07_KNOWLEDGE_GRAPH.md + graph.json       Grafo di conoscenza (nodi/relazioni), Markdown + JSON per LLM
│   ├── 08_P1_MAIN_SYNTHESIS.md                  Sintesi di P1_Main (versione estesa/definitiva)
│   ├── 09_P2_SELFAGENCY_SYNTHESIS.md            Sintesi di P2_SelfAgency (estensione self-agency)
│   ├── 10_P3_CRITIQUE_SYNTHESIS.md              Sintesi di P3_Critique (valutazione critica esterna)
│   ├── 11_C1_PHILOSOPHY_SYNTHESIS.md            Sintesi di C1_Philosophy (argomento per il Postulato 2)
│   ├── 12_C2_POWERANALYSIS_SYNTHESIS.md         Sintesi di C2_PowerAnalysis (power analysis Monte Carlo)
│   └── 13_AR_RESPONSE_SYNTHESIS.md              ⚠️ Riservato — storico revisione, mai pubblico
│
├── media/                             [383 MB]  MATERIALE MULTIMEDIALE DIVULGATIVO
│   ├── Decodificare_il_Paper_0.mp4
│   ├── Il_Protocollo_del_Paper_0.mp4
│   ├── La_Sentienza_Neuromorfica.mp4
│   ├── Beyond_Digital_AI.mp4
│   ├── Coscienza_Artificiale.mp4
│   ├── How_dead_matter_becomes_sentient.m4a      ⚠️ 104 MB, supera il limite hard di GitHub (100 MB/file)
│   ├── Architettura_della_Self-Agency.png
│   ├── Il_Mistero_del_Rumore_1_f.png
│   ├── Operational_Framework_for_Interoceptive_Sentience.png
│   ├── Orchestrating_Memristive_Chaos.pptx
│   └── Continuous_Sentience_Physics.pptx
│
├── (radice)                                      CODICE — DIGITAL TWIN E METROLOGIA
│   ├── valenza_metrologia.py                    Engine metrologico Python (SDE, D_KL k-NN, Psi(t))
│   ├── valenza_metrologia.rs                    Stesso engine, Rust puro (binario zero-dipendenze)
│   ├── lib.rs                                   Estensione nativa Python via PyO3
│   ├── Cargo.toml / Cargo.lock                  Config Cargo (bin + lib PyO3)
│   ├── demo_pyo3_integration.py                 Demo del binding Rust→Python
│   │
│   ├── demarcation_tests.py                     Test delle 3 condizioni di demarcazione operativa
│   ├── dashboard_valenza.py                     Dashboard grafica a 4 quadranti (matplotlib/seaborn)
│   ├── dashboard_valenza.png                    Artifact visivo di esempio (checked-in, non generato)
│   │
│   ├── hardware_driver_v2.py                    Driver hardware (mock, Keithley/PicoScope, parametri di laboratorio preregistrati)
│   │
│   ├── test_valenza_metrologia.py               Unit test motore di metrologia
│   ├── test_hardware_session.py                 Unit test sessione hardware
│   │
│   ├── paper0_cli.py                            Entry-point unico a sottocomandi (per packaging)
│   │
│   ├── install.sh / install.ps1                 Setup automatico ambiente (venv + pip + maturin)
│   ├── build_exe.ps1                            Build eseguibile standalone (PyInstaller, no Docker)
│   ├── Dockerfile / docker-compose.yml          Containerizzazione per riproducibilità
│   │
│   ├── requirements.txt / requirements-dev.txt  Dipendenze Python pinnate (runtime / build)
│   ├── references.bib                           Bibliografia BibTeX (45 citazioni)
│   │
│   ├── AGENTS.md                                Istruzioni per assistenti AI (standard cross-tool)
│   ├── CLAUDE.md / GEMINI.md                    Stub che rimandano ad AGENTS.md
│   ├── README.md / README.it.md / README.zh.md  Guida del repository (EN default, IT, ZH)
│   ├── PROJECT_STRUCTURE.md                     Questo file
│   ├── CHANGELOG.md                             Storico delle versioni del software
│   ├── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
│   ├── LICENSE / LICENSE-MIT / LICENSE-APACHE   Dual license MIT/Apache-2.0
│   ├── CITATION.cff                             Metadati di citazione del software
│   ├── .github/                                 Template issue/PR
│   └── .gitignore / .gitattributes
```

## Nota sulle dimensioni per un eventuale deposito Zenodo

| Componente | Dimensione | Considerazione |
|---|---|---|
| Codice (root, esclusi artefatti) | ~190 KB | Trascurabile |
| `docs/` (manoscritti) | 3.5 MB | Trascurabile, ma esclusa dal repo pubblico (submission attiva a rivista) |
| `docs_v0.2/` | 156 KB | Da decidere se includere (contiene sintesi di contenuto non ancora pubblico — vedi sotto) |
| `media/` | **383 MB** | Dominante — un singolo file (104 MB) supera il limite hard di GitHub. Esclusa dal repo pubblico |

Vedi [docs_v0.2/06_ZENODO_PREPARATION.md](docs_v0.2/06_ZENODO_PREPARATION.md) per la
raccomandazione completa su cosa includere in un deposito Zenodo/repository pubblico e
cosa tenere separato.
