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
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy project source (after deps for better layer cache)
COPY . /app

# Environment for structured logs and gunicorn tuning
ENV LOG_FORMAT=json \
    GUNICORN_CMD_ARGS="--workers 4 --bind 0.0.0.0:8000 --access-logfile - --error-logfile -"

EXPOSE 8000

CMD ["gunicorn", "codebase_analysis.api:app"] 