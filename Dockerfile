# Multi-stage build for file-context-copier
FROM python:3.11-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-install-project --extra service

# Production stage
FROM python:3.11-slim

# Install uv for runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy source code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app pyproject.toml ./

# Install the project
RUN uv pip install -e . --extra service

# Create directory for processing files
RUN mkdir -p /app/workspace && chown app:app /app/workspace

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "file_context_copier.service:app", "--host", "0.0.0.0", "--port", "8000"]