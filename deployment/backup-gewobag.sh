#!/bin/bash
# Gewobag Bot Backup-Script
# Erstellt Backups von Datenbank und Logs

# Konfiguration
BACKUP_DIR="/home/botuser/backups"
PROJECT_DIR="/home/botuser/gewobag-bot"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backup-Verzeichnis erstellen
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}🔄 Gewobag Bot Backup gestartet - $DATE${NC}"

# 1. Datenbank sichern
echo -e "${YELLOW}📊 Sichere Datenbank...${NC}"
if [ -f "$PROJECT_DIR/gewobag_wohnungen.db" ]; then
    cp "$PROJECT_DIR/gewobag_wohnungen.db" "$BACKUP_DIR/gewobag_wohnungen_$DATE.db"
    echo -e "${GREEN}✅ Datenbank gesichert: gewobag_wohnungen_$DATE.db${NC}"
else
    echo -e "${RED}❌ Datenbank nicht gefunden!${NC}"
fi

# 2. Logs sichern
echo -e "${YELLOW}📋 Sichere Logs...${NC}"
if [ -d "$PROJECT_DIR/logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$PROJECT_DIR" logs/
    echo -e "${GREEN}✅ Logs gesichert: logs_$DATE.tar.gz${NC}"
else
    echo -e "${RED}❌ Logs-Verzeichnis nicht gefunden!${NC}"
fi

# 3. Konfigurationsdateien sichern
echo -e "${YELLOW}⚙️  Sichere Konfiguration...${NC}"
if [ -f "$PROJECT_DIR/user_data.json" ] && [ -f "$PROJECT_DIR/filter_config.json" ]; then
    tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
        -C "$PROJECT_DIR" \
        user_data.json \
        filter_config.json \
        bezirke_verfuegbar.json 2>/dev/null
    echo -e "${GREEN}✅ Konfiguration gesichert: config_$DATE.tar.gz${NC}"
else
    echo -e "${RED}❌ Konfigurationsdateien nicht gefunden!${NC}"
fi

# 4. Alte Backups löschen (älter als RETENTION_DAYS)
echo -e "${YELLOW}🗑️  Lösche alte Backups (älter als $RETENTION_DAYS Tage)...${NC}"
find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✅ Alte Backups gelöscht${NC}"

# 5. Backup-Größe anzeigen
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo -e "${GREEN}📦 Backup-Verzeichnis Größe: $BACKUP_SIZE${NC}"

# 6. Anzahl der Backups anzeigen
DB_COUNT=$(find "$BACKUP_DIR" -name "*.db" | wc -l)
LOG_COUNT=$(find "$BACKUP_DIR" -name "logs_*.tar.gz" | wc -l)
CONFIG_COUNT=$(find "$BACKUP_DIR" -name "config_*.tar.gz" | wc -l)

echo -e "${GREEN}📊 Backup-Statistik:${NC}"
echo -e "   Datenbank-Backups: $DB_COUNT"
echo -e "   Log-Backups: $LOG_COUNT"
echo -e "   Config-Backups: $CONFIG_COUNT"

echo -e "${GREEN}✅ Backup abgeschlossen - $DATE${NC}"

# Optional: Backup zu Remote-Server senden (auskommentiert)
# echo -e "${YELLOW}☁️  Sende Backup zu Remote-Server...${NC}"
# rsync -avz "$BACKUP_DIR/" user@remote-server:/path/to/backups/
# echo -e "${GREEN}✅ Remote-Backup abgeschlossen${NC}"

exit 0
