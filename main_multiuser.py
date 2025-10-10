#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Bot - Multi-User Hauptskript
=====================================

Kombiniert Wohnungssuche und automatische Bewerbung für mehrere Nutzer.

Author: Gewobag Bot Team
Version: 2.1
"""

import sys
import logging
import argparse
import time
import random
from pathlib import Path

# Import multi-user modules
from user_manager import UserManager, print_user_list, print_user_info
from gewobag_bot_multiuser import scrape_wohnungen_for_user
from application_bot_multiuser import run_application_bot_for_user
from user_logger import get_user_logger

# Import original functions for setup
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("gewobag_bot", "gewobag-bot.py")
    gewobag_bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gewobag_bot)

    extract_bezirke_from_website = gewobag_bot.extract_bezirke_from_website
    save_bezirke_liste = gewobag_bot.save_bezirke_liste
    BEZIRKE_LISTE_FILE = gewobag_bot.BEZIRKE_LISTE_FILE

except Exception as e:
    print(f"❌ Fehler beim Laden der Module: {e}")
    sys.exit(1)

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gewobag-multiuser.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_initial_config():
    """Initial configuration (database, bezirke list)."""
    logger.info("=" * 80)
    logger.info("🔧 INITIALE KONFIGURATION (MULTI-USER)")
    logger.info("=" * 80)

    # Initialize database with multi-user support
    from migrate_database import init_database_with_multiuser
    logger.info("📦 Initialisiere Datenbank mit Multi-User-Support...")
    init_database_with_multiuser()

    # Create bezirke list
    bezirke_path = Path(BEZIRKE_LISTE_FILE)
    if not bezirke_path.exists():
        logger.info(f"📋 Erstelle Bezirksliste ({BEZIRKE_LISTE_FILE})...")
        bezirke = extract_bezirke_from_website()
        if bezirke:
            save_bezirke_liste(bezirke)
            logger.info(f"✅ Bezirksliste mit {len(bezirke)} Einträgen erstellt")
        else:
            logger.warning("⚠️  Konnte keine Bezirke extrahieren")

    logger.info("✅ Initiale Konfiguration abgeschlossen")
    logger.info("=" * 80)
    logger.info("\n💡 Nächster Schritt:")
    logger.info("   python main_multiuser.py --create-user <username>")


def create_user(username: str):
    """Create a new user profile."""
    user_manager = UserManager()

    if user_manager.create_user(username):
        logger.info(f"\n✅ User '{username}' erfolgreich erstellt!")
        logger.info(f"\n📝 Bitte bearbeiten Sie:")
        logger.info(f"   {user_manager.get_user_data_path(username)}")
        logger.info(f"   {user_manager.get_filter_config_path(username)}")
        logger.info(f"\n💡 Testen Sie mit:")
        logger.info(f"   python main_multiuser.py --user {username} --scrape")
    else:
        logger.error(f"❌ User '{username}' existiert bereits!")


def run_for_single_user(username: str, mode: str, headless: bool = True, max_applications: int = None):
    """
    Run bot for a single user.

    Args:
        username: Username
        mode: 'scrape', 'apply', or 'full'
        headless: Run browser in headless mode
        max_applications: Max number of applications
    """
    user_manager = UserManager()

    if not user_manager.user_exists(username):
        logger.error(f"❌ User '{username}' existiert nicht!")
        logger.info(f"💡 Erstellen Sie ihn mit: python main_multiuser.py --create-user {username}")
        return

    # Validate user config
    validation = user_manager.validate_user_config(username)
    if not validation["valid"]:
        logger.error(f"❌ Konfiguration für User '{username}' ungültig:")
        for error in validation["errors"]:
            logger.error(f"   • {error}")
        return

    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"⚠️  {warning}")

    logger.info("=" * 80)
    logger.info(f"🤖 BOT-AUSFÜHRUNG FÜR USER: {username}")
    logger.info("=" * 80)

    if mode == 'scrape':
        logger.info(f"\n🔍 Modus: Nur Wohnungssuche")
        wohnungen = scrape_wohnungen_for_user(username)
        if wohnungen:
            logger.info(f"\n✅ {len(wohnungen)} Wohnungen für User '{username}' gefunden")

    elif mode == 'apply':
        logger.info(f"\n📝 Modus: Nur Bewerbungen")
        stats = run_application_bot_for_user(username, headless=headless, max_applications=max_applications)
        logger.info(f"\n✅ Bewerbungen abgeschlossen: {stats}")

    elif mode == 'full':
        logger.info(f"\n🤖 Modus: Vollautomatisch (Suche + Bewerbung)")

        # Step 1: Scrape
        logger.info(f"\n📍 Schritt 1/2: Wohnungssuche...")
        wohnungen = scrape_wohnungen_for_user(username)

        if not wohnungen:
            logger.info(f"\nℹ️  Keine Wohnungen für User '{username}' gefunden")
            return

        logger.info(f"\n✅ {len(wohnungen)} Wohnungen gefunden")

        # Step 2: Apply
        logger.info(f"\n📍 Schritt 2/2: Automatische Bewerbungen...")
        stats = run_application_bot_for_user(username, headless=headless, max_applications=max_applications)

        logger.info("\n" + "=" * 80)
        logger.info(f"✅ VOLLAUTOMATISCHE AUSFÜHRUNG FÜR USER '{username}' ABGESCHLOSSEN")
        logger.info(f"   Erfolgreich: {stats['success']} | Fehlgeschlagen: {stats['failed']}")
        logger.info("=" * 80)


def run_for_all_users(mode: str, headless: bool = True, max_applications: int = None):
    """
    Run bot for all users sequentially.

    Args:
        mode: 'scrape', 'apply', or 'full'
        headless: Run browser in headless mode
        max_applications: Max number of applications per user
    """
    user_manager = UserManager()
    users = user_manager.list_users()

    if not users:
        logger.error("❌ Keine User gefunden!")
        logger.info("💡 Erstellen Sie zuerst einen User mit: python main_multiuser.py --create-user <username>")
        return

    logger.info("=" * 80)
    logger.info(f"🤖 BOT-AUSFÜHRUNG FÜR ALLE USER (SEQUENTIELL)")
    logger.info(f"   Anzahl User: {len(users)}")
    logger.info(f"   Modus: {mode}")
    logger.info("=" * 80)

    total_stats = {'success': 0, 'failed': 0, 'total': 0}

    for idx, username in enumerate(users, 1):
        logger.info(f"\n\n{'='*80}")
        logger.info(f"👤 USER {idx}/{len(users)}: {username}")
        logger.info(f"{'='*80}")

        # Run for this user
        run_for_single_user(username, mode, headless=headless, max_applications=max_applications)

        # Pause between users (to avoid detection)
        if idx < len(users):
            pause = random.uniform(60, 120)  # 1-2 minutes between users
            logger.info(f"\n⏸️  Pausiere {pause:.0f} Sekunden vor nächstem User...")
            time.sleep(pause)

    logger.info("\n\n" + "=" * 80)
    logger.info("✅ ALLE USER ABGESCHLOSSEN")
    logger.info("=" * 80)


def main():
    """Main function with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Gewobag Bot - Multi-User Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Setup
  python main_multiuser.py --setup                        # Initiale Konfiguration
  python main_multiuser.py --create-user user1            # User erstellen
  python main_multiuser.py --list-users                   # Alle User auflisten
  python main_multiuser.py --info user1                   # User-Info anzeigen

  # Einzelner User
  python main_multiuser.py --user user1 --scrape          # Suchen für user1
  python main_multiuser.py --user user1 --apply           # Bewerben für user1
  python main_multiuser.py --user user1 --full            # Vollautomatisch für user1

  # Alle User
  python main_multiuser.py --all-users --scrape           # Suchen für alle User
  python main_multiuser.py --all-users --full             # Vollautomatisch für alle User

  # Optionen
  python main_multiuser.py --user user1 --show-browser    # Mit sichtbarem Browser
  python main_multiuser.py --user user1 --max 3           # Max. 3 Bewerbungen
        """
    )

    # Setup commands
    setup_group = parser.add_argument_group('Setup')
    setup_group.add_argument('--setup', action='store_true',
                             help='Initiale Konfiguration durchführen')
    setup_group.add_argument('--create-user', metavar='USERNAME',
                             help='Neuen User erstellen')

    # Info commands
    info_group = parser.add_argument_group('Information')
    info_group.add_argument('--list-users', action='store_true',
                            help='Alle User auflisten')
    info_group.add_argument('--info', metavar='USERNAME',
                            help='User-Informationen anzeigen')

    # Execution commands
    exec_group = parser.add_argument_group('Ausführung')
    exec_target = exec_group.add_mutually_exclusive_group()
    exec_target.add_argument('--user', metavar='USERNAME',
                             help='Bot für einzelnen User ausführen')
    exec_target.add_argument('--all-users', action='store_true',
                             help='Bot für alle User nacheinander ausführen')

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--scrape', action='store_true',
                            help='Nur Wohnungen suchen')
    mode_group.add_argument('--apply', action='store_true',
                            help='Nur bewerben')
    mode_group.add_argument('--full', action='store_true',
                            help='Vollautomatisch: Suchen + Bewerben')

    # Options
    parser.add_argument('--show-browser', action='store_true',
                        help='Browser-Fenster anzeigen')
    parser.add_argument('--max', type=int, metavar='N',
                        help='Maximale Anzahl Bewerbungen pro User')
    parser.add_argument('--no-submit', action='store_true',
                        help='Formular NICHT absenden (nur zum Testen)')

    args = parser.parse_args()

    try:
        # Setup commands
        if args.setup:
            setup_initial_config()

        elif args.create_user:
            create_user(args.create_user)

        elif args.list_users:
            print_user_list()

        elif args.info:
            print_user_info(args.info)

        # Execution commands
        elif args.user or args.all_users:
            # Determine mode
            if args.scrape:
                mode = 'scrape'
            elif args.apply:
                mode = 'apply'
            elif args.full:
                mode = 'full'
            else:
                # Default mode: full
                mode = 'full'
                logger.info("ℹ️  Kein Modus angegeben - verwende 'full' (Standard)")

            headless = not args.show_browser

            if args.user:
                run_for_single_user(args.user, mode, headless=headless, max_applications=args.max)
            else:  # args.all_users
                run_for_all_users(mode, headless=headless, max_applications=args.max)

        else:
            parser.print_help()
            print("\n💡 Starten Sie mit: python main_multiuser.py --setup")

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
║                    🏠 GEWOBAG BOT v2.1 (MULTI-USER) 🤖                   ║
║                                                                           ║
║         Automatische Wohnungssuche und Bewerbung für Gewobag             ║
║                       Mehrere Nutzer - Separate Sessions                 ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    main()
