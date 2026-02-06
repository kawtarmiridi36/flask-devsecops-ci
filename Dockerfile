# =========================
# STAGE 1: builder
# =========================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY app/Flask_app/requirements.txt requirements.txt

RUN python -m pip install --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# =========================
# STAGE 2: runtime
# =========================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -m -u 10001 appuser

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY app/Flask_app/requirements.txt requirements.txt

RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

# on copie uniquement le vrai projet Flask
COPY app/Flask_app /app

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["python", "run.py"]
