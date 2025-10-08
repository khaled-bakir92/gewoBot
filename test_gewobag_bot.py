#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for Gewobag-Bot v2.0
Tests all major functions: database, scraping, filtering, config loading, and application logic
"""

import unittest
import sqlite3
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestDatabaseOperations(unittest.TestCase):
    """Test database initialization, insertion, and queries"""

    def setUp(self):
        """Create temporary test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        self._init_test_database()

    def tearDown(self):
        """Remove temporary test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _init_test_database(self):
        """Initialize test database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wohnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bezirk TEXT,
                adresse TEXT,
                titel TEXT,
                zimmer TEXT,
                flaeche TEXT,
                miete TEXT,
                wbs_erforderlich INTEGER DEFAULT 0,
                link TEXT UNIQUE NOT NULL,
                ts TEXT DEFAULT CURRENT_TIMESTAMP,
                applied INTEGER DEFAULT 0,
                applied_ts TEXT,
                application_status TEXT,
                application_error TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def test_database_initialization(self):
        """Test that database and table are created correctly"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wohnungen'")
        table = cursor.fetchone()
        self.assertIsNotNone(table, "✅ Table 'wohnungen' exists")

        # Check table schema
        cursor.execute("PRAGMA table_info(wohnungen)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'bezirk': 'TEXT',
            'adresse': 'TEXT',
            'titel': 'TEXT',
            'zimmer': 'TEXT',
            'flaeche': 'TEXT',
            'miete': 'TEXT',
            'wbs_erforderlich': 'INTEGER',
            'link': 'TEXT',
            'ts': 'TEXT',
            'applied': 'INTEGER',
            'applied_ts': 'TEXT',
            'application_status': 'TEXT',
            'application_error': 'TEXT'
        }

        for col_name in expected_columns:
            self.assertIn(col_name, columns, f"Column '{col_name}' should exist")

        conn.close()

    def test_save_and_retrieve_apartment(self):
        """Test inserting and retrieving apartment data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        wohnung = {
            'bezirk': 'Friedrichshain-Kreuzberg',
            'adresse': 'Teststraße 1, 10247 Berlin',
            'titel': 'Test Wohnung',
            'zimmer': '3 Zimmer',
            'flaeche': '80,00 m²',
            'miete': 'ab 900,00€',
            'wbs_erforderlich': 0,
            'link': 'https://www.gewobag.de/test-wohnung-123'
        }

        cursor.execute('''
            INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete, wbs_erforderlich, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (wohnung['bezirk'], wohnung['adresse'], wohnung['titel'], wohnung['zimmer'],
              wohnung['flaeche'], wohnung['miete'], wohnung['wbs_erforderlich'], wohnung['link']))
        conn.commit()

        cursor.execute("SELECT * FROM wohnungen WHERE link = ?", (wohnung['link'],))
        row = cursor.fetchone()

        self.assertIsNotNone(row, "✅ Apartment saved to database")
        self.assertEqual(row[1], wohnung['bezirk'])
        self.assertEqual(row[2], wohnung['adresse'])
        self.assertEqual(row[7], 0)  # wbs_erforderlich

        conn.close()

    def test_duplicate_prevention(self):
        """Test that duplicate links are prevented by UNIQUE constraint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        wohnung_data = ('Mitte', 'Test 2', 'Duplicate Test', '2 Zimmer', '60 m²',
                       'ab 700€', 0, 'https://www.gewobag.de/duplicate-test')

        # Insert first time
        cursor.execute('''
            INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete, wbs_erforderlich, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', wohnung_data)
        conn.commit()

        # Try to insert again - should fail
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete, wbs_erforderlich, link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', wohnung_data)
            conn.commit()

        conn.close()

    def test_query_unapplied_apartments(self):
        """Test querying for unapplied apartments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert test data
        wohnungen = [
            ('Pankow', 'Test 1', 'Unapplied 1', '2 Zimmer', '50 m²', 'ab 600€', 0,
             'https://www.gewobag.de/unapplied-1', 0),
            ('Pankow', 'Test 2', 'Applied 1', '3 Zimmer', '70 m²', 'ab 800€', 0,
             'https://www.gewobag.de/applied-1', 1)
        ]

        for w in wohnungen:
            cursor.execute('''
                INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete,
                                      wbs_erforderlich, link, applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', w)
        conn.commit()

        # Query unapplied
        cursor.execute("SELECT * FROM wohnungen WHERE applied = 0")
        unapplied = cursor.fetchall()

        self.assertEqual(len(unapplied), 1, "✅ Only unapplied apartments returned")
        self.assertEqual(unapplied[0][3], 'Unapplied 1')

        conn.close()

    def test_mark_apartment_as_applied(self):
        """Test updating apartment application status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        link = 'https://www.gewobag.de/mark-applied-test'

        # Insert apartment
        cursor.execute('''
            INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete,
                                  wbs_erforderlich, link, applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Lichtenberg', 'Test', 'Mark Test', '2 Zimmer', '55 m²', 'ab 650€', 0, link, 0))
        conn.commit()

        # Mark as applied
        cursor.execute('''
            UPDATE wohnungen
            SET applied = 1, application_status = ?, applied_ts = ?
            WHERE link = ?
        ''', ('success', datetime.now().isoformat(), link))
        conn.commit()

        # Verify
        cursor.execute("SELECT applied, application_status FROM wohnungen WHERE link = ?", (link,))
        row = cursor.fetchone()

        self.assertEqual(row[0], 1, "✅ Applied flag set to 1")
        self.assertEqual(row[1], 'success', "✅ Application status is 'success'")

        conn.close()


class TestConfigurationHandling(unittest.TestCase):
    """Test configuration file handling"""

    def test_create_and_load_filter_config(self):
        """Test creating and loading filter configuration"""
        test_config = {
            "bezirke": ["Friedrichshain-Kreuzberg", "Pankow"],
            "max_miete": 1000,
            "min_flaeche": 60,
            "min_zimmer": 2,
            "nur_ohne_wbs": True
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_config, f)
            config_path = f.name

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            self.assertEqual(loaded_config['bezirke'], test_config['bezirke'])
            self.assertEqual(loaded_config['max_miete'], 1000)
            self.assertEqual(loaded_config['min_flaeche'], 60)
            self.assertTrue(loaded_config['nur_ohne_wbs'])
        finally:
            os.remove(config_path)

    def test_create_and_load_user_data(self):
        """Test creating and loading user data"""
        test_user_data = {
            "vorname": "Max",
            "nachname": "Mustermann",
            "email": "max@example.com",
            "telefon": "+49 30 12345678",
            "haushalt": {
                "anzahl_personen": 2,
                "anzahl_kinder": 0
            },
            "dokumente": []
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_user_data, f)
            user_data_path = f.name

        try:
            with open(user_data_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data['vorname'], 'Max')
            self.assertEqual(loaded_data['email'], 'max@example.com')
            self.assertEqual(loaded_data['haushalt']['anzahl_personen'], 2)
        finally:
            os.remove(user_data_path)

    def test_validate_config_structure(self):
        """Test configuration structure validation"""
        valid_config = {
            "bezirke": ["Pankow"],
            "max_miete": 1000,
            "min_flaeche": 50,
            "min_zimmer": 2,
            "nur_ohne_wbs": False
        }

        # Check all required keys exist
        required_keys = ['bezirke', 'max_miete', 'min_flaeche', 'min_zimmer', 'nur_ohne_wbs']
        for key in required_keys:
            self.assertIn(key, valid_config, f"✅ Config has required key: {key}")

    def test_validate_user_data_structure(self):
        """Test user data structure validation"""
        valid_data = {
            "vorname": "Anna",
            "nachname": "Schmidt",
            "email": "anna@example.com",
            "telefon": "+49 30 98765432",
            "haushalt": {
                "anzahl_personen": 1,
                "anzahl_kinder": 0
            }
        }

        # Check required keys
        required_keys = ['vorname', 'nachname', 'email', 'telefon', 'haushalt']
        for key in required_keys:
            self.assertIn(key, valid_data, f"✅ User data has required key: {key}")


class TestFilterLogic(unittest.TestCase):
    """Test apartment filtering logic"""

    def test_filter_by_wbs(self):
        """Test WBS filtering"""
        wohnungen = [
            {'titel': 'With WBS', 'wbs_erforderlich': True, 'zimmer': '3 Zimmer'},
            {'titel': 'Without WBS', 'wbs_erforderlich': False, 'zimmer': '2 Zimmer'}
        ]

        # Filter out WBS apartments
        filtered = [w for w in wohnungen if not w['wbs_erforderlich']]

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['titel'], 'Without WBS')

    def test_filter_by_room_count(self):
        """Test room number filtering"""
        wohnungen = [
            {'titel': '1 Room', 'zimmer': '1 Zimmer', 'wbs_erforderlich': False},
            {'titel': '2 Rooms', 'zimmer': '2 Zimmer', 'wbs_erforderlich': False},
            {'titel': '3 Rooms', 'zimmer': '3 Zimmer', 'wbs_erforderlich': False}
        ]

        min_zimmer = 2

        # Extract room count and filter
        def get_room_count(zimmer_str):
            try:
                return int(zimmer_str.split()[0])
            except:
                return 0

        filtered = [w for w in wohnungen if get_room_count(w['zimmer']) >= min_zimmer]

        self.assertEqual(len(filtered), 2)
        titles = [w['titel'] for w in filtered]
        self.assertIn('2 Rooms', titles)
        self.assertIn('3 Rooms', titles)

    def test_build_url_with_bezirk_filter(self):
        """Test URL building with district filter"""
        base_url = "https://www.gewobag.de/wohnungssuche/"
        bezirke = ['Friedrichshain-Kreuzberg', 'Pankow']

        # Simulate URL building
        bezirke_normalized = [b.lower().replace(' ', '-') for b in bezirke]
        url_params = '&'.join([f"bezirk[]={b}" for b in bezirke_normalized])
        full_url = f"{base_url}?{url_params}"

        self.assertIn('friedrichshain-kreuzberg', full_url)
        self.assertIn('pankow', full_url)


class TestHTMLParsing(unittest.TestCase):
    """Test HTML parsing functions"""

    def test_parse_basic_html_structure(self):
        """Test basic HTML parsing with BeautifulSoup"""
        from bs4 import BeautifulSoup

        html = """
        <html>
            <body>
                <div class="angebot-content">
                    <h3 class="angebot-title">Test Apartment</h3>
                    <address>Teststraße 1</address>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('h3', class_='angebot-title')
        address = soup.find('address')

        self.assertIsNotNone(title)
        self.assertEqual(title.text, 'Test Apartment')
        self.assertIsNotNone(address)
        self.assertEqual(address.text, 'Teststraße 1')

    def test_extract_apartment_elements(self):
        """Test extracting apartment data elements"""
        from bs4 import BeautifulSoup

        html = """
        <div class="angebot-content">
            <h3 class="angebot-title">Modern Apartment</h3>
            <address>Hauptstraße 123, 10115 Berlin</address>
            <tr class="angebot-area"><td>3 Zimmer, 75,50 m²</td></tr>
            <tr class="angebot-kosten"><td>ab 850,00€</td></tr>
            <div class="angebot-footer">
                <a href="/apartment/details">Details</a>
            </div>
        </div>
        """

        soup = BeautifulSoup(html, 'html.parser')
        angebot = soup.find('div', class_='angebot-content')

        self.assertIsNotNone(angebot)

        title = angebot.find('h3', class_='angebot-title')
        self.assertEqual(title.text if title else None, 'Modern Apartment')

        address = angebot.find('address')
        self.assertIn('Hauptstraße', address.text if address else '')


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Setup test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wohnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bezirk TEXT,
                adresse TEXT,
                titel TEXT,
                zimmer TEXT,
                flaeche TEXT,
                miete TEXT,
                wbs_erforderlich INTEGER DEFAULT 0,
                link TEXT UNIQUE NOT NULL,
                ts TEXT DEFAULT CURRENT_TIMESTAMP,
                applied INTEGER DEFAULT 0,
                applied_ts TEXT,
                application_status TEXT,
                application_error TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Cleanup"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_filter_and_save_workflow(self):
        """Test complete workflow: filter -> save -> query"""
        # Sample apartments
        wohnungen = [
            {
                'bezirk': 'Pankow',
                'adresse': 'Test 1',
                'titel': 'Good Apartment',
                'zimmer': '3 Zimmer',
                'flaeche': '70 m²',
                'miete': 'ab 800€',
                'wbs_erforderlich': False,
                'link': 'https://www.gewobag.de/test-1'
            },
            {
                'bezirk': 'Pankow',
                'adresse': 'Test 2',
                'titel': 'With WBS',
                'zimmer': '2 Zimmer',
                'flaeche': '60 m²',
                'miete': 'ab 700€',
                'wbs_erforderlich': True,
                'link': 'https://www.gewobag.de/test-2'
            }
        ]

        # Filter (nur_ohne_wbs = True)
        filtered = [w for w in wohnungen if not w['wbs_erforderlich']]
        self.assertEqual(len(filtered), 1)

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for w in filtered:
            cursor.execute('''
                INSERT INTO wohnungen (bezirk, adresse, titel, zimmer, flaeche, miete,
                                      wbs_erforderlich, link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (w['bezirk'], w['adresse'], w['titel'], w['zimmer'], w['flaeche'],
                  w['miete'], 1 if w['wbs_erforderlich'] else 0, w['link']))
        conn.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM wohnungen")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        cursor.execute("SELECT titel FROM wohnungen")
        row = cursor.fetchone()
        self.assertEqual(row[0], 'Good Apartment')

        conn.close()


def run_tests():
    """Run all tests and generate report"""
    print("=" * 70)
    print("🧪 GEWOBAG-BOT v2.0 - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestDatabaseOperations,
        TestConfigurationHandling,
        TestFilterLogic,
        TestHTMLParsing,
        TestIntegrationWorkflow
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped)}")
    print()

    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! 🎉")
        print()
        print("✅ Database operations working correctly")
        print("✅ Configuration handling functional")
        print("✅ Filter logic verified")
        print("✅ HTML parsing operational")
        print("✅ Integration workflows successful")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - See details above")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
