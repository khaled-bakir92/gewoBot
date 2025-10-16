#!/bin/bash
# Schnelles Fix-Script für VPS Deployment
# Führen Sie dieses Script auf dem VPS aus

echo "🔧 Gewobag Bot - Scheduler Fix"
echo "================================"
echo ""

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

# Schritt 6: Scheduler-Logs anzeigen
echo "📋 Scheduler-Logs (letzte 20 Zeilen):"
docker-compose logs --tail=20 gewobag-scheduler
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
