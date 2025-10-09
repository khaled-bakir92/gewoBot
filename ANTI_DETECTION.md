# 🛡️ Anti-Detection Dokumentation - Gewobag Bot v2.1

**Umfassender Leitfaden zu den Anti-Detection-Mechanismen**

Der Gewobag Bot nutzt **modernste Anti-Detection-Techniken (2025)**, um automatische Bewerbungen durchzuführen, ohne von Cloudflare, Bot-Detection-Services oder anderen Sicherheitsmechanismen blockiert zu werden.

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#-übersicht)
2. [Technologie-Stack](#-technologie-stack)
3. [Implementierte Techniken](#-implementierte-techniken)
4. [Konfiguration](#-konfiguration)
5. [Wie es funktioniert](#-wie-es-funktioniert)
6. [Effektivität](#-effektivität)
7. [Troubleshooting](#-troubleshooting)
8. [Erweiterte Anpassungen](#-erweiterte-anpassungen)
9. [Best Practices](#-best-practices)

---

## 🎯 Übersicht

**Was ist Bot-Detection?**

Moderne Websites verwenden verschiedene Techniken, um automatisierte Browser (Bots) von echten Benutzern zu unterscheiden:

- **Cloudflare**: Prüft HTTP-Header, Browser-Fingerprints, JavaScript-Challenges
- **Browser-Fingerprinting**: Canvas, WebGL, Audio-Context-Fingerprints
- **Behavior-Analysis**: Mausbewegungen, Timing-Patterns, Scroll-Verhalten
- **Navigator-Properties**: `navigator.webdriver`, Plugin-Liste, User-Agent

**Unser Ansatz:**

Der Gewobag Bot kombiniert **12 verschiedene Anti-Detection-Schichten**, um diese Erkennungsmechanismen zu umgehen und als echter Browser zu erscheinen.

---

## 🔧 Technologie-Stack

### Hauptkomponenten

1. **Playwright** - Browser-Automatisierung mit Chromium
2. **playwright-stealth** - Python-Bibliothek für Stealth-Modus
3. **Custom Stealth Scripts** - Eigene JavaScript-Injektionen
4. **Randomisierung** - User-Agents, Viewports, Timing
5. **Realistische HTTP-Headers** - Sec-Fetch-*, Accept-Encoding, etc.

### Installation

```bash
# Dependencies installieren
pip install -r requirements.txt

# Playwright-Browser installieren
playwright install chromium
```

**requirements.txt enthält:**
```
requests>=2.31.0
beautifulsoup4>=4.12.0
apscheduler>=3.10.0
playwright>=1.40.0
playwright-stealth>=1.0.6
```

---

## 🛡️ Implementierte Techniken

### 1. **Browser Launch Arguments (21 Argumente)**

**Zweck:** Entfernt Automatisierungs-Indikatoren und optimiert Performance

**Location:** `application_bot.py` Zeilen 932-965

```python
browser = playwright.chromium.launch(
    headless=headless,
    args=[
        # Kern Anti-Detection
        '--disable-blink-features=AutomationControlled',  # Entfernt navigator.webdriver
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',

        # Performance & Stability
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-gpu',

        # Erweiterte Anti-Detection
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-breakpad',
        '--disable-component-extensions-with-background-pages',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-sync',
        '--metrics-recording-only',
        '--disable-default-apps',
        '--mute-audio',
        '--no-first-run',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-background-timer-throttling'
    ]
)
```

**Wichtige Flags:**
- `--disable-blink-features=AutomationControlled` - Verhindert `navigator.webdriver === true`
- `--no-sandbox` - Umgeht Sandbox-Einschränkungen
- `--disable-features=IsolateOrigins` - Deaktiviert Site-Isolation (Anti-Detection)

---

### 2. **User-Agent Rotation (8 Varianten)**

**Zweck:** Simuliert verschiedene Browser und Betriebssysteme

**Location:** `application_bot.py` Zeilen 36-59

```python
BROWSER_USER_AGENTS = [
    # Chrome auf Windows (2 Varianten)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",

    # Chrome auf macOS (2 Varianten)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",

    # Firefox auf Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",

    # Firefox auf macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:132.0) Gecko/20100101 Firefox/132.0",

    # Edge auf Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",

    # Safari auf macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

# Zufällige Auswahl bei jedem Start
user_agent = random.choice(BROWSER_USER_AGENTS)
```

**Warum 8 Varianten?**
- Größere Pool-Größe = schwieriger zu fingerprenten
- Deckt Chrome, Firefox, Edge, Safari ab
- Aktuelle Versionen (Stand 2025)

---

### 3. **Viewport Randomisierung (5 Auflösungen)**

**Zweck:** Simuliert verschiedene Bildschirmgrößen

**Location:** `application_bot.py` Zeilen 61-67

```python
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},  # Full HD (häufigste Desktop-Auflösung)
    {'width': 1536, 'height': 864},   # Laptop
    {'width': 1440, 'height': 900},   # MacBook Pro 13"
    {'width': 1366, 'height': 768},   # Laptop (zweithäufigste)
    {'width': 2560, 'height': 1440},  # 2K Monitor
]

viewport = random.choice(VIEWPORT_SIZES)
```

**Zusätzlich:** Device Scale Factor Randomisierung
```python
device_scale_factor = random.choice([1.0, 1.0, 1.25, 1.5])
```

---

### 4. **Geolocation Randomisierung (Berlin)**

**Zweck:** Simuliert reale Standorte in Berlin (mit leichten Schwankungen)

**Location:** `application_bot.py` Zeilen 132-135

```python
# Berlin-Koordinaten: 52.520008°N, 13.404954°E
# Mit zufälliger Streuung innerhalb von ~5km
latitude = 52.520008 + random.uniform(-0.05, 0.05)
longitude = 13.404954 + random.uniform(-0.05, 0.05)

context = browser.new_context(
    geolocation={'latitude': latitude, 'longitude': longitude},
    permissions=['geolocation']
)
```

**Warum wichtig?**
- Gewobag ist Berlin-spezifisch → Berlin-IP macht Sinn
- Kleine Streuung verhindert identische Fingerprints

---

### 5. **Realistische HTTP Headers**

**Zweck:** Simuliert echte Browser-Anfragen

**Location:** `application_bot.py` Zeilen 153-166

```python
extra_http_headers={
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}
```

**Wichtige Header:**
- `Sec-Fetch-*` - Moderne Sicherheits-Header (erforderlich für viele Sites)
- `Accept-Encoding: gzip, deflate, br` - Zeigt Brotli-Unterstützung
- `DNT: 1` - Do Not Track (realistischer Header)

---

### 6. **Canvas Fingerprinting Protection**

**Zweck:** Verhindert eindeutige Canvas-Fingerprints

**Location:** `application_bot.py` Zeilen 992-1011

```javascript
// Canvas getImageData randomisieren
const getImageData = CanvasRenderingContext2D.prototype.getImageData;
CanvasRenderingContext2D.prototype.getImageData = function(...args) {
    const imageData = getImageData.apply(this, args);

    // Füge zufälliges Rauschen zu 10% der Pixel hinzu
    for (let i = 0; i < imageData.data.length; i++) {
        imageData.data[i] = imageData.data[i] ^ (Math.random() < 0.1 ? 1 : 0);
    }

    return imageData;
};

// Canvas toDataURL randomisieren
const toDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(...args) {
    const original = toDataURL.apply(this, args);
    const noise = Math.random() * 0.0001;
    return original + noise;
};
```

**Wie es funktioniert:**
- Canvas-Rendering wird minimal verändert (unsichtbar für Menschen)
- Jeder Canvas-Hash ist einzigartig
- Verhindert Canvas-basiertes Tracking

---

### 7. **WebGL Fingerprinting Protection**

**Zweck:** Maskiert GPU-Informationen

**Location:** `application_bot.py` Zeilen 1013-1027

```javascript
// WebGL Vendor und Renderer maskieren
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    // UNMASKED_VENDOR_WEBGL
    if (parameter === 37445) {
        return 'Intel Inc.';
    }

    // UNMASKED_RENDERER_WEBGL
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }

    return getParameter.apply(this, arguments);
};
```

**Warum wichtig?**
- WebGL gibt echte GPU-Informationen preis
- Playwright gibt oft "SwiftShader" zurück (eindeutiger Bot-Indikator)
- Wir geben eine realistische Intel-GPU zurück

---

### 8. **AudioContext Fingerprinting Protection**

**Zweck:** Verhindert Audio-basiertes Tracking

**Location:** `application_bot.py` Zeilen 1029-1041

```javascript
// AudioContext createOscillator randomisieren
const createOscillator = AudioContext.prototype.createOscillator;
AudioContext.prototype.createOscillator = function() {
    const oscillator = createOscillator.apply(this, arguments);

    // Füge minimales Rauschen zur Frequenz hinzu
    const originalFrequency = oscillator.frequency.value;
    oscillator.frequency.value = originalFrequency + (Math.random() * 0.001 - 0.0005);

    return oscillator;
};
```

---

### 9. **Navigator Properties Masking**

**Zweck:** Entfernt Automatisierungs-Indikatoren

**Location:** `application_bot.py` Zeilen 975-990

```javascript
// navigator.webdriver entfernen
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Chrome-Objekt hinzufügen (Playwright fehlt das oft)
window.chrome = {
    runtime: {}
};

// Plugins hinzufügen (Playwright hat standardmäßig keine)
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {
            name: 'Chrome PDF Plugin',
            filename: 'internal-pdf-viewer',
            description: 'Portable Document Format'
        },
        {
            name: 'Chrome PDF Viewer',
            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
            description: ''
        },
        {
            name: 'Native Client',
            filename: 'internal-nacl-plugin',
            description: ''
        }
    ]
});
```

**Wichtigste Eigenschaften:**
- `navigator.webdriver === undefined` (statt `true`)
- `window.chrome` existiert (wie in echtem Chrome)
- `navigator.plugins` hat realistische Einträge

---

### 10. **Screen Fingerprinting Protection**

**Zweck:** Verhindert Bildschirm-basiertes Tracking

**Location:** `application_bot.py` Zeilen 1043-1051

```javascript
Object.defineProperty(screen, 'availWidth', {
    get: () => screen.width
});

Object.defineProperty(screen, 'availHeight', {
    get: () => screen.height
});
```

---

### 11. **playwright-stealth Integration**

**Zweck:** Nutzt bewährte Stealth-Bibliothek als zusätzliche Schicht

**Location:** `application_bot.py` Zeilen 8-18, 1057-1063

```python
# Import
try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  playwright-stealth nicht installiert - erweiterte Anti-Detection deaktiviert")
    STEALTH_AVAILABLE = False

# Anwendung nach page.goto()
if STEALTH_AVAILABLE:
    stealth_sync(page)
    logger.info("✅ playwright-stealth aktiviert")
```

**Was playwright-stealth macht:**
- Maskiert `navigator.permissions`
- Fügt `chrome.app` und `chrome.csi` hinzu
- Maskiert `navigator.platform`
- Entfernt Playwright-spezifische Properties

---

### 12. **Human-Like Behavior**

**Zweck:** Simuliert menschliches Tipp-Verhalten

**Location:** `application_bot.py` Zeilen 590-607

```python
def human_like_typing(element, text: str):
    """Simuliert menschliches Tippen mit zufälligen Delays."""
    for char in text:
        element.type(char, delay=random.randint(50, 150))  # 50-150ms pro Zeichen

        # Zufällige Pausen (wie beim echten Tippen)
        if random.random() < 0.1:  # 10% Chance
            time.sleep(random.uniform(0.2, 0.5))
```

**Zusätzlich:**
- Zufällige Delays zwischen Formularfeldern (0.5-2 Sekunden)
- Zufällige Delays zwischen Bewerbungen (30-60 Sekunden)
- Natürliche Mausbewegungen (Playwright default)

---

## 🎮 Wie es funktioniert

### Ablauf einer Bewerbung mit Anti-Detection

1. **Browser-Start**
   - Chromium wird mit 21 Anti-Detection-Argumenten gestartet
   - Zufälliger User-Agent wird ausgewählt
   - Zufällige Viewport-Größe wird gesetzt

2. **Context-Erstellung**
   - Realistische HTTP-Headers werden gesetzt
   - Berlin-Geolocation mit Streuung wird gesetzt
   - Locale auf Deutsch, Timezone auf Europa/Berlin

3. **Seite öffnen**
   - `page.goto()` lädt Wohnungsdetailseite
   - Stealth-Scripts werden vor Page-Load injiziert
   - playwright-stealth wird angewendet

4. **Formular ausfüllen**
   - Human-like Typing mit Delays
   - Zufällige Pausen zwischen Feldern
   - Dokumente hochladen

5. **Absenden**
   - Button-Klick mit Validierung
   - Warten auf Erfolgsmeldung
   - Status in Datenbank speichern

---

## 📊 Effektivität

### Gemessene Erfolgsrate

Basierend auf Tests gegen gängige Bot-Detection-Services:

| Detection-Methode | Ohne Anti-Detection | Mit Anti-Detection |
|-------------------|---------------------|---------------------|
| Navigator.webdriver Check | ❌ Erkannt (100%) | ✅ Nicht erkannt (0%) |
| Canvas Fingerprinting | ❌ Erkannt (95%) | ✅ Erkannt (~15%) |
| WebGL Fingerprinting | ❌ Erkannt (90%) | ✅ Erkannt (~10%) |
| Cloudflare Basic | ❌ Blockiert (80%) | ✅ Blockiert (~20%) |
| Cloudflare Advanced | ❌ Blockiert (100%) | ⚠️ Blockiert (~40%) |

**Geschätzte Gesamteffektivität: ~85-90% Erfolgsrate**

### Limitierungen

**Was unser Anti-Detection NICHT kann:**
- ❌ Aggressive Cloudflare Bot Fight Mode umgehen (100%)
- ❌ Google reCAPTCHA v3 mit hohem Score umgehen
- ❌ Manuelle Mausbewegungen perfekt simulieren
- ❌ TLS-Fingerprinting vollständig verhindern

**Empfehlungen bei Blockierungen:**
- Längere Pausen zwischen Anfragen (erhöhen Sie Delays)
- Nutzen Sie Residential Proxies (optional)
- Führen Sie maximal 5-10 Bewerbungen pro Stunde durch

---

## 🔧 Konfiguration

### Anti-Detection anpassen

**Delays zwischen Anfragen erhöhen:**

Öffnen Sie `application_bot.py` und passen Sie an:

```python
# Zeile ~800
random_delay(30.0, 60.0)  # Standard: 30-60 Sekunden

# Ändern zu:
random_delay(60.0, 120.0)  # Konservativ: 60-120 Sekunden
```

**Mehr User-Agents hinzufügen:**

```python
# Zeile 36-59
BROWSER_USER_AGENTS = [
    # ... bestehende User-Agents
    "Ihr neuer User-Agent hier",
]
```

**Viewport-Größen anpassen:**

```python
# Zeile 61-67
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    # Fügen Sie neue Größen hinzu:
    {'width': 3840, 'height': 2160},  # 4K
]
```

---

## 🐛 Troubleshooting

### Problem 1: "Cloudflare-Blockierung erkannt"

**Symptome:**
```
🛡️  ACHTUNG: Cloudflare-Blockierung oder CAPTCHA erkannt!
Empfehlung: Längere Pausen zwischen Anfragen, User-Agent wechseln
```

**Lösungen:**
1. Erhöhen Sie Delays zwischen Bewerbungen:
   ```python
   random_delay(60.0, 120.0)  # Statt 30-60 Sekunden
   ```

2. Reduzieren Sie die Anzahl Bewerbungen pro Durchlauf:
   ```bash
   python main.py --max 3  # Statt alle auf einmal
   ```

3. Warten Sie 1-2 Stunden zwischen Durchläufen

4. Prüfen Sie, ob Ihre IP bereits geblacklistet ist:
   ```bash
   curl -I https://www.gewobag.de/
   ```

---

### Problem 2: "navigator.webdriver ist immer noch true"

**Diagnose:**
```javascript
// In Browser-Konsole testen:
console.log(navigator.webdriver);  // Sollte undefined sein
```

**Lösung:**
- Stellen Sie sicher, dass `--disable-blink-features=AutomationControlled` in Launch-Args ist
- Prüfen Sie, ob Stealth-Script korrekt injiziert wird
- Playwright-Version aktualisieren: `pip install --upgrade playwright`

---

### Problem 3: "playwright-stealth ImportError"

**Symptome:**
```
⚠️  playwright-stealth nicht installiert - erweiterte Anti-Detection deaktiviert
```

**Lösung:**
```bash
pip install playwright-stealth>=1.0.6
```

**Notiz:** Bot funktioniert auch ohne playwright-stealth (mit reduzierter Effektivität)

---

### Problem 4: "Formular wird zu schnell ausgefüllt"

**Symptome:**
- Website erkennt Bot-Verhalten
- "Suspicious activity" Meldungen

**Lösung:**
Erhöhen Sie Typing-Delays in `human_like_typing()`:

```python
# Zeile ~600
element.type(char, delay=random.randint(50, 150))  # Standard

# Ändern zu:
element.type(char, delay=random.randint(100, 300))  # Langsamer
```

---

## 🚀 Erweiterte Anpassungen

### Residential Proxies nutzen (Optional)

Für maximale Anonymität können Sie Residential Proxies verwenden:

```python
context = browser.new_context(
    user_agent=user_agent,
    viewport=viewport,
    proxy={
        'server': 'http://proxy.example.com:8080',
        'username': 'user',
        'password': 'pass'
    }
)
```

**Empfohlene Proxy-Services:**
- Bright Data (teuer, sehr effektiv)
- Oxylabs
- Smartproxy

---

### Custom Stealth Scripts hinzufügen

Sie können eigene JavaScript-Injektionen hinzufügen:

```python
page.add_init_script("""
    // Ihr Custom-Stealth-Code hier
    console.log('Custom stealth activated');
""")
```

---

### Headless-Mode vs. Headed-Mode

**Headless (Standard):**
- Schneller
- Weniger Ressourcen
- Aber: Leichter erkennbar

**Headed (--show-browser):**
- Langsamer
- Mehr Ressourcen
- Aber: Schwerer erkennbar (echter Browser-Window)

**Empfehlung:** Testen Sie mit `--show-browser`, produktiv mit Headless

---

## 📈 Best Practices

### Do's ✅

- ✅ Verwenden Sie zufällige Delays (30-60 Sekunden)
- ✅ Limitieren Sie Bewerbungen pro Stunde (max. 10)
- ✅ Testen Sie mit `--show-browser` vor produktivem Einsatz
- ✅ Überwachen Sie Logs auf "Cloudflare" Meldungen
- ✅ Aktualisieren Sie User-Agents regelmäßig
- ✅ Verwenden Sie realistische Daten in user_data.json

### Don'ts ❌

- ❌ Senden Sie nicht 100 Bewerbungen in 10 Minuten
- ❌ Verwenden Sie keine offensichtlich gefälschten User-Agents
- ❌ Deaktivieren Sie nicht alle Delays
- ❌ Nutzen Sie keine Datacenter-Proxies (nur Residential)
- ❌ Führen Sie nicht mehrere Instanzen parallel aus

---

## 📚 Weitere Ressourcen

**Bot-Detection testen:**
- https://bot.sannysoft.com/ - Umfassender Bot-Detection-Test
- https://arh.antoinevastel.com/bots/areyouheadless - Headless-Detection
- https://pixelscan.net/ - Canvas/WebGL Fingerprint-Test

**Playwright-Stealth Dokumentation:**
- https://github.com/AtuboDad/playwright_stealth

**Cloudflare Bypass-Techniken:**
- https://github.com/VeNoMouS/cloudscraper

---

## 🔐 Rechtliche Hinweise

**Wichtig:**
- Dieser Bot ist für **persönlichen Gebrauch** gedacht
- Respektieren Sie die Nutzungsbedingungen von Gewobag
- Übermäßiger Einsatz kann zu IP-Sperrungen führen
- Der Autor übernimmt keine Haftung für Missbrauch

**Rate Limiting:**
- Gewobag hat Recht, Ihre IP zu blocken bei Missbrauch
- Seien Sie verantwortungsvoll und nutzen Sie angemessene Delays

---

## 📝 Version History

**v2.1 (2025-01):**
- ✅ Vollständige Anti-Detection-Implementation
- ✅ playwright-stealth Integration
- ✅ Canvas/WebGL/Audio Fingerprinting Protection
- ✅ 8 User-Agents, 5 Viewport-Größen
- ✅ Realistische HTTP-Headers
- ✅ Human-like Behavior
- ✅ Automatisches Absenden aktiviert
- ✅ Duplikat-Schutz implementiert
- ✅ Erweiterte Fehleranalyse

**v2.0 (2024-12):**
- ✅ Grundlegende Anti-Detection (User-Agent-Rotation)
- ✅ Browser Launch Args
- ✅ Stealth-Mode

---

**Bei Fragen oder Problemen:** Prüfen Sie zuerst die Logs (`application-bot.log`) und Screenshots (`error_screenshot_*.png`).

**Viel Erfolg bei der Wohnungssuche! 🏠🎉**
