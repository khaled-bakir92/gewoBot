#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Wohnungs-Bot
Extrahiert Wohnungsangebote von der Gewobag-Website und speichert sie in einer SQLite-Datenbank.
"""

import sqlite3
import logging
import sys
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler


# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gewobag-bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Konstanten
GEWOBAG_BASE_URL = "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/"
DB_NAME = "gewobag_wohnungen.db"
REQUEST_TIMEOUT = 30
BEZIRKE_LISTE_FILE = "bezirke_verfuegbar.json"
FILTER_CONFIG_FILE = "filter_config.json"

# Anti-Detection: Verschiedene realistische User-Agents
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",

    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",

    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Anti-Detection: Verschiedene Accept-Language Header
ACCEPT_LANGUAGES = [
    "de-DE,de;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "de,en-US;q=0.9,en;q=0.8",
    "de-DE,de;q=0.8,en-US;q=0.5,en;q=0.3",
]

# Anti-Detection: Mögliche Referer
REFERERS = [
    "https://www.google.com/",
    "https://www.google.de/",
    "https://www.google.com/search?q=gewobag+wohnungen",
    "https://www.google.de/search?q=gewobag+mietangebote+berlin",
]

# Retry-Konfiguration
MAX_RETRIES = 3
RETRY_DELAY_MIN = 5  # Sekunden
RETRY_DELAY_MAX = 15  # Sekunden


def load_filter_config() -> Dict[str, any]:
    """
    Lädt die Filter-Konfiguration aus der JSON-Konfigurationsdatei.

    Returns:
        Dictionary mit allen Filtern (bezirke, miete, fläche, zimmer)
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
        logger.warning(f"Konfigurationsdatei '{FILTER_CONFIG_FILE}' nicht gefunden - verwende Default-Filter")
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
        # Filtere leere Strings aus Bezirksliste für Logging
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
            logger.info(f"Aktive Filter: {' | '.join(active_filters)}")
        else:
            logger.info("Keine Filter aktiv - suche alle Wohnungen")

        return filter_config

    except json.JSONDecodeError as e:
        logger.error(f"Fehler beim Laden der Konfigurationsdatei: {e}")
        return default_config
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Laden der Konfiguration: {e}")
        return default_config


def build_url_with_filters(filter_config: Dict[str, any]) -> str:
    """
    Baut die Gewobag-URL mit allen konfigurierten Filtern.

    Args:
        filter_config: Dictionary mit Filterwerten

    Returns:
        Vollständige URL mit allen Filtern
    """
    # URL-Parameter mit Filtern aus Konfiguration
    params = (
        f"?objekttyp%5B%5D=wohnung"
        f"&gesamtmiete_von={filter_config.get('gesamtmiete_von', '')}"
        f"&gesamtmiete_bis={filter_config.get('gesamtmiete_bis', '')}"
        f"&gesamtflaeche_von={filter_config.get('gesamtflaeche_von', '')}"
        f"&gesamtflaeche_bis={filter_config.get('gesamtflaeche_bis', '')}"
        f"&zimmer_von={filter_config.get('zimmer_von', '')}"
        f"&zimmer_bis={filter_config.get('zimmer_bis', '')}"
        f"&sort-by="
    )

    gewuenschte_bezirke = filter_config.get('gewuenschte_bezirke', [])

    # Filtere leere Strings aus der Bezirksliste
    gewuenschte_bezirke = [b for b in gewuenschte_bezirke if b and b.strip()]

    if gewuenschte_bezirke:
        # Bezirksfilter hinzufügen: &bezirke[]=wert1&bezirke[]=wert2
        bezirk_params = "".join(f"&bezirke%5B%5D={bezirk}" for bezirk in gewuenschte_bezirke)
        url = GEWOBAG_BASE_URL + params + bezirk_params
    else:
        url = GEWOBAG_BASE_URL + params

    return url


def extract_bezirke_from_website() -> List[Dict[str, str]]:
    """
    Extrahiert alle verfügbaren Bezirke direkt von der Gewobag-Website.

    Returns:
        Liste von Dictionaries mit Bezirksinformationen (value, name, typ)
    """
    logger.info("Extrahiere verfügbare Bezirke von der Gewobag-Website...")

    # Basis-URL laden (ohne Filter)
    base_params = (
        "?objekttyp%5B%5D=wohnung&gesamtmiete_von=&gesamtmiete_bis="
        "&gesamtflaeche_von=&gesamtflaeche_bis=&zimmer_von=&zimmer_bis=&sort-by="
    )
    url = GEWOBAG_BASE_URL + base_params

    html = fetch_html(url)
    if not html:
        logger.error("Konnte Website nicht laden - kann Bezirke nicht extrahieren")
        return []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        bezirke_liste = []

        # Suche nach allen Bezirks-Checkboxen (name="bezirke[]")
        checkboxes = soup.find_all('input', attrs={'name': 'bezirke[]'})

        if not checkboxes:
            logger.warning("Keine Bezirks-Checkboxen auf der Website gefunden")
            return []

        for checkbox in checkboxes:
            value = checkbox.get('value', '')
            title = checkbox.get('data-title', '')

            # Bestimme Typ (Hauptbezirk oder Ortsteil)
            css_classes = checkbox.get('class', [])
            ist_hauptbezirk = 'selectable-group-option' in css_classes

            if value and title:
                bezirke_liste.append({
                    'value': value,
                    'name': title,
                    'typ': 'Hauptbezirk' if ist_hauptbezirk else 'Ortsteil'
                })

        logger.info(f"{len(bezirke_liste)} Bezirke/Ortsteile gefunden")
        return bezirke_liste

    except Exception as e:
        logger.error(f"Fehler beim Extrahieren der Bezirke: {e}")
        return []


def save_bezirke_liste(bezirke: List[Dict[str, str]]) -> bool:
    """
    Speichert die Liste der verfügbaren Bezirke in einer JSON-Datei.

    Args:
        bezirke: Liste der Bezirke

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        output = {
            'stand': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'anzahl': len(bezirke),
            'bezirke': bezirke
        }

        with open(BEZIRKE_LISTE_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(f"Bezirksliste erfolgreich in '{BEZIRKE_LISTE_FILE}' gespeichert")
        return True

    except Exception as e:
        logger.error(f"Fehler beim Speichern der Bezirksliste: {e}")
        return False


def create_example_filter_config() -> bool:
    """
    Erstellt eine Beispiel-Konfigurationsdatei, falls noch keine existiert.

    Returns:
        True bei Erfolg, False bei Fehler
    """
    config_path = Path(FILTER_CONFIG_FILE)

    if config_path.exists():
        logger.info(f"Konfigurationsdatei '{FILTER_CONFIG_FILE}' existiert bereits")
        return True

    try:
        example_config = {
            '_kommentar': 'Konfiguration für Wohnungsfilter',
            '_beispiel_bezirke': [
                'friedrichshain-kreuzberg',
                'mitte',
                'pankow-prenzlauer-berg'
            ],
            'gewuenschte_bezirke': [],

            '_kommentar_miete': 'Gesamtmiete in Euro (leer = keine Einschränkung)',
            'gesamtmiete_von': '',
            'gesamtmiete_bis': '',

            '_kommentar_flaeche': 'Wohnfläche in m² (leer = keine Einschränkung)',
            'gesamtflaeche_von': '',
            'gesamtflaeche_bis': '',

            '_kommentar_zimmer': 'Anzahl Zimmer (leer = keine Einschränkung)',
            'zimmer_von': '',
            'zimmer_bis': '',

            "_kommentar_wbs": "WBS-Filter: 'mit' = nur WBS-Wohnungen, 'ohne' = nur ohne WBS, 'egal' oder leer = alle",
            'wbs': ''
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, ensure_ascii=False, indent=2)

        logger.info(f"Beispiel-Konfigurationsdatei '{FILTER_CONFIG_FILE}' erstellt")
        return True

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Konfigurationsdatei: {e}")
        return False


def init_database() -> None:
    """
    Initialisiert die SQLite-Datenbank und erstellt die Tabelle, falls sie nicht existiert.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wohnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bezirk TEXT,
                adresse TEXT,
                titel TEXT,
                zimmer TEXT,
                flaeche TEXT,
                miete TEXT,
                wbs_erforderlich INTEGER DEFAULT 0,
                link TEXT UNIQUE,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied INTEGER DEFAULT 0,
                applied_ts TIMESTAMP,
                application_status TEXT,
                application_error TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Datenbank '{DB_NAME}' erfolgreich initialisiert")
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Initialisieren der Datenbank: {e}")
        raise


def get_random_headers() -> Dict[str, str]:
    """
    Generiert zufällige, realistische HTTP-Header für Anti-Detection.

    Returns:
        Dictionary mit zufälligen Headern
    """
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': random.choice(ACCEPT_LANGUAGES),
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': random.choice(REFERERS),
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'max-age=0',
    }


def random_delay(min_seconds: float = 2.0, max_seconds: float = 7.0) -> None:
    """
    Wartet eine zufällige Zeit, um menschliches Verhalten zu simulieren.

    Args:
        min_seconds: Minimale Wartezeit
        max_seconds: Maximale Wartezeit
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"⏸️  Pausiere {delay:.2f} Sekunden (Anti-Detection)...")
    time.sleep(delay)


def fetch_html(url: str, retry_count: int = 0) -> Optional[str]:
    """
    Lädt den HTML-Code von der angegebenen URL mit Anti-Detection und Retry-Logik.

    Args:
        url: Die URL der Gewobag-Mietangebote
        retry_count: Aktueller Retry-Versuch (intern)

    Returns:
        HTML-Code als String oder None bei Fehler
    """
    # Zufällige Header für jeden Request
    headers = get_random_headers()

    try:
        logger.info(f"🌐 Lade Seite: {url}")
        logger.debug(f"User-Agent: {headers['User-Agent'][:50]}...")

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        # Erfolgreicher Request
        if response.status_code == 200:
            response.encoding = 'utf-8'
            logger.info(f"✅ Seite erfolgreich geladen (Status: {response.status_code})")
            return response.text

        # Rate Limiting (429) oder Forbidden (403)
        elif response.status_code in [403, 429]:
            if retry_count < MAX_RETRIES:
                retry_delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                logger.warning(
                    f"⚠️  HTTP {response.status_code} - "
                    f"Retry {retry_count + 1}/{MAX_RETRIES} in {retry_delay:.1f}s..."
                )
                time.sleep(retry_delay)
                return fetch_html(url, retry_count + 1)
            else:
                logger.error(f"❌ HTTP {response.status_code} - Max Retries erreicht")
                return None

        # Andere HTTP-Fehler
        else:
            logger.warning(f"⚠️  HTTP {response.status_code} für {url}")
            response.raise_for_status()
            return None

    except requests.exceptions.Timeout:
        if retry_count < MAX_RETRIES:
            retry_delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
            logger.warning(
                f"⏱️  Timeout (>{REQUEST_TIMEOUT}s) - "
                f"Retry {retry_count + 1}/{MAX_RETRIES} in {retry_delay:.1f}s..."
            )
            time.sleep(retry_delay)
            return fetch_html(url, retry_count + 1)
        else:
            logger.error(f"❌ Timeout - Max Retries erreicht")
            return None

    except requests.exceptions.ConnectionError as e:
        if retry_count < MAX_RETRIES:
            retry_delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
            logger.warning(
                f"🔌 Verbindungsfehler - "
                f"Retry {retry_count + 1}/{MAX_RETRIES} in {retry_delay:.1f}s..."
            )
            time.sleep(retry_delay)
            return fetch_html(url, retry_count + 1)
        else:
            logger.error(f"❌ Verbindungsfehler - Max Retries erreicht: {e}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Fehler beim Laden der Seite: {e}")
        return None


def get_total_pages(html: str) -> int:
    """
    Ermittelt die Gesamtzahl der verfügbaren Seiten aus dem HTML.

    Args:
        html: HTML-Code der ersten Seite

    Returns:
        Anzahl der Seiten (mindestens 1)
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Suche nach Paginierung: <a class="page-numbers">2</a>, <a class="page-numbers">3</a>, etc.
        page_links = soup.find_all('a', class_='page-numbers')

        if not page_links:
            logger.info("Keine Paginierung gefunden - nur 1 Seite vorhanden")
            return 1

        # Extrahiere alle Seitenzahlen und finde das Maximum
        page_numbers = []
        for link in page_links:
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))

        if page_numbers:
            total = max(page_numbers)
            logger.info(f"Paginierung gefunden: {total} Seiten insgesamt")
            return total
        else:
            return 1

    except Exception as e:
        logger.warning(f"Fehler beim Ermitteln der Seitenzahl: {e}")
        return 1


def parse_wohnungen(html: str) -> List[Dict[str, str]]:
    """
    Parst den HTML-Code und extrahiert alle Wohnungsangebote.

    Args:
        html: HTML-Code der Seite

    Returns:
        Liste von Dictionaries mit Wohnungsinformationen
    """
    try:
        logger.info("Starte Parsing des HTML-Codes")
        soup = BeautifulSoup(html, 'html.parser')
        angebote = soup.find_all('div', class_='angebot-content')

        if not angebote:
            logger.warning("Keine Angebote gefunden!")
            return []

        logger.info(f"{len(angebote)} Angebote gefunden")
        wohnungen = []

        for idx, angebot in enumerate(angebote, 1):
            try:
                wohnung = extract_wohnung_data(angebot)
                if wohnung:
                    wohnungen.append(wohnung)
                    logger.debug(f"Angebot {idx} erfolgreich extrahiert: {wohnung['titel']}")
            except Exception as e:
                logger.warning(f"Fehler beim Extrahieren von Angebot {idx}: {e}")
                continue

        logger.info(f"{len(wohnungen)} Angebote erfolgreich extrahiert")
        return wohnungen

    except Exception as e:
        logger.error(f"Fehler beim Parsing: {e}")
        return []


def extract_wohnung_data(angebot) -> Optional[Dict[str, str]]:
    """
    Extrahiert die Daten aus einem einzelnen Angebot.

    Args:
        angebot: BeautifulSoup-Element eines Angebots

    Returns:
        Dictionary mit Wohnungsdaten oder None bei Fehler
    """
    wohnung = {
        'bezirk': '',
        'adresse': '',
        'titel': '',
        'zimmer': '',
        'flaeche': '',
        'miete': '',
        'wbs_erforderlich': 0,
        'link': ''
    }

    # Bezirk extrahieren
    bezirk_element = angebot.find('tr', class_='angebot-region')
    if bezirk_element:
        td = bezirk_element.find('td')
        if td:
            wohnung['bezirk'] = td.get_text(strip=True)

    # Adresse extrahieren
    address_element = angebot.find('address')
    if address_element:
        wohnung['adresse'] = address_element.get_text(strip=True)

    # Titel extrahieren
    titel_element = angebot.find('h3', class_='angebot-title')
    if titel_element:
        wohnung['titel'] = titel_element.get_text(strip=True)

    # Fläche und Zimmer extrahieren und trennen
    area_element = angebot.find('tr', class_='angebot-area')
    if area_element:
        td = area_element.find('td')
        if td:
            area_text = td.get_text(strip=True)
            # Format: "3 Zimmer | 80,38 m²" -> trennen bei "|"
            if '|' in area_text:
                parts = area_text.split('|')
                wohnung['zimmer'] = parts[0].strip()  # "3 Zimmer"
                wohnung['flaeche'] = parts[1].strip()  # "80,38 m²"
            else:
                # Falls kein "|" vorhanden, alles in flaeche
                wohnung['flaeche'] = area_text
                wohnung['zimmer'] = ''

    # Gesamtmiete extrahieren
    kosten_element = angebot.find('tr', class_='angebot-kosten')
    if kosten_element:
        td = kosten_element.find('td')
        if td:
            wohnung['miete'] = td.get_text(strip=True)

    # WBS-Status extrahieren
    wbs_element = angebot.find('div', class_='pictograms typ-wbs')
    if wbs_element:
        wohnung['wbs_erforderlich'] = 1
        logger.debug(f"WBS erforderlich für: {wohnung['titel']}")
    else:
        wohnung['wbs_erforderlich'] = 0

    # Link extrahieren
    footer = angebot.find('div', class_='angebot-footer')
    if footer:
        link_element = footer.find('a', class_='read-more-link')
        if link_element and link_element.get('href'):
            wohnung['link'] = link_element.get('href')

    # Validierung: Link muss vorhanden sein
    if not wohnung['link']:
        logger.warning("Angebot ohne Link gefunden - überspringe")
        return None

    return wohnung


def save_to_database(wohnungen: List[Dict[str, str]]) -> tuple:
    """
    Speichert die Wohnungen in der SQLite-Datenbank.

    Args:
        wohnungen: Liste von Wohnungs-Dictionaries

    Returns:
        Tuple (neu_gespeichert, bereits_vorhanden)
    """
    if not wohnungen:
        logger.info("Keine Wohnungen zum Speichern vorhanden")
        return (0, 0)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        neu_gespeichert = 0
        bereits_vorhanden = 0

        for wohnung in wohnungen:
            try:
                cursor.execute("""
                    INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete, wbs_erforderlich, link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    wohnung['bezirk'],
                    wohnung['adresse'],
                    wohnung['titel'],
                    wohnung['zimmer'],
                    wohnung['flaeche'],
                    wohnung['miete'],
                    wohnung['wbs_erforderlich'],
                    wohnung['link']
                ))
                neu_gespeichert += 1
                logger.info(f"Neue Wohnung gespeichert: {wohnung['titel']} in {wohnung['bezirk']}")
            except sqlite3.IntegrityError:
                bereits_vorhanden += 1
                logger.debug(f"Wohnung bereits vorhanden: {wohnung['link']}")

        conn.commit()
        conn.close()

        logger.info(f"Speicherung abgeschlossen: {neu_gespeichert} neu, {bereits_vorhanden} bereits vorhanden")
        return (neu_gespeichert, bereits_vorhanden)

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern in die Datenbank: {e}")
        return (0, 0)


def fetch_all_pages(base_url: str) -> List[Dict[str, str]]:
    """
    Lädt alle paginierten Seiten und sammelt alle Wohnungen mit Anti-Detection.

    Args:
        base_url: Die Basis-URL (Seite 1)

    Returns:
        Liste aller Wohnungen von allen Seiten
    """
    all_wohnungen = []

    # Erste Seite laden
    logger.info("📄 Starte Paginierung - lade Seite 1...")
    html = fetch_html(base_url)
    if not html:
        logger.error("Konnte Seite 1 nicht laden - Abbruch")
        return []

    # Wohnungen von Seite 1 extrahieren
    wohnungen_page1 = parse_wohnungen(html)
    all_wohnungen.extend(wohnungen_page1)
    logger.info(f"📊 Seite 1: {len(wohnungen_page1)} Wohnungen gefunden")

    # Gesamtzahl der Seiten ermitteln
    total_pages = get_total_pages(html)

    # Falls es weitere Seiten gibt, diese auch laden
    if total_pages > 1:
        logger.info(f"📚 Paginierung erkannt: {total_pages} Seiten insgesamt")

        for page_num in range(2, total_pages + 1):
            # Zufällige Pause zwischen Seiten (menschliches Verhalten simulieren)
            random_delay(min_seconds=2.0, max_seconds=7.0)

            # URL für Seite N erstellen
            # Format: https://www.gewobag.de/.../page/2/?filter=...
            if '/page/' in base_url:
                # Falls bereits ein /page/ in der URL ist (sollte nicht vorkommen)
                logger.warning(f"URL enthält bereits '/page/' - überspringe Seite {page_num}")
                continue

            # Prüfe, ob URL bereits Query-Parameter hat
            if '?' in base_url:
                # Füge /page/N vor dem ? ein
                parts = base_url.split('?', 1)
                page_url = f"{parts[0]}page/{page_num}/?{parts[1]}"
            else:
                # Keine Query-Parameter - füge /page/N/ hinzu
                page_url = f"{base_url}page/{page_num}/"

            logger.info(f"📄 Lade Seite {page_num}/{total_pages}...")
            html = fetch_html(page_url)

            if not html:
                logger.warning(f"⚠️  Konnte Seite {page_num} nicht laden - überspringe")
                continue

            wohnungen = parse_wohnungen(html)
            all_wohnungen.extend(wohnungen)
            logger.info(f"📊 Seite {page_num}: {len(wohnungen)} Wohnungen gefunden")

    logger.info(f"✅ Alle {total_pages} Seiten erfolgreich geladen - insgesamt {len(all_wohnungen)} Wohnungen gefunden")
    return all_wohnungen


def apply_client_side_filters(wohnungen: List[Dict[str, str]], filter_config: Dict[str, any]) -> List[Dict[str, str]]:
    """
    Wendet clientseitige Filter an (für Filter, die die Website nicht korrekt verarbeitet).

    Args:
        wohnungen: Liste der Wohnungen
        filter_config: Filter-Konfiguration

    Returns:
        Gefilterte Liste der Wohnungen
    """
    filtered = []
    zimmer_von = filter_config.get('zimmer_von', '')
    zimmer_bis = filter_config.get('zimmer_bis', '')
    wbs_filter = filter_config.get('wbs', '').lower()

    # Wenn keine clientseitigen Filter aktiv sind, alles zurückgeben
    if not zimmer_von and not zimmer_bis and not wbs_filter:
        return wohnungen

    for wohnung in wohnungen:
        # Zimmerfilter anwenden
        if zimmer_von or zimmer_bis:
            zimmer_text = wohnung.get('zimmer', '')
            try:
                # Extrahiere Zimmerzahl aus "3 Zimmer" -> 3
                zimmer_str = zimmer_text.split()[0] if zimmer_text else '0'
                zimmer_zahl = float(zimmer_str.replace(',', '.'))

                # Filter anwenden
                if zimmer_von and zimmer_zahl < float(zimmer_von):
                    continue
                if zimmer_bis and zimmer_zahl > float(zimmer_bis):
                    continue
            except (ValueError, IndexError):
                logger.debug(f"Konnte Zimmerzahl nicht parsen: {zimmer_text}")
                continue

        # WBS-Filter anwenden
        if wbs_filter and wbs_filter in ['mit', 'ohne']:
            wbs_erforderlich = wohnung.get('wbs_erforderlich', 0)
            if wbs_filter == 'mit' and wbs_erforderlich != 1:
                continue  # Nur WBS-Wohnungen gewünscht, aber diese hat kein WBS
            if wbs_filter == 'ohne' and wbs_erforderlich == 1:
                continue  # Nur ohne WBS gewünscht, aber diese hat WBS

        filtered.append(wohnung)

    if len(filtered) < len(wohnungen):
        logger.info(f"Clientseitige Filterung: {len(wohnungen)} -> {len(filtered)} Wohnungen")

    return filtered


def scrape_wohnungen() -> List[Dict[str, str]]:
    """
    Hauptfunktion: Lädt alle Seiten, parst sie und speichert die Angebote.

    Returns:
        Liste der gefundenen Wohnungen (nur die aktuell gefilterten)
    """
    logger.info("=" * 70)
    logger.info("Starte Gewobag Wohnungssuche (mit Paginierung)")
    logger.info("=" * 70)

    # Filter aus Konfiguration laden
    filter_config = load_filter_config()

    # URL mit Filtern erstellen (ohne zimmer_von, da Website das nicht korrekt verarbeitet)
    # Workaround: zimmer_von clientseitig filtern
    url_filter_config = filter_config.copy()
    if filter_config.get('zimmer_von'):
        logger.info("Hinweis: zimmer_von wird clientseitig gefiltert (Website-Bug)")
        url_filter_config['zimmer_von'] = ''  # Von Website-URL entfernen

    url = build_url_with_filters(url_filter_config)

    # Alle Seiten laden und Wohnungen sammeln
    wohnungen = fetch_all_pages(url)
    if not wohnungen:
        logger.warning("Keine Wohnungen gefunden")
        return []

    # Clientseitige Zimmerfilterung anwenden
    wohnungen = apply_client_side_filters(wohnungen, filter_config)

    if not wohnungen:
        logger.warning("Keine Wohnungen nach Filterung übrig")
        return []

    # In Datenbank speichern (für historische Zwecke)
    neu, vorhanden = save_to_database(wohnungen)

    logger.info("=" * 70)
    logger.info(f"Zusammenfassung: {len(wohnungen)} Angebote gefunden (mit aktiven Filtern), {neu} neu gespeichert, {vorhanden} bereits bekannt")
    logger.info("=" * 70)

    # WICHTIG: Nur die aktuell gefilterten Wohnungen zurückgeben, nicht alle aus der DB
    return wohnungen


def print_wohnungen(wohnungen: List[Dict[str, str]]) -> None:
    """
    Gibt die Wohnungen formatiert auf der Konsole aus.

    Args:
        wohnungen: Liste von Wohnungs-Dictionaries
    """
    if not wohnungen:
        print("\nKeine Wohnungen gefunden.\n")
        return

    print(f"\n{'=' * 80}")
    print(f"GEFUNDENE WOHNUNGEN ({len(wohnungen)})")
    print(f"{'=' * 80}\n")

    for idx, w in enumerate(wohnungen, 1):
        wbs_status = "✓ WBS erforderlich" if w.get('wbs_erforderlich', 0) == 1 else "✗ Kein WBS"
        print(f"[{idx}] {w['titel']}")
        print(f"    Bezirk:      {w['bezirk']}")
        print(f"    Adresse:     {w['adresse']}")
        print(f"    Zimmer:      {w['zimmer']}")
        print(f"    Fläche:      {w['flaeche']}")
        print(f"    Miete:       {w['miete']}")
        print(f"    WBS:         {wbs_status}")
        print(f"    Link:        {w['link']}")
        print()


def scheduled_job():
    """Job-Funktion für den Scheduler."""
    try:
        scrape_wohnungen()
    except Exception as e:
        logger.error(f"Fehler im geplanten Job: {e}")


def run_scheduler(interval_minutes: int = 60):
    """
    Startet den Scheduler für regelmäßige Ausführung.

    Args:
        interval_minutes: Intervall in Minuten zwischen den Ausführungen
    """
    logger.info(f"Starte Scheduler (Intervall: {interval_minutes} Minuten)")

    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_job, 'interval', minutes=interval_minutes)

    # Erste Ausführung sofort
    logger.info("Führe ersten Scan durch...")
    scheduled_job()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler wurde beendet")


if __name__ == "__main__":
    try:
        # Datenbank initialisieren
        init_database()

        # Beim ersten Start: Bezirksliste von der Website holen
        bezirke_path = Path(BEZIRKE_LISTE_FILE)
        if not bezirke_path.exists():
            logger.info(f"'{BEZIRKE_LISTE_FILE}' nicht gefunden - erstelle Bezirksliste...")
            bezirke = extract_bezirke_from_website()
            if bezirke:
                save_bezirke_liste(bezirke)
                print(f"\n✓ Bezirksliste mit {len(bezirke)} Einträgen erstellt: {BEZIRKE_LISTE_FILE}")
            else:
                logger.warning("Konnte keine Bezirke von der Website extrahieren")

        # Beispiel-Konfiguration erstellen, falls noch nicht vorhanden
        create_example_filter_config()

        # Einmalige Ausführung
        wohnungen = scrape_wohnungen()
        print_wohnungen(wohnungen)

        # Optional: Scheduler starten
        # Auskommentieren, um den Scheduler zu aktivieren
        # print("\nStarte automatischen Scheduler...")
        # print("Drücke Ctrl+C zum Beenden")
        # run_scheduler(interval_minutes=60)

    except KeyboardInterrupt:
        logger.info("Programm durch Benutzer beendet")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)
