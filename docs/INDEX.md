# 📚 Gewobag Bot - Dokumentationsübersicht

Willkommen zur vollständigen Dokumentation des Gewobag Bots v2.2!

## 📖 Hauptdokumentation

### [README.md](README.md) - Vollständige Anleitung
Die komplette Anleitung mit allen Features, Installation, Konfiguration und Troubleshooting.

**Inhalt:**
- Installation & Setup
- Konfiguration (user_data.json, filter_config.json)
- Verwendung (Web-Frontend & CLI)
- Neue Features (Fehlererkennung, Nachrichtenanzeige)
- Docker Deployment
- Troubleshooting

### [CLAUDE.md](CLAUDE.md) - Entwickler-Dokumentation
Technische Dokumentation für Entwickler und zum Verständnis des Codes.

**Inhalt:**
- Projektarchitektur
- Code-Struktur
- Wichtige Funktionen
- Anti-Detection-Mechanismen
- Debugging & Entwicklung

## 🚀 Schnellstart

### [QUICKSTART.md](QUICKSTART.md) - Schnellstart-Anleitung
Kurze Anleitung für den schnellen Einstieg.

**Inhalt:**
- Installation in 3 Schritten
- Erste Konfiguration
- Erste Ausführung

## 🖥️ Web-Frontend

### [FRONTEND.md](FRONTEND.md) - Web-Frontend Anleitung
Anleitung für die Verwendung der grafischen Benutzeroberfläche.

**Inhalt:**
- Web-Frontend starten
- Dashboard Features
- Benutzerdaten bearbeiten
- Filter einstellen
- Bot steuern (Start/Stop/Pause)
- Bewerbungsübersicht

## 🐳 Docker & Deployment

### [DEPLOYMENT.md](DEPLOYMENT.md) - Docker Deployment Guide
Vollständige Anleitung für Docker-Deployment.

**Inhalt:**
- Docker Installation
- Docker Compose Setup
- Verschiedene Modi
- Automatische Ausführung (Cron)
- Logs & Monitoring

### [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Docker Schnellstart
Kurze Anleitung für schnelles Docker-Setup.

### [DOCKER_TEST.md](DOCKER_TEST.md) - Docker Testing
Anleitung zum Testen der Docker-Umgebung.

## 🌐 VPS Deployment

### [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - VPS Deployment
Vollständige Anleitung für Deployment auf einem VPS (Virtual Private Server).

**Inhalt:**
- VPS-Anforderungen
- Installation auf VPS
- Automatische Ausführung
- Monitoring & Logs
- Security Best Practices

### [VPS_fromGithub.md](VPS_fromGithub.md) - Deployment von GitHub
Anleitung zum Deployment direkt von GitHub auf einem VPS.

### [VPS_DEPLOYMENT_FIX.md](VPS_DEPLOYMENT_FIX.md) - VPS Troubleshooting
Lösungen für häufige VPS-Deployment-Probleme.

### [VOLUME_FIX_SUMMARY.md](VOLUME_FIX_SUMMARY.md) - Docker Volume Fixes
Lösungen für Docker Volume-Probleme.

## 🛡️ Anti-Detection

### [ANTI_DETECTION.md](ANTI_DETECTION.md) - Anti-Detection Strategien
Detaillierte Dokumentation aller Anti-Detection-Mechanismen.

**Inhalt:**
- User-Agent-Rotation
- Browser-Fingerprinting-Schutz
- Playwright Stealth
- Human-Like Behavior
- Rate Limiting

### [README_ANTI_DETECTION.md](README_ANTI_DETECTION.md) - Anti-Detection Übersicht
Kurze Übersicht über Anti-Detection-Features.

## 🎮 Bot-Befehle & Selektoren

### [BOT_BEFEHLE.md](BOT_BEFEHLE.md) - Bot Befehle Übersicht
Alle verfügbaren CLI-Befehle und deren Verwendung.

**Inhalt:**
- Setup-Befehle
- Scraping-Befehle
- Application-Befehle
- Debugging-Befehle

### [SELECTORS.md](SELECTORS.md) - CSS-Selektoren
Dokumentation aller verwendeten CSS-Selektoren für das Formular.

**Inhalt:**
- Formular-Selektoren
- iFrame-Selektoren
- Success/Error-Message-Selektoren

## 📊 Neue Features in v2.2

### Intelligente Fehlererkennung

Der Bot erkennt jetzt automatisch verschiedene Fehlertypen nach dem Submit:

```
================================================================================
❌ FEHLERMELDUNG IM IFRAME ERKANNT:
Das Objekt ist nicht mehr veröffentlicht
================================================================================
⚠️  WOHNUNG NICHT MEHR VERFÜGBAR: Das Objekt wurde bereits von der Website entfernt
```

**Unterstützte Fehlertypen:**
- ⚠️ **WOHNUNG NICHT MEHR VERFÜGBAR** - Objekt wurde von der Website entfernt
- ⚠️ **PFLICHTFELD FEHLT** - Nicht alle erforderlichen Felder ausgefüllt
- ⚠️ **UNGÜLTIGE EINGABE** - Fehlerhafte Daten eingegeben

### Klare Erfolgsmeldungen

```
================================================================================
✅ ERFOLGSMELDUNG IM IFRAME ERKANNT:
Vielen Dank für Ihre Anfrage! Wir werden uns in Kürze bei Ihnen melden.
================================================================================
```

## 🔧 Troubleshooting

Für Troubleshooting siehe:
- [README.md - Troubleshooting](README.md#-troubleshooting)
- [VPS_DEPLOYMENT_FIX.md](VPS_DEPLOYMENT_FIX.md)
- [VOLUME_FIX_SUMMARY.md](VOLUME_FIX_SUMMARY.md)

## 📞 Support

Bei Problemen oder Fragen:
1. Überprüfen Sie die relevante Dokumentation
2. Schauen Sie in die Log-Dateien
3. Testen Sie mit `--show-browser` für Debugging

---

**Viel Erfolg mit dem Gewobag Bot! 🏠🎉**
