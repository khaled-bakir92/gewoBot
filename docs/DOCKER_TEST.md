# 🐳 Docker Test-Anleitung

## Problem: Docker Daemon nicht gestartet

Der Docker Daemon muss laufen, bevor wir das Image bauen können.

## ✅ Lösung: Docker Desktop starten

### Auf macOS:

1. **Docker Desktop öffnen:**
   - Öffne die Anwendung "Docker" aus dem Programme-Ordner
   - Oder über Spotlight: `Cmd + Space` → "Docker" eingeben
   - Warte bis das Docker-Icon in der Menüleiste erscheint (kleiner Wal)

2. **Warten bis Docker läuft:**
   ```bash
   # Prüfen ob Docker bereit ist
   docker info
   ```

3. **Dann Docker Build starten:**
   ```bash
   cd "/Users/khaled/Desktop/bot new"
   docker-compose build
   ```

---

## 🧪 Vollständiger Test-Ablauf

### Schritt 1: Docker Daemon prüfen
```bash
docker info
# Sollte Docker-Info anzeigen (nicht "Cannot connect to Docker daemon")
```

### Schritt 2: Image bauen
```bash
cd "/Users/khaled/Desktop/bot new"
docker-compose build
```

**Erwartete Ausgabe:**
- Baut zwei Stages (Builder + Runtime)
- Installiert Python-Packages
- Installiert Playwright-Browser
- Dauer: ca. 3-5 Minuten beim ersten Mal

### Schritt 3: Image-Größe prüfen
```bash
docker images | grep gewobag
```

**Erwartete Größe:** ~1.5-2 GB (wegen Chromium-Browser)

### Schritt 4: Test-Container starten (nur Setup)
```bash
docker-compose run --rm gewobag-bot python main.py --setup
```

**Erwartete Ausgabe:**
- Erstellt Datenbank-Schema
- Erstellt Konfigurationsdateien (falls nicht vorhanden)
- Lädt Bezirke von Website

### Schritt 5: Container mit Healthcheck prüfen
```bash
# Container im Hintergrund starten
docker-compose up -d

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f
```

### Schritt 6: Interaktive Shell testen
```bash
docker-compose run --rm gewobag-bot /bin/bash
```

**Im Container:**
```bash
# Python-Version prüfen
python --version

# Playwright-Browser prüfen
playwright --version

# Datenbank prüfen (falls vorhanden)
ls -la /app/gewobag_wohnungen.db

# Exit
exit
```

### Schritt 7: Volume-Mounts testen
```bash
# Erstelle Test-Konfiguration
echo '{"test": "data"}' > user_data.json

# Container starten und Datei prüfen
docker-compose run --rm gewobag-bot cat /app/user_data.json
```

**Erwartete Ausgabe:** `{"test": "data"}`

### Schritt 8: Test mit echten Daten (optional)
```bash
# Nur wenn user_data.json und filter_config.json konfiguriert sind!
docker-compose run --rm gewobag-bot python main.py --scrape --max 1
```

### Schritt 9: Container aufräumen
```bash
# Container stoppen
docker-compose down

# Images löschen (optional)
docker rmi bot-new-gewobag-bot
```

---

## 🐛 Troubleshooting

### Problem: "Cannot connect to Docker daemon"
**Lösung:** Docker Desktop starten (siehe oben)

### Problem: "version is obsolete"
**Status:** ✅ Bereits behoben (version-Zeile entfernt)

### Problem: "No such file or directory: user_data.json"
**Lösung:**
```bash
# Template erstellen
python main.py --setup

# Oder Docker verwenden
docker-compose run --rm gewobag-bot python main.py --setup
```

### Problem: "Permission denied" bei Volumes
**Lösung:**
```bash
# User-ID im Container prüfen
docker-compose run --rm gewobag-bot id
# Sollte: uid=1000(botuser) gid=1000(botuser) zeigen

# Dateien auf Host anpassen
chown -R 1000:1000 gewobag_wohnungen.db logs/
```

### Problem: Image zu groß
**Erklärung:** Chromium-Browser ist ~1 GB groß (notwendig für Playwright)

**Alternative:** Headless-Mode mit externem Browser (komplizierter)

### Problem: Build schlägt fehl bei Playwright
**Lösung:**
```bash
# Mit --no-cache neu bauen
docker-compose build --no-cache

# Oder manuell im Container installieren
docker-compose run --rm gewobag-bot playwright install chromium
```

---

## ✅ Erfolgs-Kriterien

Nach erfolgreichem Test sollten folgende Punkte erfüllt sein:

- [ ] Docker Daemon läuft (`docker info` funktioniert)
- [ ] Image wurde erfolgreich gebaut (`docker images` zeigt gewobag-bot)
- [ ] Container startet ohne Fehler (`docker-compose up`)
- [ ] Healthcheck ist "healthy" (`docker-compose ps`)
- [ ] Volumes werden korrekt gemountet (Dateien sichtbar im Container)
- [ ] Python-Skripte laufen im Container (`python main.py --setup`)
- [ ] Playwright-Browser ist installiert (`playwright --version`)
- [ ] Logs werden geschrieben (`docker-compose logs`)

---

## 📊 Performance-Benchmarks

**Erwartete Zeiten:**

- **Build (erster Durchlauf):** 3-5 Minuten
- **Build (mit Cache):** 10-30 Sekunden
- **Container-Start:** 2-5 Sekunden
- **Scraping (1 Seite):** 10-20 Sekunden
- **Bewerbung (1 Wohnung):** 30-60 Sekunden

---

## 🚀 Next Steps nach erfolgreichem Test

1. **Konfiguration vorbereiten:**
   ```bash
   python main.py --setup
   # user_data.json und filter_config.json bearbeiten
   ```

2. **Production-Build:**
   ```bash
   docker-compose build --no-cache
   ```

3. **Deployment:**
   - Siehe `DEPLOYMENT.md` für Cron-Setup
   - Siehe `DEPLOYMENT.md` für Cloud-Deployment

4. **Monitoring einrichten:**
   - Log-Rotation konfigurieren
   - Benachrichtigungen einrichten (optional)

---

**Status:** Bereit für Test, sobald Docker Desktop gestartet ist! 🎉
