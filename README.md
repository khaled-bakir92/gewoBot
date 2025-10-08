# Gewobag-Bot - Wohnungssuche Automatisierung

Ein Python-Bot, der automatisch Wohnungsangebote von der Gewobag-Website (Berlin) scrapt und in einer SQLite-Datenbank speichert. Mit konfigurierbaren Bezirksfiltern für gezielte Wohnungssuche.

---

## 📋 Inhaltsverzeichnis

- [Features](#features)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Bezirksfilter konfigurieren](#bezirksfilter-konfigurieren)
- [Verwendung](#verwendung)
- [Dateien und Struktur](#dateien-und-struktur)
- [Automatisierung](#automatisierung)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- 🏠 **Automatisches Scraping** von Gewobag-Wohnungsangeboten
- 🗺️ **Bezirksfilter** - Suche nur in gewünschten Berliner Bezirken/Ortsteilen
- 💾 **SQLite-Datenbank** - Automatische Speicherung aller Angebote
- 🔄 **Duplikatserkennung** - Verhindert doppelte Einträge
- 📊 **Detaillierte Logs** - Alle Aktivitäten werden protokolliert
- ⏰ **Scheduler-Support** - Optional für automatische regelmäßige Ausführung
- 📝 **JSON-Konfiguration** - Einfache Filtereinstellung über JSON-Datei

---

## 🚀 Installation

### Voraussetzungen

- Python 3.7 oder höher
- pip (Python Package Manager)

### 1. Repository klonen oder herunterladen

```bash
cd /Users/khaled/Desktop/bot\ new
```

### 2. Virtuelle Umgebung aktivieren

```bash
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Benötigte Pakete:**
- `requests` - HTTP-Anfragen
- `beautifulsoup4` - HTML-Parsing
- `apscheduler` - Zeitgesteuerte Ausführung (optional)

---

## 🎯 Schnellstart

### Erste Ausführung

```bash
python gewobag-bot.py
```

Beim ersten Start wird automatisch:
1. ✅ Die Datenbank `gewobag_wohnungen.db` erstellt
2. ✅ Eine Liste aller verfügbaren Bezirke heruntergeladen → `bezirke_verfuegbar.json`
3. ✅ Eine Beispiel-Konfigurationsdatei erstellt → `filter_config.json`
4. ✅ Alle verfügbaren Wohnungen gescrapt und gespeichert

**Ausgabe:**
```
✓ Bezirksliste mit 64 Einträgen erstellt: bezirke_verfuegbar.json

======================================================================
Starte Gewobag Wohnungssuche
======================================================================
...
Zusammenfassung: 20 Angebote gefunden, 20 neu gespeichert, 0 bereits bekannt
======================================================================

GEFUNDENE WOHNUNGEN (20)
[1] Familiengerecht!
    Bezirk:      Wilhelmstadt
    Adresse:     Heerstr. 366, 13593 Berlin/Spandau
    ...
```

---

## 🗺️ Bezirksfilter konfigurieren

### Schritt 1: Verfügbare Bezirke ansehen

Öffnen Sie die automatisch erstellte Datei `bezirke_verfuegbar.json`:

```json
{
  "stand": "2025-10-08 02:36:04",
  "anzahl": 64,
  "bezirke": [
    {
      "value": "friedrichshain-kreuzberg",
      "name": "Friedrichshain-Kreuzberg",
      "typ": "Hauptbezirk"
    },
    {
      "value": "friedrichshain-kreuzberg-friedrichshain",
      "name": "Friedrichshain",
      "typ": "Ortsteil"
    },
    {
      "value": "mitte",
      "name": "Mitte",
      "typ": "Hauptbezirk"
    },
    ...
  ]
}
```

### Schritt 2: Filter konfigurieren

Öffnen Sie `filter_config.json` und tragen Sie die gewünschten **`value`**-Werte ein:

```json
{
  "_kommentar": "Tragen Sie hier die gewünschten Bezirke ein (value aus bezirke_verfuegbar.json)",
  "_beispiel": [
    "friedrichshain-kreuzberg",
    "mitte",
    "pankow-prenzlauer-berg"
  ],
  "gewuenschte_bezirke": [
    "friedrichshain-kreuzberg",
    "mitte",
    "neukoelln"
  ]
}
```

### Filter-Beispiele

**Alle Bezirke durchsuchen (Standard):**
```json
"gewuenschte_bezirke": []
```

**Nur ein spezifischer Bezirk:**
```json
"gewuenschte_bezirke": ["spandau"]
```

**Mehrere Hauptbezirke:**
```json
"gewuenschte_bezirke": [
  "friedrichshain-kreuzberg",
  "mitte",
  "pankow"
]
```

**Nur bestimmte Ortsteile:**
```json
"gewuenschte_bezirke": [
  "pankow-prenzlauer-berg",
  "friedrichshain-kreuzberg-friedrichshain",
  "neukoelln-neukoelln"
]
```

**Mix aus Hauptbezirken und Ortsteilen:**
```json
"gewuenschte_bezirke": [
  "mitte",
  "pankow-prenzlauer-berg",
  "neukoelln-britz",
  "tempelhof-schoeneberg-schoeneberg"
]
```

### Schritt 3: Bot mit Filtern ausführen

```bash
python gewobag-bot.py
```

Der Bot verwendet automatisch die Filter aus `filter_config.json`.

**Beispiel-Ausgabe mit Filter:**
```
Lade 1 Bezirksfilter aus Konfiguration
Bezirksfilter aktiv für: spandau
Lade Seite von https://www.gewobag.de/...&bezirke%5B%5D=spandau
...
Zusammenfassung: 10 Angebote gefunden (mit aktiven Filtern), 10 neu gespeichert
```

---

## 📖 Verwendung

### Einmalige Ausführung

```bash
python gewobag-bot.py
```

- Scrapt alle Wohnungen (mit aktiven Filtern)
- Speichert neue Angebote in der Datenbank
- Zeigt alle gefundenen Wohnungen an
- Loggt alle Aktivitäten in `gewobag-bot.log`

### Automatische Ausführung (Scheduler)

Bearbeiten Sie `gewobag-bot.py` und kommentieren Sie die Scheduler-Zeilen ein:

```python
if __name__ == "__main__":
    try:
        init_database()

        # Scheduler aktivieren (auskommentieren):
        print("\nStarte automatischen Scheduler...")
        print("Drücke Ctrl+C zum Beenden")
        run_scheduler(interval_minutes=60)  # Alle 60 Minuten
```

**Dann ausführen:**
```bash
python gewobag-bot.py
```

Der Bot läuft jetzt kontinuierlich und scrapt stündlich neue Angebote.

### Datenbank zurücksetzen

```bash
rm gewobag_wohnungen.db
python gewobag-bot.py
```

---

## 📁 Dateien und Struktur

### Haupt-Dateien

| Datei | Beschreibung |
|-------|--------------|
| `gewobag-bot.py` | Haupt-Script mit gesamter Logik |
| `filter_config.json` | **Ihre Filterkonfiguration** (bearbeitbar) |
| `bezirke_verfuegbar.json` | Liste aller verfügbaren Bezirke (automatisch generiert) |
| `gewobag_wohnungen.db` | SQLite-Datenbank mit allen Wohnungen |
| `gewobag-bot.log` | Log-Datei aller Aktivitäten |
| `requirements.txt` | Python-Abhängigkeiten |
| `README.md` | Diese Anleitung |

### Optionale Dateien

| Datei | Beschreibung |
|-------|--------------|
| `view.html` | Beispiel-HTML der Gewobag-Website (Entwicklung) |
| `lage-filter.html` | HTML-Struktur der Bezirksfilter (Referenz) |
| `CLAUDE.md` | Projektdokumentation für Claude Code |

### Datenbank-Schema

**Tabelle: `wohnungen`**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Auto-Increment Primary Key |
| `bezirk` | TEXT | Bezirk/Ortsteil (z.B. "Friedrichshain") |
| `adresse` | TEXT | Vollständige Adresse |
| `titel` | TEXT | Wohnungs-Titel |
| `zimmer` | TEXT | Zimmeranzahl (z.B. "3 Zimmer") |
| `flaeche` | TEXT | Wohnfläche (z.B. "80,38 m²") |
| `miete` | TEXT | Gesamtmiete (z.B. "ab 933,00€") |
| `link` | TEXT | **UNIQUE** - Link zum Angebot (verhindert Duplikate) |
| `ts` | TIMESTAMP | Zeitpunkt der Speicherung |

### Datenbank abfragen

```bash
# Alle Wohnungen anzeigen
sqlite3 gewobag_wohnungen.db "SELECT * FROM wohnungen;"

# Nur wichtige Spalten anzeigen
sqlite3 gewobag_wohnungen.db "SELECT bezirk, zimmer, flaeche, miete, titel FROM wohnungen;"

# Nur Bezirke und Titel
sqlite3 gewobag_wohnungen.db "SELECT bezirk, titel FROM wohnungen;"

# Anzahl Wohnungen pro Bezirk
sqlite3 gewobag_wohnungen.db "SELECT bezirk, COUNT(*) FROM wohnungen GROUP BY bezirk;"

# Wohnungen nach Zimmeranzahl filtern
sqlite3 gewobag_wohnungen.db "SELECT titel, zimmer, flaeche, miete FROM wohnungen WHERE zimmer = '3 Zimmer';"

# Wohnungen nach Datum sortiert
sqlite3 gewobag_wohnungen.db "SELECT titel, bezirk, zimmer, flaeche, ts FROM wohnungen ORDER BY ts DESC;"

# Datenbank-Schema anzeigen
sqlite3 gewobag_wohnungen.db ".schema wohnungen"
```

---

## ⏰ Automatisierung

### Option 1: Cron-Job (macOS/Linux)

```bash
# Crontab bearbeiten
crontab -e

# Alle 2 Stunden ausführen
0 */2 * * * cd /Users/khaled/Desktop/bot\ new && source venv/bin/activate && python gewobag-bot.py >> cron.log 2>&1
```

### Option 2: APScheduler (im Script)

Siehe [Automatische Ausführung](#automatische-ausführung-scheduler) oben.

### Option 3: macOS Launch Agent

Erstellen Sie `~/Library/LaunchAgents/com.gewobag.bot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gewobag.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/khaled/Desktop/bot new/venv/bin/python</string>
        <string>/Users/khaled/Desktop/bot new/gewobag-bot.py</string>
    </array>
    <key>StartInterval</key>
    <integer>7200</integer> <!-- Alle 2 Stunden -->
    <key>WorkingDirectory</key>
    <string>/Users/khaled/Desktop/bot new</string>
</dict>
</plist>
```

```bash
# Launch Agent laden
launchctl load ~/Library/LaunchAgents/com.gewobag.bot.plist
```

---

## 🔧 Troubleshooting

### Problem: Keine Wohnungen gefunden

**Lösung:**
- Prüfen Sie Ihre Internetverbindung
- Überprüfen Sie, ob `filter_config.json` gültige Bezirke enthält
- Testen Sie ohne Filter (leere Liste): `"gewuenschte_bezirke": []`

### Problem: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'requests'
```

**Lösung:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: Filter funktioniert nicht

**Lösung:**
- Überprüfen Sie die Schreibweise in `filter_config.json`
- Die Werte müssen exakt mit `bezirke_verfuegbar.json` übereinstimmen
- Beispiel: `"friedrichshain-kreuzberg"` ✅, `"Friedrichshain-Kreuzberg"` ❌

### Problem: Timeout-Fehler

```
Timeout beim Laden der Seite (>30s)
```

**Lösung:**
- Erhöhen Sie `REQUEST_TIMEOUT` in `gewobag-bot.py`:
```python
REQUEST_TIMEOUT = 60  # Von 30 auf 60 Sekunden
```

### Problem: Bezirksliste ist veraltet

**Lösung:**
```bash
rm bezirke_verfuegbar.json
python gewobag-bot.py  # Lädt neue Liste von der Website
```

### Problem: Datenbank ist beschädigt

**Lösung:**
```bash
rm gewobag_wohnungen.db
python gewobag-bot.py  # Erstellt neue Datenbank
```

---

## 📊 Log-Dateien

### Konsolen-Ausgabe

Der Bot gibt detaillierte Informationen aus:
```
2025-10-08 02:36:04 - INFO - Datenbank erfolgreich initialisiert
2025-10-08 02:36:04 - INFO - Bezirksfilter aktiv für: spandau
2025-10-08 02:36:04 - INFO - Lade Seite von https://www.gewobag.de/...
2025-10-08 02:36:05 - INFO - 10 Angebote gefunden
2025-10-08 02:36:05 - INFO - Neue Wohnung gespeichert: Familiengerecht! in Wilhelmstadt
```

### Log-Datei

Alle Logs werden auch in `gewobag-bot.log` gespeichert:

```bash
# Letzte 50 Zeilen anzeigen
tail -50 gewobag-bot.log

# Nur Fehler anzeigen
grep ERROR gewobag-bot.log

# Live-Logs verfolgen
tail -f gewobag-bot.log
```

---

## 🎓 Erweiterte Nutzung

### Bezirksliste manuell aktualisieren

```python
from gewobag-bot import extract_bezirke_from_website, save_bezirke_liste

bezirke = extract_bezirke_from_website()
save_bezirke_liste(bezirke)
```

### Nur scrapen, nicht speichern

Bearbeiten Sie `gewobag-bot.py` und kommentieren Sie aus:
```python
# In scrape_wohnungen():
# neu, vorhanden = save_to_database(wohnungen)  # Auskommentieren
```

### Eigene Filter-Logik hinzufügen

Bearbeiten Sie die Funktion `parse_wohnungen()` um zusätzliche Filter hinzuzufügen:

```python
# Beispiel: Nur Wohnungen unter 800€
if wohnung:
    miete_text = wohnung['miete'].replace('ab ', '').replace('€', '').replace(',', '.')
    try:
        miete = float(miete_text)
        if miete <= 800:
            wohnungen.append(wohnung)
    except:
        pass
```

---

## 📝 Änderungshistorie

### Version 2.1 (2025-10-08)
- ✨ **NEU:** Getrennte Datenbank-Spalten für `zimmer` und `flaeche`
- 🔧 Automatisches Parsen von "3 Zimmer | 80,38 m²" in separate Felder
- 📊 Verbesserte Datenbank-Queries möglich (Filterung nach Zimmeranzahl)
- 📝 README aktualisiert mit neuen SQL-Beispielen

### Version 2.0 (2025-10-08)
- ✨ **NEU:** JSON-basierte Bezirksfilter
- ✨ **NEU:** Automatische Extraktion aller verfügbaren Bezirke von der Website
- ✨ **NEU:** `bezirke_verfuegbar.json` - Liste aller 64 Bezirke/Ortsteile
- ✨ **NEU:** `filter_config.json` - Benutzerfreundliche Filterkonfiguration
- 🔧 URL-Builder mit dynamischen Bezirksparametern
- 📚 Vollständige README-Dokumentation

### Version 1.0 (Ursprünglich)
- 🏠 Basis-Scraping von Gewobag-Wohnungen
- 💾 SQLite-Datenbank mit Duplikatserkennung
- 📊 Logging und Konsolenausgabe
- ⏰ APScheduler-Integration

---

## 📄 Lizenz

Dieses Projekt dient ausschließlich zu Bildungszwecken. Bitte beachten Sie die Nutzungsbedingungen der Gewobag-Website.

---

## 🤝 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die [Troubleshooting](#troubleshooting)-Sektion
2. Prüfen Sie die Log-Datei `gewobag-bot.log`
3. Testen Sie ohne Filter

---

**Viel Erfolg bei der Wohnungssuche! 🏠✨**
