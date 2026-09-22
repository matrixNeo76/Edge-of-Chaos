# AGENTS.md — Guida rapida per assistenti AI

Questo file segue la convenzione [agents.md](https://agents.md/), letta da diversi
strumenti agentici (Codex CLI, Cursor, aider, e altri). Per Claude Code e Gemini CLI
vedi `CLAUDE.md` / `GEMINI.md`, che rimandano qui per evitare di duplicare e
disallineare le istruzioni.

## Cos'è questo repository

**Edge-of-Chaos** è la piattaforma software (digital twin Python + estensione nativa
Rust via PyO3) a supporto del programma di ricerca Lakatosiano *P0_Distilled v0.1* su
sentienza interocettiva primaria in substrati neuromorfici continui. Il repository
contiene **solo il software**: i manoscritti scientifici vivono in `docs/` (se presente
nel tuo checkout — non fa parte del repository pubblico, vedi sotto).

**Prima di fare qualunque cosa**, leggi [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
per la mappa del repository, e se presente `docs_v0.2/` per il contesto approfondito
(programma scientifico, glossario matematico, mappa codice↔paper, stato ambiente,
grafo di conoscenza in `docs_v0.2/graph.json`).

## Comandi principali

```bash
# Test
python -m unittest test_valenza_metrologia -v
python -m unittest test_hardware_session -v

# Rust
cargo check --all-targets
cargo run --release --bin valenza_metrologia

# Estensione nativa PyO3 (richiede maturin)
maturin build --release --out dist_wheel
pip install dist_wheel/*.whl

# CLI unico (per packaging / uso rapido)
python paper0_cli.py metrologia|dashboard|demarcazione|hardware|test

# Build eseguibile standalone (no Docker)
./build_exe.ps1
```

## Convenzioni del codice

- Docstring e commenti in italiano nel codice esistente — mantieni la lingua
  coerente all'interno di un file, non mescolare.
- Nessun formatter Python imposto: segui lo stile del file che stai modificando.
- Rust: convenzioni `rustfmt` standard.
- Commenti spiegano il *perché*, non il *cosa* — non ripetere quello che i nomi delle
  variabili già dicono.

## Cosa sapere prima di modificare qualcosa

- Diversi script sono **digital twin/prototipi semplificati**, non l'implementazione
  finale e preregistrata del protocollo sperimentale del paper (vedi
  `docs_v0.2/03_CODE_ARCHITECTURE_MAP.md` se presente nel tuo checkout). Non assumere
  che una funzione implementi fedelmente l'equazione del paper senza verificarlo.
- `test_hardware_session.py::test_noise_calibration_edge_of_chaos` è un fallimento
  **noto e non risolto** per una soglia di tolleranza troppo stretta — non è un
  regressione che hai introdotto tu, vedi `docs_v0.2/04_ENVIRONMENT_STATUS_AND_FIXES.md`.
- `valenza_metrologia.py`, `valenza_metrologia.rs` e `lib.rs` implementano Ψ(t) con
  formule **leggermente diverse tra loro** — disallineamento noto, non un bug da
  correggere silenziosamente senza segnalarlo.

## Cosa NON toccare senza chiedere esplicitamente

- **`docs/`** (se presente): manoscritti scientifici gestiti separatamente per
  submission a rivista, OSF e Zenodo/ORCID. Non modificare, rinominare o cancellare
  nulla lì dentro.
- **`docs_v0.2/13_AR_RESPONSE_SYNTHESIS.md`** (se presente): riservato, rivela storico
  di revisione paritaria — non includerlo mai in output pubblici o in un repository
  pubblico.
- **`media/`**: materiale divulgativo pesante, tenuto fuori dal repository pubblico
  per dimensione — non re-includerlo in commit/push senza una decisione esplicita.
- Licenze (`LICENSE*`) e `CITATION.cff`: non cambiare i termini di licenza senza
  chiedere all'autore.

## Test prima di aprire una PR

Vedi la checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).
