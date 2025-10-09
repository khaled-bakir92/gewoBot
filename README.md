# 🏠 Gewobag Bot v2.1 🤖

**Automatische Wohnungssuche und Bewerbung für Gewobag (Berlin)**

Dieser Bot sucht automatisch nach Wohnungen auf der Gewobag-Website, filtert nach Ihren Kriterien und bewirbt sich **vollautomatisch** mit Ihren Daten.

## 🆕 Neu in Version 2.1

- ✅ **Vollautomatisches Absenden aktiviert** - Keine manuelle Bestätigung mehr nötig!
- 🚀 **Einfacherer Start** - Einfach `python main.py` ohne Argumente ausführen
- 📋 **Detailliertes Fehler-Logging** mit spezifischen Fehlertypen und Empfehlungen
- 📸 **Automatische Screenshots bei Fehlern** für besseres Debugging
- 🎯 **Intelligente Fehlererkennung** (Cloudflare, Netzwerk, iFrame, Selektoren)
- 🛡️ **Doppelter Duplikat-Schutz** - Verhindert mehrfache Bewerbungen auf dieselbe Wohnung
- 📊 **Erweiterte Statistiken** - Zeigt alle bisherigen Bewerbungen an

---

## ✨ Features

- 🔍 **Automatische Wohnungssuche** mit konfigurierbaren Filtern
- 🌐 **Multi-Page Scraping** für alle verfügbaren Seiten
- 🗂️ **SQLite-Datenbank** zur Speicherung aller Wohnungen
- 🤖 **Browser-Automatisierung** mit Playwright
- 📝 **Automatisches Ausfüllen** des Bewerbungsformulars
- 📎 **Dokument-Upload** (Personalausweis, Gehaltsnachweise, etc.)
- 🛡️ **Anti-Detection** (User-Agent-Rotation, zufällige Delays, Stealth-Modus)
- ♻️ **Retry-Logik** bei Fehlern (HTTP 403/429)
- 📊 **Detailliertes Logging** aller Operationen
- ✅ **Status-Tracking** (erfolgreich/fehlgeschlagen)
- 🔒 **Duplikat-Schutz** - Keine doppelten Bewerbungen auf dieselbe Wohnung

---

## 🚀 Installation

### 1. Repository klonen
```bash
cd ~/Desktop/bot\ new
```

### 2. Virtual Environment aktivieren
```bash
source venv/bin/activate
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Initiale Konfiguration
```bash
python main.py --setup
```

Dies erstellt automatisch:
- `gewobag_wohnungen.db` (Datenbank)
- `user_data.json` (Template für Ihre Daten)
- `filter_config.json` (Template für Suchfilter)
- `bezirke_verfuegbar.json` (Liste aller Berliner Bezirke)

---

## ⚙️ Konfiguration

### 📋 user_data.json (WICHTIG!)

**Diese Datei enthält Ihre persönlichen Daten für die Bewerbung.**

Bearbeiten Sie `user_data.json` und tragen Sie Ihre echten Daten ein:

```json
{
  "personal_info": {
    "vorname": "Ihr Vorname",
    "nachname": "Ihr Nachname",
    "email": "ihre.email@example.com",
    "telefon": "+49 123 456789",
    "geburtsdatum": "01.01.1990",
    "staatsangehoerigkeit": "Deutsch"
  },
  "household": {
    "anzahl_personen": 1,
    "haushaltseinkommen": "3000"
  },
  "documents": {
    "personalausweis": "/absoluter/pfad/zu/personalausweis.pdf",
    "gehaltsnachweis_1": "/absoluter/pfad/zu/gehaltsnachweis1.pdf",
    "gehaltsnachweis_2": "/absoluter/pfad/zu/gehaltsnachweis2.pdf",
    "gehaltsnachweis_3": "/absoluter/pfad/zu/gehaltsnachweis3.pdf",
    "schufa": "/absoluter/pfad/zu/schufa.pdf",
    "mietschuldenfreiheit": "/absoluter/pfad/zu/mietschuldenfreiheit.pdf"
  },
  "nachricht": "Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich um die ausgeschriebene Wohnung..."
}
```

**⚠️ WICHTIG:**
- Verwenden Sie **absolute Pfade** für Dokumente (z.B. `/Users/khaled/Documents/ausweis.pdf`)
- Alle PDF-Dateien müssen existieren
- Diese Datei enthält sensible Daten → **NICHT committen!**

---

### 🔍 filter_config.json

**Konfigurieren Sie Ihre Suchfilter:**

```json
{
  "gewuenschte_bezirke": [
    "friedrichshain-kreuzberg",
    "mitte",
    "pankow-prenzlauer-berg"
  ],
  "gesamtmiete_von": "800",
  "gesamtmiete_bis": "1500",
  "gesamtflaeche_von": "60",
  "gesamtflaeche_bis": "100",
  "zimmer_von": "2",
  "zimmer_bis": "4",
  "wbs": ""
}
```

**Verfügbare Bezirke** finden Sie in `bezirke_verfuegbar.json`.

**WBS-Filter:**
- `"mit"` = nur WBS-Wohnungen
- `"ohne"` = nur ohne WBS
- `""` (leer) = egal

**Hinweis:** Leere Strings = keine Einschränkung für diesen Filter.

---

## 📖 Verwendung

### 🎯 Einfachster Weg (NEU!): Vollautomatisch
```bash
python main.py
```
- **Kein Argument nötig!** - Startet automatisch im Vollautomatik-Modus
- Sucht neue Wohnungen
- Bewirbt sich **automatisch** auf alle gefundenen Wohnungen
- **Sendet Formulare automatisch ab** (kein manuelles Eingreifen nötig)
- **Empfohlen für regelmäßige Ausführung**

---

### Modus 1: Nur Wohnungen suchen
```bash
python main.py --scrape
```
- Durchsucht Gewobag-Website mit Ihren Filtern
- Speichert Ergebnisse in Datenbank
- **Sendet KEINE Bewerbungen**

---

### Modus 2: Nur bewerben (auf bereits gefundene Wohnungen)
```bash
python main.py --apply
```
- Öffnet alle Wohnungen aus der Datenbank, für die noch keine Bewerbung gesendet wurde
- Füllt Bewerbungsformular automatisch aus
- **Sendet Formulare automatisch ab** ✅

**Mit sichtbarem Browser (Debugging):**
```bash
python main.py --show-browser
```

**Nur 3 Bewerbungen senden:**
```bash
python main.py --max 3
```

---

### Modus 3: Vollautomatisch (explizit)
```bash
python main.py --full
```
- Sucht neue Wohnungen
- Bewirbt sich automatisch auf alle neuen Wohnungen
- Identisch zu `python main.py` (ohne Argumente)

**Mit sichtbarem Browser:**
```bash
python main.py --show-browser
```

---

## 🛡️ Automatisches Absenden

**✅ Automatisches Absenden ist ab v2.1 STANDARDMÄSSIG AKTIVIERT!**

Der Bot füllt das Formular aus und sendet es automatisch ab. Keine manuelle Bestätigung mehr nötig!

**Was passiert beim Absenden:**
1. Bot füllt alle Formularfelder aus
2. Bot prüft, ob der Absende-Button sichtbar und aktiviert ist
3. Bot klickt auf "Absenden"
4. Bot wartet 3-5 Sekunden
5. Bot sucht nach Erfolgsmeldung (z.B. "Vielen Dank", "erfolgreich gesendet")
6. Status wird in Datenbank gespeichert (`applied = 1`, `application_status = 'success'`)

**Bei Fehlern:**
- Screenshot wird automatisch gespeichert (`error_screenshot_*.png`)
- Detaillierte Fehlermeldung im Log (`application-bot.log`)
- Status: `application_status = 'failed'` mit Fehlerbeschreibung
- Empfehlungen werden ausgegeben (z.B. "Cloudflare-Blockierung erkannt")

**Duplikat-Schutz (NEU!):**
Der Bot prüft **zweimal**, ob eine Wohnung bereits beworben wurde:
1. **Vor dem Abrufen** der Wohnungen (`WHERE applied = 0 OR applied IS NULL`)
2. **Vor jeder einzelnen Bewerbung** (zusätzliche Sicherheitsprüfung)

Falls ein Duplikat erkannt wird:
```
⚠️  DUPLIKAT ERKANNT: Wohnung wurde bereits am 2025-01-09 14:30:22 beworben (Status: success)
❌ ABBRUCH: Diese Wohnung wurde bereits beworben! Überspringe...
```

**Für Debugging (mit sichtbarem Browser):**
```bash
python main.py --show-browser
```

---

## 📊 Datenbank-Status prüfen

```bash
sqlite3 gewobag_wohnungen.db
```

**Alle Wohnungen anzeigen:**
```sql
SELECT titel, bezirk, miete, applied, application_status FROM wohnungen;
```

**Nur unbeworbene Wohnungen:**
```sql
SELECT * FROM wohnungen WHERE applied = 0 OR applied IS NULL;
```

**Erfolgreiche Bewerbungen:**
```sql
SELECT titel, adresse, applied_ts, application_status
FROM wohnungen
WHERE application_status = 'success'
ORDER BY applied_ts DESC;
```

**Fehlgeschlagene Bewerbungen mit Fehlermeldung:**
```sql
SELECT titel, adresse, application_error, applied_ts
FROM wohnungen
WHERE application_status = 'failed'
ORDER BY applied_ts DESC;
```

**Statistik anzeigen:**
```sql
SELECT
    COUNT(*) as gesamt,
    SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as beworben,
    SUM(CASE WHEN application_status = 'success' THEN 1 ELSE 0 END) as erfolgreich,
    SUM(CASE WHEN application_status = 'failed' THEN 1 ELSE 0 END) as fehlgeschlagen
FROM wohnungen;
```

**Duplikate prüfen (sollte immer 0 sein!):**
```sql
SELECT link, COUNT(*) as anzahl
FROM wohnungen
WHERE applied = 1
GROUP BY link
HAVING COUNT(*) > 1;
```

---

## 📝 Logs und Fehleranalyse

**Log-Dateien:**
- `gewobag-bot.log` - Wohnungssuche
- `application-bot.log` - Bewerbungen (detaillierte Fehleranalyse!)
- `gewobag-main.log` - Hauptskript

**Logs anzeigen:**
```bash
tail -f gewobag-main.log
tail -f application-bot.log  # Empfohlen für Fehleranalyse
```

**Screenshot-Dateien bei Fehlern:**
- `error_screenshot_*.png` - Screenshot beim Formular-Fehler
- `timeout_error_*.png` - Screenshot bei Timeout
- `general_error_*.png` - Screenshot bei allgemeinen Fehlern

**Intelligente Fehleranalyse (NEU in v2.1):**

Das Log enthält jetzt detaillierte Fehleranalysen:

```
❌ Fehler beim Ausfüllen des Formulars
Fehlertyp: PlaywrightTimeoutError
Fehlermeldung: Timeout 60000ms exceeded
URL: https://www.gewobag.de/...
🛡️  ACHTUNG: Cloudflare-Blockierung oder CAPTCHA erkannt!
Empfehlung: Längere Pausen zwischen Anfragen, User-Agent wechseln
📸 Screenshot gespeichert: error_screenshot_20250109_143022.png
```

**Fehlertypen und Empfehlungen:**
- **Cloudflare/CAPTCHA**: Längere Pausen, User-Agent wechseln
- **Netzwerkfehler**: Internetverbindung prüfen, Proxy erwägen
- **iFrame nicht geladen**: Längere Wartezeit, Website-Struktur evtl. geändert
- **Formular-Element nicht gefunden**: Selektoren müssen aktualisiert werden

---

## 🧪 Testen

**Test-Modus mit sichtbarem Browser:**
```bash
# Nur 1 Bewerbung senden (für Test)
python main.py --max 1 --show-browser
```

**Überprüfen Sie manuell:**
1. Werden alle Formularfelder korrekt ausgefüllt?
2. Wird das Formular automatisch abgesendet?
3. Erscheint eine Erfolgsmeldung?
4. Wird der Status in der Datenbank korrekt gespeichert?

**Nach dem Test:**
```bash
# Datenbank prüfen
sqlite3 gewobag_wohnungen.db
SELECT titel, applied, application_status, application_error FROM wohnungen WHERE applied = 1;
```

---

## 🐛 Troubleshooting

### Problem: "Import-Fehler"
**Lösung:**
```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

### Problem: "Formularfelder werden nicht gefunden"
**Ursache:** Die Website hat ihre Struktur geändert.

**Lösung:**
1. Führen Sie aus: `python main.py --apply --show-browser`
2. Inspizieren Sie das Formular im Browser
3. Aktualisieren Sie die Selektoren in `application_bot.py` → Funktion `fill_application_form()`

---

### Problem: "Keine Wohnungen gefunden"
**Lösungen:**
- Überprüfen Sie `filter_config.json` (evtl. zu restriktiv?)
- Testen Sie mit leeren Filtern
- Prüfen Sie `gewobag-bot.log` für Parsing-Fehler

---

### Problem: "Bewerbungen schlagen fehl"
**Lösungen:**
1. **Prüfen Sie die Log-Datei:**
   ```bash
   tail -n 50 application-bot.log
   ```
2. **Schauen Sie sich den Screenshot an:**
   - Öffnen Sie `error_screenshot_*.png` oder `timeout_error_*.png`
   - Sehen Sie, was genau auf der Seite angezeigt wurde
3. **Überprüfen Sie `user_data.json`:**
   - Sind alle Pflichtfelder ausgefüllt? (Vorname, Nachname, E-Mail, Anrede)
   - Sind die Dokument-Pfade korrekt? (absolute Pfade verwenden!)
4. **Testen Sie mit sichtbarem Browser:**
   ```bash
   python main.py --max 1 --show-browser
   ```
5. **Cloudflare-Blockierung:**
   - Log zeigt "Cloudflare" oder "CAPTCHA"?
   - Lösung: Längere Pausen zwischen Anfragen (erhöhen Sie `random_delay()` in `application_bot.py`)
6. **Formular-Struktur geändert:**
   - Log zeigt "Element nicht gefunden"?
   - Lösung: Selektoren in `fill_application_form()` müssen aktualisiert werden

---

## 🔒 Sicherheit & Datenschutz

- ✅ **user_data.json enthält sensible Daten** → Zu `.gitignore` hinzufügen!
- ✅ **Niemals persönliche Daten committen**
- ✅ **Anti-Detection ist nicht perfekt** → Verwenden Sie den Bot verantwortungsvoll
- ✅ **Respektieren Sie die Nutzungsbedingungen** der Website
- ✅ **Rate Limiting:** Der Bot wartet 30-60 Sekunden zwischen Bewerbungen

---

## 📁 Projektstruktur

```
bot new/
├── main.py                      # Haupt-CLI-Interface
├── gewobag-bot.py               # Web-Scraper
├── application_bot.py           # Browser-Automatisierung
├── user_data.json               # Ihre persönlichen Daten (NICHT committen!)
├── filter_config.json           # Suchfilter
├── bezirke_verfuegbar.json      # Liste aller Bezirke (auto-generiert)
├── gewobag_wohnungen.db         # SQLite-Datenbank (auto-generiert)
├── gewobag-bot.log              # Scraping-Logs
├── application-bot.log          # Bewerbungs-Logs
├── gewobag-main.log             # Main-Logs
├── requirements.txt             # Python-Dependencies
├── README.md                    # Diese Datei
└── CLAUDE.md                    # Entwickler-Dokumentation
```

---

## 🤝 Hilfe & Support

**Bei Problemen:**
1. Prüfen Sie die Log-Dateien
2. Führen Sie Tests mit `--show-browser` aus
3. Überprüfen Sie Ihre Konfigurationsdateien

---

## ⚖️ Rechtliches

Dieser Bot ist für den **persönlichen Gebrauch** gedacht.

**Haftungsausschluss:**
- Verwenden Sie den Bot auf eigene Verantwortung
- Respektieren Sie die Nutzungsbedingungen der Gewobag-Website
- Der Autor übernimmt keine Haftung für Schäden oder Sperrungen

---

## 📄 Lizenz

Dieses Projekt ist für den privaten Gebrauch bestimmt.

---

**Viel Erfolg bei der Wohnungssuche! 🏠🎉**
