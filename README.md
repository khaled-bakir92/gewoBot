# 🏠 Gewobag Bot v2.2 🤖

**Automatische Wohnungssuche und Bewerbung für Gewobag (Berlin)**

Dieser Bot sucht automatisch nach Wohnungen auf der Gewobag-Website, filtert nach Ihren Kriterien und bewirbt sich **vollautomatisch** mit Ihren Daten.

## 🆕 Neu in Version 2.2

- 🖥️ **Web-Frontend** - Benutzerfreundliche grafische Oberfläche
- 📊 **Live-Dashboard** - Echtzeit-Statistiken und Status-Updates
- 🎮 **Bot-Steuerung über GUI** - Start, Stop, Pause direkt im Browser
- 📝 **Intelligente Fehlererkennung** - Erkennt und meldet spezifische Fehler nach Submit
- ⚠️ **Detaillierte Nachrichten** - Zeigt genau an, warum eine Bewerbung fehlgeschlagen ist

## ✨ Features

- 🔍 Automatische Wohnungssuche mit konfigurierbaren Filtern
- 🤖 Browser-Automatisierung mit Playwright
- 📝 Automatisches Ausfüllen des Bewerbungsformulars
- ✅ **Intelligente Nachrichtenerkennung** nach Submit
- ❌ **Fehlermeldungs-Analyse** (z.B. "Objekt nicht mehr verfügbar")
- 🛡️ Anti-Detection (User-Agent-Rotation, Stealth-Modus)
- 🔒 Duplikat-Schutz - Keine doppelten Bewerbungen

## 🚀 Schnellstart

### Installation
```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
playwright install chromium

# Initiale Konfiguration
python main.py --setup
```

### Konfiguration
1. Bearbeiten Sie `user_data.json` mit Ihren persönlichen Daten
2. Passen Sie `filter_config.json` an Ihre Suchkriterien an

### Verwendung

**Web-Frontend (Empfohlen):**
```bash
python web_api.py
# Dann Browser öffnen: http://localhost:5000
```

**CLI (Vollautomatisch):**
```bash
python main.py
```

**Nur Wohnungen suchen:**
```bash
python main.py --scrape
```

**Nur bewerben:**
```bash
python main.py --apply
```

**Mit sichtbarem Browser (Debugging):**
```bash
python main.py --show-browser
```

## 📚 Vollständige Dokumentation

Alle Dokumentationen befinden sich im `docs/` Ordner:

- **[README.md](docs/README.md)** - Vollständige Anleitung (Deutsch)
- **[CLAUDE.md](docs/CLAUDE.md)** - Entwickler-Dokumentation
- **[FRONTEND.md](docs/FRONTEND.md)** - Web-Frontend Anleitung
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Docker Deployment Guide
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Schnellstart-Anleitung
- **[VPS_DEPLOYMENT_GUIDE.md](docs/VPS_DEPLOYMENT_GUIDE.md)** - VPS Deployment
- **[ANTI_DETECTION.md](docs/ANTI_DETECTION.md)** - Anti-Detection Strategien
- **[BOT_BEFEHLE.md](docs/BOT_BEFEHLE.md)** - Bot Befehle Übersicht

## 📊 Neue Features: Intelligente Nachrichtenerkennung

### Fehlermeldungen werden jetzt erkannt:

```
================================================================================
❌ FEHLERMELDUNG IM IFRAME ERKANNT:
Das Objekt ist nicht mehr veröffentlicht
================================================================================
⚠️  WOHNUNG NICHT MEHR VERFÜGBAR: Das Objekt wurde bereits von der Website entfernt
```

### Erfolgsmeldungen werden klar angezeigt:

```
================================================================================
✅ ERFOLGSMELDUNG IM IFRAME ERKANNT:
Vielen Dank für Ihre Anfrage! Wir werden uns in Kürze bei Ihnen melden.
================================================================================
```

### Unterstützte Fehlertypen:

- ⚠️ **WOHNUNG NICHT MEHR VERFÜGBAR** - Objekt wurde von der Website entfernt
- ⚠️ **PFLICHTFELD FEHLT** - Nicht alle erforderlichen Felder ausgefüllt
- ⚠️ **UNGÜLTIGE EINGABE** - Fehlerhafte Daten eingegeben

## 🐳 Docker Deployment

```bash
# Docker Image bauen
docker-compose build

# Bot starten
docker-compose run --rm gewobag-bot

# Im Hintergrund laufen lassen
docker-compose up -d
```

Siehe [DEPLOYMENT.md](docs/DEPLOYMENT.md) für Details.

## 📁 Projektstruktur

```
bot new/
├── main.py                      # Haupt-CLI-Interface
├── gewobag-bot.py               # Web-Scraper
├── application_bot.py           # Browser-Automatisierung
├── web_api.py                   # Flask Web-API (Backend)
├── frontend/                    # Web-Frontend
├── docs/                        # Dokumentation
├── user_data.json               # Ihre persönlichen Daten
├── filter_config.json           # Suchfilter
├── gewobag_wohnungen.db         # SQLite-Datenbank
└── venv/                        # Python Virtual Environment
```

## 🔒 Sicherheit & Datenschutz

- ✅ `user_data.json` enthält sensible Daten → Zu `.gitignore` hinzufügen!
- ✅ Niemals persönliche Daten committen
- ✅ Respektieren Sie die Nutzungsbedingungen der Website

## 🐛 Troubleshooting

**Problem:** "Import-Fehler"
```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**Problem:** "Keine Wohnungen gefunden"
- Überprüfen Sie `filter_config.json` (evtl. zu restriktiv?)
- Testen Sie mit leeren Filtern

**Problem:** "Bewerbungen schlagen fehl"
1. Prüfen Sie die Log-Datei: `tail -n 50 application-bot.log`
2. Schauen Sie sich Screenshots an: `error_screenshot_*.png`
3. Testen Sie mit sichtbarem Browser: `python main.py --max 1 --show-browser`

Siehe [docs/README.md](docs/README.md) für detailliertes Troubleshooting.

## ⚖️ Rechtliches

Dieser Bot ist für den **persönlichen Gebrauch** gedacht.

**Haftungsausschluss:**
- Verwenden Sie den Bot auf eigene Verantwortung
- Respektieren Sie die Nutzungsbedingungen der Gewobag-Website
- Der Autor übernimmt keine Haftung für Schäden oder Sperrungen

---

**Viel Erfolg bei der Wohnungssuche! 🏠🎉**

Für detaillierte Informationen siehe [docs/README.md](docs/README.md)
