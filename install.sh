#!/usr/bin/env bash
# ==============================================================================
# Script di Installazione Automatica per Linux
# Progetto: Valenza Metrologia & Digital Twin (P0_Distilled v0.1)
# ==============================================================================
set -e

echo "=========================================================="
echo "  Installatore Valenza Metrologia (Linux)"
echo "=========================================================="

# 1. Verifica Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERRORE] Python3 non e' installato. Per favore installa Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Rilevato Python $PYTHON_VERSION"

# 2. Creazione virtualenv
echo "[1/4] Creazione dell'ambiente virtuale isolato (venv)..."
python3 -m venv venv
source venv/bin/activate

# 3. Installazione dipendenze Python
echo "[2/4] Aggiornamento pip e installazione dipendenze (numpy, scipy, maturin)..."
pip install --upgrade pip
pip install numpy scipy matplotlib seaborn maturin

# 4. Compilazione nativa Rust via Maturin
if command -v cargo &> /dev/null; then
    echo "[3/4] Compilazione del modulo nativo Rust ad alte prestazioni..."
    maturin develop --release
else
    echo "[3/4] [AVVISO] Toolchain Rust/Cargo non trovata. Verranno usati gli script Python tradizionali."
fi

# 5. Esecuzione Test di Convalida
echo "[4/4] Esecuzione dei test di convalida metrologica..."
python test_valenza_metrologia.py

echo "=========================================================="
echo "  Installazione Completata con Successo!"
echo "  Per attivare l'ambiente: source venv/bin/activate"
echo "  Per eseguire la metrologia: python valenza_metrologia.py"
echo "=========================================================="
