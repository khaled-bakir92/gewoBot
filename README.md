# 🏠 Gewobag Bot v2.0 🤖

**Automatische Wohnungssuche und Bewerbung für Gewobag (Berlin)**

Dieser Bot sucht automatisch nach Wohnungen auf der Gewobag-Website, filtert nach Ihren Kriterien und bewirbt sich automatisch mit Ihren Daten.

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
- **Automatisches Absenden ist deaktiviert** (Sie müssen manuell bestätigen)

**Mit sichtbarem Browser (Debugging):**
```bash
python main.py --apply --show-browser
```

**Nur 3 Bewerbungen senden:**
```bash
python main.py --apply --max 3
```

---

### Modus 3: Vollautomatisch (Suchen + Bewerben)
```bash
python main.py --full
```
- Sucht neue Wohnungen
- Bewirbt sich automatisch auf alle neuen Wohnungen
- **Empfohlen für regelmäßige Ausführung**

**Mit sichtbarem Browser:**
```bash
python main.py --full --show-browser
```

---

## 🛡️ Automatisches Absenden aktivieren (Optional)

**Standardmäßig ist das automatische Absenden DEAKTIVIERT.**

Das Browser-Fenster bleibt 30 Sekunden offen, damit Sie die Daten manuell prüfen und abschicken können.

**Um vollautomatisches Absenden zu aktivieren:**

Bearbeiten Sie `application_bot.py` und entfernen Sie die Kommentare bei:

```python
# try:
#     logger.info("🚀 Sende Bewerbung ab...")
#     submit_button = iframe_element.locator('button[type="submit"], input[type="submit"]').first
#     submit_button.click()
#     random_delay(3.0, 5.0)
#     logger.info("✅ Bewerbung abgesendet!")
# except Exception as e:
#     logger.error(f"❌ Fehler beim Absenden: {e}")
#     return False
```

**⚠️ ACHTUNG:** Verwenden Sie dies nur, wenn Sie die Formulare vorher manuell geprüft haben!

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
SELECT * FROM wohnungen WHERE applied = 0;
```

**Erfolgreiche Bewerbungen:**
```sql
SELECT * FROM wohnungen WHERE application_status = 'success';
```

**Fehlgeschlagene Bewerbungen:**
```sql
SELECT * FROM wohnungen WHERE application_status = 'failed';
```

---

## 📝 Logs

**Log-Dateien:**
- `gewobag-bot.log` - Wohnungssuche
- `application-bot.log` - Bewerbungen
- `gewobag-main.log` - Hauptskript

**Logs anzeigen:**
```bash
tail -f gewobag-main.log
```

---

## 🧪 Testen

**Test-Modus mit sichtbarem Browser:**
```bash
# Nur 1 Bewerbung senden (für Test)
python main.py --apply --max 1 --show-browser
```

**Überprüfen Sie manuell:**
1. Werden alle Formularfelder korrekt ausgefüllt?
2. Werden die Dokumente hochgeladen?
3. Funktioniert der Tab-Wechsel?

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
- Überprüfen Sie `user_data.json` auf fehlende/fehlerhafte Daten
- Prüfen Sie, ob alle Dokument-Pfade existieren
- Erhöhen Sie Timeouts in `application_bot.py`
- Prüfen Sie `application-bot.log` für Details

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
