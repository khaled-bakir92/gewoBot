# VPS Deployment Fix - Scheduler Error beheben

## Problem
Der Scheduler zeigt folgende Fehler:
```
error creating exec: API error (409): container c72baa95... is not running
```

**Ursache:** Der Scheduler versuchte, Befehle in einem existierenden Container auszuführen (`job-exec`), aber der Container war nicht mehr aktiv.

## Lösung
Die neue Konfiguration verwendet `job-run` statt `job-exec`. Das bedeutet:
- ✅ Der Scheduler startet **neue Container** für jeden Job
- ✅ Container werden nach dem Job automatisch gelöscht
- ✅ Keine dauerhaft laufenden Bot-Container mehr nötig

## Deployment-Schritte auf VPS

### 1. Neue Dateien hochladen
```bash
# Auf lokalem Rechner (Desktop)
scp docker-compose.yml ofelia-config.ini root@vmd181811.contaboserver.net:~/gewoBot/

# ODER: Wenn SSH-Key fehlt, Files manuell kopieren (z.B. via FTP/SCP-Client)
# Benötigte Dateien:
#   - docker-compose.yml (aktualisiert)
#   - ofelia-config.ini (NEU!)
```

### 2. Auf VPS einloggen
```bash
ssh root@vmd181811.contaboserver.net
cd ~/gewoBot
```

### 3. **WICHTIG:** Pfade in ofelia-config.ini anpassen
```bash
# Aktuellen Pfad ermitteln
pwd
# Sollte /root/gewoBot sein

# Wenn anders, ofelia-config.ini bearbeiten:
nano ofelia-config.ini
# Alle Zeilen mit "volume = /root/gewoBot/..." anpassen

# Beispiel: Wenn Pfad /home/user/gewobag ist:
# volume = /home/user/gewobag/user_data.json:/app/user_data.json:ro
```

### 4. Alte Container stoppen und entfernen
```bash
# Alle Services stoppen
docker-compose down

# Prüfen, ob alle Container weg sind
docker-compose ps
```

### 5. Docker Image neu bauen
```bash
# Wichtig: Image mit richtigem Namen bauen
docker-compose build gewobag-bot

# Prüfen, ob Image erstellt wurde
docker images | grep gewobot
```

Erwartete Ausgabe:
```
gewobot-gewobag-bot   latest   abc123def456   ...
```

### 6. Nur Web-Frontend und Scheduler starten
```bash
# Web-Frontend starten (dauerhaft)
docker-compose up -d gewobag-web

# Scheduler starten (startet Bot alle 15 Min automatisch)
docker-compose up -d gewobag-scheduler
```

**Wichtig:** Der `gewobag-bot` Container läuft **nicht** dauerhaft! Er wird nur vom Scheduler gestartet.

### 7. Logs prüfen
```bash
# Scheduler-Logs (sollten jetzt keine Fehler mehr zeigen)
docker-compose logs -f gewobag-scheduler

# Warten auf nächsten Job (max 15 Min)
# Erwartete Ausgabe:
# [Job "gewobag-bot-job"] Started - python main.py --full
# [Job "gewobag-bot-job"] Finished in "45s"
```

### 8. Bot-Logs prüfen (nach Job-Ausführung)
```bash
# Logs im Volume prüfen
tail -f logs/gewobag-main.log
tail -f logs/application-bot.log
```

## Manuelle Ausführung (falls nötig)

Wenn Sie den Bot **manuell** ausführen möchten (nicht über Scheduler):

```bash
# Einmalig ausführen
docker-compose run --rm --profile manual gewobag-bot python main.py --full

# Nur Scraping
docker-compose run --rm --profile manual gewobag-bot python main.py --scrape

# Nur Bewerbungen
docker-compose run --rm --profile manual gewobag-bot python main.py --apply
```

## Scheduler-Einstellungen anpassen

### Zeitplan ändern
Bearbeiten Sie `docker-compose.yml` auf dem VPS:

```yaml
# Aktuelle Einstellung: Alle 15 Minuten
ofelia.job-run.gewobag-bot-job.schedule: "@every 15m"

# Alle 30 Minuten
ofelia.job-run.gewobag-bot-job.schedule: "@every 30m"

# Stündlich
ofelia.job-run.gewobag-bot-job.schedule: "@hourly"

# Alle 6 Stunden
ofelia.job-run.gewobag-bot-job.schedule: "@every 6h"

# Cron-Syntax: Mo-Fr, 9-18 Uhr, alle 15 Min
ofelia.job-run.gewobag-bot-job.schedule: "*/15 9-18 * * 1-5"
```

Nach Änderung:
```bash
docker-compose up -d gewobag-scheduler
```

## Status-Übersicht

### Alle Services anzeigen
```bash
docker-compose ps
```

Erwartete Ausgabe:
```
NAME                  STATUS          PORTS
gewobag-scheduler     Up 10 minutes
gewobag-web           Up 10 minutes   0.0.0.0:5000->5000/tcp
```

**Wichtig:** `gewobag-bot` sollte **NICHT** in der Liste sein (läuft nur temporär)!

### Laufende Container anzeigen (während Job läuft)
```bash
docker ps
```

Während der Bot läuft, sehen Sie kurzzeitig:
```
CONTAINER ID   IMAGE                         COMMAND                  STATUS
abc123...      gewobot-gewobag-bot:latest   "python main.py --full"  Up 5 seconds
```

### Scheduler-Jobs anzeigen
```bash
docker-compose logs gewobag-scheduler | grep "registered"
```

Erwartete Ausgabe:
```
New job registered "gewobag-bot-job" - "python main.py --full" - "@every 15m"
```

## Troubleshooting

### Fehler: "No such image: gewobot-gewobag-bot:latest"
```bash
# Image neu bauen
docker-compose build gewobag-bot
docker images | grep gewobot
```

### Fehler: "network gewobot_default not found"
```bash
# Netzwerk wird automatisch erstellt bei:
docker-compose up -d gewobag-web
```

### Scheduler läuft, aber keine Jobs
```bash
# Scheduler neu starten
docker-compose restart gewobag-scheduler

# Logs prüfen
docker-compose logs gewobag-scheduler
```

### Bot-Container bleibt hängen
```bash
# Hängende Container finden
docker ps -a | grep gewobag

# Container manuell entfernen
docker rm -f <container-id>
```

### Volumes sind leer oder falsch
```bash
# Prüfen Sie die Dateien auf dem VPS
ls -lah ~/gewoBot/
# Sollte enthalten:
# - user_data.json
# - filter_config.json
# - gewobag_wohnungen.db
# - logs/
# - documents/
```

## Vorteile der neuen Konfiguration

✅ **Keine Container-Konflikte** - Jeder Job läuft in frischem Container
✅ **Automatische Bereinigung** - Container werden nach Job gelöscht
✅ **Weniger Ressourcen** - Bot läuft nur wenn nötig (nicht 24/7)
✅ **Bessere Logs** - Klare Trennung zwischen Job-Läufen
✅ **Einfacher zu debuggen** - Fehler sind isoliert pro Job

## Nächste Schritte

1. ✅ Neue docker-compose.yml auf VPS deployen
2. ✅ Services neu starten
3. ✅ 15 Minuten warten und Logs prüfen
4. ✅ Web-Frontend aufrufen: http://<VPS-IP>:5000
5. ✅ Scheduler-Zeitplan nach Bedarf anpassen

## Erfolgreiche Ausführung erkennen

**Scheduler-Log:**
```
[Job "gewobag-bot-job"] Started - python main.py --full
[Job "gewobag-bot-job"] Finished in "42s"
```

**Bot-Log (logs/gewobag-main.log):**
```
2025-10-16 10:15:22 - __main__ - INFO - 🚀 Gewobag Bot v2.2 gestartet (Modus: Vollautomatik)
2025-10-16 10:15:23 - gewobag_bot - INFO - 🔍 Starte Wohnungssuche...
2025-10-16 10:15:45 - application_bot - INFO - ✅ Bewerbung erfolgreich gesendet!
2025-10-16 10:16:02 - __main__ - INFO - ✅ Bot-Durchlauf erfolgreich abgeschlossen
```

## Support

Bei weiteren Problemen:
1. Logs prüfen: `docker-compose logs -f`
2. Container-Status: `docker-compose ps`
3. Manuelle Ausführung testen
4. VPS-Ressourcen prüfen: `free -h` und `df -h`
