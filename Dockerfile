# Dockerfile for the Edge-of-Chaos digital twin and metrology.
# Builds the native module from the locked Cargo dependencies, installs the Python dependencies
# from requirements.txt (same ranges as pyproject.toml) and runs the test suites at build time.
FROM python:3.12-slim

LABEL maintainer="Francesco Iavarone"
LABEL description="Container for neuromorphic substrate metrology and valence computation"

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Rust toolchain for the native module (minimal profile: compiler and cargo only)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Dependencies first, so that a change to the Python code does not rebuild them
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt pytest

# Native module from the locked Cargo dependencies
COPY pyproject.toml Cargo.toml Cargo.lock lib.rs thermodynamic_valence.rs ./
RUN maturin build --release --locked --out /tmp/wheels && pip install --no-cache-dir /tmp/wheels/*.whl

# Source and tests (see .dockerignore for what stays out)
COPY . .

# Run as an unprivileged user from here on
RUN useradd --create-home app && chown -R app:app /app
USER app

# Test suites at build time (the parity test runs, since the native module is installed)
RUN MPLBACKEND=Agg python -m pytest -q

CMD ["python", "valence_dashboard.py"]
