#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Bot - Hauptskript
Kombiniert Wohnungssuche und automatische Bewerbung
"""

import sys
import logging
import argparse
from pathlib import Path
import json
from datetime import datetime

# Import der Module
try:
    import importlib.util

    # Lade gewobag-bot.py dynamisch
    spec = importlib.util.spec_from_file_location("gewobag_bot", "gewobag-bot.py")
    gewobag_bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gewobag_bot)

    # Importiere Funktionen aus gewobag-bot
    scrape_wohnungen = gewobag_bot.scrape_wohnungen
    init_database = gewobag_bot.init_database
    create_example_filter_config = gewobag_bot.create_example_filter_config
    extract_bezirke_from_website = gewobag_bot.extract_bezirke_from_website
    save_bezirke_liste = gewobag_bot.save_bezirke_liste
    BEZIRKE_LISTE_FILE = gewobag_bot.BEZIRKE_LISTE_FILE

    # Importiere aus application_bot.py
    from application_bot import run_application_bot, get_unapplied_wohnungen

except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    print("Stellen Sie sicher, dass gewobag-bot.py und application_bot.py vorhanden sind.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fehler beim Laden der Module: {e}")
    sys.exit(1)


# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gewobag-main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Heartbeat-Datei für Bot-Status-Tracking
HEARTBEAT_FILE = '.bot_heartbeat.json'


def update_bot_heartbeat(mode: str, status: str, message: str = None):
    """
    Aktualisiert die Heartbeat-Datei mit dem aktuellen Bot-Status.

    Args:
        mode: Bot-Modus (scrape, apply, full, setup)
        status: Status (started, running, completed, failed)
        message: Optional - Zusätzliche Nachricht
    """
    try:
        heartbeat_data = {
            'mode': mode,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'message': message
        }

        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump(heartbeat_data, f, indent=2)

        logger.debug(f"Heartbeat aktualisiert: {mode} - {status}")
    except Exception as e:
        logger.warning(f"Konnte Heartbeat nicht aktualisieren: {e}")


def setup_initial_config():
    """
    Führt die initiale Konfiguration durch (beim ersten Start).
    """
    logger.info("=" * 80)
    logger.info("🔧 INITIALE KONFIGURATION")
    logger.info("=" * 80)

    # Datenbank initialisieren
    logger.info("📦 Initialisiere Datenbank...")
    init_database()

    # Bezirksliste erstellen
    bezirke_path = Path(BEZIRKE_LISTE_FILE)
    if not bezirke_path.exists():
        logger.info(f"📋 Erstelle Bezirksliste ({BEZIRKE_LISTE_FILE})...")
        bezirke = extract_bezirke_from_website()
        if bezirke:
            save_bezirke_liste(bezirke)
            logger.info(f"✅ Bezirksliste mit {len(bezirke)} Einträgen erstellt")
        else:
            logger.warning("⚠️  Konnte keine Bezirke extrahieren")

    # Filter-Konfiguration erstellen
    logger.info("⚙️  Erstelle Filter-Konfiguration...")
    create_example_filter_config()

    logger.info("✅ Initiale Konfiguration abgeschlossen")
    logger.info("=" * 80)


def run_scrape_only():
    """
    Führt nur die Wohnungssuche durch (ohne Bewerbung).
    """
    update_bot_heartbeat('scrape', 'started')

    logger.info("\n" + "=" * 80)
    logger.info("🔍 MODUS: NUR WOHNUNGSSUCHE")
    logger.info("=" * 80)

    wohnungen = scrape_wohnungen()

    if wohnungen:
        logger.info(f"\n✅ {len(wohnungen)} Wohnungen gefunden")
        logger.info("💡 Führen Sie 'python main.py --apply' aus, um sich zu bewerben")
        update_bot_heartbeat('scrape', 'completed', f'{len(wohnungen)} Wohnungen gefunden')
    else:
        logger.info("\nℹ️  Keine Wohnungen gefunden")
        update_bot_heartbeat('scrape', 'completed', 'Keine Wohnungen gefunden')


def run_apply_only(headless: bool = True, max_applications: int = None):
    """
    Führt nur die Bewerbungen durch (für bereits gefundene Wohnungen).

    Args:
        headless: Browser im Headless-Modus
        max_applications: Maximale Anzahl Bewerbungen
    """
    update_bot_heartbeat('apply', 'started')

    logger.info("\n" + "=" * 80)
    logger.info("📝 MODUS: NUR BEWERBUNGEN")
    logger.info("=" * 80)

    # Prüfe, ob unbeworbene Wohnungen vorhanden sind
    unapplied = get_unapplied_wohnungen()

    if not unapplied:
        logger.info("ℹ️  Keine neuen Wohnungen für Bewerbung gefunden")
        logger.info("💡 Führen Sie zuerst 'python main.py --scrape' aus")
        update_bot_heartbeat('apply', 'completed', 'Keine Wohnungen zum Bewerben')
        return

    logger.info(f"📊 {len(unapplied)} Wohnungen ohne Bewerbung gefunden")

    # Starte Bewerbungsbot
    run_application_bot(headless=headless, max_applications=max_applications)
    update_bot_heartbeat('apply', 'completed', f'{len(unapplied)} Bewerbungen versendet')


def run_full_automation(headless: bool = True, max_applications: int = None):
    """
    Führt die komplette Automatisierung durch: Suche + Bewerbung.

    Args:
        headless: Browser im Headless-Modus
        max_applications: Maximale Anzahl Bewerbungen
    """
    update_bot_heartbeat('full', 'started')

    logger.info("\n" + "=" * 80)
    logger.info("🤖 MODUS: VOLLAUTOMATISCH (SUCHE + BEWERBUNG)")
    logger.info("=" * 80)

    # Schritt 1: Wohnungen suchen
    logger.info("\n📍 Schritt 1/2: Wohnungssuche...")
    wohnungen = scrape_wohnungen()

    if not wohnungen:
        logger.info("\nℹ️  Keine Wohnungen gefunden - keine Bewerbungen möglich")
        update_bot_heartbeat('full', 'completed', 'Keine Wohnungen gefunden')
        return

    logger.info(f"\n✅ {len(wohnungen)} Wohnungen gefunden")

    # Schritt 2: Bewerbungen versenden
    logger.info("\n📍 Schritt 2/2: Automatische Bewerbungen...")

    # Prüfe, ob unbeworbene Wohnungen vorhanden sind
    unapplied = get_unapplied_wohnungen()

    if not unapplied:
        logger.info("ℹ️  Alle Wohnungen haben bereits eine Bewerbung")
        update_bot_heartbeat('full', 'completed', f'{len(wohnungen)} Wohnungen gefunden, alle bereits beworben')
        return

    logger.info(f"📊 {len(unapplied)} neue Wohnungen - starte Bewerbungen...")

    # Starte Bewerbungsbot
    run_application_bot(headless=headless, max_applications=max_applications)

    logger.info("\n" + "=" * 80)
    logger.info("✅ VOLLAUTOMATISCHE AUSFÜHRUNG ABGESCHLOSSEN")
    logger.info("=" * 80)

    update_bot_heartbeat('full', 'completed', f'{len(unapplied)} Bewerbungen versendet')


def main():
    """
    Hauptfunktion mit Kommandozeilen-Argumenten.
    """
    parser = argparse.ArgumentParser(
        description='Gewobag Bot - Automatische Wohnungssuche und Bewerbung',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py                             # Vollautomatisch (Standard): Suchen + Bewerben
  python main.py --scrape                    # Nur Wohnungen suchen
  python main.py --apply                     # Nur auf gefundene Wohnungen bewerben
  python main.py --full                      # Suchen + Bewerben (vollautomatisch)
  python main.py --show-browser              # Mit sichtbarem Browser (Debugging)
  python main.py --max 3                     # Maximal 3 Bewerbungen versenden
  python main.py --setup                     # Initiale Konfiguration erstellen
        """
    )

    # Modi
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--scrape', action='store_true',
                       help='Nur Wohnungen suchen (ohne Bewerbung)')
    group.add_argument('--apply', action='store_true',
                       help='Nur auf bereits gefundene Wohnungen bewerben')
    group.add_argument('--full', action='store_true',
                       help='Vollautomatisch: Suchen + Bewerben (Standard)')
    group.add_argument('--setup', action='store_true',
                       help='Initiale Konfiguration durchführen')

    # Optionen
    parser.add_argument('--show-browser', action='store_true',
                        help='Browser-Fenster anzeigen (Standard: versteckt)')
    parser.add_argument('--max', type=int, metavar='N',
                        help='Maximale Anzahl Bewerbungen pro Durchlauf')

    args = parser.parse_args()

    # Führe gewählten Modus aus
    try:
        if args.setup:
            setup_initial_config()

        elif args.scrape:
            # Stelle sicher, dass die Basiskonfiguration existiert
            init_database()
            create_example_filter_config()
            run_scrape_only()

        elif args.apply:
            headless = not args.show_browser
            run_apply_only(headless=headless, max_applications=args.max)

        elif args.full:
            headless = not args.show_browser
            run_full_automation(headless=headless, max_applications=args.max)

        else:
            # STANDARD-MODUS: Vollautomatische Ausführung wenn keine Argumente übergeben wurden
            logger.info("ℹ️  Kein Modus angegeben - starte vollautomatischen Modus (Standard)")
            headless = not args.show_browser
            run_full_automation(headless=headless, max_applications=args.max)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Programm durch Benutzer abgebrochen")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                       🏠 GEWOBAG BOT v2.0 🤖                              ║
║                                                                           ║
║         Automatische Wohnungssuche und Bewerbung für Gewobag             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    main()
