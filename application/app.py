from flask import Flask, request, jsonify, make_response, render_template
from flask_cors import CORS
import uuid
from datetime import datetime, timedelta
import threading
import time
import os
import sqlite3
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS Configuration
CORS(app,
     resources={ 
         r"/api/*": {
             "origins": [
                 "https://abhinavpanwar.netlify.app",
                 "http://127.0.0.1:5500",
                 "http://localhost:5500"
             ],
             "supports_credentials": True,
             "allow_headers": ["Content-Type"],
             "methods": ["GET", "POST", "OPTIONS", "HEAD"],
             "expose_headers": ["Content-Type"],
             "max_age": 600
         }
     })

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    PREFERRED_URL_SCHEME='https'
)

active_sessions = {}
lock = threading.Lock()
SESSION_TIMEOUT = 15  # Time in seconds before considering a session expired
CLEANUP_INTERVAL = 5  # Time in seconds between session cleanup runs

# Database Connection Function
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# Initialize Database Function
def init_db():
    try:
        conn = get_db_connection('headline.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS headline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL DEFAULT ''
        )''')
        if not conn.execute('SELECT 1 FROM headline LIMIT 1').fetchone():
            conn.execute('INSERT INTO headline (text) VALUES ("")')
        conn.commit()
        conn.close()

        # Polls DB Schema
        conn = get_db_connection('polls.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_index INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE
        )''')
        
        # Check if created_at column exists in polls table, add if not
        cursor = conn.execute("PRAGMA table_info(polls)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'created_at' not in columns:
            conn.execute('ALTER TABLE polls ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        
        conn.commit()
        conn.close()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

# Session Cleanup Thread
def cleanup_sessions():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        now = datetime.now()
        with lock:
            expired = [k for k, v in active_sessions.items()
                       if (now - v['last_active']).total_seconds() > SESSION_TIMEOUT]
            for device_id in expired:
                del active_sessions[device_id]
                logger.debug(f"Cleaned up expired session: {device_id}")

# Start the session cleanup thread
threading.Thread(target=cleanup_sessions, daemon=True).start()

# Home Route
@app.route('/')
def home():
    return render_template('index.html', server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# End Session API Route
@app.route('/api/active_users/end', methods=['POST'])
def end_session():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    device_id = request.json.get('device_id')
    with lock:
        if device_id in active_sessions:
            del active_sessions[device_id]
            logger.info(f"Ended session for device: {device_id}")
    return jsonify({"status": "session_ended"})

# Active Users API Route
@app.route('/api/active_users', methods=['GET', 'OPTIONS'])
def active_users():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    device_id = request.cookies.get('device_id', str(uuid.uuid4()))
    now = datetime.now()

    with lock:
        if device_id in active_sessions:
            active_sessions[device_id]['last_active'] = now
        else:
            active_sessions[device_id] = {'last_active': now, 'created': now}
            logger.info(f"New session started for device: {device_id}")

    response = make_response(jsonify({
        'active_users': len(active_sessions),
        'your_device_id': device_id,
        'last_active': active_sessions[device_id]['last_active'].isoformat()
    }))

    if not request.cookies.get('device_id'):
        response.set_cookie(
            'device_id',
            value=device_id,
            max_age=365 * 24 * 60 * 60,
            secure=True,
            httponly=True,
            samesite='None',
            path='/'
        )
    return response

# Healthcheck Route
@app.route('/api/healthcheck')
def healthcheck():
    with lock:
        active_count = len(active_sessions)
        oldest_session = min(
            (s['created'] for s in active_sessions.values()),
            default=datetime.now()
        )

    return jsonify({
        "status": "healthy",
        "active_users": active_count,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.3.1"  # Updated version number
    })

# Get Headline API
@app.route('/api/get_h3', methods=['GET'])
def get_h3():
    try:
        conn = get_db_connection('headline.db')
        result = conn.execute('SELECT text FROM headline WHERE id = 1').fetchone()
        return jsonify({'h3_text': result['text'] if result else ""})
    except Exception as e:
        logger.error(f"Error getting headline: {str(e)}")
        return jsonify({'error': 'Failed to get headline'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Set Headline API
@app.route('/api/set_h3', methods=['POST'])
def set_h3():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.get_json()
        new_text = data.get('new_text', '')
        
        conn = get_db_connection('headline.db')
        conn.execute('UPDATE headline SET text = ? WHERE id = 1', (new_text,))
        conn.commit()
        return jsonify({'status': 'updated', 'new_text': new_text})
    except Exception as e:
        logger.error(f"Error setting headline: {str(e)}")
        return jsonify({'error': 'Failed to update headline'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Create Poll API
@app.route('/api/poll', methods=['POST'])
def create_poll():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        options = [opt.strip() for opt in data.get('options', []) if opt.strip()]
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        if len(options) < 2:
            return jsonify({"error": "At least 2 options are required"}), 400

        conn = get_db_connection('polls.db')
        with conn:
            conn.execute('DELETE FROM polls')  # Clear existing poll before creating a new one
            conn.execute('INSERT INTO polls (question, options) VALUES (?, ?)', 
                        (question, json.dumps(options)))
            poll = conn.execute('SELECT id, question FROM polls ORDER BY id DESC LIMIT 1').fetchone()
            logger.info(f"Created new poll: {poll['id']}")
            return jsonify({
                "status": "success",
                "message": "Poll created successfully",
                "poll_id": poll['id'],
                "question": question,
                "options": options
            })
    except Exception as e:
        logger.error(f"Error creating poll: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Get Current Poll API
@app.route('/api/current_poll', methods=['GET'])
def current_poll():
    try:
        conn = get_db_connection('polls.db')
        poll = conn.execute('''SELECT id, question, options, created_at 
                            FROM polls ORDER BY created_at DESC LIMIT 1''').fetchone()
        
        if poll:
            return jsonify({
                'poll_id': poll['id'],
                'question': poll['question'],
                'options': json.loads(poll['options']),
                'created_at': poll['created_at']
            })
        return jsonify({'error': 'No active poll'}), 404
    except Exception as e:
        logger.error(f"Error getting current poll: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Submit Poll Response API
@app.route('/api/submit_response', methods=['POST'])
def submit_response():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        data = request.get_json()
        option_index = data.get('option_index')
        poll_id = data.get('poll_id')
        
        if option_index is None:
            return jsonify({'error': 'Missing option_index'}), 400

        conn = get_db_connection('polls.db')
        with conn:
            if not poll_id:
                poll = conn.execute('''SELECT id FROM polls ORDER BY id DESC LIMIT 1''').fetchone()
                if not poll:
                    return jsonify({'error': 'No active poll to respond to'}), 404
                poll_id = poll['id']
            
            poll = conn.execute('''SELECT options FROM polls WHERE id = ?''', (poll_id,)).fetchone()
            if not poll:
                return jsonify({'error': 'Invalid poll_id'}), 400
            
            options = json.loads(poll['options'])
            if option_index < 0 or option_index >= len(options):
                return jsonify({'error': 'Invalid option_index'}), 400
            
            conn.execute('''INSERT INTO responses (poll_id, option_index) VALUES (?, ?)''', 
                        (poll_id, option_index))
            logger.info(f"Submitted response to poll {poll_id}, option {option_index}")
            return jsonify({
                'status': 'success',
                'poll_id': poll_id,
                'option_index': option_index
            })
    except Exception as e:
        logger.error(f"Error submitting response: {str(e)}")
        return jsonify({'error': 'Failed to submit response'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Get Poll Results API
@app.route('/api/poll_results', methods=['GET'])
def get_poll_results():
    try:
        conn = get_db_connection('polls.db')
        
        # Get the latest poll
        poll = conn.execute('''SELECT id, question, options FROM polls ORDER BY id DESC LIMIT 1''').fetchone()
        if not poll:
            return jsonify({'error': 'No active poll found'}), 404
            
        # Get all responses for this poll
        responses = conn.execute('''SELECT option_index, COUNT(*) as count 
                                 FROM responses 
                                 WHERE poll_id = ?
                                 GROUP BY option_index''', (poll['id'],)).fetchall()
        
        # Format the results
        options = json.loads(poll['options'])
        results = {i: 0 for i in range(len(options))}
        for row in responses:
            results[row['option_index']] = row['count']
        
        return jsonify({
            'poll_id': poll['id'],
            'question': poll['question'],
            'options': options,
            'results': results,
            'total_responses': sum(results.values())
        })
    except Exception as e:
        logger.error(f"Error getting poll results: {str(e)}")
        return jsonify({'error': 'Failed to get poll results'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Add this endpoint to your Flask app
@app.route('/api/end_poll', methods=['POST'])
def end_poll():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    try:
        conn = get_db_connection('polls.db')
        with conn:
            # Delete all responses first (due to foreign key constraint)
            conn.execute('DELETE FROM responses')
            # Then delete the poll
            conn.execute('DELETE FROM polls')
            logger.info("Ended current poll and cleared all responses")
        return jsonify({"status": "poll_ended"})
    except Exception as e:
        logger.error(f"Error ending poll: {str(e)}")
        return jsonify({"error": "Failed to end poll"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)