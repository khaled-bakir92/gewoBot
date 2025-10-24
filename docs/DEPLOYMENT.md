# 🐳 Docker Deployment Guide - Gewobag Bot v2.1

Vollständige Anleitung für das Deployment des Gewobag-Bots mit Docker.

---

## 📋 Voraussetzungen

- **Docker** installiert (Version 20.10+)
- **Docker Compose** installiert (Version 1.29+)
- Konfigurationsdateien vorbereitet:
  - `user_data.json`
  - `filter_config.json`

---

## 🚀 Schnellstart

### 1. Repository vorbereiten

```bash
cd /Users/khaled/Desktop/bot\ new

# Konfigurationsdateien erstellen (falls noch nicht vorhanden)
python main.py --setup
```

### 2. Konfigurationsdateien ausfüllen

**user_data.json** - Tragen Sie Ihre persönlichen Daten ein!

**filter_config.json** - Konfigurieren Sie Ihre Suchfilter

### 3. Docker Image bauen

```bash
docker-compose build
```

### 4. Bot starten

```bash
# Einmalige Ausführung (Vollautomatik)
docker-compose run --rm gewobag-bot

# Im Hintergrund laufen lassen
docker-compose up -d
```

---

## 🛠️ Verfügbare Modi

### Modus 1: Vollautomatik (Standard)
```bash
docker-compose run --rm gewobag-bot
```
Führt Suche + Bewerbung automatisch aus.

### Modus 2: Nur Suchen
```bash
docker-compose run --rm gewobag-bot python main.py --scrape
```

### Modus 3: Nur Bewerben
```bash
docker-compose run --rm gewobag-bot python main.py --apply
```

### Modus 4: Setup (erste Installation)
```bash
docker-compose run --rm gewobag-bot python main.py --setup
```

### Modus 5: Mit Browser-Fenster (Debugging)
```bash
# ACHTUNG: Funktioniert nur lokal, nicht in Headless-Umgebungen!
docker-compose run --rm gewobag-bot python main.py --show-browser
```

### Modus 6: Limit für Bewerbungen
```bash
docker-compose run --rm gewobag-bot python main.py --max 3
```

---

## 📂 Volume-Struktur

Docker verwendet folgende Volume-Mappings:

```yaml
volumes:
  # Konfiguration (read-only)
  - ./user_data.json:/app/user_data.json:ro
  - ./filter_config.json:/app/filter_config.json:ro

  # Datenbank (read-write)
  - ./gewobag_wohnungen.db:/app/gewobag_wohnungen.db

  # Logs (read-write)
  - ./logs:/app/logs

  # Dokumente (read-only)
  - ./documents:/app/documents:ro
```

**Wichtig:**
- Konfigurationsdateien werden **read-only** gemountet (Schutz vor versehentlichen Änderungen)
- Datenbank wird **read-write** gemountet (für Updates)
- Logs werden in separates Verzeichnis geschrieben

---

## ⚙️ Erweiterte Konfiguration

### Resource Limits anpassen

In `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max 4 CPU-Kerne
      memory: 4G     # Max 4 GB RAM
    reservations:
      cpus: '1'      # Min 1 CPU-Kern
      memory: 1G     # Min 1 GB RAM
```

### Umgebungsvariablen

```yaml
environment:
  - TZ=Europe/Berlin              # Zeitzone
  - PYTHONUNBUFFERED=1            # Direktes Logging
  - LOG_LEVEL=INFO                # Log-Level (DEBUG, INFO, WARNING, ERROR)
```

### Logging-Konfiguration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"    # Max Dateigröße pro Log-Datei
    max-file: "5"      # Max Anzahl Log-Dateien
```

---

## 🔄 Automatische Ausführung (Cron)

### Option 1: Docker Restart-Policy

```yaml
services:
  gewobag-bot:
    restart: always
    command: >
      sh -c "while true; do
        python main.py --full;
        echo 'Warte 6 Stunden...';
        sleep 21600;
      done"
```

### Option 2: Host-Crontab

```bash
# Crontab bearbeiten
crontab -e

# Alle 6 Stunden ausführen
0 */6 * * * cd /Users/khaled/Desktop/bot\ new && docker-compose run --rm gewobag-bot >> /var/log/gewobag-cron.log 2>&1
```

### Option 3: Systemd Timer (Linux)

Erstelle `/etc/systemd/system/gewobag-bot.service`:

```ini
[Unit]
Description=Gewobag Bot
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/Users/khaled/Desktop/bot new
ExecStart=/usr/bin/docker-compose run --rm gewobag-bot

[Install]
WantedBy=multi-user.target
```

Erstelle `/etc/systemd/system/gewobag-bot.timer`:

```ini
[Unit]
Description=Run Gewobag Bot every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gewobag-bot.timer
sudo systemctl start gewobag-bot.timer
```

---

## 📊 Monitoring & Logs

### Logs anzeigen

```bash
# Container-Logs (Live)
docker-compose logs -f gewobag-bot

# Logs aus Volume (detailliert)
tail -f logs/gewobag-main.log
tail -f logs/application-bot.log

# Alle Logs der letzten Stunde
find logs/ -name "*.log" -mmin -60 -exec tail -n 50 {} \;
```

### Datenbank inspizieren

```bash
# Lokaler Zugriff
sqlite3 gewobag_wohnungen.db "SELECT * FROM wohnungen WHERE applied = 1;"

# Innerhalb des Containers
docker-compose exec gewobag-bot sqlite3 /app/gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen;"
```

### Container-Status prüfen

```bash
# Laufende Container
docker-compose ps

# Resource-Nutzung
docker stats gewobag-bot

# Healthcheck-Status
docker inspect gewobag-bot | grep -A 10 Health
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" bei Volumes

**Lösung:**

```bash
# User-ID im Container prüfen
docker-compose run --rm gewobag-bot id

# Dateien auf Host anpassen
sudo chown -R 1000:1000 gewobag_wohnungen.db logs/
```

---

### Problem: "Browser not found" (Playwright)

**Ursache:** Playwright-Browser nicht installiert

**Lösung:**

```bash
# Image neu bauen (mit --no-cache)
docker-compose build --no-cache

# Oder manuell im Container installieren
docker-compose run --rm gewobag-bot playwright install chromium
```

---

### Problem: Logs werden nicht geschrieben

**Lösung:**

```bash
# Logs-Verzeichnis erstellen
mkdir -p logs

# Berechtigungen setzen
chmod 777 logs/

# Container neu starten
docker-compose restart
```

---

### Problem: Datenbank ist gesperrt

**Ursache:** Mehrere Container greifen gleichzeitig zu

**Lösung:**

```bash
# Alle Container stoppen
docker-compose down

# Nur einen Container starten
docker-compose run --rm gewobag-bot
```

---

### Problem: "Out of Memory" (OOM)

**Lösung:**

```yaml
# In docker-compose.yml Memory-Limit erhöhen
deploy:
  resources:
    limits:
      memory: 4G  # von 2G auf 4G erhöhen
```

---

## 🔒 Sicherheit

### 1. Sensible Daten schützen

```bash
# user_data.json niemals committen!
echo "user_data.json" >> .gitignore
echo "documents/" >> .gitignore

# Berechtigungen einschränken
chmod 600 user_data.json
chmod 700 documents/
```

### 2. Docker Security Best Practices

```dockerfile
# Non-root User verwenden (bereits implementiert)
USER botuser

# Read-only Root Filesystem (optional)
docker run --read-only --tmpfs /tmp gewobag-bot

# Capabilities einschränken
docker run --cap-drop ALL gewobag-bot
```

### 3. Network Isolation

```yaml
# In docker-compose.yml
networks:
  bot-network:
    driver: bridge

services:
  gewobag-bot:
    networks:
      - bot-network
```

---

## 🚢 Production Deployment

### Docker Swarm (Multi-Node)

```bash
# Swarm initialisieren
docker swarm init

# Stack deployen
docker stack deploy -c docker-compose.yml gewobag

# Status prüfen
docker stack services gewobag
```

### Kubernetes (K8s)

Beispiel `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gewobag-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gewobag-bot
  template:
    metadata:
      labels:
        app: gewobag-bot
    spec:
      containers:
      - name: gewobag-bot
        image: gewobag-bot:latest
        volumeMounts:
        - name: config
          mountPath: /app/user_data.json
          subPath: user_data.json
        - name: db
          mountPath: /app/gewobag_wohnungen.db
      volumes:
      - name: config
        secret:
          secretName: gewobag-config
      - name: db
        persistentVolumeClaim:
          claimName: gewobag-db-pvc
```

---

## 📈 Performance-Optimierung

### 1. Multi-Stage Build nutzen

Bereits implementiert in `Dockerfile`:
- Stage 1: Builder (nur Build-Dependencies)
- Stage 2: Runtime (minimales Image)

### 2. Image-Größe reduzieren

```bash
# Image-Größe prüfen
docker images gewobag-bot

# Ungenutzte Layers entfernen
docker builder prune -a
```

### 3. Build-Cache nutzen

```bash
# Mit Cache bauen
docker-compose build

# Cache ignorieren (bei Problemen)
docker-compose build --no-cache
```

---

## 🔄 Updates & Wartung

### Bot-Code aktualisieren

```bash
# Neueste Version ziehen
git pull origin main

# Image neu bauen
docker-compose build

# Container neu starten
docker-compose down
docker-compose up -d
```

### Datenbank-Backup

```bash
# Backup erstellen
cp gewobag_wohnungen.db gewobag_wohnungen.db.backup.$(date +%Y%m%d)

# Oder mit SQLite
sqlite3 gewobag_wohnungen.db ".backup backup_$(date +%Y%m%d).db"
```

### Alte Images aufräumen

```bash
# Ungenutzte Images löschen
docker image prune -a

# Alte Containers löschen
docker container prune
```

---

## 📞 Support

Bei Problemen:

1. **Logs prüfen:** `docker-compose logs -f`
2. **Healthcheck prüfen:** `docker inspect gewobag-bot`
3. **Interaktive Shell:** `docker-compose run --rm gewobag-bot /bin/bash`
4. **Image neu bauen:** `docker-compose build --no-cache`

---

## ✅ Checkliste für Production

- [ ] `user_data.json` vollständig ausgefüllt
- [ ] `filter_config.json` konfiguriert
- [ ] Dokumente im `documents/` Verzeichnis
- [ ] Docker & Docker Compose installiert
- [ ] Image erfolgreich gebaut
- [ ] Test-Lauf mit `--max 1` erfolgreich
- [ ] Logs-Verzeichnis erstellt
- [ ] Backup-Strategie definiert
- [ ] Monitoring eingerichtet (optional)
- [ ] Cron-Job/Timer konfiguriert (optional)

---

**Viel Erfolg mit dem Deployment! 🚀**
