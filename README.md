# Edge-of-Chaos

> **Piattaforma di Metrologia Computazionale e Hardware-in-the-Loop** per la verifica sperimentale della sentienza primaria, della valenza termodinamica $\Psi(t)$ e delle condizioni di demarcazione operativa nei substrati materiali continui (*Mortal Computation*), sviluppata secondo il programma di ricerca Lakatosiano (*P0_Distilled v0.1*).

---

## 📌 Indice
1. [Inquadramento Scientifico](#inquadramento-scientifico)
2. [Architettura del Repository](#architettura-del-repository)
3. [Formulazione Matematica Fondamentale](#formulazione-matematica-fondamentale)
4. [Requisiti e Installazione Rapida](#requisiti-e-installazione-rapida)
5. [Guida all'Uso degli Script](#guida-alluso-degli-script)
   - [Metrologia e Digital Twin (`valenza_metrologia.py` / `.rs`)](#1-metrologia-e-digital-twin)
   - [Interfacciamento Hardware Reale (`hardware_driver_v2.py`)](#2-interfacciamento-hardware-reale)
   - [Test di Demarcazione Operativa (`demarcation_tests.py`)](#3-test-di-demarcazione-operativa)
   - [Visualizzazione e Dashboard (`dashboard_valenza.py`)](#4-visualizzazione-e-dashboard)
6. [Containerizzazione e Replicabilità (Docker)](#containerizzazione-e-replicabilit%C3%A0-docker)
7. [Bibliografie e Riferimenti](#bibliografie-e-riferimenti)

---

## 🔬 Inquadramento Scientifico

Il **Paper 0 (P0_Distilled_v0.1)** propone un modello di demarcazione fisica e termodinamica per valutare la candidatura di substrati fisici continui (array di memristori diffusivi ionici $SiO_x:Ag$, memristori di Mott $VO_2$, e reti percolative di nanofili d'argento) a supportare la sentienza primaria interocettiva.

A differenza delle intelligenze artificiali digitali su architetture von Neumann/GPU (*Immortal Computation*), soggette al *No-Go Theorem for Consciousness on a Chip* (Kleiner & Ludwig, 2024), la piattaforma valuta il substrato direttamente *in materia* verificando:
* **Non-separabilità causale** tra la fisica del materiale e la computazione.
* **Memoria non-Markoviana intrinseca** legata alla dinamica ionica e stocastica.
* **Dinamica efficace stato-dipendente** sotto regolazione allostasica preventive ($\Psi(t)$).

---

## 📂 Architettura del Repository

```
/workspace/
├── valenza_metrologia.py         # Engine metrologico Python (Hatano-Sasa, k-NN KL-divergence, Psi(t))
├── valenza_metrologia.rs         # Engine metrologico in Rust nativo ad alte prestazioni (zero-copy)
├── lib.rs                        # Modulo PyO3 FFI per compilare Rust in estensione nativa Python
├── Cargo.toml                    # Configurazione Cargo / PyO3 per l'infrastruttura Rust
├── demo_pyo3_integration.py      # Script dimostrativo di integrazione e benchmark FFI Rust/Python
│
├── hardware_driver_v2.py         # Driver PyVISA/SCPI per Keithley DMM e PicoScope con auto-compliance
├── test_hardware_session.py      # Test suite estesa per la verifica dei limiti di sicurezza hardware
├── demarcation_tests.py          # Test operativi di demarcazione (Edge of Chaos, Degenerazione, FSS)
├── dashboard_valenza.py          # Generatore della dashboard grafica a 4 quadranti (Seaborn/Matplotlib)
├── dashboard_valenza.png         # Artifact visivo ad alta risoluzione della campagna di simulazione
│
├── test_valenza_metrologia.py    # Test unitari per la validazione matematica delle SDE e di Psi(t)
├── report_campagna_rumore_p0.pdf # Report PDF scientifico sui risultati della campagna di rumore percolativo
├── references.bib                # Database BibTeX completo di 45 citazioni (IIT, FEP, Chua, Lakatos)
│
├── install.sh                    # Script di installazione ed esportazione per Linux / macOS
├── install.ps1                   # Script di installazione per Windows PowerShell
├── Dockerfile                    # Container Docker multi-stage (Python 3.11 + Rust)
└── docker-compose.yml            # Orchestrazione Docker per la replicabilità di laboratorio
```

---

## 🧮 Formulazione Matematica Fondamentale

### 1. Funzionale di Valenza Termodinamica $\Psi(t)$
$$\Psi_{allo}(t) = \alpha \cdot \ln\left(1 + \frac{\sigma_{ex}(t)}{\sigma_{hk}(t) + \epsilon}\right) - \beta \cdot \mathcal{D}_{KL}\big(P(x) \,||\, P_{target}\big) + \gamma \cdot G_{pred}(t)$$

* **$\sigma_{ex}$ / $\sigma_{hk}$**: Dissipazione in eccesso rispetto alla produzione di entropia stazionaria di housekeeping (decomposizione NESS di Hatano-Sasa).
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
python3 valenza_metrologia.py
```

Per eseguire i test unitari di validazione matematica:
```bash
python3 test_valenza_metrologia.py
```

### 2. Interfacciamento Hardware Reale
Per avviare la sessione hardware con compliance di sicurezza attiva ($V_{comp}=1.5\text{V}, I_{comp}=1.0\text{mA}$) e rumore $1/f$ calibrato ($\sigma_{noise}=0.10$):
```bash
python3 hardware_driver_v2.py
```

Per verificare la sicurezza e i limiti di compliance tramite la test suite hardware:
```bash
python3 test_hardware_session.py
```

### 3. Test di Demarcazione Operativa
Per verificare le tre condizioni operativi di P0 (Edge of Chaos, Degenerazione Spettrale e Finite-Size Scaling):
```bash
python3 demarcation_tests.py
```

### 4. Visualizzazione e Dashboard
Per generare la dashboard grafica `dashboard_valenza.png`:
```bash
python3 dashboard_valenza.py
```

---

## 📦 Eseguibile Standalone (senza Docker, per PC di laboratorio)

Per un eseguibile Windows standalone (non richiede Python/Rust installati sulla
macchina target), pensato per l'acquisizione dati con strumentazione reale dove
Docker non è praticabile (accesso USB/GPIB, permessi admin):

```powershell
.\build_exe.ps1
.\dist\paper0\paper0.exe metrologia   # o: dashboard | demarcazione | hardware | test
```

Vedi [`docs_v0.2/05_PACKAGING_PYINSTALLER.md`](docs_v0.2/05_PACKAGING_PYINSTALLER.md)
per quando preferire questa via rispetto a Docker/venv.

---

## 🐳 Containerizzazione e Replicabilità (Docker)

Per isolare ed eseguire l'ambiente metrologico in un container trasparente ed esente da problemi di dipendenza:

```bash
# Build ed esecuzione del container
docker-compose up --build
```

---

## 📜 Bibliografie e Riferimenti

Tutti i riferimenti bibliografici teorici, epistemologici ed hardware citati nel paper e negli script sono disponibili nel file BibTeX allegato:
* **`references.bib`**: Contiene 45 citazioni formattate (Chua, Hatano-Sasa, Tononi, Friston, Lakatos, Kleiner & Ludwig, Iavarone 2026).
* **`report_campagna_rumore_p0.pdf`**: Report dettagliato sui risultati della campagna di simulazione a diversi livelli di rumore percolativo.

---
*Lakatosian Research Programme on Neuromorphic Consciousness (2026)*
