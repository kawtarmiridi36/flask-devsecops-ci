# -------- STAGE 1 : build + installation deps --------
# Use specific, patched version instead of generic tag
FROM python:3.12.8-slim-bookworm AS builder

# Add security scanning metadata
LABEL org.opencontainers.image.source="https://github.com/${{ github.repository }}"
LABEL org.opencontainers.image.licenses="MIT"
LABEL security.scan.enabled="true"

# Security hardening
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 1. Update ALL packages before installing anything
# 2. Use pinned versions for reproducibility
# 3. Clean up immediately to reduce attack surface
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        pkg-config=0.29.2-1 \
        && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for build stage too
RUN useradd -r -u 1001 -m -d /app builder

# Switch to non-root user
USER builder

WORKDIR /app

# Copy dependencies first (better layer caching)
COPY --chown=builder:builder requirements.txt .

# Create virtual environment with security optimizations
RUN python -m venv --without-pip /opt/venv && \
    /opt/venv/bin/python -m ensurepip --upgrade && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip==24.0 && \
    /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.txt

# -------- STAGE 2 : production image --------
FROM python:3.12.8-slim-bookworm AS production

# Same security hardening
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Update ALL system packages in final image too
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
        ca-certificates=20230311 \
        libexpat1=2.5.0-1 \
        && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    # Remove unnecessary files
    find /usr/local -depth \
        \( -type d -a \( -name test -o -name tests \) \) \
        -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
        -exec rm -rf '{}' + && \
    # Create app user with high UID (>10000 for Checkov compliance)
    useradd -r -u 10001 -m -d /app appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv/

# Copy application code
COPY --chown=appuser:appuser app ./app/
COPY --chown=appuser:appuser config.py run.py ./

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=2)" || exit 1

EXPOSE 5000

# Use exec form for proper signal handling
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--worker-class", "sync", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
