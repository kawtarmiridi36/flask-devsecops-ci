# =========================
# STAGE 1: builder (wheels)
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# deps système (si besoin de compiler des libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# On copie requirements en premier (cache docker)
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# =========================
# STAGE 2: runtime (small + non-root)
# =========================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# user non-root
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Copier wheels + requirements
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Installer deps depuis wheels (offline)
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

# Copier ton code
# (ton code est dans app/Flask_app/..., donc on copie app/ vers /app/app/)
COPY app/ /app/app/

# Permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Healthcheck: adapte le port/endpoint si besoin
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health').read()" || exit 1

# Démarrage (adapte si ton entrypoint est différent)
CMD ["python", "app/Flask_app/run.py"]

