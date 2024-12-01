# Usa l'immagine base Python slim
FROM python:3.10-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file requirements e app nella directory di lavoro
COPY requirements.txt /app/requirements.txt

# Installa dipendenze di sistema per Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta 8080
EXPOSE 8080

# Comando per avviare l'applicazione
CMD ["python", "app.py"]