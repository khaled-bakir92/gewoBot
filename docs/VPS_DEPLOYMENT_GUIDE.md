# 🚀 VPS Deployment Guide - Gewobag Bot v2.2

Vollständige Anleitung zum Deployment des Gewobag Bots auf einem VPS mit automatischer Ausführung alle 15 Minuten.

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [VPS Vorbereitung](#vps-vorbereitung)
3. [Projekt-Upload zum VPS](#projekt-upload-zum-vps)
4. [Docker Installation](#docker-installation)
5. [Projekt-Setup auf VPS](#projekt-setup-auf-vps)
6. [Automatische Ausführung (3 Optionen)](#automatische-ausführung)
   - [Option 1: Docker mit ofagent (empfohlen)](#option-1-docker-mit-ofagent-empfohlen)
   - [Option 2: Systemd Timer](#option-2-systemd-timer)
   - [Option 3: Cron](#option-3-cron)
7. [Web-Frontend mit Nginx](#web-frontend-mit-nginx)
8. [SSL/HTTPS mit Let's Encrypt](#ssl-https-mit-lets-encrypt)
9. [Monitoring und Logs](#monitoring-und-logs)
10. [Troubleshooting](#troubleshooting)

---

## 📦 Voraussetzungen

### Lokaler Rechner
- Git installiert
- SSH-Zugang zum VPS

### VPS-Anforderungen
- **Betriebssystem**: Ubuntu 20.04/22.04 oder Debian 11/12
- **RAM**: Mindestens 2GB (empfohlen: 4GB)
- **CPU**: Mindestens 2 vCPUs
- **Speicher**: Mindestens 20GB
- **Netzwerk**: Öffentliche IP-Adresse
- **Ports**: 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Empfohlene VPS-Anbieter
- Hetzner Cloud (günstig, deutsch)
- DigitalOcean
- Linode
- Vultr
- Contabo

---

## 🖥️ VPS Vorbereitung

### 1. SSH-Verbindung zum VPS

```bash
# Mit Password
ssh root@YOUR_VPS_IP

# Mit SSH-Key (empfohlen)
ssh -i ~/.ssh/id_rsa root@YOUR_VPS_IP
```

### 2. System aktualisieren

```bash
apt update && apt upgrade -y
```

### 3. Firewall konfigurieren (UFW)

```bash
# UFW installieren
apt install ufw -y

# Standard-Regeln
ufw default deny incoming
ufw default allow outgoing

# SSH erlauben (WICHTIG! Sonst sperrst du dich aus)
ufw allow 22/tcp

# HTTP und HTTPS erlauben
ufw allow 80/tcp
ufw allow 443/tcp

# Firewall aktivieren
ufw enable

# Status prüfen
ufw status verbose
```

### 4. Non-Root User erstellen (empfohlen)

```bash
# User erstellen
adduser botuser

# Sudo-Rechte geben
usermod -aG sudo botuser

# SSH-Key für neuen User (optional)
mkdir -p /home/botuser/.ssh
cp ~/.ssh/authorized_keys /home/botuser/.ssh/
chown -R botuser:botuser /home/botuser/.ssh
chmod 700 /home/botuser/.ssh
chmod 600 /home/botuser/.ssh/authorized_keys

# Zu neuem User wechseln
su - botuser
```

---

## 📤 Projekt-Upload zum VPS

### Option 1: Mit Git (empfohlen)

```bash
# Auf VPS
cd ~
git clone https://github.com/YOUR_USERNAME/gewobag-bot.git
cd gewobag-bot

# Falls privates Repository
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/gewobag-bot.git
```

### Option 2: Mit SCP (von lokalem Rechner)

```bash
# Gesamtes Projekt hochladen
cd ~/Desktop
scp -r "bot new" root@YOUR_VPS_IP:/home/botuser/gewobag-bot

# Einzelne Dateien
scp user_data.json filter_config.json root@YOUR_VPS_IP:/home/botuser/gewobag-bot/
```

### Option 3: Mit rsync (von lokalem Rechner)

```bash
# Effizient, nur geänderte Dateien
rsync -avz --exclude 'venv' --exclude '*.db' --exclude '*.log' \
  ~/Desktop/bot\ new/ root@YOUR_VPS_IP:/home/botuser/gewobag-bot/
```

---

## 🐳 Docker Installation

### Docker installieren

```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# User zu Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neuanmeldung erforderlich (oder Server neustarten)
newgrp docker

# Docker-Compose installieren
sudo apt install docker-compose -y

# Installation prüfen
docker --version
docker-compose --version
```

### Docker Auto-Start aktivieren

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## ⚙️ Projekt-Setup auf VPS

### 1. Verzeichnis vorbereiten

```bash
cd /home/botuser/gewobag-bot

# Logs-Verzeichnis erstellen
mkdir -p logs

# Berechtigungen setzen
sudo chown -R $USER:$USER .
```

### 2. Konfigurationsdateien anpassen

```bash
# user_data.json bearbeiten
nano user_data.json
# → Deine persönlichen Daten eintragen

# filter_config.json bearbeiten
nano filter_config.json
# → Suchfilter anpassen

# Speichern: Ctrl+O, Enter, Ctrl+X
```

### 3. Dokumente hochladen (falls nicht schon geschehen)

```bash
# Dokumente-Verzeichnis erstellen
mkdir -p documents

# Von lokalem Rechner hochladen
scp ~/path/to/personalausweis.pdf root@YOUR_VPS_IP:/home/botuser/gewobag-bot/documents/
scp ~/path/to/gehaltsnachweis.pdf root@YOUR_VPS_IP:/home/botuser/gewobag-bot/documents/
```

### 4. Docker Images bauen

```bash
cd /home/botuser/gewobag-bot
docker-compose build
```

### 5. Erste Test-Ausführung

```bash
# Setup durchführen
docker-compose run --rm gewobag-bot python main.py --setup

# Test-Suche (ohne Bewerbung)
docker-compose run --rm gewobag-bot python main.py --scrape

# Test-Bewerbung (nur 1)
docker-compose run --rm gewobag-bot python main.py --apply --max 1
```

---

## ⏰ Automatische Ausführung

### Option 1: Docker mit ofagent (empfohlen)

**Vorteil**: Einfach, alles in Docker, kein System-Cron/Systemd nötig

#### Schritt 1: ofagent-Service zu docker-compose.yml hinzufügen

```bash
nano docker-compose.yml
```

Füge diesen Service hinzu:

```yaml
services:
  # ... (bestehende Services gewobag-bot und gewobag-web)

  # ===== Scheduler Service (läuft alle 15 Minuten) =====
  gewobag-scheduler:
    image: mcuadros/ofelia:latest
    container_name: gewobag-scheduler
    restart: unless-stopped
    depends_on:
      - gewobag-bot
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      # Job-Definition: Alle 15 Minuten ausführen
      ofelia.job-exec.gewobag-bot-job.schedule: "@every 15m"
      ofelia.job-exec.gewobag-bot-job.container: "gewobag-bot"
      ofelia.job-exec.gewobag-bot-job.command: "python main.py --full"
      ofelia.job-exec.gewobag-bot-job.no-overlap: "true"
```

#### Schritt 2: Scheduler starten

```bash
docker-compose up -d gewobag-scheduler
```

#### Schritt 3: Logs prüfen

```bash
docker-compose logs -f gewobag-scheduler
```

**Alternative Zeitpläne:**
```yaml
# Alle 30 Minuten
ofelia.job-exec.gewobag-bot-job.schedule: "@every 30m"

# Stündlich
ofelia.job-exec.gewobag-bot-job.schedule: "@hourly"

# Alle 6 Stunden
ofelia.job-exec.gewobag-bot-job.schedule: "@every 6h"

# Cron-Syntax (z.B. Mo-Fr, 9-18 Uhr, alle 15 Min)
ofelia.job-exec.gewobag-bot-job.schedule: "*/15 9-18 * * 1-5"
```

---

### Option 2: Systemd Timer

**Vorteil**: Nativ in Linux integriert, sehr zuverlässig

#### Schritt 1: Service-Datei erstellen

```bash
sudo nano /etc/systemd/system/gewobag-bot.service
```

Inhalt:

```ini
[Unit]
Description=Gewobag Bot - Apartment Search and Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=botuser
WorkingDirectory=/home/botuser/gewobag-bot
ExecStart=/usr/bin/docker-compose run --rm gewobag-bot python main.py --full
StandardOutput=append:/home/botuser/gewobag-bot/logs/systemd.log
StandardError=append:/home/botuser/gewobag-bot/logs/systemd-error.log
TimeoutStartSec=600
Restart=no

[Install]
WantedBy=multi-user.target
```

#### Schritt 2: Timer-Datei erstellen

```bash
sudo nano /etc/systemd/system/gewobag-bot.timer
```

Inhalt:

```ini
[Unit]
Description=Gewobag Bot Timer - Run every 15 minutes
Requires=gewobag-bot.service

[Timer]
# Alle 15 Minuten
OnCalendar=*:0/15
# Zufällige Verzögerung (0-60 Sekunden)
RandomizedDelaySec=60
# Nach System-Start warten
OnBootSec=5min
# Falls ein Lauf verpasst wurde, nachholen
Persistent=true

[Install]
WantedBy=timers.target
```

#### Schritt 3: Timer aktivieren

```bash
# Systemd neu laden
sudo systemctl daemon-reload

# Timer aktivieren (startet automatisch bei Boot)
sudo systemctl enable gewobag-bot.timer

# Timer starten
sudo systemctl start gewobag-bot.timer

# Status prüfen
sudo systemctl status gewobag-bot.timer

# Nächste Ausführung anzeigen
systemctl list-timers gewobag-bot.timer
```

#### Schritt 4: Logs prüfen

```bash
# Systemd-Logs
sudo journalctl -u gewobag-bot.service -f

# Bot-Logs
tail -f /home/botuser/gewobag-bot/logs/systemd.log
```

#### Schritt 5: Timer verwalten

```bash
# Timer stoppen
sudo systemctl stop gewobag-bot.timer

# Timer deaktivieren (kein Auto-Start)
sudo systemctl disable gewobag-bot.timer

# Service manuell ausführen
sudo systemctl start gewobag-bot.service
```

---

### Option 3: Cron

**Vorteil**: Einfach, überall verfügbar

#### Schritt 1: Cron-Job erstellen

```bash
crontab -e
```

Füge diese Zeile hinzu:

```cron
# Alle 15 Minuten
*/15 * * * * cd /home/botuser/gewobag-bot && /usr/bin/docker-compose run --rm gewobag-bot python main.py --full >> /home/botuser/gewobag-bot/logs/cron.log 2>&1

# Alternative Zeitpläne:
# Alle 30 Minuten
# */30 * * * * ...

# Stündlich (zur vollen Stunde)
# 0 * * * * ...

# Alle 6 Stunden
# 0 */6 * * * ...

# Mo-Fr, 9-18 Uhr, alle 15 Minuten
# */15 9-18 * * 1-5 ...
```

#### Schritt 2: Cron-Service aktivieren

```bash
sudo systemctl enable cron
sudo systemctl start cron
```

#### Schritt 3: Logs prüfen

```bash
tail -f /home/botuser/gewobag-bot/logs/cron.log
```

#### Schritt 4: Cron-Jobs anzeigen

```bash
crontab -l
```

---

## 🌐 Web-Frontend mit Nginx

### 1. Nginx installieren

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2. Nginx-Konfiguration erstellen

```bash
sudo nano /etc/nginx/sites-available/gewobag-bot
```

Inhalt:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.COM;  # Oder deine VPS-IP

    # Max Upload-Größe für Dokumente
    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts (wichtig für lange Requests)
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }

    # Logs
    access_log /var/log/nginx/gewobag-bot-access.log;
    error_log /var/log/nginx/gewobag-bot-error.log;
}
```

### 3. Nginx-Konfiguration aktivieren

```bash
# Symlink erstellen
sudo ln -s /etc/nginx/sites-available/gewobag-bot /etc/nginx/sites-enabled/

# Standard-Site deaktivieren (optional)
sudo rm /etc/nginx/sites-enabled/default

# Konfiguration testen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx
```

### 4. Web-Frontend starten

```bash
cd /home/botuser/gewobag-bot
docker-compose up -d gewobag-web
```

### 5. Zugriff testen

```bash
# Im Browser öffnen
http://YOUR_VPS_IP
# oder
http://YOUR_DOMAIN.COM
```

---

## 🔒 SSL/HTTPS mit Let's Encrypt

### 1. Certbot installieren

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. SSL-Zertifikat erstellen

```bash
# Automatische Konfiguration mit Nginx
sudo certbot --nginx -d YOUR_DOMAIN.COM

# Fragen beantworten:
# - E-Mail-Adresse angeben
# - Bedingungen akzeptieren
# - Redirect HTTP → HTTPS? → Ja (2)
```

### 3. Auto-Renewal aktivieren

```bash
# Certbot erstellt automatisch einen Cron-Job
# Manuell testen:
sudo certbot renew --dry-run

# Certbot Timer prüfen
sudo systemctl status certbot.timer
```

### 4. Firewall anpassen

```bash
sudo ufw allow 443/tcp
```

### 5. Zugriff über HTTPS

```bash
# Im Browser öffnen
https://YOUR_DOMAIN.COM
```

---

## 📊 Monitoring und Logs

### Docker-Container überwachen

```bash
# Alle Container anzeigen
docker-compose ps

# Logs anzeigen (alle Services)
docker-compose logs -f

# Logs eines einzelnen Service
docker-compose logs -f gewobag-bot
docker-compose logs -f gewobag-web
docker-compose logs -f gewobag-scheduler

# Container-Ressourcen anzeigen
docker stats
```

### Bot-Logs

```bash
# Bot-Logs
tail -f /home/botuser/gewobag-bot/logs/gewobag-main.log
tail -f /home/botuser/gewobag-bot/logs/application-bot.log
tail -f /home/botuser/gewobag-bot/logs/gewobag-bot.log

# Cron-Logs (falls Cron verwendet)
tail -f /home/botuser/gewobag-bot/logs/cron.log

# Systemd-Logs (falls Systemd Timer verwendet)
tail -f /home/botuser/gewobag-bot/logs/systemd.log
sudo journalctl -u gewobag-bot.service -f
```

### Nginx-Logs

```bash
tail -f /var/log/nginx/gewobag-bot-access.log
tail -f /var/log/nginx/gewobag-bot-error.log
```

### Datenbank prüfen

```bash
cd /home/botuser/gewobag-bot
docker-compose run --rm gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen;"
docker-compose run --rm gewobag-bot sqlite3 gewobag_wohnungen.db "SELECT COUNT(*) FROM wohnungen WHERE applied = 1;"
```

---

## 🛠️ Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker-compose logs gewobag-bot

# Container neu bauen
docker-compose build --no-cache gewobag-bot
docker-compose up -d gewobag-bot
```

### Port 5000 bereits belegt

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
# Prüfen, ob Web-Service läuft
docker-compose ps gewobag-web

# Web-Service neu starten
docker-compose restart gewobag-web

# Nginx-Logs prüfen
tail -f /var/log/nginx/gewobag-bot-error.log
```

### Speicherplatz voll

```bash
# Speicherplatz prüfen
df -h

# Docker aufräumen
docker system prune -a --volumes

# Alte Logs löschen
cd /home/botuser/gewobag-bot/logs
rm *.log
```

### Systemd Timer läuft nicht

```bash
# Timer-Status prüfen
sudo systemctl status gewobag-bot.timer

# Timer neu starten
sudo systemctl restart gewobag-bot.timer

# Logs prüfen
sudo journalctl -u gewobag-bot.timer -f
```

### Cron läuft nicht

```bash
# Cron-Service prüfen
sudo systemctl status cron

# Cron-Logs prüfen
grep CRON /var/log/syslog

# Cron-Jobs anzeigen
crontab -l
```

---

## 🔧 Erweiterte Konfiguration

### Umgebungsvariablen setzen

```bash
nano .env
```

Inhalt:

```env
TZ=Europe/Berlin
PYTHONUNBUFFERED=1
FLASK_ENV=production
```

In docker-compose.yml einbinden:

```yaml
services:
  gewobag-bot:
    env_file:
      - .env
```

### Backup-Strategie

```bash
# Backup-Script erstellen
nano /home/botuser/backup-gewobag.sh
```

Inhalt:

```bash
#!/bin/bash
BACKUP_DIR="/home/botuser/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Datenbank sichern
cp /home/botuser/gewobag-bot/gewobag_wohnungen.db $BACKUP_DIR/gewobag_wohnungen_$DATE.db

# Logs sichern
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /home/botuser/gewobag-bot/logs/

# Alte Backups löschen (älter als 7 Tage)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup abgeschlossen: $DATE"
```

Ausführbar machen:

```bash
chmod +x /home/botuser/backup-gewobag.sh
```

Cron-Job für tägliches Backup:

```bash
crontab -e
```

Hinzufügen:

```cron
# Tägliches Backup um 3 Uhr morgens
0 3 * * * /home/botuser/backup-gewobag.sh >> /home/botuser/backups/backup.log 2>&1
```

---

## 📝 Checkliste für Production

- [ ] VPS mit SSH-Key gesichert
- [ ] Firewall (UFW) konfiguriert
- [ ] Docker und Docker-Compose installiert
- [ ] Projekt auf VPS hochgeladen
- [ ] user_data.json und filter_config.json angepasst
- [ ] Dokumente hochgeladen
- [ ] Docker Images gebaut
- [ ] Test-Ausführung erfolgreich
- [ ] Scheduler konfiguriert (Docker/Systemd/Cron)
- [ ] Web-Frontend mit Nginx läuft
- [ ] SSL-Zertifikat installiert (Let's Encrypt)
- [ ] Logs überwacht
- [ ] Backup-Strategie implementiert

---

## 🎉 Fertig!

Dein Gewobag Bot läuft jetzt auf deinem VPS und sucht automatisch alle 15 Minuten nach Wohnungen!

**Zugriff:**
- Web-Frontend: `https://YOUR_DOMAIN.COM`
- Logs: `docker-compose logs -f`

**Support:**
- Bei Problemen: Logs prüfen
- Issues: GitHub Issues erstellen

**Viel Erfolg bei der Wohnungssuche! 🏠🎉**
