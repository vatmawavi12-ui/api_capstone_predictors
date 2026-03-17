FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers
COPY requirements.txt .
COPY app.py .
COPY models/ ./models/

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install numpy==1.24.3
RUN pip install pandas==2.0.3
RUN pip install -r requirements.txt

# Exposer le port
EXPOSE 10000

# Commande de démarrage
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
