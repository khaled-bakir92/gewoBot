#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Application Bot - Automatisiert die Bewerbung auf Wohnungen
Verwendet Playwright für Browser-Automatisierung und füllt das Bewerbungsformular automatisch aus.
"""

import sqlite3
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

# Logging-Setup (MUSS vor allen Imports mit logging stehen)
logger = logging.getLogger(__name__)

# Anti-Detection: playwright-stealth
try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  playwright-stealth nicht installiert - erweiterte Anti-Detection deaktiviert")
    logger.warning("Installation: pip install playwright-stealth")
    STEALTH_AVAILABLE = False

# Konstanten
DB_NAME = "gewobag_wohnungen.db"
USER_DATA_FILE = "user_data.json"
FILTER_CONFIG_FILE = "filter_config.json"
APPLICATION_TIMEOUT = 60000  # 60 Sekunden für Formular-Operationen

# Anti-Detection: Erweiterte realistische User-Agents für 2025
BROWSER_USER_AGENTS = [
    # Chrome auf Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome auf macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Realistische Viewport-Größen (Auflösungen von echten Geräten)
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},  # Full HD
    {'width': 1536, 'height': 864},   # Laptop
    {'width': 1440, 'height': 900},   # MacBook
    {'width': 1366, 'height': 768},   # Laptop (häufig)
    {'width': 2560, 'height': 1440},  # 2K Monitor
]

# Retry-Konfiguration
MAX_APPLICATION_RETRIES = 2
RETRY_DELAY_MIN = 5
RETRY_DELAY_MAX = 15


def load_user_data() -> Optional[Dict]:
    """
    Lädt die persönlichen Daten aus der JSON-Datei.

    Returns:
        Dictionary mit Benutzerdaten oder None bei Fehler
    """
    user_data_path = Path(USER_DATA_FILE)

    if not user_data_path.exists():
        logger.error(f"❌ Benutzerdatei '{USER_DATA_FILE}' nicht gefunden!")
        logger.info("Bitte erstellen Sie die Datei mit Ihren persönlichen Daten.")
        return None

    try:
        with open(user_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info("✅ Benutzerdaten erfolgreich geladen")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"❌ Fehler beim Parsen der Benutzerdaten: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Benutzerdaten: {e}")
        return None


def load_filter_config() -> Dict[str, any]:
    """
    Lädt die Filter-Konfiguration aus der JSON-Konfigurationsdatei.

    Returns:
        Dictionary mit allen Filtern (bezirke, miete, fläche, zimmer, wbs)
    """
    config_path = Path(FILTER_CONFIG_FILE)

    default_config = {
        'gewuenschte_bezirke': [],
        'gesamtmiete_von': '',
        'gesamtmiete_bis': '',
        'gesamtflaeche_von': '',
        'gesamtflaeche_bis': '',
        'zimmer_von': '',
        'zimmer_bis': '',
        'wbs': ''
    }

    if not config_path.exists():
        logger.warning(f"⚠️  Konfigurationsdatei '{FILTER_CONFIG_FILE}' nicht gefunden - keine Filter aktiv")
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Filter aus Konfiguration extrahieren
        filter_config = {
            'gewuenschte_bezirke': config.get('gewuenschte_bezirke', []),
            'gesamtmiete_von': config.get('gesamtmiete_von', ''),
            'gesamtmiete_bis': config.get('gesamtmiete_bis', ''),
            'gesamtflaeche_von': config.get('gesamtflaeche_von', ''),
            'gesamtflaeche_bis': config.get('gesamtflaeche_bis', ''),
            'zimmer_von': config.get('zimmer_von', ''),
            'zimmer_bis': config.get('zimmer_bis', ''),
            'wbs': config.get('wbs', '').lower()  # Normalisieren zu lowercase
        }

        # Logging der aktiven Filter
        active_filters = []
        bezirke_gefiltert = [b for b in filter_config['gewuenschte_bezirke'] if b and b.strip()]
        if bezirke_gefiltert:
            active_filters.append(f"Bezirke: {', '.join(bezirke_gefiltert)}")
        if filter_config['gesamtmiete_von'] or filter_config['gesamtmiete_bis']:
            active_filters.append(f"Miete: {filter_config['gesamtmiete_von']} - {filter_config['gesamtmiete_bis']} €")
        if filter_config['gesamtflaeche_von'] or filter_config['gesamtflaeche_bis']:
            active_filters.append(f"Fläche: {filter_config['gesamtflaeche_von']} - {filter_config['gesamtflaeche_bis']} m²")
        if filter_config['zimmer_von'] or filter_config['zimmer_bis']:
            active_filters.append(f"Zimmer: {filter_config['zimmer_von']} - {filter_config['zimmer_bis']}")
        if filter_config['wbs']:
            wbs_text = "nur mit WBS" if filter_config['wbs'] == 'mit' else "nur ohne WBS" if filter_config['wbs'] == 'ohne' else "WBS egal"
            active_filters.append(f"WBS: {wbs_text}")

        if active_filters:
            logger.info(f"🔍 Aktive Bewerbungs-Filter: {' | '.join(active_filters)}")
        else:
            logger.info("ℹ️  Keine Bewerbungs-Filter aktiv")

        return filter_config

    except json.JSONDecodeError as e:
        logger.error(f"❌ Fehler beim Laden der Filter-Konfiguration: {e}")
        return default_config
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Laden der Filter-Konfiguration: {e}")
        return default_config


def wohnung_erfuellt_filter(wohnung: Dict[str, any], filter_config: Dict[str, any]) -> bool:
    """
    Prüft, ob eine Wohnung alle Filter-Kriterien erfüllt.

    Args:
        wohnung: Dictionary mit Wohnungsdaten
        filter_config: Dictionary mit Filter-Konfiguration

    Returns:
        True wenn Wohnung alle Filter erfüllt, False sonst
    """
    # Bezirksfilter
    gewuenschte_bezirke = [b for b in filter_config.get('gewuenschte_bezirke', []) if b and b.strip()]
    if gewuenschte_bezirke:
        wohnung_bezirk = wohnung.get('bezirk', '').lower()
        if not any(wohnung_bezirk == bezirk.lower() for bezirk in gewuenschte_bezirke):
            logger.debug(f"❌ Bezirk '{wohnung.get('bezirk')}' nicht in Filterliste")
            return False

    # Mieten-Filter
    miete_von = filter_config.get('gesamtmiete_von', '')
    miete_bis = filter_config.get('gesamtmiete_bis', '')
    if miete_von or miete_bis:
        miete_text = wohnung.get('miete', '').replace('€', '').replace('.', '').replace(',', '.').strip()
        try:
            miete_wert = float(miete_text.split()[0]) if miete_text else 0
            if miete_von and miete_wert < float(miete_von):
                logger.debug(f"❌ Miete {miete_wert}€ < {miete_von}€")
                return False
            if miete_bis and miete_wert > float(miete_bis):
                logger.debug(f"❌ Miete {miete_wert}€ > {miete_bis}€")
                return False
        except (ValueError, IndexError):
            logger.debug(f"⚠️  Konnte Miete nicht parsen: {wohnung.get('miete')}")
            return False

    # Flächen-Filter
    flaeche_von = filter_config.get('gesamtflaeche_von', '')
    flaeche_bis = filter_config.get('gesamtflaeche_bis', '')
    if flaeche_von or flaeche_bis:
        flaeche_text = wohnung.get('flaeche', '').replace('m²', '').replace(',', '.').strip()
        try:
            flaeche_wert = float(flaeche_text.split()[0]) if flaeche_text else 0
            if flaeche_von and flaeche_wert < float(flaeche_von):
                logger.debug(f"❌ Fläche {flaeche_wert}m² < {flaeche_von}m²")
                return False
            if flaeche_bis and flaeche_wert > float(flaeche_bis):
                logger.debug(f"❌ Fläche {flaeche_wert}m² > {flaeche_bis}m²")
                return False
        except (ValueError, IndexError):
            logger.debug(f"⚠️  Konnte Fläche nicht parsen: {wohnung.get('flaeche')}")
            return False

    # Zimmer-Filter
    zimmer_von = filter_config.get('zimmer_von', '')
    zimmer_bis = filter_config.get('zimmer_bis', '')
    if zimmer_von or zimmer_bis:
        zimmer_text = wohnung.get('zimmer', '')
        try:
            # Extrahiere Zimmerzahl aus "3 Zimmer" -> 3
            zimmer_str = zimmer_text.split()[0] if zimmer_text else '0'
            zimmer_zahl = float(zimmer_str.replace(',', '.'))

            if zimmer_von and zimmer_zahl < float(zimmer_von):
                logger.debug(f"❌ Zimmer {zimmer_zahl} < {zimmer_von}")
                return False
            if zimmer_bis and zimmer_zahl > float(zimmer_bis):
                logger.debug(f"❌ Zimmer {zimmer_zahl} > {zimmer_bis}")
                return False
        except (ValueError, IndexError):
            logger.debug(f"⚠️  Konnte Zimmerzahl nicht parsen: {zimmer_text}")
            return False

    # WBS-Filter
    wbs_filter = filter_config.get('wbs', '').lower()
    if wbs_filter and wbs_filter in ['mit', 'ohne']:
        wbs_erforderlich = wohnung.get('wbs_erforderlich', 0)
        if wbs_filter == 'mit' and wbs_erforderlich != 1:
            logger.debug(f"❌ WBS erforderlich, aber Wohnung hat kein WBS")
            return False
        if wbs_filter == 'ohne' and wbs_erforderlich == 1:
            logger.debug(f"❌ Kein WBS gewünscht, aber Wohnung erfordert WBS")
            return False

    return True


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Wartet eine zufällige Zeit, um menschliches Verhalten zu simulieren.

    Args:
        min_seconds: Minimale Wartezeit
        max_seconds: Maximale Wartezeit
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"⏸️  Pausiere {delay:.2f} Sekunden...")
    time.sleep(delay)


def human_like_typing(page: Page, selector: str, text: str, delay_range: tuple = (50, 150)) -> None:
    """
    Tippt Text mit zufälligen Verzögerungen zwischen Zeichen (simuliert menschliches Tippen).

    Args:
        page: Playwright Page-Objekt
        selector: CSS-Selektor des Input-Feldes
        text: Zu tippender Text
        delay_range: Tuple (min_ms, max_ms) für Verzögerung zwischen Zeichen
    """
    element = page.locator(selector)
    element.click()

    for char in text:
        element.type(char, delay=random.randint(delay_range[0], delay_range[1]))


def setup_browser_context(browser: Browser) -> BrowserContext:
    """
    Erstellt einen Browser-Kontext mit erweiterten Anti-Detection-Einstellungen (2025).

    Args:
        browser: Playwright Browser-Objekt

    Returns:
        Konfigurierter BrowserContext mit maximaler Tarnung
    """
    # Zufälliger User-Agent
    user_agent = random.choice(BROWSER_USER_AGENTS)

    # Zufällige Viewport-Größe
    viewport = random.choice(VIEWPORT_SIZES)

    # Zufällige Berlin-Koordinaten (innerhalb von Berlin streuen)
    latitude = 52.520008 + random.uniform(-0.05, 0.05)
    longitude = 13.404954 + random.uniform(-0.05, 0.05)

    # Zufällige Device Scale Factor (1.0, 1.25, 1.5, 2.0)
    device_scale_factor = random.choice([1.0, 1.0, 1.25, 1.5])  # 1.0 ist am häufigsten

    # Browser-Kontext mit erweiterten realistischen Einstellungen
    context = browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale='de-DE',
        timezone_id='Europe/Berlin',
        permissions=['geolocation'],
        geolocation={'latitude': latitude, 'longitude': longitude},
        color_scheme='light',
        has_touch=False,
        is_mobile=False,
        device_scale_factor=device_scale_factor,
        extra_http_headers={
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }
    )

    logger.info(f"🔧 Browser-Kontext erstellt:")
    logger.debug(f"   User-Agent: {user_agent[:70]}...")
    logger.debug(f"   Viewport: {viewport['width']}x{viewport['height']}")
    logger.debug(f"   Device Scale: {device_scale_factor}")
    logger.debug(f"   Geolocation: {latitude:.4f}, {longitude:.4f}")

    return context


def fill_application_form(page: Page, user_data: Dict, wohnung_link: str) -> bool:
    """
    Füllt das Bewerbungsformular im iFrame automatisch aus.

    Args:
        page: Playwright Page-Objekt
        user_data: Dictionary mit persönlichen Daten
        wohnung_link: Link zur Wohnung

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        logger.info(f"🌐 Öffne Wohnungsseite: {wohnung_link}")
        page.goto(wohnung_link, wait_until='domcontentloaded', timeout=APPLICATION_TIMEOUT)

        # Warte kurz, um natürliches Verhalten zu simulieren
        random_delay(2.0, 4.0)

        # Cookie-Banner akzeptieren (falls vorhanden)
        try:
            logger.info("🍪 Prüfe Cookie-Banner...")
            cookie_accept_button = page.locator('button:has-text("Alle akzeptieren"), button:has-text("Accept"), .brlbs-btn-accept-all, #BorlabsCookieBoxBtnAcceptAll').first
            if cookie_accept_button.is_visible(timeout=5000):
                logger.info("🍪 Akzeptiere Cookies...")
                cookie_accept_button.click()
                random_delay(1.0, 2.0)
            else:
                logger.info("ℹ️  Kein Cookie-Banner gefunden")
        except Exception as e:
            logger.debug(f"Cookie-Banner nicht gefunden oder bereits akzeptiert: {e}")

        # Suche nach dem "Anfrage senden" Button
        logger.info("🔍 Suche 'Anfrage senden' Button...")
        anfrage_button = page.locator('button[data-tab="rental-contact"]').first

        if not anfrage_button.is_visible():
            logger.error("❌ 'Anfrage senden' Button nicht gefunden!")
            return False

        # Klicke auf "Anfrage senden"
        logger.info("🖱️  Klicke auf 'Anfrage senden'...")
        anfrage_button.click(timeout=APPLICATION_TIMEOUT)

        # Warte auf das iFrame
        random_delay(2.0, 4.0)

        # Suche nach dem iFrame
        logger.info("🔍 Warte auf Formular-iFrame...")
        iframe_element = page.frame_locator('iframe#contact-iframe')

        if not iframe_element:
            logger.error("❌ Formular-iFrame nicht gefunden!")
            return False

        logger.info("✅ iFrame gefunden - fülle Formular aus...")

        # Extrahiere persönliche Daten
        personal_info = user_data.get('personal_info', {})
        household = user_data.get('household', {})
        documents = user_data.get('documents', {})
        nachricht = user_data.get('nachricht', '')

        # Warte kurz, bis das Formular vollständig geladen ist
        random_delay(2.0, 3.0)

        # Formularfelder mit exakten IDs aus appli.html

        # Anrede (Dropdown - Pflichtfeld)
        # ID: salutation-dropdown (ng-select), formcontrolname="salutation"
        try:
            anrede = personal_info.get('anrede', 'Herr')
            logger.debug(f"Setze Anrede: {anrede}...")
            # Klicke auf den ng-select dropdown
            anrede_dropdown = iframe_element.locator('#salutation-dropdown, #salutation').first
            anrede_dropdown.click()
            random_delay(0.5, 1.0)
            # Wähle "Herr" oder "Frau" aus der Dropdown-Liste
            iframe_element.locator(f'span.ng-option-label:has-text("{anrede}"), [role="option"]:has-text("{anrede}")').first.click()
            random_delay(0.5, 1.0)
            logger.info(f"✓ Anrede: {anrede}")
        except Exception as e:
            logger.warning(f"⚠️  Anrede-Feld nicht ausgefüllt: {e}")

        # Vorname (Pflichtfeld)
        # ID: firstName, formcontrolname="firstName"
        try:
            vorname = personal_info.get('vorname', '')
            if vorname:
                logger.debug("Fülle Vorname aus...")
                vorname_field = iframe_element.locator('#firstName').first
                vorname_field.fill(vorname)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Vorname: {vorname}")
        except Exception as e:
            logger.warning(f"⚠️  Vorname-Feld nicht ausgefüllt: {e}")

        # Nachname (Pflichtfeld)
        # ID: lastName, formcontrolname="lastName"
        try:
            nachname = personal_info.get('nachname', '')
            if nachname:
                logger.debug("Fülle Nachname aus...")
                nachname_field = iframe_element.locator('#lastName').first
                nachname_field.fill(nachname)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Nachname: {nachname}")
        except Exception as e:
            logger.warning(f"⚠️  Nachname-Feld nicht ausgefüllt: {e}")

        # E-Mail (Pflichtfeld)
        # ID: email, formcontrolname="email"
        try:
            email = personal_info.get('email', '')
            if email:
                logger.debug("Fülle E-Mail aus...")
                email_field = iframe_element.locator('#email').first
                email_field.fill(email)
                random_delay(0.5, 1.0)
                logger.info(f"✓ E-Mail: {email}")
        except Exception as e:
            logger.warning(f"⚠️  E-Mail-Feld nicht ausgefüllt: {e}")

        # Telefonnummer (Optional)
        # ID: phone-number, formcontrolname="phoneNumber"
        try:
            telefon_raw = personal_info.get('telefon', '')
            telefon = str(telefon_raw) if telefon_raw else ''  # Konvertiere zu String
            if telefon:
                logger.debug("Fülle Telefonnummer aus...")
                telefon_field = iframe_element.locator('#phone-number').first
                telefon_field.fill(telefon)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Telefon: {telefon}")
        except Exception as e:
            logger.debug(f"Telefon-Feld übersprungen: {e}")

        # Straße (Optional)
        # ID: street, formcontrolname="street"
        try:
            strasse = personal_info.get('strasse', '')
            if strasse:
                logger.debug("Fülle Straße aus...")
                strasse_field = iframe_element.locator('#street').first
                strasse_field.fill(strasse)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Straße: {strasse}")
        except Exception as e:
            logger.debug(f"Straße-Feld übersprungen: {e}")

        # Hausnummer (Optional)
        # ID: house-number, formcontrolname="houseNumber"
        try:
            hausnummer_raw = personal_info.get('hausnummer', '')
            hausnummer = str(hausnummer_raw) if hausnummer_raw else ''  # Konvertiere zu String
            if hausnummer:
                logger.debug("Fülle Hausnummer aus...")
                hausnummer_field = iframe_element.locator('#house-number').first
                hausnummer_field.fill(hausnummer)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Hausnummer: {hausnummer}")
        except Exception as e:
            logger.debug(f"Hausnummer-Feld übersprungen: {e}")

        # PLZ (Optional)
        # ID: zip-code, formcontrolname="zipCode"
        try:
            plz_raw = personal_info.get('plz', '')
            plz = str(plz_raw) if plz_raw else ''  # Konvertiere zu String
            if plz:
                logger.debug("Fülle PLZ aus...")
                plz_field = iframe_element.locator('#zip-code').first
                plz_field.fill(plz)
                random_delay(0.5, 1.0)
                logger.info(f"✓ PLZ: {plz}")
        except Exception as e:
            logger.debug(f"PLZ-Feld übersprungen: {e}")

        # Stadt (Optional)
        # ID: city, formcontrolname="city"
        try:
            stadt = personal_info.get('stadt', '')
            if stadt:
                logger.debug("Fülle Stadt aus...")
                stadt_field = iframe_element.locator('#city').first
                stadt_field.fill(stadt)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Stadt: {stadt}")
        except Exception as e:
            logger.debug(f"Stadt-Feld übersprungen: {e}")

        # Adresszusatz (Optional)
        try:
            adresszusatz = personal_info.get('adresszusatz', '')
            if adresszusatz:
                logger.debug("Fülle Adresszusatz aus...")
                adresszusatz_field = iframe_element.locator(
                    'input[placeholder*="Adresszusatz"], '
                    'input[id*="adresszusatz"], '
                    'input[name*="addressAddition"]'
                ).first
                adresszusatz_field.fill(adresszusatz)
                random_delay(0.5, 1.0)
                logger.info(f"✓ Adresszusatz: {adresszusatz}")
        except Exception as e:
            logger.debug(f"Adresszusatz-Feld übersprungen: {e}")

        # "Für wen wird die Wohnungsanfrage gestellt?" (Pflichtfeld)
        # WICHTIG: Dieses Feld erscheint nach Personenanzahl im Formular!
        # Wird weiter unten ausgefüllt (nach Gesamtzahl Personen)

        # Personenanzahl - Zwei Varianten möglich:
        # Variante 1: "Gesamtzahl der einziehenden Personen (Erwachsene + Kinder)"
        # Variante 2: Separate Felder für "Anzahl Erwachsene" und "Anzahl Kinder"

        anzahl_erwachsene = household.get('anzahl_personen', 1)
        anzahl_kinder = household.get('anzahl_kinder', 0)
        gesamtanzahl = anzahl_erwachsene + anzahl_kinder

        # Versuche zuerst Variante 1: Gesamtzahl-Feld
        gesamtzahl_ausgefuellt = False
        try:
            logger.debug(f"Suche 'Gesamtzahl Personen'-Feld...")
            gesamtzahl_field = iframe_element.locator(
                'input[placeholder*="Gesamtzahl"], '
                'input[id*="gesamtzahl"], '
                'input[name*="totalPersons"], '
                'input[aria-label*="Gesamtzahl"]'
            ).first

            if gesamtzahl_field.is_visible(timeout=2000):
                logger.debug(f"Setze Gesamtzahl Personen: {gesamtanzahl}...")
                gesamtzahl_field.fill(str(gesamtanzahl))
                random_delay(0.5, 1.0)
                logger.info(f"✓ Gesamtzahl Personen: {gesamtanzahl}")
                gesamtzahl_ausgefuellt = True
        except Exception as e:
            logger.debug(f"Gesamtzahl-Feld nicht gefunden oder nicht sichtbar: {e}")

        # Variante 2: Separate Felder (nur wenn Variante 1 nicht gefunden wurde)
        if not gesamtzahl_ausgefuellt:
            # Anzahl Erwachsene
            try:
                logger.debug(f"Setze Anzahl Erwachsene: {anzahl_erwachsene}...")
                erwachsene_field = iframe_element.locator(
                    'input[placeholder*="Erwachsene"], '
                    'input[id*="erwachsen"], '
                    'input[name*="adult"], '
                    'input[aria-label*="Erwachsene"]'
                ).first
                erwachsene_field.fill(str(anzahl_erwachsene))
                random_delay(0.5, 1.0)
                logger.info(f"✓ Anzahl Erwachsene: {anzahl_erwachsene}")
            except Exception as e:
                logger.warning(f"⚠️  Erwachsene-Feld nicht ausgefüllt: {e}")

            # Anzahl Kinder
            try:
                logger.debug(f"Setze Anzahl Kinder: {anzahl_kinder}...")
                kinder_field = iframe_element.locator(
                    'input[placeholder*="Kinder"], '
                    'input[id*="kinder"], '
                    'input[name*="child"], '
                    'input[aria-label*="Kinder"]'
                ).first
                kinder_field.fill(str(anzahl_kinder))
                random_delay(0.5, 1.0)
                logger.info(f"✓ Anzahl Kinder: {anzahl_kinder}")
            except Exception as e:
                logger.debug(f"Kinder-Feld übersprungen: {e}")

        # "Für wen wird die Wohnungsanfrage gestellt?" (Pflichtfeld)
        # WICHTIG: Dieses Feld erscheint NACH Personenanzahl im Formular!
        try:
            fuer_wen_raw = personal_info.get('fuer_wen_anfrage', 'Für mich selbst')
            logger.debug(f"Setze 'Für wen wird die Anfrage gestellt': {fuer_wen_raw}...")

            # Verbesserte Selektoren basierend auf Playwright MCP Analyse
            fuer_wen_dropdown = iframe_element.locator(
                'ng-select[aria-label*="Stellen Sie diese Wohnungsanfrage"], '
                'ng-select[aria-label*="für sich selbst"], '
                '[role="listbox"][aria-label*="Stellen Sie"], '
                'ng-select:has-text("Stellen Sie diese Wohnungsanfrage")'
            ).first

            # Warte bis sichtbar und klicke
            if fuer_wen_dropdown.is_visible(timeout=5000):
                fuer_wen_dropdown.click()
                random_delay(1.0, 2.0)  # Längere Wartezeit damit Dropdown öffnet

                # Mögliche Option-Werte (aus real Website):
                # - "Für mich selbst"
                # - "Für eine andere Person/einen Dritten"
                # Aber im Formular könnten sie anders heißen, also alle Varianten probieren
                option_found = False
                possible_values = [
                    fuer_wen_raw,  # Original Wert
                    "Für mich selbst",  # Standard
                    "mich selbst",  # Ohne "Für"
                    "Myself",  # Falls Englisch
                    "selbst"  # Kurz
                ]

                for option_value in possible_values:
                    try:
                        option = iframe_element.locator(
                            f'span.ng-option-label:has-text("{option_value}"), '
                            f'[role="option"]:has-text("{option_value}"), '
                            f'div.ng-option:has-text("{option_value}")'
                        ).first

                        if option.is_visible(timeout=2000):
                            option.click()
                            random_delay(0.5, 1.0)
                            logger.info(f"✓ Für wen wird die Anfrage gestellt: {option_value}")
                            option_found = True
                            break
                    except:
                        continue

                if not option_found:
                    # Fallback: Klicke einfach die erste Option
                    try:
                        first_option = iframe_element.locator('[role="option"]').first
                        first_option.click()
                        random_delay(0.5, 1.0)
                        logger.info("✓ Für wen wird die Anfrage gestellt: (erste Option gewählt)")
                        option_found = True
                    except:
                        pass

                if not option_found:
                    logger.warning(f"⚠️  Keine passende Option gefunden!")
                    logger.warning(f"⚠️  ACHTUNG: Dies ist ein PFLICHTFELD! Bewerbung könnte fehlschlagen!")
            else:
                logger.warning(f"⚠️  'Für wen'-Dropdown nicht gefunden - überspringe")
        except Exception as e:
            logger.warning(f"⚠️  'Für wen'-Feld konnte nicht ausgefüllt werden: {e}")
            logger.warning(f"⚠️  ACHTUNG: Dies ist ein PFLICHTFELD! Bewerbung könnte fehlschlagen!")

        # Mobilfunknummer (Pflichtfeld) - erscheint NACH "Für wen"-Dropdown im Formular!
        # Label: for="formly_18_input_$$_telephone_number_$$_0"
        try:
            # Konvertiere zu String, falls als Integer gespeichert
            mobil_raw = personal_info.get('mobil', personal_info.get('telefon', ''))
            mobil = str(mobil_raw) if mobil_raw else ''

            if mobil:
                logger.debug(f"Fülle Mobilfunknummer aus: {mobil}...")
                mobil_field = iframe_element.locator(
                    'input[id*="telephone_number"], '
                    'input[placeholder*="Mobilfunknummer"], '
                    'input[id*="mobilfunknummer"], '
                    'input[id*="mobil"], '
                    'input[name*="mobilePhone"], '
                    'input[name*="mobile"], '
                    'input[aria-label*="Mobilfunknummer"]'
                ).first

                # Prüfe ob Feld sichtbar ist
                if mobil_field.is_visible(timeout=5000):
                    mobil_field.fill(mobil)
                    random_delay(0.5, 1.0)
                    logger.info(f"✓ Mobilfunknummer: {mobil}")
                else:
                    logger.warning(f"⚠️  Mobilfunknummer-Feld nicht sichtbar!")
                    logger.warning(f"⚠️  ACHTUNG: Dies ist ein PFLICHTFELD! Bewerbung könnte fehlschlagen!")
        except Exception as e:
            logger.warning(f"⚠️  Mobilfunknummer-Feld konnte nicht ausgefüllt werden: {e}")
            logger.warning(f"⚠️  ACHTUNG: Dies ist ein PFLICHTFELD! Bewerbung könnte fehlschlagen!")

        # WBS vorhanden? (Radio Button) - OPTIONAL: erscheint nicht immer
        # ID: formly_4_radio_$_wbs_available_$_0-Ja / formly_4_radio_$_wbs_available_$_0-Nein
        try:
            wbs = household.get('wbs_vorhanden', False)
            logger.debug(f"Suche WBS-Feld...")

            # Prüfe, ob WBS-Feld überhaupt vorhanden ist
            wbs_field = iframe_element.locator(
                'input[id*="wbs_available"], '
                'input[data-cy*="wbs_available"]'
            ).first

            if wbs_field.is_visible(timeout=3000):
                logger.debug(f"WBS-Feld gefunden - setze: {'Ja' if wbs else 'Nein'}...")
                if wbs:
                    # Suche Radio Button mit ID oder data-cy für "Ja"
                    wbs_ja = iframe_element.locator(
                        'input[id*="wbs_available"][id*="-Ja"], '
                        'input[data-cy*="wbs_available"][data-cy*="-Ja"], '
                        'input[type="radio"][value="ja"]'
                    ).first
                    wbs_ja.check()
                else:
                    # Suche Radio Button mit ID oder data-cy für "Nein"
                    wbs_nein = iframe_element.locator(
                        'input[id*="wbs_available"][id*="-Nein"], '
                        'input[data-cy*="wbs_available"][data-cy*="-Nein"], '
                        'input[type="radio"][value="nein"]'
                    ).first
                    wbs_nein.check()
                random_delay(0.5, 1.0)
                logger.info(f"✓ WBS vorhanden: {'Ja' if wbs else 'Nein'}")

                # Bedingte WBS-Felder (erscheinen nur wenn WBS=Ja)
                if wbs:
                    try:
                        random_delay(1.0, 2.0)  # Warte, bis bedingte Felder erscheinen

                        # 1. Gültigkeit des WBS (Datepicker)
                        wbs_gueltig_bis = household.get('wbs_gueltig_bis', '')
                        if wbs_gueltig_bis:
                            wbs_gueltig_field = iframe_element.locator(
                                'input[id*="wbs_valid"], '
                                'input[id*="wbs_gueltig"], '
                                'input[placeholder*="Gültigkeit"], '
                                'input[aria-label*="Gültigkeit"]'
                            ).first
                            if wbs_gueltig_field.is_visible(timeout=3000):
                                wbs_gueltig_field.fill(wbs_gueltig_bis)
                                random_delay(0.5, 1.0)
                                logger.info(f"✓ WBS gültig bis: {wbs_gueltig_bis}")

                        # 2. Art / Bezeichnung des WBS (Input oder Dropdown)
                        wbs_art = household.get('wbs_art', '')
                        if wbs_art:
                            try:
                                # Versuche zuerst Input-Feld
                                wbs_art_field = iframe_element.locator(
                                    'input[id*="wbs_type"], '
                                    'input[id*="wbs_art"], '
                                    'input[placeholder*="Bezeichnung"], '
                                    'input[aria-label*="Art"]'
                                ).first
                                if wbs_art_field.is_visible(timeout=2000):
                                    wbs_art_field.fill(wbs_art)
                                    random_delay(0.5, 1.0)
                                    logger.info(f"✓ WBS Art: {wbs_art}")
                            except:
                                # Falls kein Input-Feld, versuche Dropdown
                                wbs_art_dropdown = iframe_element.locator(
                                    'ng-select[id*="wbs_type"], '
                                    'ng-select[id*="wbs_art"]'
                                ).first
                                if wbs_art_dropdown.is_visible(timeout=2000):
                                    wbs_art_dropdown.click()
                                    iframe_element.locator(f'span.ng-option-label:has-text("{wbs_art}")').first.click()
                                    random_delay(0.5, 1.0)
                                    logger.info(f"✓ WBS Art: {wbs_art}")

                        # 3. Anzahl Räume/Zimmer im WBS (Input)
                        wbs_zimmer = household.get('wbs_zimmer', '')
                        if wbs_zimmer:
                            wbs_zimmer_field = iframe_element.locator(
                                'input[id*="wbs_rooms"], '
                                'input[id*="wbs_zimmer"], '
                                'input[placeholder*="Räume"], '
                                'input[placeholder*="Zimmer"], '
                                'input[aria-label*="Zimmer"]'
                            ).first
                            if wbs_zimmer_field.is_visible(timeout=3000):
                                wbs_zimmer_field.fill(str(wbs_zimmer))
                                random_delay(0.5, 1.0)
                                logger.info(f"✓ WBS Zimmer: {wbs_zimmer}")
                    except Exception as e:
                        logger.debug(f"Bedingte WBS-Felder übersprungen: {e}")

                # Bedingte Einkommensfelder (erscheinen nur wenn WBS=Nein)
                if not wbs:
                    try:
                        random_delay(1.0, 2.0)  # Warte, bis bedingtes Feld erscheinen kann

                        einkommen_passt = household.get('einkommen_in_spanne', True)
                        logger.debug(f"Suche Haushaltseinkommen-Feld...")

                        if einkommen_passt:
                            # Suche Radio Button für "Ja"
                            einkommen_ja = iframe_element.locator(
                                'input[id*="income_within_range"][id*="-Ja"], '
                                'input[id*="nettoeinkommen"][id*="-Ja"], '
                                'input[aria-label*="Haushaltsnettoeinkommen"][value*="ja"]'
                            ).first
                            if einkommen_ja.is_visible(timeout=3000):
                                einkommen_ja.check()
                                random_delay(0.5, 1.0)
                                logger.info(f"✓ Haushaltseinkommen in Spanne: Ja")
                        else:
                            # Suche Radio Button für "Nein"
                            einkommen_nein = iframe_element.locator(
                                'input[id*="income_within_range"][id*="-Nein"], '
                                'input[id*="nettoeinkommen"][id*="-Nein"], '
                                'input[aria-label*="Haushaltsnettoeinkommen"][value*="nein"]'
                            ).first
                            if einkommen_nein.is_visible(timeout=3000):
                                einkommen_nein.check()
                                random_delay(0.5, 1.0)
                                logger.info(f"✓ Haushaltseinkommen in Spanne: Nein")
                    except Exception as e:
                        logger.debug(f"Haushaltseinkommen-Feld übersprungen: {e}")
            else:
                logger.debug("WBS-Feld nicht vorhanden - überspringe")
        except Exception as e:
            logger.debug(f"WBS-Block übersprungen: {e}")

        # § 9 Abs. 2 WoFG Bescheinigung vorhanden? (Radio Button) - OPTIONAL
        # ID: formly_14_radio_gewobag_paragraph_9_bescheinigung_vorhanden_0-Ja / -Nein
        # Erscheint manchmal bei Formularen (unabhängig von WBS)
        try:
            paragraph_9 = household.get('paragraph_9_bescheinigung', False)
            logger.debug(f"Suche § 9 Abs. 2 WoFG Bescheinigung-Feld...")

            # Prüfe, ob das Feld überhaupt vorhanden ist
            paragraph_9_field = iframe_element.locator(
                'input[id*="paragraph_9_bescheinigung"], '
                'input[id*="paragraph_9"], '
                'input[name*="paragraph_9"]'
            ).first

            if paragraph_9_field.is_visible(timeout=3000):
                logger.debug(f"§ 9 Abs. 2 WoFG Bescheinigung-Feld gefunden - setze: {'Ja' if paragraph_9 else 'Nein'}...")
                if paragraph_9:
                    # Suche Radio Button für "Ja"
                    paragraph_9_ja = iframe_element.locator(
                        'input[id*="paragraph_9_bescheinigung"][id*="-Ja"], '
                        'input[id*="paragraph_9"][id*="-Ja"], '
                        'input[data-cy*="paragraph_9"][data-cy*="-Ja"]'
                    ).first
                    paragraph_9_ja.check()
                else:
                    # Suche Radio Button für "Nein"
                    paragraph_9_nein = iframe_element.locator(
                        'input[id*="paragraph_9_bescheinigung"][id*="-Nein"], '
                        'input[id*="paragraph_9"][id*="-Nein"], '
                        'input[data-cy*="paragraph_9"][data-cy*="-Nein"]'
                    ).first
                    paragraph_9_nein.check()
                random_delay(0.5, 1.0)
                logger.info(f"✓ § 9 Abs. 2 WoFG Bescheinigung: {'Ja' if paragraph_9 else 'Nein'}")
            else:
                logger.debug("§ 9 Abs. 2 WoFG Bescheinigung-Feld nicht vorhanden - überspringe")
        except Exception as e:
            logger.debug(f"§ 9 Abs. 2 WoFG Bescheinigung-Block übersprungen: {e}")

        # Anmerkungen (Textarea)
        try:
            if nachricht:
                logger.debug("Fülle Anmerkungen aus...")
                anmerkungen_field = iframe_element.locator('textarea[placeholder*="Anmerkungen"], textarea[id*="anmerkung"], textarea[name*="message"], textarea[name*="comment"]').first
                anmerkungen_field.fill(nachricht)
                random_delay(1.0, 2.0)
                logger.info(f"✓ Anmerkungen: {len(nachricht)} Zeichen")
        except Exception as e:
            logger.debug(f"Anmerkungen-Feld übersprungen: {e}")

        # Datenschutz-Checkboxen (2 Stück - beide müssen aktiviert werden)
        try:
            logger.debug("Aktiviere Datenschutz-Checkboxen...")
            checkboxes = iframe_element.locator('input[type="checkbox"]').all()
            checked_count = 0
            for checkbox in checkboxes:
                try:
                    if not checkbox.is_checked():
                        checkbox.check()
                        checked_count += 1
                        random_delay(0.3, 0.7)
                except:
                    pass
            logger.info(f"✓ {checked_count} Datenschutz-Checkbox(en) aktiviert")
        except Exception as e:
            logger.warning(f"⚠️  Datenschutz-Checkboxen nicht aktiviert: {e}")

        logger.info("📝 Formular ausgefüllt - bereit zum Absenden")

        # AUTOMATISCHES ABSENDEN AKTIVIERT
        try:
            logger.info("🚀 Sende Bewerbung automatisch ab...")
            submit_button = iframe_element.locator('button[type="submit"], input[type="submit"]').first

            # Prüfe, ob der Button sichtbar und aktiviert ist
            if not submit_button.is_visible(timeout=5000):
                raise Exception("Absende-Button nicht sichtbar")

            if not submit_button.is_enabled(timeout=5000):
                raise Exception("Absende-Button ist deaktiviert (möglicherweise fehlen Pflichtfelder)")

            # Klicke auf Absende-Button
            submit_button.click(timeout=APPLICATION_TIMEOUT)
            logger.info("✅ Bewerbung wurde abgesendet!")

            # Warte kurz, um sicherzustellen, dass die Anfrage gesendet wurde
            random_delay(5.0, 8.0)

            # WICHTIG: Prüfe auf Erfolgs- oder Fehlermeldungen IM IFRAME (nicht auf Hauptseite!)

            # ZUERST: Prüfe auf FEHLERMELDUNGEN
            try:
                error_message = iframe_element.locator(
                    'div[class*="error"], '
                    'div[class*="Error"], '
                    'div[class*="alert"], '
                    'p[class*="error"], '
                    'span[class*="error"], '
                    '[role="alert"], '
                    'div:has-text("nicht mehr veröffentlicht"), '
                    'div:has-text("nicht mehr verfügbar"), '
                    'div:has-text("Objekt ist nicht mehr"), '
                    'div:has-text("Pflichtfeld"), '
                    'div:has-text("erforderlich"), '
                    'div:has-text("fehlt"), '
                    'div:has-text("ungültig")'
                ).first

                if error_message.is_visible(timeout=3000):
                    error_text = error_message.inner_text()
                    logger.error("="*80)
                    logger.error("❌ FEHLERMELDUNG IM IFRAME ERKANNT:")
                    logger.error(error_text)
                    logger.error("="*80)

                    # Analysiere spezifische Fehler
                    if "nicht mehr veröffentlicht" in error_text.lower() or "nicht mehr verfügbar" in error_text.lower():
                        logger.warning("⚠️  WOHNUNG NICHT MEHR VERFÜGBAR: Das Objekt wurde bereits von der Website entfernt")
                    elif "pflichtfeld" in error_text.lower() or "erforderlich" in error_text.lower():
                        logger.warning("⚠️  PFLICHTFELD FEHLT: Nicht alle erforderlichen Felder wurden ausgefüllt")
                    elif "ungültig" in error_text.lower():
                        logger.warning("⚠️  UNGÜLTIGE EINGABE: Bitte überprüfen Sie die eingegebenen Daten")

                    return False
            except:
                logger.debug("Keine explizite Fehlermeldung IM IFRAME gefunden")

            # DANN: Prüfe auf ERFOLGSMELDUNGEN
            try:
                # Suche nach Erfolgsmeldung IM IFRAME (wo das Formular ist)
                success_message = iframe_element.locator(
                    'div[class*="success"], '
                    'div[class*="Success"], '
                    'p:has-text("Vielen Dank"), '
                    'p:has-text("erfolgreich"), '
                    'p:has-text("gesendet"), '
                    'div:has-text("Ihre Anfrage wurde"), '
                    'div:has-text("Anfrage wurde versendet"), '
                    'div:has-text("Anfrage erfolgreich")'
                ).first

                if success_message.is_visible(timeout=10000):
                    success_text = success_message.inner_text()
                    logger.info("="*80)
                    logger.info("✅ ERFOLGSMELDUNG IM IFRAME ERKANNT:")
                    logger.info(success_text)
                    logger.info("="*80)
                    return True
            except:
                logger.debug("Keine explizite Erfolgsmeldung IM IFRAME gefunden")

            # Fallback: Prüfe auch die Hauptseite (für alte Formulare)
            try:
                success_message_main = page.locator(
                    'div[class*="success"], '
                    'div[class*="Success"], '
                    'p:has-text("Vielen Dank"), '
                    'p:has-text("erfolgreich"), '
                    'p:has-text("gesendet")'
                ).first

                if success_message_main.is_visible(timeout=5000):
                    success_text = success_message_main.inner_text()
                    logger.info(f"✅ Erfolgsmeldung auf HAUPTSEITE erkannt: {success_text[:100]}")
                    return True
            except:
                logger.debug("Keine Erfolgsmeldung auf Hauptseite gefunden")

            # Prüfe ob das Formular noch sichtbar ist (wenn nicht = wahrscheinlich erfolgreich)
            try:
                form_still_visible = iframe_element.locator('button[type="submit"]').first.is_visible(timeout=3000)
                if not form_still_visible:
                    logger.info("✅ Formular wurde geschlossen - wahrscheinlich erfolgreich abgesendet")
                    return True
            except:
                # Formular nicht mehr gefunden = wahrscheinlich erfolgreich
                logger.info("✅ Formular nicht mehr gefunden - wahrscheinlich erfolgreich abgesendet")
                return True

            # Wenn wir hier ankommen: Button wurde geklickt, aber keine eindeutige Bestätigung
            logger.warning("⚠️  Keine eindeutige Erfolgsmeldung gefunden, aber Button wurde geklickt")
            logger.warning("⚠️  Markiere als erfolgreich (Button-Klick erfolgt)")
            return True

        except Exception as e:
            error_msg = f"Fehler beim automatischen Absenden: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Fehlerdetails: {type(e).__name__} - {str(e)}")

            # Versuche Screenshot zu machen für Debugging
            try:
                screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                logger.info(f"📸 Screenshot gespeichert: {screenshot_path}")
            except:
                logger.debug("Konnte keinen Screenshot erstellen")

            return False

    except PlaywrightTimeoutError as e:
        error_msg = f"Timeout beim Laden des Formulars oder Elements (>{APPLICATION_TIMEOUT/1000}s): {str(e)}"
        logger.error(f"⏱️  {error_msg}")
        logger.error(f"Timeout-Details: Konnte Element nicht innerhalb der Wartezeit finden")
        logger.error(f"URL: {wohnung_link}")

        # Screenshot bei Timeout
        try:
            screenshot_path = f"timeout_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Timeout-Screenshot gespeichert: {screenshot_path}")
        except:
            pass

        return False

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        logger.error(f"❌ Fehler beim Ausfüllen des Formulars")
        logger.error(f"Fehlertyp: {error_type}")
        logger.error(f"Fehlermeldung: {error_msg}")
        logger.error(f"URL: {wohnung_link}")

        # Erweiterte Fehleranalyse
        if "cloudflare" in error_msg.lower() or "captcha" in error_msg.lower():
            logger.error("🛡️  ACHTUNG: Cloudflare-Blockierung oder CAPTCHA erkannt!")
            logger.error("Empfehlung: Längere Pausen zwischen Anfragen, User-Agent wechseln")

        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            logger.error("🌐 ACHTUNG: Netzwerkfehler erkannt!")
            logger.error("Empfehlung: Internetverbindung prüfen, evtl. Proxy verwenden")

        elif "iframe" in error_msg.lower():
            logger.error("📦 ACHTUNG: iFrame konnte nicht geladen werden!")
            logger.error("Empfehlung: Längere Wartezeit, Website-Struktur hat sich möglicherweise geändert")

        elif "selector" in error_msg.lower() or "not found" in error_msg.lower():
            logger.error("🔍 ACHTUNG: Formular-Element nicht gefunden!")
            logger.error("Empfehlung: Website-Struktur hat sich geändert, Selektoren müssen aktualisiert werden")

        # Screenshot bei allgemeinen Fehlern
        try:
            screenshot_path = f"general_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Fehler-Screenshot gespeichert: {screenshot_path}")
        except:
            pass

        logger.error("Stack Trace:", exc_info=True)
        return False


def mark_application_in_db(link: str, status: str, error: Optional[str] = None) -> None:
    """
    Markiert eine Bewerbung in der Datenbank als abgesendet oder fehlgeschlagen.

    Args:
        link: Link zur Wohnung
        status: Status der Bewerbung ('success', 'failed', 'pending')
        error: Optionale Fehlermeldung
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE wohnungen
            SET applied = 1,
                applied_ts = ?,
                application_status = ?,
                application_error = ?
            WHERE link = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, error, link))

        conn.commit()
        conn.close()

        logger.info(f"✅ Datenbank aktualisiert: {link} -> Status: {status}")

    except sqlite3.Error as e:
        logger.error(f"❌ Fehler beim Update der Datenbank: {e}")


def get_unapplied_wohnungen(filter_config: Dict[str, any] = None) -> List[Dict[str, str]]:
    """
    Holt alle Wohnungen aus der Datenbank, für die noch keine Bewerbung abgesendet wurde
    und die die Filter-Kriterien erfüllen.

    Args:
        filter_config: Optional - Filter-Konfiguration (wird geladen wenn nicht übergeben)

    Returns:
        Liste von Wohnungs-Dictionaries, die Filter erfüllen
    """
    try:
        # Filter laden wenn nicht übergeben
        if filter_config is None:
            filter_config = load_filter_config()

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM wohnungen
            WHERE applied = 0 OR applied IS NULL
            ORDER BY ts DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        # Alle unbeworbenen Wohnungen sammeln
        alle_wohnungen = []
        for row in rows:
            alle_wohnungen.append({
                'id': row['id'],
                'bezirk': row['bezirk'],
                'adresse': row['adresse'],
                'titel': row['titel'],
                'zimmer': row['zimmer'],
                'flaeche': row['flaeche'],
                'miete': row['miete'],
                'wbs_erforderlich': row['wbs_erforderlich'],
                'link': row['link'],
                'ts': row['ts']
            })

        logger.info(f"📊 {len(alle_wohnungen)} unbeworbene Wohnungen in Datenbank gefunden")

        # Filter anwenden
        gefilterte_wohnungen = []
        for wohnung in alle_wohnungen:
            if wohnung_erfuellt_filter(wohnung, filter_config):
                gefilterte_wohnungen.append(wohnung)
            else:
                logger.info(f"⏭️  Überspringe: {wohnung['titel']} ({wohnung['bezirk']}) - erfüllt nicht alle Filter-Kriterien")

        if len(gefilterte_wohnungen) < len(alle_wohnungen):
            logger.info(f"✅ {len(gefilterte_wohnungen)} von {len(alle_wohnungen)} Wohnungen erfüllen die Filter-Kriterien")

        return gefilterte_wohnungen

    except sqlite3.Error as e:
        logger.error(f"❌ Fehler beim Abrufen der Wohnungen: {e}")
        return []


def is_already_applied(link: str) -> bool:
    """
    Prüft, ob für diese Wohnung bereits eine Bewerbung abgesendet wurde.

    Args:
        link: Link zur Wohnung

    Returns:
        True wenn bereits beworben, False wenn noch nicht beworben
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT applied, application_status, applied_ts
            FROM wohnungen
            WHERE link = ? AND applied = 1
        """, (link,))

        result = cursor.fetchone()
        conn.close()

        if result:
            applied, status, applied_ts = result
            logger.warning(f"⚠️  DUPLIKAT ERKANNT: Wohnung wurde bereits am {applied_ts} beworben (Status: {status})")
            return True

        return False

    except sqlite3.Error as e:
        logger.error(f"❌ Fehler bei Duplikat-Prüfung: {e}")
        # Im Fehlerfall: Sicherheitshalber als "nicht beworben" behandeln
        return False


def apply_to_wohnung(wohnung: Dict, user_data: Dict, headless: bool = True) -> bool:
    """
    Bewirbt sich auf eine einzelne Wohnung.

    Args:
        wohnung: Dictionary mit Wohnungsdaten
        user_data: Dictionary mit persönlichen Daten
        headless: Ob der Browser im Headless-Modus laufen soll

    Returns:
        True bei Erfolg, False bei Fehler
    """
    logger.info("=" * 80)
    logger.info(f"🏠 Starte Bewerbung für: {wohnung['titel']}")
    logger.info(f"📍 Bezirk: {wohnung['bezirk']}")
    logger.info(f"🔗 Link: {wohnung['link']}")
    logger.info("=" * 80)

    # DUPLIKAT-SCHUTZ: Prüfe VOR der Bewerbung, ob bereits beworben
    if is_already_applied(wohnung['link']):
        logger.error(f"❌ ABBRUCH: Diese Wohnung wurde bereits beworben! Überspringe...")
        return False

    retry_count = 0

    while retry_count <= MAX_APPLICATION_RETRIES:
        try:
            with sync_playwright() as p:
                # Browser starten mit erweiterten Anti-Detection-Args
                logger.info("🌐 Starte Browser mit erweiterten Anti-Detection-Einstellungen...")
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        # Kern Anti-Detection
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials',

                        # Performance & Stability
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',

                        # Weitere Anti-Detection
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-breakpad',
                        '--disable-backing-store-limit',
                        '--disable-extensions',
                        '--disable-translate',
                        '--metrics-recording-only',
                        '--mute-audio',
                        '--no-first-run',
                        '--safebrowsing-disable-auto-update',
                        '--no-default-browser-check',
                        '--no-pings',
                        '--password-store=basic',
                        '--use-mock-keychain',

                        # Window Size (wird durch Context überschrieben)
                        '--window-size=1920,1080',
                    ]
                )

                # Browser-Kontext mit erweiterten Anti-Detection-Einstellungen
                context = setup_browser_context(browser)

                # Neue Seite öffnen
                page = context.new_page()

                # Erweiterte Stealth-Skripte injizieren (Canvas, WebGL, Audio Fingerprinting)
                logger.debug("🔒 Injiziere erweiterte Anti-Detection-Skripte...")
                page.add_init_script("""
                    // Navigator.webdriver entfernen
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Chrome-Objekt hinzufügen
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // Plugins überschreiben
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                            {name: 'Native Client', filename: 'internal-nacl-plugin'}
                        ]
                    });

                    // Languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['de-DE', 'de', 'en-US', 'en']
                    });

                    // Permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );

                    // Canvas Fingerprinting Randomisierung
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                        const imageData = getImageData.apply(this, args);
                        for (let i = 0; i < imageData.data.length; i++) {
                            imageData.data[i] = imageData.data[i] ^ (Math.random() < 0.1 ? 1 : 0);
                        }
                        return imageData;
                    };

                    // WebGL Vendor & Renderer Randomisierung
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.apply(this, arguments);
                    };

                    // Screen-Fingerprinting-Schutz
                    Object.defineProperty(screen, 'colorDepth', {
                        get: () => 24
                    });
                    Object.defineProperty(screen, 'pixelDepth', {
                        get: () => 24
                    });

                    // AudioContext Fingerprinting
                    const audioContext = window.AudioContext || window.webkitAudioContext;
                    if (audioContext) {
                        const originalCreateOscillator = audioContext.prototype.createOscillator;
                        audioContext.prototype.createOscillator = function() {
                            const oscillator = originalCreateOscillator.apply(this, arguments);
                            const originalStart = oscillator.start;
                            oscillator.start = function() {
                                originalStart.apply(this, arguments);
                            };
                            return oscillator;
                        };
                    }
                """)

                # playwright-stealth anwenden (falls verfügbar)
                if STEALTH_AVAILABLE:
                    logger.debug("🔒 Wende playwright-stealth an...")
                    try:
                        stealth_sync(page)
                        logger.info("✅ playwright-stealth aktiviert")
                    except Exception as e:
                        logger.warning(f"⚠️  playwright-stealth konnte nicht angewendet werden: {e}")

                # Bewerbungsformular ausfüllen
                success = fill_application_form(page, user_data, wohnung['link'])

                # Browser schließen
                browser.close()

                if success:
                    logger.info("✅ Bewerbung erfolgreich!")
                    mark_application_in_db(wohnung['link'], 'success')
                    return True
                else:
                    raise Exception("Formular konnte nicht ausgefüllt werden")

        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            logger.error(f"❌ Fehler bei Bewerbung (Versuch {retry_count}/{MAX_APPLICATION_RETRIES + 1}): {error_msg}")

            if retry_count <= MAX_APPLICATION_RETRIES:
                retry_delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                logger.info(f"🔄 Wiederhole in {retry_delay:.1f} Sekunden...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Max. Anzahl Wiederholungen erreicht - Bewerbung fehlgeschlagen")
                mark_application_in_db(wohnung['link'], 'failed', error_msg)
                return False

    return False


def run_application_bot(headless: bool = True, max_applications: int = None) -> None:
    """
    Hauptfunktion: Bewirbt sich automatisch auf alle neuen Wohnungen.

    Args:
        headless: Ob der Browser im Headless-Modus laufen soll
        max_applications: Maximale Anzahl Bewerbungen pro Durchlauf (None = unbegrenzt)
    """
    logger.info("=" * 80)
    logger.info("🤖 GEWOBAG APPLICATION BOT GESTARTET")
    logger.info("=" * 80)

    # Benutzerdaten laden
    user_data = load_user_data()
    if not user_data:
        logger.error("❌ Konnte Benutzerdaten nicht laden - Abbruch")
        return

    # Filter-Konfiguration laden
    filter_config = load_filter_config()

    # Unbeworbene Wohnungen abrufen (mit Filter-Prüfung)
    wohnungen = get_unapplied_wohnungen(filter_config)

    if not wohnungen:
        logger.info("ℹ️  Keine neuen Wohnungen für Bewerbung gefunden (die Filter erfüllen)")
        return

    # Limitiere Anzahl der Bewerbungen
    if max_applications and len(wohnungen) > max_applications:
        logger.info(f"⚠️  Limitiere auf {max_applications} Bewerbungen (von {len(wohnungen)})")
        wohnungen = wohnungen[:max_applications]

    # Bewerbungsstatistik
    success_count = 0
    failed_count = 0

    # Bewerbe dich auf jede Wohnung
    for idx, wohnung in enumerate(wohnungen, 1):
        logger.info(f"\n📋 Bewerbung {idx}/{len(wohnungen)}")
        logger.info(f"📍 Wohnung: {wohnung['titel']} ({wohnung['bezirk']})")

        # ZUSÄTZLICHE SICHERHEITSPRÜFUNG: Überspringe bereits beworbene Wohnungen
        if is_already_applied(wohnung['link']):
            logger.warning(f"⚠️  Überspringe Duplikat - diese Wohnung wurde bereits beworben")
            failed_count += 1
            continue

        success = apply_to_wohnung(wohnung, user_data, headless=headless)

        if success:
            success_count += 1
            logger.info(f"✅ Bewerbung {idx}/{len(wohnungen)}: ERFOLGREICH")
        else:
            failed_count += 1
            logger.error(f"❌ Bewerbung {idx}/{len(wohnungen)}: FEHLGESCHLAGEN")

        # Pause zwischen Bewerbungen (außer bei der letzten)
        if idx < len(wohnungen):
            pause = random.uniform(30, 60)  # 30-60 Sekunden zwischen Bewerbungen
            logger.info(f"⏸️  Pausiere {pause:.0f} Sekunden vor nächster Bewerbung...")
            time.sleep(pause)

    # Abschlussbericht
    logger.info("\n" + "=" * 80)
    logger.info("📊 BEWERBUNGS-ZUSAMMENFASSUNG")
    logger.info("=" * 80)
    logger.info(f"✅ Erfolgreich: {success_count}")
    logger.info(f"❌ Fehlgeschlagen: {failed_count}")
    logger.info(f"📈 Gesamt verarbeitet: {len(wohnungen)}")
    logger.info("=" * 80)

    # Zusätzliche Statistik: Gesamtanzahl aller Bewerbungen in DB
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Gesamtanzahl aller Bewerbungen
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE applied = 1")
        total_applied = cursor.fetchone()[0]

        # Erfolgreiche Bewerbungen
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE application_status = 'success'")
        total_success = cursor.fetchone()[0]

        # Fehlgeschlagene Bewerbungen
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE application_status = 'failed'")
        total_failed = cursor.fetchone()[0]

        conn.close()

        logger.info("\n📊 GESAMTSTATISTIK (alle bisherigen Bewerbungen):")
        logger.info(f"   ✅ Erfolgreich: {total_success}")
        logger.info(f"   ❌ Fehlgeschlagen: {total_failed}")
        logger.info(f"   📈 Gesamt beworben: {total_applied}")

    except sqlite3.Error as e:
        logger.error(f"❌ Fehler beim Abrufen der Gesamtstatistik: {e}")


if __name__ == "__main__":
    import sys

    # Logging-Setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('application-bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Starte Application Bot
    # headless=False zeigt den Browser an (für Debugging)
    # headless=True versteckt den Browser (für Produktion)
    run_application_bot(headless=False, max_applications=1)
