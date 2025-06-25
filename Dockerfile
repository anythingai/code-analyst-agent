# syntax=docker/dockerfile:1

#########################
# Builder Stage          #
#########################
FROM python:3.11-slim AS builder

WORKDIR /src

# System-level deps required to build wheels (WeasyPrint etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git build-essential \
        libpango1.0-0 libgdk-pixbuf2.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /src/

# Build wheels for all Python dependencies (leverages cache)
RUN pip install --upgrade pip wheel && \
    pip wheel . --wheel-dir=/wheels

#########################
# Runtime Stage          #
#########################
FROM python:3.11-slim

WORKDIR /app

# Install minimal OS packages for runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git libpango1.0-0 libgdk-pixbuf2.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy project source (after deps for better layer cache)
COPY --chown=appuser:appuser . /app

# Create reports directory with proper permissions
RUN mkdir -p /app/reports && chown -R appuser:appuser /app/reports

# Environment for structured logs and gunicorn tuning
ENV LOG_FORMAT=json \
    PYTHONUNBUFFERED=1 \
    GUNICORN_CMD_ARGS="--workers 4 --bind 0.0.0.0:8000 --access-logfile - --error-logfile - --timeout 120"

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/healthz')" || exit 1

CMD ["gunicorn", "codebase_analysis.api:app"] 