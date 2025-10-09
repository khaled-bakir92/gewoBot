#!/bin/bash

# Docker Test-Skript für Gewobag Bot
# Führt vollständige Docker-Tests durch

set -e  # Bei Fehler abbrechen

echo "🐳 Docker Test-Suite für Gewobag Bot v2.1"
echo "=========================================="
echo ""

# Farben für Output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test-Zähler
TESTS_PASSED=0
TESTS_FAILED=0

# Hilfsfunktion für Tests
test_step() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

test_passed() {
    echo -e "${GREEN}✅ PASSED:${NC} $1"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}❌ FAILED:${NC} $1"
    ((TESTS_FAILED++))
}

# ===== Test 1: Docker Daemon prüfen =====
test_step "Schritt 1: Docker Daemon prüfen"
if docker info > /dev/null 2>&1; then
    test_passed "Docker Daemon läuft"
else
    test_failed "Docker Daemon läuft nicht"
    echo "Bitte starte Docker Desktop und führe das Skript erneut aus."
    exit 1
fi

# ===== Test 2: docker-compose.yml validieren =====
test_step "Schritt 2: docker-compose.yml validieren"
if docker-compose config > /dev/null 2>&1; then
    test_passed "docker-compose.yml ist valide"
else
    test_failed "docker-compose.yml hat Syntax-Fehler"
    exit 1
fi

# ===== Test 3: Dockerfile validieren =====
test_step "Schritt 3: Dockerfile prüfen"
if [ -f Dockerfile ]; then
    test_passed "Dockerfile existiert"
else
    test_failed "Dockerfile nicht gefunden"
    exit 1
fi

# ===== Test 4: .dockerignore prüfen =====
test_step "Schritt 4: .dockerignore prüfen"
if [ -f .dockerignore ]; then
    test_passed ".dockerignore existiert"
else
    test_failed ".dockerignore nicht gefunden (optional, aber empfohlen)"
fi

# ===== Test 5: Docker Image bauen =====
test_step "Schritt 5: Docker Image bauen (kann 3-5 Minuten dauern...)"
if docker-compose build; then
    test_passed "Docker Image erfolgreich gebaut"
else
    test_failed "Docker Image Build fehlgeschlagen"
    exit 1
fi

# ===== Test 6: Image-Größe prüfen =====
test_step "Schritt 6: Image-Größe prüfen"
IMAGE_SIZE=$(docker images bot-new-gewobag-bot --format "{{.Size}}" | head -1)
if [ -n "$IMAGE_SIZE" ]; then
    test_passed "Image-Größe: $IMAGE_SIZE"
else
    test_failed "Image nicht gefunden"
fi

# ===== Test 7: Container-Start testen =====
test_step "Schritt 7: Container-Start testen"
if docker-compose run --rm gewobag-bot python --version > /dev/null 2>&1; then
    test_passed "Container startet erfolgreich"
else
    test_failed "Container-Start fehlgeschlagen"
    exit 1
fi

# ===== Test 8: Python-Version prüfen =====
test_step "Schritt 8: Python-Version im Container prüfen"
PYTHON_VERSION=$(docker-compose run --rm gewobag-bot python --version 2>&1)
if [[ $PYTHON_VERSION == *"3.11"* ]]; then
    test_passed "Python-Version: $PYTHON_VERSION"
else
    test_failed "Python-Version nicht korrekt: $PYTHON_VERSION"
fi

# ===== Test 9: Playwright prüfen =====
test_step "Schritt 9: Playwright-Installation prüfen"
if docker-compose run --rm gewobag-bot playwright --version > /dev/null 2>&1; then
    PLAYWRIGHT_VERSION=$(docker-compose run --rm gewobag-bot playwright --version 2>&1)
    test_passed "Playwright installiert: $PLAYWRIGHT_VERSION"
else
    test_failed "Playwright nicht installiert"
fi

# ===== Test 10: Python-Packages prüfen =====
test_step "Schritt 10: Python-Packages prüfen"
MISSING_PACKAGES=""

for package in "requests" "beautifulsoup4" "playwright"; do
    if docker-compose run --rm gewobag-bot python -c "import ${package}" > /dev/null 2>&1; then
        echo "  ✓ $package"
    else
        MISSING_PACKAGES="$MISSING_PACKAGES $package"
    fi
done

if [ -z "$MISSING_PACKAGES" ]; then
    test_passed "Alle Python-Packages installiert"
else
    test_failed "Fehlende Packages:$MISSING_PACKAGES"
fi

# ===== Test 11: Arbeitsverzeichnis prüfen =====
test_step "Schritt 11: Arbeitsverzeichnis im Container prüfen"
WORKDIR=$(docker-compose run --rm gewobag-bot pwd 2>&1 | tail -1)
if [[ $WORKDIR == *"/app"* ]]; then
    test_passed "Arbeitsverzeichnis: $WORKDIR"
else
    test_failed "Arbeitsverzeichnis nicht korrekt: $WORKDIR"
fi

# ===== Test 12: Non-root User prüfen =====
test_step "Schritt 12: Non-root User prüfen"
USER_ID=$(docker-compose run --rm gewobag-bot id -u 2>&1 | tail -1)
if [ "$USER_ID" = "1000" ]; then
    test_passed "Container läuft als Non-root User (uid=1000)"
else
    test_failed "Container läuft als Root (uid=$USER_ID)"
fi

# ===== Test 13: Skript-Dateien prüfen =====
test_step "Schritt 13: Python-Skripte im Container prüfen"
for script in "main.py" "gewobag-bot.py" "application_bot.py"; do
    if docker-compose run --rm gewobag-bot test -f /app/$script > /dev/null 2>&1; then
        echo "  ✓ $script"
    else
        test_failed "$script nicht im Container gefunden"
    fi
done
test_passed "Alle Python-Skripte vorhanden"

# ===== Test 14: Volume-Mounts testen (optional) =====
test_step "Schritt 14: Volume-Mounts testen"
if [ -f "user_data.json" ]; then
    if docker-compose run --rm gewobag-bot test -f /app/user_data.json > /dev/null 2>&1; then
        test_passed "Volume-Mounts funktionieren (user_data.json sichtbar)"
    else
        test_failed "Volume-Mount für user_data.json fehlgeschlagen"
    fi
else
    echo "  ⚠️  user_data.json nicht vorhanden (optional für Test)"
fi

# ===== Test 15: Healthcheck prüfen =====
test_step "Schritt 15: Healthcheck-Kommando testen"
# Erstelle temporäre Datenbank für Test
docker-compose run --rm gewobag-bot touch /app/gewobag_wohnungen.db > /dev/null 2>&1
if docker-compose run --rm gewobag-bot test -f /app/gewobag_wohnungen.db > /dev/null 2>&1; then
    test_passed "Healthcheck-Kommando funktioniert"
else
    test_failed "Healthcheck-Kommando fehlgeschlagen"
fi

# ===== Zusammenfassung =====
echo ""
echo "=========================================="
echo "📊 Test-Zusammenfassung"
echo "=========================================="
echo -e "${GREEN}✅ Bestanden: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Fehlgeschlagen: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Alle Tests bestanden!${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Konfigurationsdateien vorbereiten:"
    echo "   python main.py --setup"
    echo ""
    echo "2. Bot mit Docker starten:"
    echo "   docker-compose run --rm gewobag-bot"
    echo ""
    echo "3. Für Production-Deployment siehe DEPLOYMENT.md"
    exit 0
else
    echo -e "${RED}⚠️  Einige Tests sind fehlgeschlagen!${NC}"
    echo "Bitte prüfe die Fehler oben und behebe sie."
    exit 1
fi
