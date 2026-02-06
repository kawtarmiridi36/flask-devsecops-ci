# -------- STAGE 1 : builder pour installer les dépendances --------
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Installer compilateur si besoin
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier seulement requirements pour profiter du cache Docker
COPY requirements.txt .

# Installer les dépendances globalement (pas besoin de venv)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Créer un utilisateur non-root
RUN useradd -m appuser && chown -R appuser:appuser /app

# Switch sur l’utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
