#!/usr/bin/env python3
"""
Gewobag Bot - Web API
Flask-basierte REST API für das Frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import sqlite3
import subprocess
import threading
import time
from datetime import datetime
import logging

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Globale Variablen für Bot-Steuerung
bot_process = None
bot_status = {
    'running': False,
    'paused': False,
    'mode': None,
    'started_at': None,
    'last_activity': None,
    'message': 'Bot ist gestoppt'
}

# Pfade
USER_DATA_PATH = 'user_data.json'
FILTER_CONFIG_PATH = 'filter_config.json'
BEZIRKE_PATH = 'bezirke_verfuegbar.json'
DB_PATH = 'gewobag_wohnungen.db'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_json_file(filepath):
    """Lädt JSON-Datei"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Fehler beim Laden von {filepath}: {e}")
        return {}

def save_json_file(filepath, data):
    """Speichert JSON-Datei"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern von {filepath}: {e}")
        return False

def get_db_stats():
    """Holt Statistiken aus der Datenbank"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Gesamtzahl
        cursor.execute("SELECT COUNT(*) FROM wohnungen")
        total = cursor.fetchone()[0]

        # Beworben
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE applied = 1")
        applied = cursor.fetchone()[0]

        # Erfolgreich
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE application_status = 'success'")
        success = cursor.fetchone()[0]

        # Fehlgeschlagen
        cursor.execute("SELECT COUNT(*) FROM wohnungen WHERE application_status = 'failed'")
        failed = cursor.fetchone()[0]

        # Letzte Aktivität
        cursor.execute("SELECT MAX(applied_ts) FROM wohnungen WHERE applied = 1")
        last_activity = cursor.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'applied': applied,
            'success': success,
            'failed': failed,
            'pending': total - applied,
            'last_activity': last_activity
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der DB-Statistiken: {e}")
        return {
            'total': 0,
            'applied': 0,
            'success': 0,
            'failed': 0,
            'pending': 0,
            'last_activity': None
        }

def get_recent_applications(limit=10):
    """Holt die letzten Bewerbungen"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT titel, adresse, bezirk, miete, flaeche, zimmer,
                   application_status, applied_ts, application_error
            FROM wohnungen
            WHERE applied = 1
            ORDER BY applied_ts DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        applications = []
        for row in rows:
            applications.append({
                'titel': row['titel'],
                'adresse': row['adresse'],
                'bezirk': row['bezirk'],
                'miete': row['miete'],
                'flaeche': row['flaeche'],
                'zimmer': row['zimmer'],
                'status': row['application_status'],
                'timestamp': row['applied_ts'],
                'error': row['application_error']
            })

        return applications
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der letzten Bewerbungen: {e}")
        return []

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve Frontend"""
    return send_from_directory('frontend', 'index.html')

# ============================================================================
# API ROUTES - USER DATA
# ============================================================================

@app.route('/api/user-data', methods=['GET'])
def get_user_data():
    """Gibt die aktuellen User-Daten zurück"""
    data = load_json_file(USER_DATA_PATH)
    return jsonify(data)

@app.route('/api/user-data', methods=['POST'])
def save_user_data():
    """Speichert User-Daten"""
    try:
        data = request.json
        if save_json_file(USER_DATA_PATH, data):
            logger.info("User-Daten erfolgreich gespeichert")
            return jsonify({'success': True, 'message': 'Daten erfolgreich gespeichert'})
        else:
            return jsonify({'success': False, 'message': 'Fehler beim Speichern'}), 500
    except Exception as e:
        logger.error(f"Fehler beim Speichern der User-Daten: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# API ROUTES - FILTER CONFIG
# ============================================================================

@app.route('/api/filter-config', methods=['GET'])
def get_filter_config():
    """Gibt die aktuellen Filter zurück"""
    data = load_json_file(FILTER_CONFIG_PATH)
    return jsonify(data)

@app.route('/api/filter-config', methods=['POST'])
def save_filter_config():
    """Speichert Filter-Konfiguration"""
    try:
        data = request.json
        if save_json_file(FILTER_CONFIG_PATH, data):
            logger.info("Filter-Konfiguration erfolgreich gespeichert")
            return jsonify({'success': True, 'message': 'Filter erfolgreich gespeichert'})
        else:
            return jsonify({'success': False, 'message': 'Fehler beim Speichern'}), 500
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Filter-Konfiguration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/bezirke', methods=['GET'])
def get_bezirke():
    """Gibt alle verfügbaren Bezirke zurück"""
    data = load_json_file(BEZIRKE_PATH)
    return jsonify(data)

# ============================================================================
# API ROUTES - BOT CONTROL
# ============================================================================

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Startet den Bot"""
    global bot_process, bot_status

    try:
        # Prüfe ob Bot bereits läuft
        if bot_status['running'] and not bot_status['paused']:
            return jsonify({
                'success': False,
                'message': 'Bot läuft bereits'
            }), 400

        # Hole Parameter
        data = request.json or {}
        mode = data.get('mode', 'full')  # 'full', 'scrape', 'apply'
        max_applications = data.get('max_applications', None)

        # Baue Kommando
        cmd = ['python', 'main.py']

        if mode == 'scrape':
            cmd.append('--scrape')
        elif mode == 'apply':
            cmd.append('--apply')
        else:
            cmd.append('--full')

        if max_applications:
            cmd.extend(['--max', str(max_applications)])

        # Starte Bot-Prozess
        bot_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Update Status
        bot_status['running'] = True
        bot_status['paused'] = False
        bot_status['mode'] = mode
        bot_status['started_at'] = datetime.now().isoformat()
        bot_status['last_activity'] = datetime.now().isoformat()
        bot_status['message'] = f'Bot läuft im {mode}-Modus'

        logger.info(f"Bot gestartet im {mode}-Modus")

        return jsonify({
            'success': True,
            'message': f'Bot erfolgreich gestartet ({mode})',
            'status': bot_status
        })

    except Exception as e:
        logger.error(f"Fehler beim Starten des Bots: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stoppt den Bot"""
    global bot_process, bot_status

    try:
        if bot_process:
            bot_process.terminate()
            bot_process.wait(timeout=10)
            bot_process = None

        bot_status['running'] = False
        bot_status['paused'] = False
        bot_status['mode'] = None
        bot_status['message'] = 'Bot wurde gestoppt'

        logger.info("Bot gestoppt")

        return jsonify({
            'success': True,
            'message': 'Bot erfolgreich gestoppt',
            'status': bot_status
        })

    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Bots: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@app.route('/api/bot/pause', methods=['POST'])
def pause_bot():
    """Pausiert den Bot"""
    global bot_status

    try:
        if not bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot läuft nicht'
            }), 400

        bot_status['paused'] = True
        bot_status['message'] = 'Bot ist pausiert'

        logger.info("Bot pausiert")

        return jsonify({
            'success': True,
            'message': 'Bot pausiert',
            'status': bot_status
        })

    except Exception as e:
        logger.error(f"Fehler beim Pausieren des Bots: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@app.route('/api/bot/resume', methods=['POST'])
def resume_bot():
    """Setzt pausierte Bot-Ausführung fort"""
    global bot_status

    try:
        if not bot_status['paused']:
            return jsonify({
                'success': False,
                'message': 'Bot ist nicht pausiert'
            }), 400

        bot_status['paused'] = False
        bot_status['message'] = f'Bot läuft im {bot_status["mode"]}-Modus'

        logger.info("Bot fortgesetzt")

        return jsonify({
            'success': True,
            'message': 'Bot fortgesetzt',
            'status': bot_status
        })

    except Exception as e:
        logger.error(f"Fehler beim Fortsetzen des Bots: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Gibt den aktuellen Bot-Status zurück"""
    global bot_process, bot_status

    # Prüfe ob Prozess noch läuft
    if bot_process and bot_process.poll() is not None:
        bot_status['running'] = False
        bot_status['paused'] = False
        bot_status['mode'] = None
        bot_status['message'] = 'Bot wurde beendet'
        bot_process = None

    return jsonify({
        'status': bot_status,
        'stats': get_db_stats()
    })

# ============================================================================
# API ROUTES - DATABASE & STATISTICS
# ============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Gibt detaillierte Statistiken zurück"""
    stats = get_db_stats()
    recent = get_recent_applications(limit=10)

    return jsonify({
        'stats': stats,
        'recent_applications': recent
    })

@app.route('/api/applications/recent', methods=['GET'])
def get_recent():
    """Gibt die letzten Bewerbungen zurück"""
    limit = request.args.get('limit', 10, type=int)
    applications = get_recent_applications(limit)
    return jsonify(applications)

@app.route('/api/applications/all', methods=['GET'])
def get_all_applications():
    """Gibt alle Wohnungen aus der Datenbank zurück"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, titel, adresse, bezirk, zimmer, flaeche, miete,
                   wbs_erforderlich, link, applied, application_status,
                   applied_ts, application_error, ts
            FROM wohnungen
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        applications = []
        for row in rows:
            applications.append({
                'id': row['id'],
                'titel': row['titel'],
                'adresse': row['adresse'],
                'bezirk': row['bezirk'],
                'zimmer': row['zimmer'],
                'flaeche': row['flaeche'],
                'miete': row['miete'],
                'wbs_erforderlich': bool(row['wbs_erforderlich']),
                'link': row['link'],
                'applied': bool(row['applied']),
                'status': row['application_status'],
                'timestamp': row['applied_ts'],
                'error': row['application_error']
            })

        return jsonify(applications)

    except Exception as e:
        logger.error(f"Fehler beim Abrufen aller Wohnungen: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Prüfe ob Frontend-Ordner existiert
    if not os.path.exists('frontend'):
        os.makedirs('frontend')
        logger.info("Frontend-Ordner erstellt")

    PORT = 8080  # Geänderter Port, da 5000 oft von AirPlay Receiver belegt ist

    logger.info("Starte Gewobag Bot Web API...")
    logger.info(f"Frontend verfügbar unter: http://localhost:{PORT}")
    logger.info(f"API verfügbar unter: http://localhost:{PORT}/api/")

    app.run(host='0.0.0.0', port=PORT, debug=True)
