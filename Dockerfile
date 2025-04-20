# Fase di compilazione: installa tutte le dipendenze di build
FROM python:3.12-slim AS compile-image

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia il requirements.txt e installa le dipendenze
COPY requirements.txt .
RUN pip install --user -r requirements.txt


# Fase finale: immagine leggera per l'esecuzione dell'app
FROM python:3.12-slim AS build-image

# Installa solo le librerie runtime necessarie
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia i pacchetti installati dalla fase precedente
COPY --from=compile-image /root/.local /root/.local

# Copia il resto dell'applicazione
COPY . .

# Imposta il PATH per eseguire i pacchetti installati
ENV PATH=/root/.local/bin:$PATH

# Comando di avvio
CMD ["python", "main.py"]
