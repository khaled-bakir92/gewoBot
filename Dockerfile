# Multi-stage Dockerfile für Gewobag Bot v2.1
# Optimiert für Production-Deployment

# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder

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
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen für Sicherheit
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app /data /ms-playwright && \
    chown -R botuser:botuser /app /data /ms-playwright

# Arbeitsverzeichnis
WORKDIR /app

# Python-Packages von Builder kopieren
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# PATH erweitern
ENV PATH=/home/botuser/.local/bin:$PATH

# Playwright-Browser installieren (als root, aber in User-Verzeichnis)
RUN pip install playwright && \
    playwright install chromium && \
    chown -R botuser:botuser /ms-playwright

# Application-Code kopieren
COPY --chown=botuser:botuser . .

# Zu Non-root User wechseln
USER botuser

# Volume für persistente Daten (Datenbank, Logs, Config)
VOLUME ["/app/data"]

# Health-Check (prüft ob Datenbank existiert)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -f /app/data/gewobag_wohnungen.db || exit 1

# Standard-Befehl (kann mit docker-compose überschrieben werden)
CMD ["python", "main.py", "--full"]
