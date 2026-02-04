# -------- STAGE 1 : build + installation deps --------
FROM python:3.12.8-slim-bookworm AS builder

# [Keep all your existing code here...]

# -------- STAGE 2 : production image --------
# CHANGE THIS LINE: Use a different alias, NOT "builder"
FROM python:3.12.8-slim-bookworm AS production  # CHANGED FROM "builder" to "production"

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

# FIX THIS LINE: Copy from "builder" (stage 1) to "production" (stage 2)
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv  # This is now correct

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser config.py run.py ./

# Switch to non-root user
USER appuser

# [Rest of your Dockerfile remains the same...]
