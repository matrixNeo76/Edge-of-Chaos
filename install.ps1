# ==============================================================================
# Automated Installation Script for Windows (PowerShell)
# Project: Thermodynamic Valence & Digital Twin (P0_Distilled v0.1)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Thermodynamic Valence Installer (Windows PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not present in the PATH." -ForegroundColor Red
    Write-Host "Download and install Python 3.9+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pyVersion = python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
Write-Host "[OK] Detected Python $pyVersion" -ForegroundColor Green

# 2. Create virtualenv
Write-Host "[1/4] Creating the isolated virtual environment (venv)..." -ForegroundColor Yellow
python -m venv venv
& .\venv\Scripts\Activate.ps1

# 3. Install dependencies
Write-Host "[2/4] Upgrading pip and installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install numpy scipy matplotlib seaborn maturin

# 4. Rust build
if (Get-Command "cargo" -ErrorAction SilentlyContinue) {
    Write-Host "[3/4] Building the high-performance native Rust module..." -ForegroundColor Yellow
    maturin develop --release
} else {
    Write-Host "[3/4] [WARNING] Rust toolchain not found. The traditional Python scripts will be used." -ForegroundColor Yellow
}

# 5. Run tests
Write-Host "[4/4] Running metrology validation tests..." -ForegroundColor Yellow
python test_thermodynamic_valence.py

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Installation Completed Successfully!" -ForegroundColor Green
Write-Host "  To activate the environment: .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "  To run the metrology: python thermodynamic_valence.py" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
