# Build dependencies in a separate stage.
FROM python:3.11-slim AS builder

WORKDIR /app
# Install PyTorch from the CPU-only package index.
RUN pip install --no-cache-dir uv && \
    uv pip install --system torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu

# Install the application requirements.
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Runtime image.
FROM python:3.11-slim

# Install curl for the health check.
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Run the application as a non-root user.
RUN useradd -m -s /bin/bash appuser

# Copy installed Python packages from the build stage.
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code and scripts.
COPY src/ ./src/
COPY data/ ./data/
COPY notebooks/ ./notebooks/
COPY scripts/ ./scripts/

# Store downloaded Hugging Face models in the application cache directory.
ENV HF_HOME=/app/.cache/huggingface

# Create the database directory and set script permissions.
RUN mkdir -p /app/chroma_db && \
    chmod +x /app/scripts/start.sh && \
    chown -R appuser:appuser /app

# Check that Streamlit responds on its health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit listens on this port.
EXPOSE 8501

# Switch to the application user.
USER appuser

# Start the application through the startup script.
ENTRYPOINT ["/app/scripts/start.sh"]
