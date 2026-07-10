# backend/Dockerfile
FROM python:3.11-slim

# Installer les dépendances système pour PostGIS
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port
EXPOSE 8000

# Lancer le serveur
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "cimetiere.wsgi:application"]