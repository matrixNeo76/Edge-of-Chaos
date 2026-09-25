# ==============================================================================
# build_exe.ps1 — Standalone packaging (PyInstaller) for lab use
# Project: Thermodynamic Valence & Digital Twin (P0_Distilled v0.1)
#
# Produces a standalone Windows executable (onedir) that does not require
# Python installed on the target machine. Intended for the lab PC that runs
# hardware_driver_v2.py with real instrumentation (Keithley/PicoScope), where
# Docker is not a good option (USB/GPIB access, admin permissions).
#
# It does NOT replace install.sh/install.ps1 or Docker: those remain the path
# for development and for the scientific reproducibility of the digital twin
# (see docs_v0.2/05_PACKAGING_PYINSTALLER.md for the rationale, if present in
# your checkout).
#
# IMPORTANT: always builds in a DEDICATED, ISOLATED venv. Building with the
# "system" Python interpreter (especially if it has hundreds of unrelated
# packages installed) can blow up PyInstaller's analysis time from ~90 seconds
# to several minutes — verified empirically in this project.
# ==============================================================================
$ErrorActionPreference = "Stop"
# NOTE: native tools invoked below (maturin, cargo, pyinstaller) write routine
# status lines to stderr. With $ErrorActionPreference="Stop", PowerShell 5.1
# turns those stderr lines into terminating NativeCommandError exceptions even
# on success (exit code 0) — verified empirically in this project. Every call
# to such a tool is therefore wrapped with a local 'Continue' preference and
# an explicit $LASTEXITCODE check.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Standalone Executable Build (PyInstaller) - P0_Distilled" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = $PSScriptRoot
$BuildVenv = Join-Path $RepoRoot "venv_build"

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not present in the PATH." -ForegroundColor Red
    exit 1
}

# 2. Dedicated, isolated build venv (never the system Python)
Write-Host "[1/5] Creating the isolated build venv ($BuildVenv)..." -ForegroundColor Yellow
if (Test-Path $BuildVenv) {
    Write-Host "      Build venv already exists, reusing it." -ForegroundColor DarkYellow
} else {
    python -m venv $BuildVenv
}
$VenvPython = Join-Path $BuildVenv "Scripts\python.exe"

# 3. Minimal dependencies (only the project's own, no extra packages)
Write-Host "[2/5] Installing only the required dependencies..." -ForegroundColor Yellow
$ErrorActionPreference = "Continue"
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r (Join-Path $RepoRoot "requirements.txt") pyinstaller --quiet
$ErrorActionPreference = "Stop"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Dependency installation failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit 1
}

# 4. Native Rust extension (optional: if missing, the CLI still works with the
#    Python scripts alone; the thermodynamic_valence_rust module is not
#    imported by paper0_cli.py, so its absence does not block the build)
if (Get-Command "cargo" -ErrorAction SilentlyContinue) {
    Write-Host "[3/5] Building the native Rust module (maturin)..." -ForegroundColor Yellow
    $ErrorActionPreference = "Continue"
    & $VenvPython -m pip install maturin --quiet
    Push-Location $RepoRoot
    # Start from an empty folder: an older wheel left there would otherwise be installed
    if (Test-Path "dist_wheel") { Remove-Item "dist_wheel" -Recurse -Force }
    & $VenvPython -m maturin build --release --out dist_wheel
    if ($LASTEXITCODE -eq 0) {
        $wheel = Get-ChildItem "dist_wheel\*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($wheel) {
            & $VenvPython -m pip install --force-reinstall $wheel.FullName --quiet
        }
    }
    Pop-Location
    $ErrorActionPreference = "Stop"
} else {
    Write-Host "[3/5] [WARNING] Rust toolchain not found. Proceeding without the native module." -ForegroundColor Yellow
}

# 5. PyInstaller build (onedir: faster startup than --onefile, preferable for
#    a tool that gets restarted often in a lab setting)
Write-Host "[4/5] Building the executable with PyInstaller (onedir)..." -ForegroundColor Yellow
$ErrorActionPreference = "Continue"
Push-Location $RepoRoot
# The test modules are loaded by name by `paper0 test`, which PyInstaller cannot see:
# they are listed explicitly so that the command works in the executable.
$TestModules = @("test_thermodynamic_valence", "test_hardware_session", "test_demarcation",
                 "test_necessary_conditions", "test_engine_parity")
$HiddenImports = $TestModules | ForEach-Object { "--hidden-import=$_" }
& $VenvPython -m PyInstaller --onedir --noconfirm --name paper0 @HiddenImports paper0_cli.py
Pop-Location
$ErrorActionPreference = "Stop"

# 6. Outcome
$ExePath = Join-Path $RepoRoot "dist\paper0\paper0.exe"
if (Test-Path $ExePath) {
    Write-Host "[5/5] Build completed." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Executable ready: $ExePath" -ForegroundColor Green
    Write-Host "  Usage examples:" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe metrology" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe dashboard" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe hardware" -ForegroundColor Green
    Write-Host "    dist\paper0\paper0.exe test" -ForegroundColor Green
    Write-Host "  Distribute the entire dist\paper0\ folder (not just the exe)." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Build failed: executable not found at $ExePath" -ForegroundColor Red
    exit 1
}
