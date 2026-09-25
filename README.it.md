# Edge-of-Chaos

*Leggi in: [English](README.md) | **Italiano** | [中文](README.zh.md)*

> **Piattaforma di Metrologia Computazionale e Hardware-in-the-Loop** per la verifica sperimentale della senzienza primaria, della valenza termodinamica $\Psi(t)$ e delle condizioni di demarcazione operativa nei substrati materiali continui (*Mortal Computation*), sviluppata secondo il programma di ricerca Lakatosiano (*P0_Distilled v0.1*).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22895263.svg)](https://doi.org/10.5281/zenodo.22895263)

---

## 📌 Indice
1. [Inquadramento Scientifico](#-inquadramento-scientifico)
2. [Architettura del Repository](#-architettura-del-repository)
3. [Formulazione Matematica Fondamentale](#-formulazione-matematica-fondamentale)
4. [Requisiti e Installazione Rapida](#-requisiti-e-installazione-rapida)
5. [Guida all'Uso degli Script](#-guida-alluso-degli-script)
   - [Metrologia e Digital Twin (`thermodynamic_valence.py` / `.rs`)](#1-metrologia-e-digital-twin)
   - [Interfacciamento Hardware Reale (`hardware_driver_v2.py`)](#2-interfacciamento-hardware-reale)
   - [Demarcazione e Condizioni Necessarie (`demarcation.py`, `necessary_conditions.py`)](#3-demarcazione-e-condizioni-necessarie)
   - [Visualizzazione e Dashboard (`valence_dashboard.py`)](#4-visualizzazione-e-dashboard)
6. [Eseguibile Standalone (senza Docker)](#-eseguibile-standalone-senza-docker-per-pc-di-laboratorio)
7. [Containerizzazione e Replicabilità (Docker)](#-containerizzazione-e-replicabilità-docker)
8. [Pubblicazioni Correlate](#-pubblicazioni-correlate)
9. [Bibliografie e Riferimenti](#-bibliografie-e-riferimenti)

---

## 🔬 Inquadramento Scientifico

Il **Paper 0 (P0_Distilled_v0.1)** propone un modello di demarcazione fisica e termodinamica per valutare la candidatura di substrati fisici continui (array di memristori diffusivi ionici $SiO_x{:}Ag$, memristori di Mott $VO_2$, e reti percolative di nanofili d'argento) a supportare la senzienza primaria interocettiva.

A differenza delle intelligenze artificiali digitali su architetture von Neumann/GPU (*Immortal Computation*), soggette al *No-Go Theorem for Consciousness on a Chip* (Kleiner & Ludwig, 2024), la piattaforma valuta il substrato direttamente *in materia* verificando:
* **Non-separabilità causale** tra la fisica del materiale e la computazione.
* **Memoria non-Markoviana intrinseca** legata alla dinamica ionica e stocastica.
* **Dinamica efficace stato-dipendente** sotto regolazione allostasica preventiva ($\Psi(t)$).

---

## 📂 Architettura del Repository

```
Edge-of-Chaos/
├── thermodynamic_valence.py       # Engine metrologico Python (proxy di dissipazione, k-NN KL-divergence, Psi(t))
├── thermodynamic_valence.rs       # Engine metrologico in Rust nativo ad alte prestazioni (zero-copy)
├── lib.rs                        # Modulo PyO3 FFI per compilare Rust in estensione nativa Python
├── Cargo.toml                    # Configurazione Cargo / PyO3 per l'infrastruttura Rust
├── demo_pyo3_integration.py      # Script dimostrativo di integrazione e benchmark FFI Rust/Python
│
├── hardware_driver_v2.py         # Driver PyVISA/SCPI per Keithley DMM e PicoScope con auto-compliance
├── test_hardware_session.py      # Test suite estesa per la verifica dei limiti di sicurezza hardware
├── demarcation.py                # Le 3 condizioni operative di demarcazione (non separabilità, memoria non markoviana, dipendenza dallo stato)
├── necessary_conditions.py       # Criteri per 3 condizioni necessarie (edge of chaos, degenerazione causale, stabilità degli esponenti)
├── synthetic_systems.py          # Sistemi sintetici con risposta nota (test e dimostrazioni)
├── demarcation_tests.py          # Modulo di compatibilità (riesporta i due moduli sopra)
├── valence_dashboard.py          # Generatore della dashboard grafica a 4 quadranti (Seaborn/Matplotlib)
├── valence_dashboard.png         # Artifact visivo ad alta risoluzione di una simulazione di esempio
│
├── test_thermodynamic_valence.py  # Test unitari per la validazione matematica delle SDE e di Psi(t)
├── test_demarcation.py           # Test delle condizioni di demarcazione su sistemi con risposta nota
├── test_necessary_conditions.py  # Test dei criteri per le condizioni necessarie
├── test_engine_parity.py         # Parità Python/Rust a parità di ingressi (richiede il modulo nativo)
├── paper0_cli.py                 # Entry-point unico a sottocomandi
├── notebooks/demo.ipynb          # Notebook dimostrativo (eseguibile su Binder)
├── references.bib                # Database BibTeX completo di 49 citazioni (IIT, FEP, Chua, Lakatos)
│
├── install.sh                    # Script di installazione per Linux / macOS
├── install.ps1                   # Script di installazione per Windows PowerShell
├── build_exe.ps1                 # Build eseguibile standalone (PyInstaller, no Docker)
├── Dockerfile                    # Container Docker multi-stage (Python 3.11 + Rust)
└── docker-compose.yml            # Orchestrazione Docker per la replicabilità di laboratorio
```

Vedi [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) per l'albero completo e annotato
(incluse le parti del progetto che restano fuori da questo repository pubblico, come
i manoscritti scientifici in fase di revisione editoriale).

---

## 🧮 Formulazione Matematica Fondamentale

### 1. Funzionale di Valenza Termodinamica $\Psi(t)$
$$\Psi_{allo}(t) = \alpha \cdot \ln\left(1 + \frac{\sigma_{ex}(t)}{\sigma_{hk}(t) + \epsilon}\right) - \beta \cdot \mathcal{D}_{KL}\big(P(x) \,||\, P_{target}\big) + \gamma \cdot G_{pred}(t)$$

* **$\sigma_{ex}$ / $\sigma_{hk}$**: Nei paper, le produzioni di entropia in eccesso e di housekeeping della decomposizione NESS di Hatano-Sasa. **Nel codice attuale sono proxy euristici, non grandezze di Hatano-Sasa**: $\sigma_{hk}$ scala come $\sigma_{noise}^2/dt$, quindi dipende dal passo di integrazione, e la vera produzione di housekeeping del modello a una variabile del digital twin è identicamente nulla. Confrontare valori di $\Psi(t)$ solo a parità di $dt$. Uno stimatore corretto (ad es. Sekizawa, Ito & Oizumi, *Phys. Rev. X* 14, 041003, 2024) non è ancora implementato.
* **$\mathcal{D}_{KL}$**: Divergenza probabilistica non-parametrica ($k$-NN) dalla nicchia target di stabilità allostasica.
* **$G_{pred}$**: Guadagno predittivo della copia efferente generata dal livello $A_2$ sul livello $A_1$.

### 2. Condizione di Attività Locale (Edge of Chaos)
$$\text{Re}\big(Y(j\omega)\big) < 0 \quad \text{per } \omega \in [\omega_1, \omega_2] \quad \land \quad \text{Tr}\big(J(E_k)\big) < 0, \quad \det\big(J(E_k)\big) > 0$$

### 3. Degenerazione Causale Spettrale
$$\rho_{deg} = \frac{\dim\left(\ker(J - \lambda_0 I)\right)}{\|\Delta W_{therm}\|}$$

---

## ⚡ Requisiti e Installazione Rapida

### Requisiti di Sistema
* **Python 3.9+** con `numpy`, `scipy`, `matplotlib`, `seaborn`
* **Rust / Cargo** (opzionale, consigliato per il modulo nativo ad alte prestazioni)

### Automated Setup

* **Linux / macOS:**
  ```bash
  chmod +x install.sh
  ./install.sh
  ```

* **Windows (PowerShell):**
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\install.ps1
  ```

---

## 💻 Guida all'Uso degli Script

### 1. Metrologia e Digital Twin
Per eseguire la simulazione del substrato $A_1/A_2$ e calcolare la valenza $\Psi(t)$:
```bash
python3 thermodynamic_valence.py
```

Per eseguire i test unitari di validazione matematica:
```bash
python3 test_thermodynamic_valence.py
```

### 2. Interfacciamento Hardware Reale
Per avviare la sessione hardware con compliance di sicurezza attiva ($V_{comp}=1.5\text{V}, I_{comp}=1.0\text{mA}$) e rumore $1/f$ calibrato ($\sigma_{noise}=0.10$):
```bash
python3 hardware_driver_v2.py
```
Di default il driver gira in **modalità mock** — nessuno strumento fisico è richiesto.
L'accesso a strumentazione reale (PyVISA) è disponibile ma opzionale.

Per verificare la sicurezza e i limiti di compliance tramite la test suite hardware:
```bash
python3 test_hardware_session.py
```

### 3. Demarcazione e Condizioni Necessarie
`demarcation.py` implementa le tre **condizioni operative di demarcazione** di P0
(sezione 3): non separabilità causale (rango numerico della matrice di risposta rispetto a
un modello di sovrapposizione lineare), memoria non markoviana (informazione mutua
condizionata oltre l'ordine di Markov k, confrontata con surrogati IAAFT) e dinamica
effettiva dipendente dallo stato (Jacobiani in tre regioni dello spazio delle fasi).
`necessary_conditions.py` implementa i criteri per tre delle cinque **condizioni
necessarie** (P1 sezione 3, Appendici B e D): edge of chaos, degenerazione causale con il
raggio robusto rho_deg e stabilità degli esponenti. Entrambi lavorano su dati misurati o
stimati; le dimostrazioni seguenti li eseguono su sistemi sintetici con risposta nota:
```bash
python3 paper0_cli.py demarcation   # surrogati ridotti; protocollo: --surrogates 100 --percentile 99
python3 paper0_cli.py conditions
```
I paper fissano l'ordine di Markov massimo a k_max = 500, che uno stimatore k-nearest-neighbour
non può gestire; k_max è un parametro (vedi la docstring di `demarcation.py`).

### 4. Visualizzazione e Dashboard
Per generare la dashboard grafica `valence_dashboard.png`:
```bash
python3 valence_dashboard.py
```

### Notebook dimostrativo
`notebooks/demo.ipynb` esegue su dati simulati il proxy della valenza con l'ablazione della
copia d'efferenza, il limite noto di G_pred, le condizioni di demarcazione e il criterio
dell'edge of chaos, con spiegazioni. Si apre nel browser senza installare nulla tramite
[Binder](https://mybinder.org/v2/gh/matrixNeo76/Edge-of-Chaos/HEAD?labpath=notebooks%2Fdemo.ipynb).

### CLI tutto-in-uno
Tutti i comandi sopra sono disponibili anche tramite un unico entry-point, lo
stesso impacchettato da `build_exe.ps1` più sotto:
```bash
python3 paper0_cli.py metrology|dashboard|demarcation|conditions|hardware|test
```

---

## 📦 Eseguibile Standalone (senza Docker, per PC di laboratorio)

Per un eseguibile Windows standalone (non richiede Python/Rust installati sulla
macchina target), pensato per l'acquisizione dati con strumentazione reale dove
Docker non è praticabile (accesso USB/GPIB, permessi admin):

```powershell
.\build_exe.ps1
.\dist\paper0\paper0.exe metrology   # o: dashboard | demarcation | conditions | hardware | test
```

---

## 🐳 Containerizzazione e Replicabilità (Docker)

Per isolare ed eseguire l'ambiente metrologico in un container trasparente ed esente da problemi di dipendenza:

```bash
# Build ed esecuzione del container
docker-compose up --build
```

---

## 📚 Pubblicazioni Correlate

Questo software è la piattaforma di metrologia digital-twin che accompagna il corpus
del programma di ricerca **P0_Distilled**, pubblicato su Zenodo. Il paper distillato è
il punto d'ingresso consigliato; gli altri sono companion/versioni estese.

| Paper | DOI |
|---|---|
| **P0_Distilled_v0.1** (punto d'ingresso principale) | [10.5281/zenodo.22895484](https://doi.org/10.5281/zenodo.22895484) |
| P1_Main (versione estesa/definitiva) | [10.5281/zenodo.22896026](https://doi.org/10.5281/zenodo.22896026) |
| P2_SelfAgency (estensione self-agency) | [10.5281/zenodo.22896870](https://doi.org/10.5281/zenodo.22896870) |
| P3_Critique (valutazione critica esterna) | [10.5281/zenodo.22896988](https://doi.org/10.5281/zenodo.22896988) |
| C1_Philosophy (argomento per il Postulato 2) | [10.5281/zenodo.22897359](https://doi.org/10.5281/zenodo.22897359) |
| C2_PowerAnalysis (power analysis Monte Carlo) | [10.5281/zenodo.22897562](https://doi.org/10.5281/zenodo.22897562) |
| ES_Summary (sintesi esecutiva) | [10.5281/zenodo.22897732](https://doi.org/10.5281/zenodo.22897732) |
| Articolo divulgativo stile Medium (EN) | [10.5281/zenodo.22898609](https://doi.org/10.5281/zenodo.22898609) |

---

## 📜 Bibliografie e Riferimenti

Tutti i riferimenti bibliografici teorici, epistemologici ed hardware citati nel paper e negli script sono disponibili nel file BibTeX allegato:
* **`references.bib`**: Contiene 49 citazioni formattate (Chua, Hatano-Sasa, Tononi, Friston, Lakatos, Kleiner & Ludwig, Iavarone 2026).

---
*Lakatosian Research Programme on Neuromorphic Consciousness (2026)*
