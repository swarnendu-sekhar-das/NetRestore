# ---- Build Stage ----
# Uses a builder pattern to compile all C-extension dependencies (chromadb, torch)
# in a separate layer, keeping the final image lightweight and secure.
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
# Install CPU-only torch FIRST to prevent uv from pulling 2GB+ of NVIDIA CUDA packages
RUN pip install uv && \
    uv pip install --system --prefix=/install torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu && \
    uv pip install --system --prefix=/install -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim

# Install curl for health checks (required by K8s liveness/readiness probes)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security (Vault/K8s best practice)
RUN useradd -m -s /bin/bash appuser

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY notebooks/ ./notebooks/

# Pre-create chroma_db directory with correct permissions
RUN mkdir -p /app/chroma_db && chown -R appuser:appuser /app

# Health-check endpoint for K8s liveness probes and Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit default port
EXPOSE 8501

# Run as non-root user
USER appuser

# Streamlit CLI flags:
# --server.headless=true : Required for Docker (no browser auto-open)
# --server.address=0.0.0.0 : Bind to all interfaces for container networking
ENTRYPOINT ["streamlit", "run", "src/app/main.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
