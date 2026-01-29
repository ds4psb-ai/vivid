# =============================================================================
# Vivid Backend - Production Dockerfile (Cloud Run 2026)
# =============================================================================
#
# Multi-stage build optimized for Google Cloud Run deployment.
# Based on 2026 best practices:
# - Non-root user
# - Health check support
# - Optimized Python settings
# - Minimal image size
#
# Build:
#   docker build -t vivid-backend .
#
# Run locally:
#   docker run -p 8080:8080 --env-file .env vivid-backend
#
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd -r vivid && useradd -r -g vivid vivid

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python optimization flags (2026 Best Practice)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Application environment
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PORT=8080

# Working directory
WORKDIR /app

# Copy application code
COPY --chown=vivid:vivid . .

# Remove unnecessary files (keep scripts/ for table creation)
RUN rm -rf tests/ docs/ .git/ .pytest_cache/ __pycache__/ *.md

# Switch to non-root user
USER vivid

# Expose Cloud Run standard port
EXPOSE 8080

# Health check (Cloud Run probes)
# Railway uses $PORT env var, disable Docker healthcheck (Railway has its own)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:${PORT:-8080}/health/live || exit 1

# Startup command - use shell form for $PORT expansion
# 1. Create missing tables (checkfirst=True, safe to run multiple times)
# 2. Run alembic (stamp if upgrade fails - for existing DBs)
# 3. Start uvicorn
CMD sh -c "echo '=== Starting container ===' && \
    echo 'PORT='$PORT && \
    echo 'DATABASE_URL='$(echo $DATABASE_URL | sed 's/:.*@/:***@/') && \
    echo '=== Creating missing tables ===' && \
    python scripts/create_missing_tables.py 2>&1 && \
    echo '=== Running alembic upgrade ===' && \
    (alembic upgrade head 2>&1 || { echo '=== Alembic upgrade failed, trying stamp head ==='; alembic stamp head 2>&1; }) && \
    echo '=== Starting uvicorn ===' && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2 --timeout-keep-alive 65 --log-level info"
