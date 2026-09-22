## Descrizione

Cosa cambia e perché.

## Tipo di modifica

- [ ] Bug fix
- [ ] Nuova funzionalità
- [ ] Documentazione
- [ ] Refactoring / pulizia

## Checklist

- [ ] `python -m unittest test_valenza_metrologia -v` passa
- [ ] `python -m unittest test_hardware_session -v` passa (o il fallimento noto è
      documentato in `docs_v0.2/04_ENVIRONMENT_STATUS_AND_FIXES.md`)
- [ ] `cargo check --all-targets` passa (se hai modificato codice Rust)
- [ ] Ho aggiornato `CHANGELOG.md`
- [ ] Ho aggiornato la documentazione rilevante, se applicabile
