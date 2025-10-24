# 🤖 Gewobag Bot - Wichtige Befehle

Schnellreferenz für die Verwaltung deines Gewobag Bots auf dem VPS.

---

## 🔐 SSH-Verbindung zum VPS

```bash
ssh root@157.173.99.84
```

Nach dem Einloggen:
```bash
cd ~/gewoBot
```

---

## 📊 STATUS & ÜBERSICHT

### Services anzeigen
```bash
docker-compose ps
```
Zeigt alle Container und ihren Status (Up/Exit/Restarting).

### Alle Logs anzeigen (Live)
```bash
docker-compose logs -f
```
Zeigt Logs aller Services in Echtzeit. Mit `Ctrl + C` beenden.

### Logs einzelner Services
```bash
# Scheduler Logs (zeigt wann Bot läuft)
docker-compose logs -f gewobag-scheduler

# Bot Logs
docker-compose logs -f gewobag-bot

# Web-Frontend Logs
docker-compose logs -f gewobag-web
```

### Letzte 50 Zeilen der Logs
```bash
docker-compose logs --tail=50 gewobag-bot
```

### Ressourcen-Verbrauch prüfen
```bash
docker stats
```
Zeigt CPU, RAM, Netzwerk-Nutzung. Mit `Ctrl + C` beenden.

---

## 🚀 STARTEN & STOPPEN

### Alle Services starten
```bash
docker-compose up -d
```
Startet Bot, Web-Frontend und Scheduler.

### Nur bestimmte Services starten
```bash
# Nur Web-Frontend
docker-compose up -d gewobag-web

# Nur Scheduler
docker-compose up -d gewobag-scheduler

# Web + Scheduler
docker-compose up -d gewobag-web gewobag-scheduler
```

### Alle Services stoppen
```bash
docker-compose down
```
Stoppt und entfernt alle Container.

### Einzelnen Service stoppen
```bash
docker-compose stop gewobag-web
```

### Einzelnen Service neu starten
```bash
docker-compose restart gewobag-web
```

---

## 🔄 NEU BAUEN & AKTUALISIEREN

### Nach Code-Änderungen: Neu bauen
```bash
# Alle Services neu bauen
docker-compose build

# Nur einen Service neu bauen
docker-compose build gewobag-web

# Neu bauen und starten
docker-compose up -d --build
```

### Projekt vom GitHub aktualisieren
```bash
cd ~/gewoBot

# Änderungen holen
git pull origin fronted-gewobot

# Neu bauen
docker-compose build

# Neu starten
docker-compose up -d
```

---

## 🧪 BOT MANUELL TESTEN

### Bot einmal manuell ausführen
```bash
# Vollständiger Lauf (Suche + Bewerbung)
docker-compose run --rm gewobag-bot python main.py --full

# Nur Suche (keine Bewerbung)
docker-compose run --rm gewobag-bot python main.py --scrape

# Nur Bewerbung (auf bereits gefundene Wohnungen)
docker-compose run --rm gewobag-bot python main.py --apply

# Nur 1 Bewerbung zum Testen
docker-compose run --rm gewobag-bot python main.py --apply --max 1

# Setup/Initialisierung
docker-compose run --rm gewobag-bot python main.py --setup
```

---

## ⚙️ KONFIGURATION BEARBEITEN

### Benutzerdaten bearbeiten
```bash
export TERM=xterm
nano user_data.json
```
Speichern: `Ctrl + O` → `Enter` → `Ctrl + X`

### Suchfilter bearbeiten
```bash
nano filter_config.json
```

### docker-compose.yml bearbeiten
```bash
nano docker-compose.yml
```

### Scheduler-Intervall ändern
In `docker-compose.yml` bei `gewobag-scheduler` Zeile ändern:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 15m"
```

Optionen:
- `@every 15m` - Alle 15 Minuten
- `@every 30m` - Alle 30 Minuten
- `@hourly` - Stündlich
- `@every 6h` - Alle 6 Stunden
- `*/15 9-18 * * 1-5` - Mo-Fr, 9-18 Uhr, alle 15 Min

Nach Änderung:
```bash
docker-compose up -d gewobag-scheduler
```

---

## 🗄️ DATENBANK

### Datenbank anschauen
```bash
# Alle Wohnungen anzeigen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT * FROM wohnungen;"

# Anzahl Wohnungen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen;"

# Anzahl Bewerbungen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen WHERE applied = 1;"

# Erfolgreiche Bewerbungen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen WHERE status = 'success';"

# Letzte 5 Wohnungen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT titel, bezirk, miete FROM wohnungen ORDER BY id DESC LIMIT 5;"
```

### Datenbank sichern
```bash
cp gewobag_wohnungen.db gewobag_wohnungen_backup_$(date +%Y%m%d).db
```

### Datenbank zurücksetzen
```bash
rm gewobag_wohnungen.db
docker-compose run --rm gewobag-bot python main.py --setup
```

---

## 🌐 WEB-FRONTEND

### Frontend öffnen
```
http://157.173.99.84:5000
```

### Frontend-Port prüfen
```bash
docker-compose port gewobag-web 8080
```

### Frontend neu laden (nach Änderungen)
```bash
docker-compose restart gewobag-web
```

---

## 🧹 AUFRÄUMEN & WARTUNG

### Docker aufräumen (Speicherplatz freigeben)
```bash
# Ungenutzte Container/Images löschen
docker system prune -a

# Mit Volumes (VORSICHT: löscht auch Datenbank!)
docker system prune -a --volumes
```

### Logs löschen
```bash
cd ~/gewoBot/logs
rm *.log
```

### Alte Backups löschen (älter als 7 Tage)
```bash
find ~/backups -name "*.db" -mtime +7 -delete
```

### Speicherplatz prüfen
```bash
df -h
```

### Docker Disk Usage
```bash
docker system df
```

---

## 🔍 TROUBLESHOOTING

### Container startet nicht
```bash
# Logs anschauen
docker-compose logs gewobag-web

# Container komplett neu bauen
docker-compose down
docker rm -f gewobag-web
docker rmi gewobot_gewobag-web
docker-compose build gewobag-web
docker-compose up -d gewobag-web
```

### Port bereits belegt
```bash
# Prüfen welcher Prozess Port 5000 nutzt
sudo netstat -tlnp | grep :5000

# Prozess beenden
sudo kill -9 <PID>
```

### Bot läuft nicht automatisch
```bash
# Scheduler-Logs prüfen
docker-compose logs gewobag-scheduler

# Scheduler neu starten
docker-compose restart gewobag-scheduler
```

### Firewall-Probleme
```bash
# Firewall-Status prüfen
sudo ufw status

# Port 5000 freigeben (falls nötig)
sudo ufw allow 5000/tcp
sudo ufw reload
```

### Speicher voll
```bash
# Größte Verzeichnisse finden
du -sh /var/* | sort -rh | head -10

# Docker aufräumen
docker system prune -a

# Logs rotieren
journalctl --vacuum-size=100M
```

---

## 📦 BACKUP & RESTORE

### Backup erstellen
```bash
# Backup-Verzeichnis erstellen
mkdir -p ~/backups

# Datenbank sichern
cp ~/gewoBot/gewobag_wohnungen.db ~/backups/gewobag_$(date +%Y%m%d_%H%M%S).db

# Konfiguration sichern
cp ~/gewoBot/user_data.json ~/backups/
cp ~/gewoBot/filter_config.json ~/backups/

# Logs sichern
tar -czf ~/backups/logs_$(date +%Y%m%d).tar.gz ~/gewoBot/logs/
```

### Backup wiederherstellen
```bash
# Datenbank wiederherstellen
cp ~/backups/gewobag_YYYYMMDD_HHMMSS.db ~/gewoBot/gewobag_wohnungen.db

# Container neu starten
docker-compose restart gewobag-bot gewobag-web
```

### Automatisches Backup (täglich um 3 Uhr)
```bash
# Crontab bearbeiten
crontab -e

# Diese Zeile hinzufügen:
0 3 * * * cp ~/gewoBot/gewobag_wohnungen.db ~/backups/gewobag_$(date +\%Y\%m\%d).db
```

---

## 🔐 SICHERHEIT

### Root-Passwort ändern
```bash
passwd
```

### SSH-Key einrichten (empfohlen)
```bash
# Auf lokalem Mac:
ssh-keygen -t rsa -b 4096
ssh-copy-id root@157.173.99.84

# Dann Passwort-Login deaktivieren:
sudo nano /etc/ssh/sshd_config
# Ändere: PasswordAuthentication no
sudo systemctl restart sshd
```

### Firewall prüfen
```bash
sudo ufw status verbose
```

### Updates installieren
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 📱 MONITORING (Optional)

### Systemressourcen live anzeigen
```bash
htop
```
Installation: `sudo apt install htop`

### Docker-Container überwachen
```bash
watch -n 2 docker-compose ps
```

### Bot-Aktivität überwachen (Live)
```bash
tail -f ~/gewoBot/logs/gewobag-bot.log
```

---

## 🆘 NOTFALL-BEFEHLE

### Alles stoppen
```bash
docker-compose down
```

### Alles neu starten
```bash
docker-compose down
docker-compose up -d
```

### Komplett zurücksetzen (VORSICHT!)
```bash
docker-compose down
docker rm -f $(docker ps -aq)
docker rmi -f $(docker images -q)
cd ~/gewoBot
docker-compose build
docker-compose up -d
```

### VPS neu starten
```bash
sudo reboot
```

Nach Neustart:
```bash
ssh root@157.173.99.84
cd ~/gewoBot
docker-compose up -d
```

---

## 🎯 TÄGLICHE ROUTINE

### Morgens:
```bash
# Status prüfen
docker-compose ps

# Logs der letzten Nacht anschauen
docker-compose logs --tail=100 gewobag-bot

# Datenbank prüfen
docker-compose exec gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen WHERE applied = 1;"
```

### Bei Problemen:
```bash
# Logs prüfen
docker-compose logs --tail=50 gewobag-bot

# Neu starten
docker-compose restart gewobag-bot gewobag-scheduler
```

---

## 📞 SUPPORT

### Logs zum Debuggen exportieren
```bash
docker-compose logs > ~/bot-logs-$(date +%Y%m%d).txt
```

### System-Info sammeln
```bash
echo "=== Docker Version ===" > ~/debug-info.txt
docker --version >> ~/debug-info.txt
echo "" >> ~/debug-info.txt

echo "=== Container Status ===" >> ~/debug-info.txt
docker-compose ps >> ~/debug-info.txt
echo "" >> ~/debug-info.txt

echo "=== Disk Usage ===" >> ~/debug-info.txt
df -h >> ~/debug-info.txt
```

---

## 📚 ZUSÄTZLICHE RESSOURCEN

**Web-Frontend:** http://157.173.99.84:5000
**Gewobag Webseite:** https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/

**Wichtige Dateien:**
- Konfiguration: `~/gewoBot/user_data.json`, `~/gewoBot/filter_config.json`
- Datenbank: `~/gewoBot/gewobag_wohnungen.db`
- Logs: `~/gewoBot/logs/`
- Docker Config: `~/gewoBot/docker-compose.yml`

---

## 🎉 VIEL ERFOLG!

Dein Bot läuft jetzt automatisch alle 15 Minuten und sucht nach deiner Traumwohnung! 🏠✨
