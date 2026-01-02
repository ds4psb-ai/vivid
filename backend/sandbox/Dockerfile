# Sandbox Runner Docker Image
# Security-hardened Python environment for isolated tool execution

FROM python:3.11-slim AS base

# Security: Non-root user
RUN groupadd -r sandbox && useradd --no-log-init -r -g sandbox sandbox

# Minimal dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python dependencies for tool execution
RUN pip install --no-cache-dir \
    httpx==0.25.0 \
    jinja2==3.1.2 \
    pydantic==2.5.0 \
    && pip cache purge

# Create working directory
WORKDIR /sandbox
RUN chown sandbox:sandbox /sandbox

# Copy execution wrapper
COPY --chown=sandbox:sandbox runner.py /sandbox/runner.py

# Security: Remove potentially dangerous files
RUN rm -rf /usr/bin/curl /usr/bin/wget /usr/bin/nc 2>/dev/null || true

# Security: Restrict file permissions
RUN chmod 755 /sandbox && \
    chmod 644 /sandbox/runner.py

# Switch to non-root user
USER sandbox

# Environment: Disable network for tools that check
ENV SANDBOX_MODE=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Entry point
ENTRYPOINT ["python", "/sandbox/runner.py"]
