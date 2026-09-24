# Dockerfile for the Digital Twin and Metrology, P0_Distilled v0.1
FROM python:3.11-slim

LABEL maintainer="Lakatosian Research Programme"
LABEL description="Container for Neuromorphic Substrate Metrology and Valence Computation"

# Install system tools and the Rust compiler
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust for the native module
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy and install Python requirements
COPY references.bib thermodynamic_valence.py thermodynamic_valence.rs test_thermodynamic_valence.py valence_dashboard.py ./
COPY hardware_driver_v2.py test_hardware_session.py demarcation.py necessary_conditions.py synthetic_systems.py demarcation_tests.py paper0_cli.py lib.rs Cargo.toml install.sh ./
COPY test_demarcation.py test_necessary_conditions.py ./

RUN pip install --no-cache-dir numpy scipy matplotlib seaborn pyvisa maturin

# Build the Rust PyO3 module
RUN maturin build --release --out dist && pip install dist/*.whl

# Automated tests at build time
RUN python3 -m unittest test_thermodynamic_valence test_hardware_session test_demarcation test_necessary_conditions

EXPOSE 8080

CMD ["python3", "valence_dashboard.py"]
