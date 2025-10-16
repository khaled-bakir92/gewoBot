# 🔄 VPS Update & Troubleshooting Guide

Schnellreferenz für Updates und Fehlerbehebung des Gewobag Bots auf dem VPS.

---

## 🚀 Standard Update (von GitHub)

### Schritt 1: Auf VPS einloggen
```bash
ssh root@157.173.99.84
cd ~/gewoBot
```

### Schritt 2: Container stoppen
```bash
docker-compose down
```

### Schritt 3: Neueste Version von GitHub holen
```bash
# Lokale Änderungen verwerfen
git fetch origin
git reset --hard origin/fronted-gewobot

# Neueste Version pullen
git pull origin fronted-gewobot
```
 # Erstelle die leere Heartbeat-Datei auf dem Host
  cd /root/gewoBot
  touch .bot_heartbeat.json

### Schritt 4: Neu bauen und starten
```bash
# Docker Images neu bauen
docker-compose build

# Alle Services starten
docker-compose up -d

# Bot stoppen (läuft über Scheduler)
docker-compose stop gewobag-bot

# Status prüfen
docker-compose ps
```

**Erwartetes Ergebnis:**
- `gewobag-bot` → **Exit 0** (gestoppt, wird vom Scheduler gestartet)
- `gewobag-web` → **Up (healthy)**
- `gewobag-scheduler` → **Up**

---

## 🛠️ Bei Docker-Compose Fehler

Wenn du Fehler wie `'ContainerConfig'` oder `KeyError` bekommst:

```bash
# Alles stoppen und komplett entfernen
docker-compose down

# Alle Container und Images löschen
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker rmi gewobot_gewobag-web gewobot_gewobag-bot 2>/dev/null || true

# Alles neu bauen
docker-compose build

# Alles starten
docker-compose up -d

# Bot stoppen (läuft über Scheduler)
docker-compose stop gewobag-bot

# Status prüfen
docker-compose ps
```

---

## 🔐 Berechtigungsproblem beheben

Wenn das Speichern im Frontend nicht funktioniert:

**Fehler:** `500 INTERNAL SERVER ERROR` beim Speichern von Benutzerdaten oder Filtern

**Lösung:**
```bash
cd ~/gewoBot

# Berechtigungen für JSON-Dateien setzen (read + write für alle)
chmod 666 user_data.json
chmod 666 filter_config.json

# Prüfen
ls -la *.json
```

**Erwartetes Ergebnis:**
```
-rw-rw-rw- ... user_data.json
-rw-rw-rw- ... filter_config.json
```

**Web-Container neu starten:**
```bash
docker-compose restart gewobag-web
```

---

## 📊 Scheduler überwachen

### Scheduler-Logs live anschauen
```bash
docker-compose logs -f gewobag-scheduler
```

**Was du sehen solltest:**
```
New job registered "gewobag-bot-job" - "python main.py --full" - "@every 15m"
Starting scheduler with 1 jobs
```

Mit `Ctrl + C` beenden.

---

### Bot-Logs prüfen (wann hat er zuletzt gelaufen?)
```bash
docker-compose logs gewobag-bot | grep "GEWOBAG BOT" | tail -10
```

Zeigt die letzten 10 Bot-Starts.

---

### Wann wurde der Scheduler gestartet?
```bash
docker-compose logs gewobag-scheduler | grep "registered"
```

**Beispiel-Ausgabe:**
```
2025-10-16T01:14:06.895Z ... New job registered "gewobag-bot-job" - "@every 15m"
```

**Bedeutung:** Scheduler startete um 01:14 UTC (03:14 Berlin Zeit)

**Nächste automatische Läufe:**
- 03:29 Uhr
- 03:44 Uhr
- 03:59 Uhr
- usw. (alle 15 Minuten)

---

### Alle Logs live anschauen
```bash
docker-compose logs -f
```

Warte bis zur nächsten 15-Minuten-Marke und du siehst:
```
gewobag-bot | 🏠 GEWOBAG BOT v2.0 🤖
gewobag-bot | 🤖 MODUS: VOLLAUTOMATISCH (SUCHE + BEWERBUNG)
gewobag-bot | 📍 Schritt 1/2: Wohnungssuche...
```

---

## 🧪 Scheduler-Test (1-Minuten-Intervall)

Wenn du nicht 15 Minuten warten willst:

### Schritt 1: Intervall ändern
```bash
nano ~/gewoBot/docker-compose.yml
```

Suche nach:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 15m"
```

Ändere zu:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 1m"
```

Speichern: `Ctrl + O` → `Enter` → `Ctrl + X`

### Schritt 2: Scheduler neu starten
```bash
docker-compose up -d gewobag-scheduler
```

### Schritt 3: Live zuschauen
```bash
docker-compose logs -f
```

Nach **1 Minute** sollte der Bot automatisch starten!

### Schritt 4: Zurück auf 15 Minuten setzen
```bash
nano ~/gewoBot/docker-compose.yml
```

Ändere zurück:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 15m"
```

```bash
docker-compose up -d gewobag-scheduler
```

---

## 🗄️ Datenbank prüfen

### Anzahl gefundener Wohnungen
```bash
docker-compose exec gewobag-web sqlite3 /app/gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen;"
```

### Anzahl Bewerbungen
```bash
docker-compose exec gewobag-web sqlite3 /app/gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen WHERE applied = 1;"
```

### Letzte 5 Wohnungen mit Zeitstempel
```bash
docker-compose exec gewobag-web sqlite3 /app/gewobag_wohnungen.db "SELECT id, titel, timestamp FROM wohnungen ORDER BY id DESC LIMIT 5;"
```

---

## ✅ Checkliste nach Update

- [ ] `docker-compose ps` zeigt alle Services als "Up"
- [ ] `gewobag-bot` ist "Exit 0" (wird vom Scheduler gestartet)
- [ ] `gewobag-web` ist "Up (healthy)"
- [ ] `gewobag-scheduler` ist "Up"
- [ ] Frontend lädt: `http://157.173.99.84:5000`
- [ ] Speichern im Frontend funktioniert (Benutzerdaten, Filter)
- [ ] Scheduler läuft (Logs zeigen "New job registered")
- [ ] Bot läuft alle 15 Minuten automatisch

---

## 🆘 Häufige Probleme

### Problem: Frontend lädt nicht
**Lösung:**
```bash
docker-compose logs gewobag-web
docker-compose restart gewobag-web
```

### Problem: API gibt 500 Fehler beim Speichern
**Lösung:**
```bash
chmod 666 ~/gewoBot/user_data.json
chmod 666 ~/gewoBot/filter_config.json
docker-compose restart gewobag-web
```

### Problem: Bot läuft nicht automatisch
**Lösung:**
```bash
# Scheduler-Logs prüfen
docker-compose logs gewobag-scheduler

# Scheduler neu starten
docker-compose restart gewobag-scheduler

# Live zuschauen
docker-compose logs -f
```

### Problem: Container startet nicht nach Update
**Lösung:**
```bash
docker-compose down
docker rm -f $(docker ps -aq)
docker-compose build
docker-compose up -d
docker-compose stop gewobag-bot
```

---

## 📞 Nützliche Befehle

```bash
# Status aller Container
docker-compose ps

# Alle Logs
docker-compose logs -f

# Nur Web-Logs
docker-compose logs -f gewobag-web

# Nur Bot-Logs
docker-compose logs gewobag-bot | tail -50

# Nur Scheduler-Logs
docker-compose logs gewobag-scheduler

# Container neu starten
docker-compose restart gewobag-web

# Speicherplatz prüfen
df -h

# Docker aufräumen
docker system prune -a
```

---

## 🎯 Quick Commands

### Update durchführen
```bash
cd ~/gewoBot && git fetch origin && git reset --hard origin/fronted-gewobot && git pull && docker-compose build && docker-compose up -d && docker-compose stop gewobag-bot
```

### Bei Fehler komplett neu
```bash
cd ~/gewoBot && docker-compose down && docker rm -f $(docker ps -aq) && docker-compose build && docker-compose up -d && docker-compose stop gewobag-bot
```

### Berechtigungen fixen + Web neu starten
```bash
cd ~/gewoBot && chmod 666 user_data.json filter_config.json && docker-compose restart gewobag-web
```

---

## 🌐 Wichtige Links

- **Frontend:** http://157.173.99.84:5000
- **GitHub Repo:** https://github.com/khaled-bakir92/gewoBot
- **Branch:** fronted-gewobot

---

**Viel Erfolg! 🏠🎉**
