# 📦 Deployment-Dateien für Gewobag Bot v2.2

Dieses Verzeichnis enthält alle notwendigen Konfigurationsdateien für das Production-Deployment auf einem VPS.

## 📁 Dateien-Übersicht

### 1. **gewobag-bot.service**
Systemd-Service-Datei für die Bot-Ausführung.

**Installation:**
```bash
sudo cp gewobag-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gewobag-bot.service
```

**Verwendung:**
```bash
# Manuell starten
sudo systemctl start gewobag-bot.service

# Status prüfen
sudo systemctl status gewobag-bot.service

# Logs anzeigen
sudo journalctl -u gewobag-bot.service -f
```

---

### 2. **gewobag-bot.timer**
Systemd-Timer für automatische Ausführung alle 15 Minuten.

**Installation:**
```bash
sudo cp gewobag-bot.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gewobag-bot.timer
sudo systemctl start gewobag-bot.timer
```

**Verwendung:**
```bash
# Timer-Status prüfen
sudo systemctl status gewobag-bot.timer

# Nächste Ausführungen anzeigen
systemctl list-timers gewobag-bot.timer

# Timer stoppen
sudo systemctl stop gewobag-bot.timer
```

**Zeitplan anpassen:**
Bearbeite die Datei und ändere `OnCalendar`:
```ini
# Alle 30 Minuten
OnCalendar=*:0/30

# Stündlich
OnCalendar=hourly

# Alle 6 Stunden
OnCalendar=0/6:00

# Mo-Fr, 9-18 Uhr, alle 15 Minuten
OnCalendar=Mon..Fri 09..18:0/15
```

---

### 3. **nginx-gewobag-bot.conf**
Nginx-Reverse-Proxy-Konfiguration für Web-Frontend.

**Installation:**
```bash
# Konfiguration kopieren
sudo cp nginx-gewobag-bot.conf /etc/nginx/sites-available/gewobag-bot

# Domain anpassen
sudo nano /etc/nginx/sites-available/gewobag-bot
# → Ändere "YOUR_DOMAIN.COM" zu deiner Domain oder VPS-IP

# Aktivieren
sudo ln -s /etc/nginx/sites-available/gewobag-bot /etc/nginx/sites-enabled/

# Nginx-Konfiguration testen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx
```

**SSL mit Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d YOUR_DOMAIN.COM
```

---

### 4. **backup-gewobag.sh**
Backup-Script für Datenbank, Logs und Konfiguration.

**Installation:**
```bash
# Ausführbar machen
chmod +x backup-gewobag.sh

# Manuell ausführen
./backup-gewobag.sh
```

**Automatisches Backup mit Cron:**
```bash
crontab -e
```

Hinzufügen:
```cron
# Tägliches Backup um 3 Uhr morgens
0 3 * * * /home/botuser/gewobag-bot/deployment/backup-gewobag.sh >> /home/botuser/backups/backup.log 2>&1
```

**Backup-Verzeichnis:**
- Standard: `/home/botuser/backups/`
- Aufbewahrung: 7 Tage (konfigurierbar)

---

### 5. **deploy.sh**
Automatisches Deployment-Script für VPS.

**Installation:**
```bash
# Ausführbar machen
chmod +x deploy.sh

# Ausführen
./deploy.sh
```

**Was macht das Script:**
1. Git Pull (falls Repository)
2. Docker Images neu bauen
3. Alte Container stoppen
4. Neue Container starten
5. Health-Check durchführen
6. Logs anzeigen

**Verwendung:**
```bash
# Manuelles Deployment
cd /home/botuser/gewobag-bot/deployment
./deploy.sh

# Automatisches Deployment (bei Git Push)
# → GitHub Actions oder Webhook verwenden
```

---

## 🚀 Schnellstart-Anleitung

### Option 1: Docker mit Ofelia Scheduler (empfohlen)

```bash
# 1. Web-Frontend + Scheduler starten
docker-compose up -d gewobag-web gewobag-scheduler

# 2. Status prüfen
docker-compose ps

# 3. Logs anzeigen
docker-compose logs -f gewobag-scheduler
```

**Zeitplan anpassen:**
Bearbeite `docker-compose.yml`:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 15m"
```

---

### Option 2: Systemd Timer

```bash
# 1. Service-Dateien installieren
sudo cp gewobag-bot.service /etc/systemd/system/
sudo cp gewobag-bot.timer /etc/systemd/system/

# 2. Systemd neu laden
sudo systemctl daemon-reload

# 3. Timer aktivieren und starten
sudo systemctl enable gewobag-bot.timer
sudo systemctl start gewobag-bot.timer

# 4. Web-Frontend starten
docker-compose up -d gewobag-web

# 5. Status prüfen
sudo systemctl status gewobag-bot.timer
systemctl list-timers gewobag-bot.timer
```

---

### Option 3: Cron

```bash
# 1. Crontab bearbeiten
crontab -e

# 2. Zeile hinzufügen
*/15 * * * * cd /home/botuser/gewobag-bot && /usr/bin/docker-compose run --rm gewobag-bot python main.py --full >> /home/botuser/gewobag-bot/logs/cron.log 2>&1

# 3. Web-Frontend starten
docker-compose up -d gewobag-web

# 4. Logs prüfen
tail -f /home/botuser/gewobag-bot/logs/cron.log
```

---

## 🌐 Web-Frontend einrichten

### 1. Nginx installieren und konfigurieren

```bash
# Nginx installieren
sudo apt install nginx -y

# Konfiguration kopieren
sudo cp deployment/nginx-gewobag-bot.conf /etc/nginx/sites-available/gewobag-bot

# Domain anpassen
sudo nano /etc/nginx/sites-available/gewobag-bot
# → Ändere "YOUR_DOMAIN.COM"

# Aktivieren
sudo ln -s /etc/nginx/sites-available/gewobag-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL mit Let's Encrypt

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx -y

# SSL-Zertifikat erstellen
sudo certbot --nginx -d YOUR_DOMAIN.COM

# Automatische Erneuerung prüfen
sudo certbot renew --dry-run
```

### 3. Zugriff testen

```bash
# HTTP
curl http://YOUR_VPS_IP

# HTTPS (nach SSL-Installation)
curl https://YOUR_DOMAIN.COM
```

---

## 📊 Monitoring

### Container-Status

```bash
# Alle Container
docker-compose ps

# Ressourcen
docker stats

# Logs
docker-compose logs -f gewobag-web
docker-compose logs -f gewobag-scheduler
docker-compose logs -f gewobag-bot
```

### Systemd-Status (falls Timer verwendet)

```bash
# Service-Status
sudo systemctl status gewobag-bot.service

# Timer-Status
sudo systemctl status gewobag-bot.timer

# Nächste Ausführungen
systemctl list-timers gewobag-bot.timer

# Logs
sudo journalctl -u gewobag-bot.service -f
```

### Nginx-Logs

```bash
# Access-Logs
tail -f /var/log/nginx/gewobag-bot-access.log

# Error-Logs
tail -f /var/log/nginx/gewobag-bot-error.log
```

### Datenbank-Statistiken

```bash
docker-compose run --rm gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) as gesamt FROM wohnungen;"
docker-compose run --rm gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) as beworben FROM wohnungen WHERE applied = 1;"
```

---

## 🔧 Wartung

### Updates durchführen

```bash
# Mit Deploy-Script (empfohlen)
cd /home/botuser/gewobag-bot/deployment
./deploy.sh

# Manuell
cd /home/botuser/gewobag-bot
git pull
docker-compose build
docker-compose up -d
```

### Backups erstellen

```bash
# Manuell
./deployment/backup-gewobag.sh

# Automatisch (Cron)
crontab -e
# → 0 3 * * * /home/botuser/gewobag-bot/deployment/backup-gewobag.sh
```

### Docker aufräumen

```bash
# Alte Images löschen
docker image prune -a

# Alte Container löschen
docker container prune

# Alles aufräumen
docker system prune -a --volumes
```

### Logs rotieren

```bash
# Alte Logs löschen
cd /home/botuser/gewobag-bot/logs
rm *.log

# Docker-Logs beschränken (bereits konfiguriert in docker-compose.yml)
# max-size: 10m
# max-file: 3
```

---

## 🛠️ Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker-compose logs gewobag-web

# Neu bauen
docker-compose build --no-cache
docker-compose up -d
```

### Port 5000 belegt

```bash
# Port prüfen
sudo netstat -tlnp | grep :5000

# Prozess beenden
sudo kill -9 <PID>

# Oder anderen Port in docker-compose.yml verwenden
ports:
  - "8080:5000"
```

### Nginx 502 Bad Gateway

```bash
# Web-Service prüfen
docker-compose ps gewobag-web

# Neu starten
docker-compose restart gewobag-web

# Logs prüfen
docker-compose logs gewobag-web
tail -f /var/log/nginx/gewobag-bot-error.log
```

### Systemd Timer läuft nicht

```bash
# Status prüfen
sudo systemctl status gewobag-bot.timer

# Neu starten
sudo systemctl restart gewobag-bot.timer

# Logs prüfen
sudo journalctl -u gewobag-bot.timer -f
```

---

## 📝 Konfiguration anpassen

### Zeitplan ändern (Docker)

Bearbeite `docker-compose.yml`:
```yaml
ofelia.job-exec.gewobag-bot-job.schedule: "@every 30m"
```

Neu starten:
```bash
docker-compose restart gewobag-scheduler
```

### Zeitplan ändern (Systemd)

Bearbeite `/etc/systemd/system/gewobag-bot.timer`:
```ini
OnCalendar=*:0/30
```

Neu laden:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gewobag-bot.timer
```

### Zeitplan ändern (Cron)

```bash
crontab -e
# → Ändere */15 zu */30 für 30 Minuten
```

---

## 📚 Weitere Informationen

Vollständige Deployment-Anleitung: `VPS_DEPLOYMENT_GUIDE.md`

Bei Problemen:
1. Logs prüfen (`docker-compose logs -f`)
2. Container-Status prüfen (`docker-compose ps`)
3. Issue auf GitHub erstellen

**Viel Erfolg! 🏠🎉**
