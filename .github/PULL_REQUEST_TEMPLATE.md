## Descrizione

Cosa cambia e perché.

## Tipo di modifica

- [ ] Bug fix
- [ ] Nuova funzionalità
- [ ] Documentazione
- [ ] Refactoring / pulizia
- [ ] Strumenti, CI o dipendenze

## Checklist

- [ ] `ruff check .` passa
- [ ] `python -m pytest -q` passa (test del codice e di `tools/`)
- [ ] Se ho modificato codice Rust: `cargo test --release --locked` passa, e il test di parità
      Python/Rust (`test_engine_parity.py`, con il modulo nativo installato) passa
- [ ] Se ho modificato una formula: docstring e deviazioni dai paper sono dichiarate
- [ ] Ho aggiornato `CHANGELOG.md`
- [ ] Ho aggiornato la documentazione rilevante, se applicabile
