# ==============================================================================
# Script di Installazione Automatica per Windows (PowerShell)
# Progetto: Valenza Metrologia & Digital Twin (P0_Distilled v0.1)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Installatore Valenza Metrologia (Windows PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verifica Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRORE] Python non e' installato o non e' presente nel PATH." -ForegroundColor Red
    Write-Host "Scarica e installa Python 3.9+ da https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pyVersion = python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
Write-Host "[OK] Rilevato Python $pyVersion" -ForegroundColor Green

# 2. Creazione virtualenv
Write-Host "[1/4] Creazione dell'ambiente virtuale isolato (venv)..." -ForegroundColor Yellow
python -m venv venv
& .\venv\Scripts\Activate.ps1

# 3. Installazione dipendenze
Write-Host "[2/4] Aggiornamento pip e installazione dipendenze..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install numpy scipy matplotlib seaborn maturin

# 4. Compilazione Rust
if (Get-Command "cargo" -ErrorAction SilentlyContinue) {
    Write-Host "[3/4] Compilazione del modulo nativo Rust ad alte prestazioni..." -ForegroundColor Yellow
    maturin develop --release
} else {
    Write-Host "[3/4] [AVVISO] Toolchain Rust non trovata. Verranno usati gli script Python tradizionali." -ForegroundColor Yellow
}

# 5. Esecuzione Test
Write-Host "[4/4] Esecuzione dei test di convalida metrologica..." -ForegroundColor Yellow
python test_valenza_metrologia.py

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Installazione Completata con Successo!" -ForegroundColor Green
Write-Host "  Per attivare l'ambiente: .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "  Per eseguire la metrologia: python valenza_metrologia.py" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
