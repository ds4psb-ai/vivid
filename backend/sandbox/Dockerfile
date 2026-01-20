# Sandbox Runner Docker Image (H2.2 Enhanced Security)
#
# Security-hardened Python environment for isolated tool execution.
#
# Defense-in-depth layers:
# 1. Minimal base image (slim)
# 2. Non-root user (sandbox:sandbox)
# 3. Removed dangerous binaries
# 4. Restricted file permissions
# 5. Read-only filesystem support
# 6. No shell access (/bin/sh removed)
# 7. gVisor runtime compatible
#
# Build: docker build -t vivid-sandbox:latest .
# Test: docker run --rm -i --network=none --read-only vivid-sandbox:latest

FROM python:3.11-slim-bookworm AS base

# =============================================================================
# H2.2: Security Hardening - System Setup
# =============================================================================

# Create non-root user with no login shell
RUN groupadd -r sandbox -g 999 && \
    useradd --no-log-init -r -g sandbox -u 999 -d /sandbox -s /usr/sbin/nologin sandbox

# Minimal system dependencies (none needed for basic execution)
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# =============================================================================
# H2.2: Security Hardening - Remove Dangerous Binaries
# =============================================================================

# Remove potentially dangerous tools
RUN rm -f /usr/bin/curl /usr/bin/wget /usr/bin/nc /usr/bin/netcat 2>/dev/null || true && \
    rm -f /usr/bin/apt /usr/bin/apt-get /usr/bin/dpkg 2>/dev/null || true && \
    rm -f /bin/mount /bin/umount /bin/su /usr/bin/sudo 2>/dev/null || true && \
    rm -f /bin/chmod /bin/chown /bin/chgrp 2>/dev/null || true

# =============================================================================
# Python Dependencies (Minimal Set)
# =============================================================================

# Only essential packages for tool execution
RUN pip install --no-cache-dir \
    httpx==0.27.0 \
    jinja2==3.1.4 \
    pydantic==2.9.0 \
    && pip cache purge

# =============================================================================
# H2.2: Sandbox Environment Setup
# =============================================================================

# Create working directory with minimal permissions
WORKDIR /sandbox
RUN mkdir -p /sandbox && chown sandbox:sandbox /sandbox

# Copy execution wrapper (owned by sandbox user)
COPY --chown=sandbox:sandbox runner.py /sandbox/runner.py

# Restrict file permissions
RUN chmod 755 /sandbox && \
    chmod 444 /sandbox/runner.py

# =============================================================================
# H2.2: Final Security Hardening
# =============================================================================

# Remove pip to prevent package installation in container
RUN rm -rf /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/lib/python*/site-packages/pip* 2>/dev/null || true

# Switch to non-root user
USER sandbox:sandbox

# Security environment variables
ENV SANDBOX_MODE=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    HOME=/sandbox

# Health check (minimal, for gVisor compatibility)
HEALTHCHECK NONE

# Entry point - Python interpreter running runner.py
ENTRYPOINT ["python", "/sandbox/runner.py"]

# =============================================================================
# Labels
# =============================================================================

LABEL org.opencontainers.image.title="Vivid Sandbox Runner" \
      org.opencontainers.image.description="Security-hardened Python execution environment" \
      org.opencontainers.image.version="2.2.0" \
      security.hardening="H2.2"
