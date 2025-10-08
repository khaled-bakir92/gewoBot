# Anti-Detection Features - Gewobag Bot

Der Bot wurde mit mehreren Anti-Detection-Maßnahmen ausgestattet, um wie ein echter Nutzer zu wirken und Blockierungen zu vermeiden.

## 🛡️ Implementierte Features

### 1. **Zufällige User-Agents**
- 12 verschiedene realistische User-Agent-Strings
- Abwechselnd: Chrome, Firefox, Safari, Edge
- Verschiedene Betriebssysteme: Windows, macOS
- Bei jedem Request wird ein zufälliger User-Agent verwendet

### 2. **Zufällige Request-Header**
Jeder Request verwendet:
- **Accept-Language**: Zufällige deutsche/englische Kombinationen
- **Referer**: Simuliert Traffic von Google (`google.de`, `google.com`)
- **DNT (Do Not Track)**: Wie bei echten Browsern
- **Sec-Fetch-*** Header: Realistische Browser-Security-Header
- **Cache-Control**: Verhindert verdächtige Cache-Muster

### 3. **Zufällige Verzögerungen**
```python
# Zwischen Seitenanfragen: 2-7 Sekunden (menschliches Verhalten)
random_delay(min_seconds=2.0, max_seconds=7.0)
```

- **Zwischen Seiten**: 2-7 Sekunden zufällige Pause
- **Bei Retries**: 5-15 Sekunden zufällige Wartezeit
- Logging zeigt exakte Pausendauer

### 4. **Intelligentes Retry-Handling**

#### HTTP 403 / 429 (Rate Limiting)
- Automatisch 3 Retry-Versuche
- Zufällige Wartezeit: 5-15 Sekunden
- Exponentielles Backoff-Verhalten

#### Timeout / Connection Error
- Automatisch 3 Retry-Versuche
- Detailliertes Logging aller Fehler
- Graceful Degradation (überspringt fehlerhafte Seiten)

### 5. **Erweiterte Logging-Ausgabe**

Alle wichtigen Events werden geloggt:
```
⏸️  Pausiere 4.23 Sekunden (Anti-Detection)...
🌐 Lade Seite: https://...
✅ Seite erfolgreich geladen (Status: 200)
⚠️  HTTP 429 - Retry 1/3 in 8.5s...
📊 Seite 2: 15 Wohnungen gefunden
```

Emoji-Symbole für schnelle Übersicht:
- 🌐 = Request gestartet
- ✅ = Erfolgreich
- ⚠️ = Warnung / Retry
- ❌ = Fehler
- ⏸️ = Pause
- 📄 = Seite laden
- 📊 = Ergebnis
- 📚 = Paginierung

## 📋 Konfiguration

### Anpassbare Parameter

```python
# In gewobag-bot.py

# Retry-Versuche
MAX_RETRIES = 3

# Wartezeit bei Retry (Sekunden)
RETRY_DELAY_MIN = 5
RETRY_DELAY_MAX = 15

# Request-Timeout (Sekunden)
REQUEST_TIMEOUT = 30
```

### Delays anpassen

```python
# In fetch_all_pages()
random_delay(min_seconds=2.0, max_seconds=7.0)

# Für noch vorsichtigeres Verhalten:
random_delay(min_seconds=5.0, max_seconds=12.0)
```

## 🚀 Verwendung

### Basis-Version (requests + BeautifulSoup)

```bash
# Standard-Ausführung
python gewobag-bot.py

# Mit aktiviertem Debug-Logging
# (zeigt User-Agent für jeden Request)
```

Debug-Modus aktivieren (in Code):
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Playwright-Version (Optional, maximale Anti-Detection)

Die Playwright-Version simuliert einen echten Browser:

```bash
# Installation
pip install playwright
playwright install chromium

# Ausführung
python gewobag-bot-playwright.py
```

**Playwright-Features:**
- ✅ Echter Browser-Fingerprint
- ✅ JavaScript-Rendering
- ✅ Scroll-Simulation (mehrere kleine Scrolls)
- ✅ Mausbewegungen
- ✅ Lazy-Loading-Unterstützung
- ✅ Realistisches Timing

## 📊 Performance

### Geschwindigkeit
- **Ohne Anti-Detection**: ~1-2 Sekunden pro Seite
- **Mit Anti-Detection**: ~4-9 Sekunden pro Seite (sicherer!)

### Beispiel (5 Seiten)
```
Ohne Anti-Detection: 5-10 Sekunden
Mit Anti-Detection:  20-45 Sekunden
```

**Trade-off**: Längere Laufzeit, aber deutlich geringeres Blockierungs-Risiko

## 🔍 Monitoring

### Log-Datei prüfen
```bash
tail -f gewobag-bot.log
```

### Typischer erfolgreicher Durchlauf
```
🌐 Lade Seite: https://www.gewobag.de/...
✅ Seite erfolgreich geladen (Status: 200)
📊 Seite 1: 20 Wohnungen gefunden
📚 Paginierung erkannt: 3 Seiten insgesamt
⏸️  Pausiere 5.12 Sekunden (Anti-Detection)...
🌐 Lade Seite: https://www.gewobag.de/.../page/2/...
✅ Seite erfolgreich geladen (Status: 200)
📊 Seite 2: 18 Wohnungen gefunden
⏸️  Pausiere 3.87 Sekunden (Anti-Detection)...
...
✅ Alle 3 Seiten erfolgreich geladen - insgesamt 56 Wohnungen gefunden
```

### Bei Problemen (429/403)
```
🌐 Lade Seite: https://...
⚠️  HTTP 429 - Retry 1/3 in 8.5s...
⏸️  Pausiere 8.50 Sekunden...
🌐 Lade Seite: https://...
✅ Seite erfolgreich geladen (Status: 200)
```

## 🎯 Best Practices

### 1. **Nicht zu häufig laufen lassen**
```bash
# ❌ Schlecht: Jede Minute
*/1 * * * * python gewobag-bot.py

# ✅ Gut: Alle 2 Stunden
0 */2 * * * python gewobag-bot.py
```

### 2. **Scheduler-Intervall anpassen**
```python
# In gewobag-bot.py
# ❌ Zu aggressiv
run_scheduler(interval_minutes=5)

# ✅ Empfohlen
run_scheduler(interval_minutes=60)  # 1 Stunde
run_scheduler(interval_minutes=120) # 2 Stunden
```

### 3. **Logging-Level anpassen**

Produktion (weniger Output):
```python
logging.basicConfig(level=logging.INFO, ...)
```

Development (detailliert):
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### 4. **Bei wiederholten 403/429**

Falls du trotz Anti-Detection blockiert wirst:

1. **Delays erhöhen**:
   ```python
   random_delay(min_seconds=10.0, max_seconds=20.0)
   ```

2. **Retry-Delays erhöhen**:
   ```python
   RETRY_DELAY_MIN = 30  # 30 Sekunden
   RETRY_DELAY_MAX = 60  # 1 Minute
   ```

3. **Zu Playwright wechseln** (echter Browser)

## 🔧 Fehlerbehebung

### Problem: Zu langsam
```python
# Delays reduzieren (VORSICHT: höheres Blockierungs-Risiko!)
random_delay(min_seconds=1.0, max_seconds=3.0)
```

### Problem: Immer noch geblockt
1. Zu Playwright-Version wechseln
2. VPN/Proxy verwenden (extern)
3. Längere Pausen zwischen Runs

### Problem: Keine Wohnungen gefunden
- Prüfe Log-Datei auf HTTP-Fehler
- Teste URL manuell im Browser
- Website-Struktur könnte geändert worden sein

## 📝 Changelog

### Version 2.0 - Anti-Detection Update
- ✅ Zufällige User-Agents (12 Varianten)
- ✅ Zufällige Accept-Language Header
- ✅ Referer-Header (Google-Simulation)
- ✅ Zufällige Delays (2-7 Sekunden)
- ✅ Retry-Logik (403/429/Timeout)
- ✅ Erweiterte Logging-Ausgabe
- ✅ Playwright-Version (optional)

### Version 1.0 - Initial
- Basis-Scraping
- Paginierung
- SQLite-Speicherung
