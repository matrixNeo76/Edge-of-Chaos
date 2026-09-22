# ==============================================================================
# build_exe.ps1 — Packaging standalone (PyInstaller) per l'uso in laboratorio
# Progetto: Valenza Metrologia & Digital Twin (P0_Distilled v0.1)
#
# Produce un eseguibile Windows standalone (onedir) che non richiede Python
# installato sulla macchina target. Pensato per il PC di laboratorio che
# esegue hardware_driver_v2.py con strumentazione reale (Keithley/PicoScope),
# dove Docker non è una buona opzione (accesso USB/GPIB, permessi admin).
#
# NON sostituisce install.sh/install.ps1 o Docker: quelli restano il percorso
# per lo sviluppo e per la riproducibilità scientifica del digital twin (vedi
# docs_v0.2/05_PACKAGING_PYINSTALLER.md per la motivazione della scelta).
#
# IMPORTANTE: costruisce sempre in un venv DEDICATO E ISOLATO. Buildare con
# l'interprete Python "di sistema" (specie se ha centinaia di pacchetti non
# correlati installati) può far esplodere i tempi di analisi di PyInstaller
# da ~90 secondi a diversi minuti — verificato empiricamente in questo progetto.
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Build Eseguibile Standalone (PyInstaller) - P0_Distilled" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = $PSScriptRoot
$BuildVenv = Join-Path $RepoRoot "venv_build"

# 1. Verifica Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRORE] Python non e' installato o non e' presente nel PATH." -ForegroundColor Red
    exit 1
}

# 2. Venv di build dedicato e isolato (mai il Python di sistema)
Write-Host "[1/5] Creazione del venv di build isolato ($BuildVenv)..." -ForegroundColor Yellow
if (Test-Path $BuildVenv) {
    Write-Host "      Venv di build gia' esistente, riutilizzo." -ForegroundColor DarkYellow
} else {
    python -m venv $BuildVenv
}
$VenvPython = Join-Path $BuildVenv "Scripts\python.exe"

# 3. Dipendenze minime (solo quelle del progetto, niente pacchetti extra)
Write-Host "[2/5] Installazione delle sole dipendenze necessarie..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install numpy scipy matplotlib seaborn pyinstaller --quiet

# 4. Estensione nativa Rust (opzionale: se manca, il CLI funziona comunque
#    con i soli script Python; il modulo valenza_metrologia_rust non e'
#    importato da paper0_cli.py, quindi la sua assenza non blocca il build)
if (Get-Command "cargo" -ErrorAction SilentlyContinue) {
    Write-Host "[3/5] Compilazione del modulo nativo Rust (maturin)..." -ForegroundColor Yellow
    & $VenvPython -m pip install maturin --quiet
    Push-Location $RepoRoot
    & $VenvPython -m maturin build --release --out dist_wheel
    if ($LASTEXITCODE -eq 0) {
        $wheel = Get-ChildItem "dist_wheel\*.whl" | Select-Object -First 1
        if ($wheel) {
            & $VenvPython -m pip install --force-reinstall $wheel.FullName --quiet
        }
    }
    Pop-Location
} else {
    Write-Host "[3/5] [AVVISO] Toolchain Rust non trovata. Si procede senza il modulo nativo." -ForegroundColor Yellow
}

# 5. Build PyInstaller (onedir: avvio piu' rapido di --onefile, preferibile
#    per uno strumento riavviato spesso in laboratorio)
Write-Host "[4/5] Build eseguibile con PyInstaller (onedir)..." -ForegroundColor Yellow
Push-Location $RepoRoot
& $VenvPython -m PyInstaller --onedir --noconfirm --name paper0 paper0_cli.py
Pop-Location

# 6. Esito
$ExePath = Join-Path $RepoRoot "dist\paper0\paper0.exe"
if (Test-Path $ExePath) {
    Write-Host "[5/5] Build completata." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Eseguibile pronto: $ExePath" -ForegroundColor Green
    Write-Host "  Esempi d'uso:" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe metrologia" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe dashboard" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe hardware" -ForegroundColor Green
    Write-Host "  Distribuire l'intera cartella dist\paper0\ (non solo l'exe)." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Host "[ERRORE] Build fallita: eseguibile non trovato in $ExePath" -ForegroundColor Red
    exit 1
}
