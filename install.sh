#!/usr/bin/env bash
# ==============================================================================
# Automated Installation Script for Linux
# Project: Thermodynamic Valence & Digital Twin (P0_Distilled v0.1)
# ==============================================================================
set -e

echo "=========================================================="
echo "  Thermodynamic Valence Installer (Linux)"
echo "=========================================================="

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Detected Python $PYTHON_VERSION"

# 2. Create virtualenv
echo "[1/4] Creating the isolated virtual environment (venv)..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
echo "[2/4] Upgrading pip and installing dependencies (numpy, scipy, maturin)..."
pip install --upgrade pip
pip install numpy scipy matplotlib seaborn maturin

# 4. Native Rust build via Maturin
if command -v cargo &> /dev/null; then
    echo "[3/4] Building the high-performance native Rust module..."
    maturin develop --release
else
    echo "[3/4] [WARNING] Rust/Cargo toolchain not found. The traditional Python scripts will be used."
fi

# 5. Run validation tests
echo "[4/4] Running metrology validation tests..."
python test_thermodynamic_valence.py

echo "=========================================================="
echo "  Installation Completed Successfully!"
echo "  To activate the environment: source venv/bin/activate"
echo "  To run the metrology: python thermodynamic_valence.py"
echo "=========================================================="
