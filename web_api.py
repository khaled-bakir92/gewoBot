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

# Pfade - Absolute Pfade basierend auf dem Skript-Verzeichnis
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_PATH = os.path.join(BASE_DIR, 'user_data.json')
FILTER_CONFIG_PATH = os.path.join(BASE_DIR, 'filter_config.json')
BEZIRKE_PATH = os.path.join(BASE_DIR, 'bezirke_verfuegbar.json')
DB_PATH = os.path.join(BASE_DIR, 'gewobag_wohnungen.db')
HEARTBEAT_FILE = os.path.join(BASE_DIR, '.bot_heartbeat.json')

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
        # Prüfe ob Verzeichnis existiert
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            logger.error(f"Verzeichnis existiert nicht: {directory}")
            return False

        # Prüfe Schreibrechte
        if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
            logger.error(f"Keine Schreibrechte für Datei: {filepath}")
            return False

        # Prüfe Verzeichnis-Schreibrechte (für neue Dateien)
        if not os.path.exists(filepath):
            parent_dir = os.path.dirname(filepath) or '.'
            if not os.access(parent_dir, os.W_OK):
                logger.error(f"Keine Schreibrechte für Verzeichnis: {parent_dir}")
                return False

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Datei erfolgreich gespeichert: {filepath}")
        return True
    except PermissionError as e:
        logger.error(f"❌ Keine Berechtigung zum Schreiben: {filepath} - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern von {filepath}: {type(e).__name__} - {e}")
        import traceback
        logger.error(traceback.format_exc())
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

def check_docker_bot_running():
    """Prüft ob der automatische Bot-Container (gewobag-bot) läuft"""
    try:
        # Prüfe ob Docker verfügbar ist
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=gewobag-bot', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Wenn der Container läuft, wird sein Name zurückgegeben
        if result.returncode == 0 and 'gewobag-bot' in result.stdout:
            return True

        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        # Docker nicht verfügbar oder Fehler
        logger.debug(f"Docker-Check fehlgeschlagen: {e}")
        return False

def load_bot_heartbeat():
    """Lädt die Heartbeat-Datei mit dem letzten Bot-Run"""
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.debug(f"Konnte Heartbeat nicht laden: {e}")
        return None

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
    try:
        logger.info(f"📥 GET /api/user-data - Lade Datei: {USER_DATA_PATH}")
        data = load_json_file(USER_DATA_PATH)
        logger.info(f"✅ GET /api/user-data - Erfolgreich geladen")
        return jsonify(data)
    except Exception as e:
        logger.error(f"❌ GET /api/user-data - Fehler: {type(e).__name__} - {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-data', methods=['POST'])
def save_user_data():
    """Speichert User-Daten"""
    try:
        logger.info(f"📤 POST /api/user-data - Speichere in: {USER_DATA_PATH}")
        data = request.json

        if not data:
            logger.error("❌ POST /api/user-data - Keine Daten erhalten")
            return jsonify({'success': False, 'message': 'Keine Daten erhalten'}), 400

        if save_json_file(USER_DATA_PATH, data):
            logger.info("✅ POST /api/user-data - User-Daten erfolgreich gespeichert")
            return jsonify({'success': True, 'message': 'Daten erfolgreich gespeichert'})
        else:
            logger.error("❌ POST /api/user-data - save_json_file() gab False zurück")
            return jsonify({'success': False, 'message': 'Fehler beim Speichern der Datei'}), 500
    except Exception as e:
        logger.error(f"❌ POST /api/user-data - Exception: {type(e).__name__} - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'{type(e).__name__}: {str(e)}'}), 500

# ============================================================================
# API ROUTES - FILTER CONFIG
# ============================================================================

@app.route('/api/filter-config', methods=['GET'])
def get_filter_config():
    """Gibt die aktuellen Filter zurück"""
    try:
        logger.info(f"📥 GET /api/filter-config - Lade Datei: {FILTER_CONFIG_PATH}")
        data = load_json_file(FILTER_CONFIG_PATH)
        logger.info(f"✅ GET /api/filter-config - Erfolgreich geladen")
        return jsonify(data)
    except Exception as e:
        logger.error(f"❌ GET /api/filter-config - Fehler: {type(e).__name__} - {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter-config', methods=['POST'])
def save_filter_config():
    """Speichert Filter-Konfiguration"""
    try:
        logger.info(f"📤 POST /api/filter-config - Speichere in: {FILTER_CONFIG_PATH}")
        data = request.json

        if not data:
            logger.error("❌ POST /api/filter-config - Keine Daten erhalten")
            return jsonify({'success': False, 'message': 'Keine Daten erhalten'}), 400

        if save_json_file(FILTER_CONFIG_PATH, data):
            logger.info("✅ POST /api/filter-config - Filter-Konfiguration erfolgreich gespeichert")
            return jsonify({'success': True, 'message': 'Filter erfolgreich gespeichert'})
        else:
            logger.error("❌ POST /api/filter-config - save_json_file() gab False zurück")
            return jsonify({'success': False, 'message': 'Fehler beim Speichern der Datei'}), 500
    except Exception as e:
        logger.error(f"❌ POST /api/filter-config - Exception: {type(e).__name__} - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'{type(e).__name__}: {str(e)}'}), 500

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

    # Hole die ECHTE letzte Aktivität aus der Datenbank
    # (unabhängig davon, ob der Bot manuell oder automatisch lief)
    real_last_activity = None
    last_activity_type = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Letzte Bewerbung (egal ob erfolgreich oder fehlgeschlagen)
        cursor.execute("SELECT MAX(applied_ts) FROM wohnungen WHERE applied = 1")
        last_application = cursor.fetchone()[0]

        # Letzter Datenbank-Eintrag (neue Wohnung gefunden)
        cursor.execute("SELECT MAX(ts) FROM wohnungen")
        last_scrape = cursor.fetchone()[0]

        conn.close()

        # Bestimme die neueste Aktivität und ihren Typ
        if last_application and last_scrape:
            if last_application > last_scrape:
                real_last_activity = last_application
                last_activity_type = "Bewerbung gesendet"
            else:
                real_last_activity = last_scrape
                last_activity_type = "Wohnung gefunden"
        elif last_application:
            real_last_activity = last_application
            last_activity_type = "Bewerbung gesendet"
        elif last_scrape:
            real_last_activity = last_scrape
            last_activity_type = "Wohnung gefunden"

        # Überschreibe die last_activity mit der echten Aktivität aus der DB
        if real_last_activity:
            bot_status['last_activity'] = real_last_activity
            bot_status['last_activity_type'] = last_activity_type

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der letzten Aktivität aus der DB: {e}")

    # Prüfe ob automatischer Bot-Container läuft (Docker)
    bot_status['auto_bot_running'] = check_docker_bot_running()

    # Lade Heartbeat-Daten (letzte Bot-Ausführung)
    heartbeat = load_bot_heartbeat()
    if heartbeat:
        bot_status['last_run'] = heartbeat.get('timestamp')
        bot_status['last_run_mode'] = heartbeat.get('mode')
        bot_status['last_run_status'] = heartbeat.get('status')
        bot_status['last_run_message'] = heartbeat.get('message')

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
    frontend_path = os.path.join(BASE_DIR, 'frontend')
    if not os.path.exists(frontend_path):
        os.makedirs(frontend_path)
        logger.info("Frontend-Ordner erstellt")

    PORT = int(os.environ.get('PORT', 5000))  # Port aus Umgebungsvariable oder Standard 5000

    logger.info("=" * 60)
    logger.info("Starte Gewobag Bot Web API...")
    logger.info(f"📂 Arbeitsverzeichnis: {BASE_DIR}")
    logger.info(f"📄 User-Daten: {USER_DATA_PATH}")
    logger.info(f"🔍 Filter-Config: {FILTER_CONFIG_PATH}")
    logger.info(f"🗄️  Datenbank: {DB_PATH}")
    logger.info(f"🌐 Frontend verfügbar unter: http://localhost:{PORT}")
    logger.info(f"🔌 API verfügbar unter: http://localhost:{PORT}/api/")
    logger.info("=" * 60)

    # Prüfe Dateiberechtigungen
    for filepath in [USER_DATA_PATH, FILTER_CONFIG_PATH, BEZIRKE_PATH]:
        if os.path.exists(filepath):
            readable = os.access(filepath, os.R_OK)
            writable = os.access(filepath, os.W_OK)
            logger.info(f"{'✅' if readable else '❌'} Lesen | {'✅' if writable else '❌'} Schreiben: {os.path.basename(filepath)}")
        else:
            logger.warning(f"⚠️  Datei existiert nicht: {os.path.basename(filepath)}")

    app.run(host='0.0.0.0', port=PORT, debug=True)
