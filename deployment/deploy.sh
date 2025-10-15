#!/bin/bash
# Gewobag Bot Deployment-Script für VPS
# Automatisiert das Deployment auf dem VPS

# Konfiguration
PROJECT_DIR="/home/botuser/gewobag-bot"
LOG_FILE="$PROJECT_DIR/logs/deploy.log"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging-Funktion
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║            🚀 GEWOBAG BOT DEPLOYMENT v2.2 🚀                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Verzeichnis prüfen
log "📂 Prüfe Projekt-Verzeichnis..."
if [ ! -d "$PROJECT_DIR" ]; then
    error "Projekt-Verzeichnis nicht gefunden: $PROJECT_DIR"
    exit 1
fi
cd "$PROJECT_DIR" || exit 1

# 2. Git Pull (falls Git-Repo)
if [ -d ".git" ]; then
    log "🔄 Git Pull..."
    git pull
else
    warning "Kein Git-Repository gefunden (überspringe)"
fi

# 3. Docker Images aktualisieren
log "🐳 Baue Docker Images..."
docker-compose build --no-cache

# 4. Alte Container stoppen
log "🛑 Stoppe alte Container..."
docker-compose down

# 5. Alte Images aufräumen
log "🗑️  Räume alte Docker Images auf..."
docker image prune -f

# 6. Container starten
log "🚀 Starte Container..."
docker-compose up -d gewobag-web gewobag-scheduler

# 7. Warte auf Startup
log "⏳ Warte auf Container-Startup..."
sleep 10

# 8. Health-Check
log "🏥 Führe Health-Check durch..."
if docker-compose ps | grep -q "gewobag-web.*Up"; then
    log "✅ Web-Frontend läuft"
else
    error "Web-Frontend läuft nicht!"
fi

if docker-compose ps | grep -q "gewobag-scheduler.*Up"; then
    log "✅ Scheduler läuft"
else
    error "Scheduler läuft nicht!"
fi

# 9. Logs anzeigen
log "📋 Letzte Logs:"
docker-compose logs --tail=20

# 10. Deployment-Informationen
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✅ DEPLOYMENT ERFOLGREICH ✅                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}📊 Container-Status:${NC}"
docker-compose ps

echo -e "\n${BLUE}🌐 Web-Frontend:${NC}"
echo -e "   Lokal:  http://localhost:5000"
echo -e "   Public: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_VPS_IP')"

echo -e "\n${BLUE}📋 Logs anzeigen:${NC}"
echo -e "   docker-compose logs -f gewobag-web"
echo -e "   docker-compose logs -f gewobag-scheduler"
echo -e "   docker-compose logs -f gewobag-bot"

echo -e "\n${BLUE}🔧 Verwaltung:${NC}"
echo -e "   docker-compose ps              # Status anzeigen"
echo -e "   docker-compose restart         # Neustart"
echo -e "   docker-compose down            # Stoppen"
echo -e "   docker-compose up -d           # Starten"

echo -e "\n${GREEN}🎉 Deployment abgeschlossen!${NC}\n"

exit 0
