# 🖥️ Gewobag Bot - Web Frontend

## Übersicht

Das Web-Frontend bietet eine benutzerfreundliche grafische Oberfläche für den Gewobag-Bot mit folgenden Funktionen:

- 📊 **Dashboard** - Übersicht über alle Statistiken und letzte Bewerbungen
- 👤 **Benutzerdaten** - Verwaltung Ihrer persönlichen Daten
- 🔍 **Filter** - Konfiguration der Wohnungssuchfilter
- 🎮 **Bot-Steuerung** - Start, Stop, Pause und Resume des Bots
- 📝 **Bewerbungen** - Übersicht aller gefundenen Wohnungen und Bewerbungen

---

## 🚀 Installation & Start

### 1. Dependencies installieren

```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Neue Dependencies installieren
pip install -r requirements.txt
```

### 2. Web-Server starten

```bash
# Web-API starten
python web_api.py
```

Der Server startet auf `http://localhost:5000`

### 3. Frontend öffnen

Öffnen Sie Ihren Browser und navigieren Sie zu:

```
http://localhost:5000
```

---

## 📋 Funktionen im Detail

### 📊 Dashboard

Das Dashboard zeigt:
- **Statistiken:**
  - Anzahl gefundener Wohnungen
  - Anzahl gesendeter Bewerbungen
  - Erfolgreich abgeschlossene Bewerbungen
  - Fehlgeschlagene Bewerbungen
- **Letzte Bewerbungen:** Die 10 neuesten Bewerbungen mit Details
- **Bot-Status:** Aktueller Status des Bots (läuft/gestoppt/pausiert)

**Auto-Refresh:** Das Dashboard aktualisiert sich automatisch alle 2 Sekunden.

---

### 👤 Benutzerdaten

Hier können Sie alle persönlichen Daten für die Bewerbungen verwalten:

**Persönliche Informationen:**
- Anrede, Vorname, Nachname
- E-Mail, Telefon, Mobil
- Geburtsdatum, Staatsangehörigkeit

**Adresse:**
- Straße, Hausnummer
- PLZ, Stadt
- Adresszusatz

**Haushalt:**
- Anzahl Personen
- Anzahl Kinder
- Haushaltseinkommen
- WBS-Informationen (falls vorhanden)

**Dokumente:**
- Personalausweis (PDF)
- Gehaltsnachweise (PDF)
- SCHUFA (PDF)
- Mietschuldenfreiheit (PDF)

**Wichtig:** Verwenden Sie absolute Pfade für die Dokumente!

Beispiel:
```
/Users/khaled/Documents/personalausweis.pdf
```

**Speichern:** Klicken Sie auf "Daten speichern", um Änderungen zu übernehmen.

---

### 🔍 Filter

Konfigurieren Sie hier Ihre Suchkriterien:

**Bezirke:**
- Wählen Sie einen oder mehrere Bezirke aus (Checkboxen)
- Die verfügbaren Bezirke werden automatisch von der Gewobag-Website geladen

**Gesamtmiete:**
- Von (€): Minimale Miete
- Bis (€): Maximale Miete

**Wohnfläche:**
- Von (m²): Minimale Fläche
- Bis (m²): Maximale Fläche

**Zimmer:**
- Von: Minimale Anzahl Zimmer
- Bis: Maximale Anzahl Zimmer

**WBS-Anforderung:**
- Egal: Alle Wohnungen
- Nur mit WBS: Nur WBS-Wohnungen
- Nur ohne WBS: Nur Wohnungen ohne WBS

**Tipp:** Leere Felder bedeuten "keine Einschränkung".

**Speichern:** Klicken Sie auf "Filter speichern", um Änderungen zu übernehmen.

---

### 🎮 Bot-Steuerung

**Status-Anzeige:**
- Aktueller Status (Gestoppt/Läuft/Pausiert)
- Modus (Full/Scrape/Apply)
- Startzeit
- Letzte Aktivität

**Steuerung:**

1. **Modus auswählen:**
   - **Vollautomatisch:** Suchen + Bewerben
   - **Nur Suchen:** Wohnungen suchen und speichern
   - **Nur Bewerben:** Auf gespeicherte Wohnungen bewerben

2. **Max. Bewerbungen (optional):**
   - Limit für Anzahl der Bewerbungen
   - Leer lassen für unbegrenzt

3. **Buttons:**
   - ▶️ **Bot starten:** Startet den Bot im gewählten Modus
   - ⏸️ **Pausieren:** Pausiert die aktuelle Ausführung
   - ▶️ **Fortsetzen:** Setzt pausierte Ausführung fort
   - ⏹️ **Stoppen:** Stoppt den Bot komplett

**Hinweis:** Die Bot-Ausgabe wird im Log-Bereich angezeigt (in Entwicklung).

---

### 📝 Bewerbungen

Übersicht aller Wohnungen aus der Datenbank:

**Tabelle mit:**
- Titel
- Adresse
- Bezirk
- Zimmer
- Fläche
- Miete
- Status (Nicht beworben / ✓ Erfolgreich / ✗ Fehlgeschlagen)
- Datum der Bewerbung

**Auto-Refresh:** Die Tabelle lädt beim Tab-Wechsel automatisch neu.

---

## 🔧 Technische Details

### Backend (web_api.py)

**Framework:** Flask 3.0+

**API-Endpunkte:**

```
GET  /api/user-data           - Benutzerdaten abrufen
POST /api/user-data           - Benutzerdaten speichern

GET  /api/filter-config       - Filter abrufen
POST /api/filter-config       - Filter speichern

GET  /api/bezirke             - Verfügbare Bezirke abrufen

POST /api/bot/start           - Bot starten
POST /api/bot/stop            - Bot stoppen
POST /api/bot/pause           - Bot pausieren
POST /api/bot/resume          - Bot fortsetzen
GET  /api/bot/status          - Bot-Status abrufen

GET  /api/statistics          - Statistiken + letzte Bewerbungen
GET  /api/applications/recent - Letzte Bewerbungen (mit Limit)
GET  /api/applications/all    - Alle Wohnungen
```

**CORS:** Aktiviert für Cross-Origin-Requests

**Port:** 5000

---

### Frontend (HTML/CSS/JavaScript)

**Technologien:**
- Vanilla JavaScript (kein Framework)
- CSS Grid & Flexbox
- Fetch API für HTTP-Requests

**Dateien:**
- `frontend/index.html` - Hauptseite
- `frontend/style.css` - Styles
- `frontend/app.js` - JavaScript-Logik

**Features:**
- Single-Page-Application (SPA)
- Tab-Navigation
- Echtzeit-Status-Updates (Polling alle 2 Sekunden)
- Responsive Design
- Benachrichtigungen (Erfolg/Fehler/Warnung)

---

## 🐛 Troubleshooting

### Problem: "Connection refused" beim Start

**Ursache:** Web-Server läuft nicht.

**Lösung:**
```bash
python web_api.py
```

---

### Problem: "CORS-Fehler" in der Browser-Konsole

**Ursache:** Flask-CORS nicht installiert.

**Lösung:**
```bash
pip install flask-cors
```

---

### Problem: "Module not found: flask"

**Ursache:** Dependencies nicht installiert.

**Lösung:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: Benutzerdaten werden nicht geladen

**Ursache:** `user_data.json` existiert nicht.

**Lösung:**
```bash
python main.py --setup
```

---

### Problem: Bot startet nicht über Frontend

**Ursache:** Prüfen Sie die Browser-Konsole und `web_api.py` Logs.

**Lösung:**
1. Öffnen Sie die Browser-Konsole (F12)
2. Prüfen Sie auf Fehler
3. Prüfen Sie Terminal-Output von `web_api.py`

---

## 🎨 Anpassungen

### Theme ändern

Bearbeiten Sie `frontend/style.css` und passen Sie die CSS-Variablen an:

```css
:root {
    --primary-color: #2563eb;    /* Hauptfarbe */
    --success-color: #10b981;    /* Erfolgsfarbe */
    --danger-color: #ef4444;     /* Fehlerfarbe */
    /* ... */
}
```

---

### Port ändern

Bearbeiten Sie `web_api.py` (letzte Zeile):

```python
app.run(host='0.0.0.0', port=8080, debug=True)  # Port von 5000 auf 8080 ändern
```

Und `frontend/app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8080/api';  // Port anpassen
```

---

## 🔒 Sicherheitshinweise

- ⚠️ **Das Frontend ist NICHT für den öffentlichen Zugriff gedacht!**
- Nur für lokale Nutzung (localhost)
- Keine Authentifizierung implementiert
- Sensible Daten (user_data.json) sind über API zugänglich
- **Nicht im Internet verfügbar machen!**

---

## 📈 Zukünftige Features (TODO)

- [ ] Live-Log-Output im Frontend
- [ ] WebSocket-Verbindung für Echtzeit-Updates
- [ ] Authentifizierung (Login)
- [ ] Dunkler Modus
- [ ] Export-Funktionen (CSV, PDF)
- [ ] Filter-Presets speichern
- [ ] Wohnungen favorisieren
- [ ] Push-Benachrichtigungen

---

## 📄 Lizenz

Dieses Frontend ist Teil des Gewobag-Bot-Projekts und für den privaten Gebrauch bestimmt.

---

**Viel Erfolg bei der Wohnungssuche! 🏠✨**
