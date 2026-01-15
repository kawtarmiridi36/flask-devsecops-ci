# -------- STAGE 1 : build + installation deps --------
FROM python:3.12-slim AS builder

# Désactiver les interactions apt
ENV DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Copier uniquement les dépendances en premier (cache Docker)
COPY requirements.txt .

# Créer un venv dans l'image et installer les deps
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# -------- STAGE 2 : image finale minimale --------
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Créer un utilisateur non-root
RUN useradd -m appuser

# Dossier de travail
WORKDIR /app

# Copier le venv du builder
COPY --from=builder /opt/venv /opt/venv

# Utiliser ce venv par défaut
ENV PATH="/opt/venv/bin:$PATH"

# Copier seulement le code de l'application
COPY app ./app
COPY config.py run.py ./

# (Optionnel) variable d'env par défaut, à surcharger en prod
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1

# Donner les droits à l'utilisateur non-root
RUN chown -R appuser:appuser /app

# Basculer sur l'utilisateur non-root
USER appuser

# Exposer le port de l'app
EXPOSE 5000

# Commande de démarrage : gunicorn avec l'objet app de run.py
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
