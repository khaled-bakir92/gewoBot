#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration - Add Multi-User Support
============================================

Adds user_id column to the wohnungen table to support multiple users.

Author: Gewobag Bot Team
Version: 2.1
"""

import sqlite3
import logging
from pathlib import Path

DB_NAME = "gewobag_wohnungen.db"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Check if column exists in table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate_database():
    """Add user_id column to wohnungen table if not exists."""
    logger.info(f"🔄 Starting database migration for '{DB_NAME}'...")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Check if user_id column already exists
        if check_column_exists(cursor, 'wohnungen', 'user_id'):
            logger.info("✅ Column 'user_id' already exists - no migration needed")
            conn.close()
            return True

        # Add user_id column
        logger.info("➕ Adding 'user_id' column to 'wohnungen' table...")
        cursor.execute("""
            ALTER TABLE wohnungen
            ADD COLUMN user_id TEXT
        """)

        # Create index for faster queries
        logger.info("📊 Creating index on 'user_id' column...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON wohnungen(user_id)
        """)

        # Create compound index for user_id + applied queries
        logger.info("📊 Creating compound index on 'user_id' and 'applied'...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_applied ON wohnungen(user_id, applied)
        """)

        conn.commit()
        conn.close()

        logger.info("✅ Database migration completed successfully!")
        logger.info("ℹ️  Existing records have user_id = NULL (legacy single-user mode)")
        return True

    except sqlite3.Error as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def init_database_with_multiuser():
    """
    Initialize database with multi-user support (for new installations).
    """
    logger.info(f"🔧 Initializing database '{DB_NAME}' with multi-user support...")

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
                application_error TEXT,
                user_id TEXT
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON wohnungen(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_applied ON wohnungen(user_id, applied)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_link ON wohnungen(link)
        """)

        conn.commit()
        conn.close()

        logger.info("✅ Database initialized with multi-user support!")
        return True

    except sqlite3.Error as e:
        logger.error(f"❌ Initialization failed: {e}")
        return False


def get_database_info():
    """Print database schema information."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print(f"\n{'='*60}")
        print(f"Database: {DB_NAME}")
        print(f"{'='*60}\n")

        # Get table info
        cursor.execute("PRAGMA table_info(wohnungen)")
        columns = cursor.fetchall()

        print("Columns:")
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            flags = []
            if pk:
                flags.append("PRIMARY KEY")
            if not_null:
                flags.append("NOT NULL")
            if default is not None:
                flags.append(f"DEFAULT {default}")

            flag_str = f" ({', '.join(flags)})" if flags else ""
            print(f"  {name:<20} {col_type:<10} {flag_str}")

        # Get indexes
        cursor.execute("PRAGMA index_list(wohnungen)")
        indexes = cursor.fetchall()

        if indexes:
            print("\nIndexes:")
            for idx in indexes:
                idx_name = idx[1]
                is_unique = "UNIQUE" if idx[2] else "INDEX"
                cursor.execute(f"PRAGMA index_info({idx_name})")
                index_cols = cursor.fetchall()
                cols = [col[2] for col in index_cols]
                print(f"  {idx_name}: {is_unique} on ({', '.join(cols)})")

        # Get row count
        cursor.execute("SELECT COUNT(*) FROM wohnungen")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")

        # Get user statistics
        if check_column_exists(cursor, 'wohnungen', 'user_id'):
            cursor.execute("""
                SELECT
                    user_id,
                    COUNT(*) as total,
                    SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as applied
                FROM wohnungen
                GROUP BY user_id
                ORDER BY user_id
            """)
            user_stats = cursor.fetchall()

            if user_stats:
                print("\nUser statistics:")
                for user_id, total, applied in user_stats:
                    user_display = user_id if user_id else "(legacy)"
                    print(f"  {user_display:<15} {total:>4} apartments, {applied:>4} applied")

        print()
        conn.close()

    except sqlite3.Error as e:
        logger.error(f"❌ Error getting database info: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate_database.py migrate     # Migrate existing database")
        print("  python migrate_database.py init        # Initialize new database")
        print("  python migrate_database.py info        # Show database info")
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        if not Path(DB_NAME).exists():
            logger.error(f"❌ Database '{DB_NAME}' does not exist!")
            logger.info("💡 Use 'init' command to create a new database")
            sys.exit(1)
        migrate_database()
        print()
        get_database_info()

    elif command == "init":
        if Path(DB_NAME).exists():
            response = input(f"⚠️  Database '{DB_NAME}' already exists. Overwrite? (yes/no): ")
            if response.lower() != "yes":
                print("❌ Aborted")
                sys.exit(1)
            Path(DB_NAME).unlink()
        init_database_with_multiuser()
        get_database_info()

    elif command == "info":
        if not Path(DB_NAME).exists():
            logger.error(f"❌ Database '{DB_NAME}' does not exist!")
            sys.exit(1)
        get_database_info()

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
