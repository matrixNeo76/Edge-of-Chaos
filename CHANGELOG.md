# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/), e il
progetto aderisce a [Semantic Versioning](https://semver.org/lang/it/) per quanto
applicabile a software di ricerca in evoluzione continua.

## [Unreleased]

### Aggiunto
- README multilingua: `README.md` (inglese, ora versione di default), `README.it.md`
  (italiano), `README.zh.md` (cinese), con collegamenti reciproci.

### Rimosso
- `hardware_driver.py` (v1): codice morto, mai importato da nessuno script del
  repository — completamente superato da `hardware_driver_v2.py`.

### Corretto
- Refuso terminologico "sentienza" → "senzienza" (italiano corretto) in
  `README.it.md` e `AGENTS.md`.
- Riferimenti rotti nel README a file esclusi dal repository pubblico
  (`docs_v0.2/...`, `report_campagna_rumore_p0.pdf`).

## [0.1.0] - 2026-09-22

### Aggiunto
- Digital twin metrologico Python (`valenza_metrologia.py`) e sua controparte Rust
  (`valenza_metrologia.rs`, `lib.rs` via PyO3).
- Test operativi di demarcazione (`demarcation_tests.py`): edge of chaos, degenerazione
  causale spettrale, finite-size scaling.
- Driver hardware mock per Keithley DMM / PicoScope (`hardware_driver.py`,
  `hardware_driver_v2.py`).
- Dashboard di visualizzazione a 4 quadranti (`dashboard_valenza.py`).
- Suite di test (`test_valenza_metrologia.py`, `test_hardware_session.py`).
- Containerizzazione (`Dockerfile`, `docker-compose.yml`) e installer
  (`install.sh`, `install.ps1`).
- Entry-point CLI unico (`paper0_cli.py`) e build standalone via PyInstaller
  (`build_exe.ps1`), come alternativa a Docker per l'uso in laboratorio.
- Licenza dual MIT/Apache-2.0, `CITATION.cff`, documentazione di packaging.

### Corretto
- Import rotto in `test_hardware_session.py` (rinominato `hardware_driver-v2.py` →
  `hardware_driver_v2.py`).
- Tipo Rust ambiguo in `valenza_metrologia.rs`/`lib.rs` (`x_val` senza annotazione).
- `Cargo.toml` non collegava `lib.rs` alla build PyO3 (mancava `[lib]` + dipendenza
  `pyo3`).
- Dipendenze mancanti (`matplotlib`, `seaborn`) negli script di installazione.
- Path hardcoded `/workspace/...` in `dashboard_valenza.py` e
  `test_valenza_metrologia.py`, sostituiti con path relativi/`cwd`.
- Generatore di rumore 1/f in `hardware_driver_v2.py` che amplificava la componente
  DC producendo segnali degeneri (media nulla/NaN).

### Noto, non risolto
- `test_hardware_session.py::test_noise_calibration_edge_of_chaos` fallisce in modo
  deterministico per una soglia di tolleranza che non isola il rumore 1/f dalla
  portante sinusoidale deterministica del segnale mock — vedi
  `docs_v0.2/04_ENVIRONMENT_STATUS_AND_FIXES.md`, Bug 8.
