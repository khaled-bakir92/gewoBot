# 🏠 Gewobag Bot - Multi-User Guide v2.1 👥

**Automatische Wohnungssuche und Bewerbung für mehrere Nutzer**

---

## ✨ Neu: Multi-User-Modus

Der Bot unterstützt jetzt **mehrere Nutzer gleichzeitig** (nacheinander)! Jeder User hat:

✅ **Eigene Konfiguration** - Separate `user_data.json` und `filter_config.json`
✅ **Separater Browser-Fingerprint** - User-Agent, Viewport, GPS-Position
✅ **Isolierte Sessions** - Eigene Cookies, LocalStorage, Cache
✅ **Eigene Logs** - Separate Log-Dateien pro User
✅ **Unabhängige Bewerbungen** - Mehrere User können sich auf dieselbe Wohnung bewerben

---

## 🚀 Schnellstart

### 1. Initiale Konfiguration
```bash
python main_multiuser.py --setup
```

### 2. User erstellen
```bash
python main_multiuser.py --create-user user1
python main_multiuser.py --create-user user2
python main_multiuser.py --create-user user3
```

### 3. Konfiguration bearbeiten
Bearbeiten Sie für jeden User:
- `users/user1/user_data.json` (Persönliche Daten)
- `users/user1/filter_config.json` (Suchfilter)

### 4. Bot starten

**Für EINEN User:**
```bash
python main_multiuser.py --user user1
```

**Für ALLE User (nacheinander):**
```bash
python main_multiuser.py --all-users
```

---

## 📖 Verwendung

### User-Management

```bash
# User erstellen
python main_multiuser.py --create-user maria

# Alle User auflisten
python main_multiuser.py --list-users

# User-Info anzeigen
python main_multiuser.py --info maria
```

### Bot-Ausführung

**Einzelner User:**
```bash
# Vollautomatisch (Standard): Suchen + Bewerben
python main_multiuser.py --user user1

# Nur Wohnungen suchen
python main_multiuser.py --user user1 --scrape

# Nur bewerben
python main_multiuser.py --user user1 --apply

# Mit sichtbarem Browser (Debugging)
python main_multiuser.py --user user1 --show-browser

# Maximal 3 Bewerbungen
python main_multiuser.py --user user1 --max 3
```

**Alle User nacheinander:**
```bash
# Vollautomatisch für alle User
python main_multiuser.py --all-users

# Nur suchen für alle User
python main_multiuser.py --all-users --scrape

# Nur bewerben für alle User
python main_multiuser.py --all-users --apply
```

---

## 📁 Projektstruktur (Multi-User)

```
bot new/
├── main_multiuser.py                    # Multi-User CLI
├── user_manager.py                      # User-Verwaltung
├── fingerprint_pool.py                  # Browser-Fingerprinting
├── user_logger.py                       # User-spezifisches Logging
├── gewobag_bot_multiuser.py             # Multi-User Scraper
├── application_bot_multiuser.py         # Multi-User Application Bot
├── migrate_database.py                  # DB-Migration (user_id)
│
├── users/                               # User-Daten
│   ├── user1/
│   │   ├── user_data.json               # Persönliche Daten
│   │   ├── filter_config.json           # Suchfilter
│   │   ├── fingerprint.json             # Browser-Fingerprint
│   │   ├── cookies/                     # Browser-Cookies/Sessions
│   │   │   └── browser_state.json       # Persistente Browser-Session
│   │   └── logs/
│   │       ├── main.log
│   │       ├── scraping.log
│   │       └── applications.log
│   ├── user2/
│   │   └── ...
│   └── user3/
│       └── ...
│
├── gewobag_wohnungen.db                 # Datenbank (mit user_id)
└── gewobag-multiuser.log                # Haupt-Log
```

---

## 🎯 Wie funktioniert Multi-User?

### 1. Separater Fingerprint pro User

Jeder User erhält:
- **Eigenen User-Agent** (aus Pool von 20 verschiedenen)
- **Eigene Viewport-Größe** (1440x900 – 1920x1080)
- **Eigene Geo-Position** (±0.02° um Berlin)
- **Eigenes Cookie-/Session-Verzeichnis**

**Beispiel:**
```bash
$ python fingerprint_pool.py show user1

Browser Fingerprint: user1
🌐 User-Agent: Mozilla/5.0 (Windows NT 10.0) ... Chrome/120.0
📺 Viewport: 1536x864
📍 Location: 52.539651, 13.410566 (Berlin)
💻 Platform: Win32
⚙️  CPU Cores: 8

$ python fingerprint_pool.py show user2

Browser Fingerprint: user2
🌐 User-Agent: Mozilla/5.0 (Macintosh) ... Safari/605.1.15
📺 Viewport: 2560x1440
📍 Location: 52.510614, 13.407194 (Berlin)
💻 Platform: MacIntel
⚙️  CPU Cores: 4
```

**Unterschiedliche Fingerprints!** ✅

### 2. Datenbank mit `user_id`

Die Datenbank speichert, welcher User sich auf welche Wohnung beworben hat:

```sql
SELECT titel, user_id, applied, application_status
FROM wohnungen
WHERE applied = 1;

-- Beispiel-Ergebnis:
-- "3-Zi-Wohnung Friedrichshain" | user1 | 1 | success
-- "3-Zi-Wohnung Friedrichshain" | user2 | 1 | success
-- "2-Zi-Wohnung Mitte"          | user1 | 1 | success
```

**Mehrere User können sich auf dieselbe Wohnung bewerben!** ✅

### 3. Sequentielle Ausführung

User agieren **nacheinander**, nicht parallel:
- User1 → Suchen → Bewerben
- 60-120 Sekunden Pause
- User2 → Suchen → Bewerben
- 60-120 Sekunden Pause
- User3 → Suchen → Bewerben

**Kein gleichzeitiger Zugriff** → Vermeidet Erkennung

---

## 🔐 Anti-Detection pro User

Jeder User hat:
- ✅ Eigenen User-Agent
- ✅ Eigene Viewport-Größe
- ✅ Eigene GPS-Koordinaten (Berlin ±2km)
- ✅ Eigene Browser-Session (Cookies, LocalStorage)
- ✅ Eigene Canvas-/WebGL-Fingerprints
- ✅ Eigene Hardware-Specs (CPU, RAM)
- ✅ Zufällige Delays zwischen Aktionen (30-60s)

→ **Jeder User erscheint wie ein echter Browser!**

---

## 🛡️ Duplikat-Schutz

Der Bot verhindert, dass ein User sich **zweimal auf dieselbe Wohnung** bewirbt:

```python
# Vor jeder Bewerbung:
is_already_applied_by_user(link, username)

# Falls bereits beworben:
⚠️  DUPLIKAT ERKANNT: User 'user1' hat sich bereits beworben!
❌ ABBRUCH: Überspringe...
```

**ABER:** Verschiedene User **können** sich auf dieselbe Wohnung bewerben!

---

## 📊 Datenbank-Abfragen

```bash
# Datenbank-Info anzeigen
python migrate_database.py info
```

**Nützliche SQL-Abfragen:**

```sql
-- Alle Bewerbungen eines Users
SELECT titel, bezirk, applied_ts, application_status
FROM wohnungen
WHERE user_id = 'user1' AND applied = 1
ORDER BY applied_ts DESC;

-- Statistik pro User
SELECT
    user_id,
    COUNT(*) as gesamt,
    SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as beworben,
    SUM(CASE WHEN application_status = 'success' THEN 1 ELSE 0 END) as erfolgreich
FROM wohnungen
GROUP BY user_id;

-- Wohnungen mit Bewerbungen von mehreren Usern
SELECT link, titel, GROUP_CONCAT(user_id) as users
FROM wohnungen
WHERE applied = 1
GROUP BY link
HAVING COUNT(DISTINCT user_id) > 1;
```

---

## 🔧 Erweiterte Konfiguration

### User-Daten pro User

**users/user1/user_data.json:**
```json
{
  "personal_info": {
    "anrede": "Herr",
    "vorname": "Max",
    "nachname": "Mustermann",
    "email": "max.mustermann@example.com",
    "telefon": "+49 123 456789"
  },
  "household": {
    "anzahl_personen": 1,
    "haushaltseinkommen": "3000"
  },
  "documents": {
    "personalausweis": "/pfad/zu/max_ausweis.pdf",
    "gehaltsnachweis_1": "/pfad/zu/max_gehalt1.pdf"
  },
  "nachricht": "Bewerbung von Max Mustermann..."
}
```

**users/user2/user_data.json:**
```json
{
  "personal_info": {
    "anrede": "Frau",
    "vorname": "Maria",
    "nachname": "Schmidt",
    "email": "maria.schmidt@example.com",
    "telefon": "+49 987 654321"
  },
  "household": {
    "anzahl_personen": 2,
    "haushaltseinkommen": "4500"
  },
  "documents": {
    "personalausweis": "/pfad/zu/maria_ausweis.pdf",
    "gehaltsnachweis_1": "/pfad/zu/maria_gehalt1.pdf"
  },
  "nachricht": "Bewerbung von Maria Schmidt..."
}
```

### Filter pro User

**users/user1/filter_config.json** (sucht 2-Zimmer):
```json
{
  "gewuenschte_bezirke": ["friedrichshain-kreuzberg", "mitte"],
  "gesamtmiete_von": "800",
  "gesamtmiete_bis": "1200",
  "zimmer_von": "2",
  "zimmer_bis": "2"
}
```

**users/user2/filter_config.json** (sucht 3-Zimmer):
```json
{
  "gewuenschte_bezirke": ["pankow-prenzlauer-berg", "charlottenburg-wilmersdorf"],
  "gesamtmiete_von": "1200",
  "gesamtmiete_bis": "1800",
  "zimmer_von": "3",
  "zimmer_bis": "3"
}
```

→ **Verschiedene Filter = verschiedene Wohnungen!**

---

## ⏰ Automatisierung mit Cron

**Alle 6 Stunden für alle User ausführen:**

```bash
# Crontab bearbeiten
crontab -e

# Eintrag hinzufügen:
0 */6 * * * cd /Users/khaled/Desktop/bot\ new && python main_multiuser.py --all-users >> /var/log/gewobag-cron.log 2>&1
```

---

## 🐛 Troubleshooting

### "User existiert nicht"
```bash
python main_multiuser.py --create-user <username>
```

### "Konfiguration ungültig"
```bash
python main_multiuser.py --info <username>
# Prüfen Sie die Fehler und bearbeiten Sie:
# users/<username>/user_data.json
```

### Fingerprint neu generieren
```bash
python fingerprint_pool.py regenerate <username>
```

### Logs anzeigen
```bash
# User-spezifische Logs
tail -f users/user1/logs/applications.log

# Haupt-Log
tail -f gewobag-multiuser.log
```

---

## 📈 Best Practices

1. **Unterschiedliche Namen verwenden** - Max, Maria, John, etc.
2. **Unterschiedliche E-Mails** - Jeder User sollte eigene E-Mail haben
3. **Unterschiedliche Filter** - Verschiedene Bezirke/Zimmeranzahlen
4. **Pausen einhalten** - Mindestens 60s zwischen Usern
5. **Logs überwachen** - Prüfen Sie regelmäßig die Logs
6. **Test mit --show-browser** - Testen Sie zuerst mit sichtbarem Browser

---

## 🆚 Single-User vs. Multi-User

### Single-User-Modus (alt):
```bash
python main.py --full
```
- Nur 1 User
- `user_data.json` im Root-Verzeichnis
- Kein User-spezifischer Fingerprint

### Multi-User-Modus (neu):
```bash
python main_multiuser.py --all-users
```
- Mehrere User
- `users/{username}/user_data.json`
- Eigener Fingerprint pro User
- Separate Sessions

→ **Multi-User-Modus ist DEUTLICH sicherer!**

---

## 📄 Weitere Dokumentation

- **CLAUDE.md** - Technische Entwickler-Dokumentation
- **README.md** - Single-User-Anleitung
- **DEPLOYMENT.md** - Docker-Deployment

---

**Viel Erfolg bei der Wohnungssuche! 🏠🎉**
