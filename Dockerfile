# Multi-stage Dockerfile für Gewobag Bot v2.2
# Optimiert für Production-Deployment mit Web-Frontend

# ===== Stage 1: Builder =====
FROM python:3.11-slim AS builder

# Umgebungsvariablen für Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Arbeitsverzeichnis erstellen
WORKDIR /app

# System-Dependencies installieren (nur für Build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt


# ===== Stage 2: Runtime =====
FROM python:3.11-slim

# Umgebungsvariablen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# System-Dependencies für Playwright installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Browser-Dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    # Zusätzliche Utilities
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen für Sicherheit
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app /app/logs /ms-playwright && \
    chown -R botuser:botuser /app /ms-playwright

# Arbeitsverzeichnis
WORKDIR /app

# Python-Packages von Builder kopieren
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# PATH und PYTHONPATH erweitern
ENV PATH=/home/botuser/.local/bin:$PATH \
    PYTHONPATH=/home/botuser/.local/lib/python3.11/site-packages

# Playwright-Browser installieren (muss als root installiert werden, dann Permissions setzen)
# Wichtig: Installation NACH PATH-Setting, aber VOR User-Wechsel
RUN python3 -m playwright install chromium && \
    chown -R botuser:botuser /ms-playwright

# Application-Code kopieren (inkl. frontend/)
COPY --chown=botuser:botuser *.py ./
COPY --chown=botuser:botuser frontend/ ./frontend/

# Template-Konfigurationsdateien kopieren (werden später durch Volumes überschrieben)
COPY --chown=botuser:botuser bezirke_verfuegbar.json ./

# Zu Non-root User wechseln
USER botuser

# Volumes für persistente Daten
# Logs und Datenbank werden direkt in /app/ gemountet
VOLUME ["/app/logs"]

# Health-Check (prüft ob Datenbank existiert oder erstellt werden kann)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD test -f /app/gewobag_wohnungen.db || exit 0

# Port für Web-Frontend exponieren
EXPOSE 5000

# Standard-Befehl (kann mit docker-compose überschrieben werden)
CMD ["python", "main.py", "--full"]
