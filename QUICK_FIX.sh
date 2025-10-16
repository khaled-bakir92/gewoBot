#!/bin/bash
# Schnelles Fix-Script für VPS Deployment
# Führen Sie dieses Script auf dem VPS aus

echo "🔧 Gewobag Bot - Scheduler Fix"
echo "================================"
echo ""

# Schritt 0: Pfade prüfen
echo "📍 Prüfe Arbeitsverzeichnis..."
CURRENT_DIR=$(pwd)
echo "Aktueller Pfad: $CURRENT_DIR"
echo ""

# Warnung wenn nicht in /root/gewoBot
if [ "$CURRENT_DIR" != "/root/gewoBot" ]; then
    echo "⚠️  WARNUNG: Sie sind nicht in /root/gewoBot!"
    echo "   Bitte prüfen Sie die Pfade in ofelia-config.ini"
    echo "   und passen Sie sie an Ihr Verzeichnis an!"
    echo ""
    read -p "Fortfahren? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Schritt 1: Alte Container stoppen
echo "📦 Stoppe alte Container..."
docker-compose down
echo "✅ Container gestoppt"
echo ""

# Schritt 2: Image neu bauen
echo "🏗️  Baue neues Docker Image..."
docker-compose build gewobag-bot
if [ $? -eq 0 ]; then
    echo "✅ Image erfolgreich gebaut"
else
    echo "❌ Fehler beim Bauen des Images!"
    exit 1
fi
echo ""

# Schritt 3: Image-Name prüfen
echo "🔍 Prüfe Image-Namen..."
docker images | grep gewobot-gewobag-bot
if [ $? -eq 0 ]; then
    echo "✅ Image gefunden"
else
    echo "❌ Image nicht gefunden!"
    exit 1
fi
echo ""

# Schritt 4: Services starten
echo "🚀 Starte Services..."
docker-compose up -d gewobag-web
docker-compose up -d gewobag-scheduler
echo "✅ Services gestartet"
echo ""

# Schritt 5: Status anzeigen
echo "📊 Service-Status:"
docker-compose ps
echo ""

# Schritt 6: Konfiguration prüfen
echo "🔍 Prüfe Ofelia-Konfiguration..."
if [ -f "ofelia-config.ini" ]; then
    echo "✅ ofelia-config.ini gefunden"
    echo "   Erste Volume-Zeile:"
    grep "^volume =" ofelia-config.ini | head -1
else
    echo "❌ ofelia-config.ini NICHT gefunden!"
    echo "   Bitte laden Sie die Datei hoch!"
    exit 1
fi
echo ""

# Schritt 7: Scheduler-Logs anzeigen
echo "📋 Scheduler-Logs (letzte 20 Zeilen):"
docker-compose logs --tail=20 gewobag-scheduler
echo ""

# Schritt 8: Job registrierung prüfen
echo "🔍 Prüfe registrierte Jobs..."
docker-compose logs gewobag-scheduler | grep "registered" | tail -1
echo ""

echo "✅ Deployment abgeschlossen!"
echo ""
echo "📌 Nächste Schritte:"
echo "   1. Warten Sie 15 Minuten auf den ersten Job"
echo "   2. Prüfen Sie die Logs: docker-compose logs -f gewobag-scheduler"
echo "   3. Web-Frontend: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📝 Manuelle Ausführung (optional):"
echo "   docker-compose run --rm --profile manual gewobag-bot python main.py --full"
echo ""
echo "⚠️  Bei Fehlern:"
echo "   - Prüfen Sie die Pfade in ofelia-config.ini"
echo "   - Stellen Sie sicher, dass alle Dateien existieren (user_data.json, etc.)"
echo ""
