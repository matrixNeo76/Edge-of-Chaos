# Dockerfile per il Digital Twin e Metrologia P0_Distilled v0.1
FROM python:3.11-slim

LABEL maintainer="Programma di Ricerca Lakatosiano"
LABEL description="Container per la Metrologia dei Substrati Neuromorfici e Calcolo della Valenza"

# Installa strumenti di sistema e compilatore Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Installa Rust per il modulo nativo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copia e installa requisiti Python
COPY references.bib valenza_metrologia.py valenza_metrologia.rs test_valenza_metrologia.py dashboard_valenza.py ./
COPY hardware_driver.py hardware_driver_v2.py test_hardware_session.py demarcation_tests.py lib.rs Cargo.toml install.sh ./

RUN pip install --no-cache-dir numpy scipy matplotlib seaborn pyvisa maturin

# Compila il modulo Rust PyO3
RUN maturin build --release --out dist && pip install dist/*.whl

# Test automatici al build
RUN python3 -m unittest test_valenza_metrologia.py test_hardware_session.py

EXPOSE 8080

CMD ["python3", "dashboard_valenza.py"]
