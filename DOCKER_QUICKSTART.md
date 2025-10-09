# 🚀 Docker Quickstart - Gewobag Bot

## ⚡ Schnellster Weg zum Testen

### Schritt 1: Docker Desktop starten
- Öffne Docker Desktop
- Warte bis das Docker-Icon in der Menüleiste erscheint

### Schritt 2: Automatischen Test ausführen
```bash
cd "/Users/khaled/Desktop/bot new"
./test_docker.sh
```

**Das Test-Skript prüft automatisch:**
- ✅ Docker Daemon Status
- ✅ docker-compose.yml Syntax
- ✅ Docker Image Build
- ✅ Container-Start
- ✅ Python & Playwright Installation
- ✅ Alle Python-Packages
- ✅ Volume-Mounts
- ✅ Healthcheck
- ✅ Non-root User (Sicherheit)

**Erwartete Dauer:** 3-5 Minuten beim ersten Mal

---

## 📝 Manuelle Test-Schritte (alternativ)

### 1. Docker prüfen
```bash
docker info
```

### 2. Image bauen
```bash
docker-compose build
```

### 3. Test-Container starten
```bash
docker-compose run --rm gewobag-bot python main.py --setup
```

### 4. Interaktive Shell öffnen
```bash
docker-compose run --rm gewobag-bot /bin/bash
```

---

## 🎯 Nach erfolgreichem Test

### Konfiguration vorbereiten
```bash
# Außerhalb Docker (auf Host)
python main.py --setup

# user_data.json und filter_config.json bearbeiten
nano user_data.json
nano filter_config.json
```

### Bot mit Docker starten
```bash
# Einmalige Ausführung (Vollautomatik)
docker-compose run --rm gewobag-bot

# Im Hintergrund laufen lassen
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

---

## 🐛 Häufige Probleme

### "Cannot connect to Docker daemon"
**Lösung:** Docker Desktop starten

### "version is obsolete"
**Status:** ✅ Bereits behoben

### "Permission denied: test_docker.sh"
**Lösung:**
```bash
chmod +x test_docker.sh
```

### Build dauert sehr lange
**Normal!** Beim ersten Mal werden ~1.5 GB heruntergeladen (Chromium-Browser)

---

## 📚 Weitere Dokumentation

- **DOCKER_TEST.md** - Detaillierte Test-Anleitung
- **DEPLOYMENT.md** - Production-Deployment
- **README.md** - Allgemeine Dokumentation

---

**Status:** Bereit zum Testen! 🎉

Führe einfach aus:
```bash
./test_docker.sh
```
