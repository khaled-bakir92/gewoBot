#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Application Bot - Multi-User Wrapper
=============================================

Wrapper für application_bot.py mit Multi-User-Support.

Author: Gewobag Bot Team
Version: 2.1
"""

import sqlite3
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# Import original functions
from application_bot import (
    random_delay,
    human_like_typing,
    fill_application_form,
    mark_application_in_db,
    is_already_applied,
    APPLICATION_TIMEOUT,
    MAX_APPLICATION_RETRIES,
    RETRY_DELAY_MIN,
    RETRY_DELAY_MAX,
    STEALTH_AVAILABLE
)

# Import multi-user modules
from user_manager import UserManager
from fingerprint_pool import FingerprintManager
from user_logger import get_user_logger

DB_NAME = "gewobag_wohnungen.db"


def load_user_data_for_user(username: str, user_manager: UserManager) -> Optional[Dict]:
    """
    Load user data for specific user.

    Args:
        username: Username
        user_manager: UserManager instance

    Returns:
        User data dict or None on error
    """
    try:
        user_data = user_manager.load_user_data(username)
        return user_data
    except Exception as e:
        return None


def setup_browser_context_for_user(
    browser: Browser,
    username: str,
    fingerprint_manager: FingerprintManager,
    cookies_dir: Path
) -> BrowserContext:
    """
    Create browser context with user-specific fingerprint.

    Args:
        browser: Playwright Browser object
        username: Username
        fingerprint_manager: FingerprintManager instance
        cookies_dir: Path to user's cookies directory

    Returns:
        Configured BrowserContext
    """
    # Get user-specific Playwright config
    config = fingerprint_manager.get_playwright_config(username)

    # Add storage state (cookies/session persistence)
    storage_state_file = cookies_dir / "browser_state.json"
    if storage_state_file.exists():
        config["storage_state"] = str(storage_state_file)

    # Create context
    context = browser.new_context(**config)

    return context


def save_browser_state(context: BrowserContext, cookies_dir: Path):
    """Save browser state (cookies, local storage) for future use."""
    try:
        storage_state_file = cookies_dir / "browser_state.json"
        storage_state = context.storage_state(path=str(storage_state_file))
    except Exception:
        pass  # Ignore errors


def get_unapplied_wohnungen_for_user(username: str) -> List[Dict[str, str]]:
    """
    Get unapplied apartments for specific user.

    Args:
        username: Username

    Returns:
        List of apartment dictionaries
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM wohnungen
            WHERE (user_id = ? OR user_id IS NULL)
              AND (applied = 0 OR applied IS NULL)
            ORDER BY ts DESC
        """, (username,))

        rows = cursor.fetchall()
        conn.close()

        wohnungen = []
        for row in rows:
            wohnungen.append({
                'id': row['id'],
                'bezirk': row['bezirk'],
                'adresse': row['adresse'],
                'titel': row['titel'],
                'zimmer': row['zimmer'],
                'flaeche': row['flaeche'],
                'miete': row['miete'],
                'wbs_erforderlich': row['wbs_erforderlich'],
                'link': row['link'],
                'ts': row['ts'],
                'user_id': row['user_id']
            })

        return wohnungen

    except sqlite3.Error:
        return []


def mark_application_in_db_for_user(
    link: str,
    username: str,
    status: str,
    error: Optional[str] = None
) -> None:
    """
    Mark application in database with user_id.

    Args:
        link: Apartment link
        username: Username
        status: Application status ('success', 'failed', 'pending')
        error: Optional error message
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE wohnungen
            SET applied = 1,
                applied_ts = ?,
                application_status = ?,
                application_error = ?,
                user_id = ?
            WHERE link = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, error, username, link))

        conn.commit()
        conn.close()

    except sqlite3.Error:
        pass


def is_already_applied_by_user(link: str, username: str, logger) -> bool:
    """
    Check if user has already applied to this apartment.

    Args:
        link: Apartment link
        username: Username
        logger: Logger instance

    Returns:
        True if already applied, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT applied, application_status, applied_ts, user_id
            FROM wohnungen
            WHERE link = ? AND applied = 1 AND user_id = ?
        """, (link, username))

        result = cursor.fetchone()
        conn.close()

        if result:
            applied, status, applied_ts, user_id = result
            logger.warning(
                f"⚠️  DUPLIKAT ERKANNT: User '{username}' hat sich bereits am {applied_ts} "
                f"beworben (Status: {status})"
            )
            return True

        return False

    except sqlite3.Error:
        return False


def apply_to_wohnung_for_user(
    wohnung: Dict,
    username: str,
    user_manager: UserManager,
    fingerprint_manager: FingerprintManager,
    logger,
    headless: bool = True
) -> bool:
    """
    Apply to apartment as specific user.

    Args:
        wohnung: Apartment dict
        username: Username
        user_manager: UserManager instance
        fingerprint_manager: FingerprintManager instance
        logger: Logger instance
        headless: Run browser in headless mode

    Returns:
        True on success, False on failure
    """
    logger.info("=" * 80)
    logger.info(f"🏠 Starte Bewerbung für: {wohnung['titel']}")
    logger.info(f"👤 User: {username}")
    logger.info(f"📍 Bezirk: {wohnung['bezirk']}")
    logger.info(f"🔗 Link: {wohnung['link']}")
    logger.info("=" * 80)

    # Check for duplicates
    if is_already_applied_by_user(wohnung['link'], username, logger):
        logger.error(f"❌ ABBRUCH: User '{username}' hat sich bereits beworben!")
        return False

    # Load user data
    user_data = load_user_data_for_user(username, user_manager)
    if not user_data:
        logger.error(f"❌ Konnte Benutzerdaten für '{username}' nicht laden")
        return False

    cookies_dir = user_manager.get_cookies_dir(username)
    retry_count = 0

    while retry_count <= MAX_APPLICATION_RETRIES:
        try:
            with sync_playwright() as p:
                logger.info("🌐 Starte Browser mit erweiterten Anti-Detection-Einstellungen...")
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
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
                        '--window-size=1920,1080',
                    ]
                )

                # Create user-specific browser context
                context = setup_browser_context_for_user(
                    browser,
                    username,
                    fingerprint_manager,
                    cookies_dir
                )

                page = context.new_page()

                # Inject anti-detection scripts
                logger.debug("🔒 Injiziere erweiterte Anti-Detection-Skripte...")
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                            {name: 'Native Client', filename: 'internal-nacl-plugin'}
                        ]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['de-DE', 'de', 'en-US', 'en']
                    });
                """)

                # Apply stealth if available
                if STEALTH_AVAILABLE:
                    try:
                        from playwright_stealth import stealth_sync
                        stealth_sync(page)
                        logger.info("✅ playwright-stealth aktiviert")
                    except Exception:
                        pass

                # Fill application form
                success = fill_application_form(page, user_data, wohnung['link'])

                # Save browser state for next time
                save_browser_state(context, cookies_dir)

                browser.close()

                if success:
                    logger.info("✅ Bewerbung erfolgreich!")
                    mark_application_in_db_for_user(wohnung['link'], username, 'success')
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
                mark_application_in_db_for_user(wohnung['link'], username, 'failed', error_msg)
                return False

    return False


def run_application_bot_for_user(
    username: str,
    headless: bool = True,
    max_applications: int = None
) -> Dict[str, int]:
    """
    Run application bot for specific user.

    Args:
        username: Username
        headless: Run browser in headless mode
        max_applications: Max number of applications (None = unlimited)

    Returns:
        Dict with statistics: {'success': int, 'failed': int, 'total': int}
    """
    # Initialize managers
    user_manager = UserManager()
    fingerprint_manager = FingerprintManager(user_manager.users_dir)

    # Get user-specific logger
    logs_dir = user_manager.get_logs_dir(username)
    logger = get_user_logger(username, logs_dir, "applications")

    logger.info("=" * 80)
    logger.info(f"🤖 GEWOBAG APPLICATION BOT - USER: {username}")
    logger.info("=" * 80)

    # Validate user configuration
    validation = user_manager.validate_user_config(username)
    if not validation["valid"]:
        logger.error("❌ User-Konfiguration ungültig:")
        for error in validation["errors"]:
            logger.error(f"   • {error}")
        return {'success': 0, 'failed': 0, 'total': 0}

    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"⚠️  {warning}")

    # Get unapplied apartments
    wohnungen = get_unapplied_wohnungen_for_user(username)

    if not wohnungen:
        logger.info(f"ℹ️  Keine neuen Wohnungen für User '{username}' gefunden")
        return {'success': 0, 'failed': 0, 'total': 0}

    # Limit applications
    if max_applications and len(wohnungen) > max_applications:
        logger.info(f"⚠️  Limitiere auf {max_applications} Bewerbungen (von {len(wohnungen)})")
        wohnungen = wohnungen[:max_applications]

    # Application statistics
    success_count = 0
    failed_count = 0

    # Apply to each apartment
    for idx, wohnung in enumerate(wohnungen, 1):
        logger.info(f"\n📋 Bewerbung {idx}/{len(wohnungen)}")
        logger.info(f"📍 Wohnung: {wohnung['titel']} ({wohnung['bezirk']})")

        success = apply_to_wohnung_for_user(
            wohnung,
            username,
            user_manager,
            fingerprint_manager,
            logger,
            headless=headless
        )

        if success:
            success_count += 1
            logger.info(f"✅ Bewerbung {idx}/{len(wohnungen)}: ERFOLGREICH")
        else:
            failed_count += 1
            logger.error(f"❌ Bewerbung {idx}/{len(wohnungen)}: FEHLGESCHLAGEN")

        # Pause between applications
        if idx < len(wohnungen):
            pause = random.uniform(30, 60)
            logger.info(f"⏸️  Pausiere {pause:.0f} Sekunden vor nächster Bewerbung...")
            time.sleep(pause)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info(f"📊 BEWERBUNGS-ZUSAMMENFASSUNG - USER: {username}")
    logger.info("=" * 80)
    logger.info(f"✅ Erfolgreich: {success_count}")
    logger.info(f"❌ Fehlgeschlagen: {failed_count}")
    logger.info(f"📈 Gesamt verarbeitet: {len(wohnungen)}")
    logger.info("=" * 80)

    return {
        'success': success_count,
        'failed': failed_count,
        'total': len(wohnungen)
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python application_bot_multiuser.py <username> [--show-browser] [--max N]")
        sys.exit(1)

    username = sys.argv[1]
    headless = "--show-browser" not in sys.argv
    max_apps = None

    if "--max" in sys.argv:
        try:
            max_idx = sys.argv.index("--max")
            max_apps = int(sys.argv[max_idx + 1])
        except (IndexError, ValueError):
            print("❌ Invalid --max argument")
            sys.exit(1)

    stats = run_application_bot_for_user(username, headless=headless, max_applications=max_apps)
    print(f"\n✅ Bot finished for user '{username}': {stats}")
