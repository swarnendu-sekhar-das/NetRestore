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

# Copy application code and automation scripts
COPY src/ ./src/
COPY data/ ./data/
COPY notebooks/ ./notebooks/
COPY scripts/ ./scripts/

# Pre-download ML models into a shared cache so they don't need internet at runtime.
# This bakes ~160MB of models into the image but eliminates startup network dependency.
#   - all-MiniLM-L6-v2:              ~80MB (embedding model for vector search)
#   - ms-marco-MiniLM-L-6-v2:        ~80MB (cross-encoder reranker)
ENV HF_HOME=/app/.cache/huggingface
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Models pre-downloaded successfully')"

# Pre-create chroma_db directory and ensure script is executable
RUN mkdir -p /app/chroma_db && \
    chmod +x /app/scripts/start.sh && \
    chown -R appuser:appuser /app

# Health-check endpoint for K8s liveness probes and Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit default port
EXPOSE 8501

# Run as non-root user
USER appuser

# Use the startup wrapper script to handle auto-initialization
ENTRYPOINT ["/app/scripts/start.sh"]
