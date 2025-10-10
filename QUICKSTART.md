# 🚀 Gewobag Bot - Schnellstart-Anleitung

## 1. Installation (Einmalig)

```bash
# 1. Aktiviere Virtual Environment
source venv/bin/activate

# 2. Installiere Dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Erstelle Konfigurationsdateien
python main.py --setup
```

---

## 2. Konfiguration

### Option A: Über Web-Interface (Empfohlen!)

```bash
# Web-Server starten
python web_api.py
```

Dann im Browser öffnen: **http://localhost:5000**

1. **Benutzerdaten Tab:** Trage deine persönlichen Daten ein
2. **Filter Tab:** Wähle gewünschte Bezirke und Filterkriterien
3. **Speichern** klicken

### Option B: Manuell (JSON-Dateien bearbeiten)

Bearbeite `user_data.json` und `filter_config.json` mit einem Texteditor.

---

## 3. Bot starten

### Option A: Über Web-Interface

1. Öffne **http://localhost:5000**
2. Gehe zu **Bot-Steuerung Tab**
3. Wähle Modus (z.B. "Vollautomatisch")
4. Klicke auf **"Bot starten"**

### Option B: Über Kommandozeile

```bash
# Vollautomatik (Suchen + Bewerben)
python main.py

# Nur Wohnungen suchen
python main.py --scrape

# Nur auf gefundene Wohnungen bewerben
python main.py --apply

# Mit sichtbarem Browser (zum Debuggen)
python main.py --show-browser
```

---

## 4. Status überwachen

### Web-Interface (Live-Updates)

Öffne **http://localhost:5000** → **Dashboard Tab**

- Live-Statistiken
- Letzte Bewerbungen
- Bot-Status

### Kommandozeile (Logs)

```bash
# Hauptlog anzeigen
tail -f gewobag-main.log

# Bewerbungs-Log anzeigen
tail -f application-bot.log
```

---

## 5. Datenbank prüfen

```bash
sqlite3 gewobag_wohnungen.db
```

**SQL-Abfragen:**

```sql
-- Alle Wohnungen
SELECT COUNT(*) FROM wohnungen;

-- Erfolgreich beworben
SELECT COUNT(*) FROM wohnungen WHERE application_status = 'success';

-- Letzte Bewerbungen
SELECT titel, adresse, applied_ts FROM wohnungen
WHERE applied = 1
ORDER BY applied_ts DESC
LIMIT 10;
```

---

## 6. Troubleshooting

### Problem: Web-Server startet nicht

```bash
# Flask installieren
pip install flask flask-cors
```

### Problem: Bot findet keine Wohnungen

1. Prüfe Filter-Einstellungen (evtl. zu restriktiv)
2. Teste mit leeren Filtern
3. Prüfe `gewobag-bot.log`

### Problem: Bewerbungen schlagen fehl

1. Prüfe `application-bot.log`
2. Schaue dir Screenshots an (`error_screenshot_*.png`)
3. Teste mit `--show-browser` Flag

---

## 🎉 Das war's!

**Viel Erfolg bei der Wohnungssuche!**

Detaillierte Dokumentation:
- [README.md](README.md) - Vollständige Anleitung
- [FRONTEND.md](FRONTEND.md) - Web-Frontend-Dokumentation
- [CLAUDE.md](CLAUDE.md) - Entwickler-Dokumentation
