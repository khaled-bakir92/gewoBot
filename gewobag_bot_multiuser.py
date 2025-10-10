#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gewobag Bot - Multi-User Wrapper
=================================

Wrapper für gewobag-bot.py mit Multi-User-Support.

Author: Gewobag Bot Team
Version: 2.1
"""

import sqlite3
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# Import original functions
import importlib.util

# Load gewobag-bot.py dynamically (has hyphen in name)
spec = importlib.util.spec_from_file_location("gewobag_bot", "gewobag-bot.py")
gewobag_bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gewobag_bot_module)

fetch_all_pages = gewobag_bot_module.fetch_all_pages
parse_wohnungen = gewobag_bot_module.parse_wohnungen
apply_client_side_filters = gewobag_bot_module.apply_client_side_filters
build_url_with_filters = gewobag_bot_module.build_url_with_filters
DB_NAME = gewobag_bot_module.DB_NAME

# Import multi-user modules
from user_manager import UserManager
from user_logger import get_user_logger


def save_to_database_for_user(wohnungen: List[Dict[str, str]], username: str, logger) -> tuple:
    """
    Save apartments to database with user_id.

    Args:
        wohnungen: List of apartment dictionaries
        username: Username
        logger: Logger instance

    Returns:
        Tuple (newly_saved, already_exists)
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
                # Insert with user_id
                cursor.execute("""
                    INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete, wbs_erforderlich, link, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    wohnung['bezirk'],
                    wohnung['adresse'],
                    wohnung['titel'],
                    wohnung['zimmer'],
                    wohnung['flaeche'],
                    wohnung['miete'],
                    wohnung['wbs_erforderlich'],
                    wohnung['link'],
                    username
                ))
                neu_gespeichert += 1
                logger.info(f"Neue Wohnung gespeichert: {wohnung['titel']} in {wohnung['bezirk']}")
            except sqlite3.IntegrityError:
                # Duplicate link - check if it's for this user
                cursor.execute("""
                    SELECT user_id FROM wohnungen WHERE link = ?
                """, (wohnung['link'],))
                result = cursor.fetchone()

                if result and result[0] == username:
                    bereits_vorhanden += 1
                    logger.debug(f"Wohnung bereits für User '{username}' vorhanden: {wohnung['link']}")
                elif result and result[0] != username:
                    # Same apartment, different user - this is OK!
                    # Try to insert again (will fail due to UNIQUE constraint on link)
                    # We need to handle this case: multiple users can want the same apartment
                    bereits_vorhanden += 1
                    logger.info(f"Wohnung bereits von anderem User gespeichert: {wohnung['link']}")
                else:
                    bereits_vorhanden += 1

        conn.commit()
        conn.close()

        logger.info(f"Speicherung abgeschlossen: {neu_gespeichert} neu, {bereits_vorhanden} bereits vorhanden")
        return (neu_gespeichert, bereits_vorhanden)

    except sqlite3.Error as e:
        logger.error(f"Fehler beim Speichern in die Datenbank: {e}")
        return (0, 0)


def scrape_wohnungen_for_user(username: str) -> List[Dict[str, str]]:
    """
    Scrape apartments for specific user based on their filter configuration.

    Args:
        username: Username

    Returns:
        List of apartment dictionaries matching user's filters
    """
    # Initialize managers
    user_manager = UserManager()

    # Get user-specific logger
    logs_dir = user_manager.get_logs_dir(username)
    logger = get_user_logger(username, logs_dir, "scraping")

    logger.info("=" * 70)
    logger.info(f"Starte Gewobag Wohnungssuche für User: {username}")
    logger.info("=" * 70)

    # Load user's filter configuration
    filter_config = user_manager.load_filter_config(username)

    # Build URL with filters
    url_filter_config = filter_config.copy()
    if filter_config.get('zimmer_von'):
        logger.info("Hinweis: zimmer_von wird clientseitig gefiltert (Website-Bug)")
        url_filter_config['zimmer_von'] = ''

    url = build_url_with_filters(url_filter_config)

    # Fetch all pages
    wohnungen = fetch_all_pages(url)
    if not wohnungen:
        logger.warning("Keine Wohnungen gefunden")
        return []

    # Apply client-side filters
    wohnungen = apply_client_side_filters(wohnungen, filter_config)

    if not wohnungen:
        logger.warning("Keine Wohnungen nach Filterung übrig")
        return []

    # Save to database
    neu, vorhanden = save_to_database_for_user(wohnungen, username, logger)

    logger.info("=" * 70)
    logger.info(
        f"Zusammenfassung: {len(wohnungen)} Angebote gefunden, "
        f"{neu} neu gespeichert, {vorhanden} bereits bekannt"
    )
    logger.info("=" * 70)

    return wohnungen


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python gewobag_bot_multiuser.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    wohnungen = scrape_wohnungen_for_user(username)
    print(f"\n✅ Scraping finished for user '{username}': {len(wohnungen)} apartments found")
