FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for NLE engine)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml .
RUN pip3 install --break-system-packages uv && \
    uv sync --no-dev

# Copy Rust NLE
COPY rust-nle/ rust-nle/
RUN cd rust-nle && cargo build --release

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Create working directory for renders
RUN mkdir -p /workspace/out

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
