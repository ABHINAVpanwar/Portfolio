from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import uuid
from datetime import datetime, timedelta
import threading
import time
import os
import logging
import pytz
import hashlib
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

ADMIN_USERNAME = 'Abhinav'
ADMIN_PASSWORD_HASH = hashlib.sha256('1289#ijFK'.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    return datetime.now(IST)

def get_client_ip():
    try:
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
        elif request.headers.get("X-Real-IP"):
            ip = request.headers.get("X-Real-IP")
        elif request.headers.get("CF-Connecting-IP"):
            ip = request.headers.get("CF-Connecting-IP")
        else:
            ip = request.remote_addr
        if ip in ('::1', '127.0.0.1'):
            ip = '127.0.0.1'
        return ip or '0.0.0.0'
    except Exception as e:
        logger.error(f"Error getting client IP: {e}")
        return '0.0.0.0'

def parse_device(user_agent):
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'Tablet'
    return 'Desktop'

# ============ MONGODB ============
MONGO_URI     = os.environ.get('MONGO_URI', 'mongodb+srv://abhinavpanwar:Abhinav1234@cluster0.vihawrj.mongodb.net/portfolio_analytics?retryWrites=true&w=majority&appName=Cluster0')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'portfolio_analytics')

try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGO_DB_NAME]

    visitors_col  = db['visitors']
    user_logs_col = db['user_logs']
    headline_col  = db['headline']
    polls_col     = db['polls']
    responses_col = db['poll_responses']
    messages_col  = db['messages']
    config_col    = db['config']

    # Seed headline doc if missing
    if not headline_col.find_one({'_id': 'headline'}):
        headline_col.insert_one({'_id': 'headline', 'text': ''})

    # Seed password doc if missing
    if not config_col.find_one({'_id': 'password'}):
        config_col.insert_one({'_id': 'password', 'value': '!password'})

    # Seed kill switch doc if missing
    if not config_col.find_one({'_id': 'kill_switch'}):
        config_col.insert_one({'_id': 'kill_switch', 'killed': False, 'updated_at': None})

    songs_col = db['songs']
    rating_col = db['rating']
    scores_col = db['scores']

    # Seed rating doc if missing
    if not rating_col.find_one({'_id': 'portfolio'}):
        rating_col.insert_one({'_id': 'portfolio', 'total': 0, 'count': 0})

    # Seed scores doc if missing
    if not scores_col.find_one({'_id': 'skills'}):
        scores_col.insert_one({'_id': 'skills',
            'F': 80, 'SM': 60, 'TM': 70, 'PS': 80, 'DM': 60, 'C': 70,
            'updated_at': None})

    logger.info("✅ MongoDB connected successfully!")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    mongo_client = None
    db = visitors_col = user_logs_col = headline_col = None
    polls_col = responses_col = messages_col = config_col = songs_col = rating_col = scores_col = None

# ============ HELPERS ============
def get_password_value():
    """Read current password from MongoDB."""
    if config_col is None:
        return '!password'
    doc = config_col.find_one({'_id': 'password'})
    return doc['value'] if doc else '!password'

def require_password(data):
    """Returns True if the provided password matches. Use in admin endpoints."""
    return (data or {}).get('password') == get_password_value()

# ============ CORS ============
ALLOWED_ORIGINS = [
    "https://abhinavpanwar.netlify.app",
    "http://127.0.0.1:5501",
    "http://localhost:5501"
]

CORS(app, resources={r"/*": {
    "origins": ALLOWED_ORIGINS,
    "supports_credentials": True,
    "allow_headers": ["Content-Type"],
    "methods": ["GET", "POST", "OPTIONS", "HEAD"],
    "max_age": 600
}})

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    PREFERRED_URL_SCHEME='https'
)

# ============ ACTIVE SESSIONS ============
active_sessions = {}
lock = threading.Lock()
SESSION_TIMEOUT  = 15
CLEANUP_INTERVAL = 5

def cleanup_sessions():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        now = datetime.now()
        with lock:
            expired = [k for k, v in active_sessions.items()
                       if (now - v['last_active']).total_seconds() > SESSION_TIMEOUT]
            for d in expired:
                del active_sessions[d]

threading.Thread(target=cleanup_sessions, daemon=True).start()

# ============ ROUTES ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if (username == ADMIN_USERNAME and
                hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html', server_time=now_ist().strftime("%Y-%m-%d %H:%M:%S"))

# ---------- Active Users ----------
@app.route('/api/active_users/end', methods=['POST'])
def end_session():
    device_id = (request.json or {}).get('device_id')
    with lock:
        active_sessions.pop(device_id, None)
    return jsonify({"status": "session_ended"})

@app.route('/api/active_users', methods=['GET', 'OPTIONS'])
def active_users():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        r.headers['Access-Control-Allow-Credentials'] = 'true'
        return r

    device_id = request.cookies.get('device_id', str(uuid.uuid4()))
    now = datetime.now()
    with lock:
        active_sessions[device_id] = active_sessions.get(device_id, {'created': now})
        active_sessions[device_id]['last_active'] = now

    response = make_response(jsonify({
        'active_users': len(active_sessions),
        'your_device_id': device_id,
        'last_active': active_sessions[device_id]['last_active'].isoformat()
    }))
    if not request.cookies.get('device_id'):
        response.set_cookie('device_id', device_id, max_age=365*24*3600,
                            secure=True, httponly=True, samesite='None', path='/')
    return response

# ---------- Healthcheck ----------
@app.route('/api/healthcheck')
def healthcheck():
    with lock:
        active_count = len(active_sessions)
    return jsonify({
        "status": "healthy",
        "active_users": active_count,
        "server_time": now_ist().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.1.0"
    })

# ---------- Headline ----------
@app.route('/api/get_h3', methods=['GET'])
def get_h3():
    if headline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    doc = headline_col.find_one({'_id': 'headline'})
    return jsonify({'h3_text': doc['text'] if doc else ''})

@app.route('/api/set_h3', methods=['POST'])
def set_h3():
    if headline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.json
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    new_text = data.get('new_text', '')
    headline_col.update_one({'_id': 'headline'}, {'$set': {'text': new_text}}, upsert=True)
    _api_log('headline_update', extra={'new_text': new_text})
    return jsonify({'status': 'updated', 'new_text': new_text})

# ---------- Polls ----------
@app.route('/api/poll', methods=['POST'])
def create_poll():
    if polls_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.json
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    question = data.get('question', '').strip()
    options  = [o.strip() for o in data.get('options', []) if o.strip()]
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    if len(options) < 2:
        return jsonify({'error': 'At least 2 options required'}), 400

    polls_col.delete_many({})
    responses_col.delete_many({})
    poll_id = str(uuid.uuid4())
    polls_col.insert_one({'_id': poll_id, 'question': question, 'options': options, 'created_at': now_ist()})
    _api_log('poll_create', extra={'question': question, 'options': options})
    return jsonify({'status': 'success', 'poll_id': poll_id, 'question': question, 'options': options})

@app.route('/api/current_poll', methods=['GET'])
def current_poll():
    if polls_col is None:
        return jsonify({'error': 'No active poll'}), 404
    poll = polls_col.find_one({})
    if not poll:
        return jsonify({'error': 'No active poll'}), 404
    return jsonify({
        'poll_id':    poll['_id'],
        'question':   poll['question'],
        'options':    poll['options'],
        'created_at': poll['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/submit_response', methods=['POST'])
def submit_response():
    if polls_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data         = request.json
    option_index = data.get('option_index')
    poll_id      = data.get('poll_id')
    if option_index is None:
        return jsonify({'error': 'Missing option_index'}), 400

    poll = polls_col.find_one({'_id': poll_id} if poll_id else {})
    if not poll:
        return jsonify({'error': 'No active poll'}), 404
    if option_index < 0 or option_index >= len(poll['options']):
        return jsonify({'error': 'Invalid option_index'}), 400

    responses_col.insert_one({'poll_id': poll['_id'], 'option_index': option_index, 'timestamp': now_ist()})
    return jsonify({'status': 'success', 'poll_id': poll['_id'], 'option_index': option_index})

@app.route('/api/poll_results', methods=['GET'])
def get_poll_results():
    if polls_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    poll = polls_col.find_one({})
    if not poll:
        return jsonify({'error': 'No active poll'}), 404

    pipeline = [
        {'$match': {'poll_id': poll['_id']}},
        {'$group': {'_id': '$option_index', 'count': {'$sum': 1}}}
    ]
    results = {i: 0 for i in range(len(poll['options']))}
    for row in responses_col.aggregate(pipeline):
        results[row['_id']] = row['count']

    return jsonify({
        'poll_id':         poll['_id'],
        'question':        poll['question'],
        'options':         poll['options'],
        'results':         results,
        'total_responses': sum(results.values())
    })

@app.route('/api/end_poll', methods=['POST'])
def end_poll():
    if polls_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    if not require_password(request.json):
        return jsonify({'error': 'Unauthorized'}), 401
    polls_col.delete_many({})
    responses_col.delete_many({})
    _api_log('poll_end')
    return jsonify({'status': 'poll_ended'})

# ---------- Password ----------
@app.route('/get_password', methods=['GET'])
def get_password():
    # NOTE: returns password to authenticated frontend — consider moving to token-based auth in future
    return jsonify({'password': get_password_value()})

@app.route('/set_password', methods=['POST'])
def set_password():
    if config_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.json
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    new_password = data.get('new_password', '').strip()
    if not new_password:
        return jsonify({'error': 'Password cannot be empty'}), 400
    config_col.update_one({'_id': 'password'}, {'$set': {'value': new_password}}, upsert=True)
    _api_log('password_change')
    return jsonify({'status': 'success', 'message': 'Password updated'})

# ---------- Chat Messages ----------
@app.route('/send_message', methods=['POST'])
def send_message():
    if messages_col is None:
        return jsonify({'status': 'error', 'message': 'DB unavailable'}), 500
    data    = request.json or {}
    sender  = data.get('sender', '').strip()
    message = data.get('message', '').strip()
    if not sender or not message:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    messages_col.insert_one({
        'sender':     sender,
        'message':    message,
        'time':       now_ist().strftime("%d-%m-%Y %I:%M %p"),
        'isFile':     False,
        'created_at': now_ist()
    })
    return jsonify({'status': 'Message received'})

@app.route('/send_file', methods=['POST'])
def receive_file():
    if messages_col is None:
        return jsonify({'status': 'error', 'message': 'DB unavailable'}), 500
    data      = request.json or {}
    sender    = data.get('sender')
    file_data = data.get('data')
    if not sender or not file_data:
        return jsonify({'status': 'error', 'message': 'Invalid file data'}), 400

    messages_col.insert_one({
        'sender':     sender,
        'fileName':   data.get('name'),
        'fileData':   file_data,
        'fileType':   data.get('type'),
        'fileSize':   data.get('size'),
        'time':       now_ist().strftime("%d-%m-%Y %I:%M %p"),
        'isFile':     True,
        'created_at': now_ist()
    })

    # Keep only last 200 messages
    total = messages_col.count_documents({})
    if total > 200:
        oldest = list(messages_col.find({}, {'_id': 1}).sort('created_at', 1).limit(total - 200))
        messages_col.delete_many({'_id': {'$in': [d['_id'] for d in oldest]}})

    logger.info(f"File received from {sender}: {data.get('name')}")
    return jsonify({'status': 'File received', 'file': data.get('name')})

@app.route('/get_messages', methods=['GET'])
def get_messages():
    if messages_col is None:
        return jsonify([])
    try:
        docs = list(messages_col.find({}, {'_id': 0, 'created_at': 0}).sort('created_at', 1))
        return jsonify(docs)
    except Exception as e:
        logger.error(f"get_messages error: {e}")
        return jsonify([])

@app.route('/clear_messages', methods=['POST'])
def clear_messages():
    if messages_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    if not require_password(request.json):
        return jsonify({'error': 'Unauthorized'}), 401
    messages_col.delete_many({})
    _api_log('chat_clear')
    return jsonify({'status': 'success', 'message': 'All chat messages cleared'})

# ============ VISITOR TRACKING ============
@app.route('/api/track_netlify_visitor', methods=['POST', 'OPTIONS'])
def track_netlify_visitor():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = 'https://abhinavpanwar.netlify.app'
        r.headers['Access-Control-Allow-Credentials'] = 'true'
        r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if visitors_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    data      = request.json
    ip        = get_client_ip()
    device_id = request.cookies.get('device_id', str(uuid.uuid4()))
    ua        = request.headers.get('User-Agent', 'Unknown')
    page_url  = data.get('page_url', 'Unknown')
    current   = now_ist()

    existing = visitors_col.find_one({'$or': [{'ip_address': ip}, {'device_id': device_id}]})
    if existing:
        visitors_col.update_one({'_id': existing['_id']}, {
            '$set': {'last_seen': current, 'user_agent': ua, 'last_page': page_url, 'device_type': parse_device(ua)},
            '$inc': {'visit_count': 1},
            '$addToSet': {'pages_visited': page_url}
        })
    else:
        visitors_col.insert_one({
            'ip_address': ip, 'device_id': device_id,
            'first_seen': current, 'last_seen': current,
            'user_agent': ua, 'device_type': parse_device(ua),
            'last_page': page_url, 'pages_visited': [page_url],
            'visit_count': 1, 'created_at': current, 'source': 'Netlify'
        })

    response = jsonify({'status': 'tracked'})
    if not request.cookies.get('device_id'):
        response.set_cookie('device_id', device_id, max_age=365*24*3600,
                            secure=True, httponly=True, samesite='None', path='/')
    return response

@app.route('/api/visitors/stats', methods=['GET'])
def get_visitor_stats():
    if visitors_col is None:
        return jsonify({'total_visitors': 0, 'today_visitors': 0, 'active_now': 0, 'device_stats': []})
    today_start    = now_ist().replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_min_ago = now_ist() - timedelta(minutes=30)
    device_stats   = list(visitors_col.aggregate([{'$group': {'_id': '$device_type', 'count': {'$sum': 1}}}]))
    return jsonify({
        'total_visitors': visitors_col.count_documents({}),
        'today_visitors': visitors_col.count_documents({'first_seen': {'$gte': today_start}}),
        'active_now':     visitors_col.count_documents({'last_seen': {'$gte': thirty_min_ago}}),
        'device_stats':   device_stats
    })

@app.route('/api/visitors/list', methods=['GET'])
def get_visitors_list():
    if visitors_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    limit    = int(request.args.get('limit', 10))
    visitors = list(visitors_col.find({}, {'_id': 0}).sort('last_seen', -1).limit(limit))
    for v in visitors:
        for key in ('first_seen', 'last_seen', 'created_at'):
            if key in v and hasattr(v[key], 'strftime'):
                v[key] = v[key].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'visitors': visitors, 'total': len(visitors)})

# ============ USER LOGS ============
def _api_log(event, extra=None):
    if user_logs_col is None:
        return
    try:
        entry = {
            'event':       event,
            'ip_address':  get_client_ip(),
            'device_type': parse_device(request.headers.get('User-Agent', '')),
            'user_agent':  request.headers.get('User-Agent', 'Unknown'),
            'page':        request.headers.get('Referer', 'server'),
            'timestamp':   now_ist()
        }
        if extra:
            entry.update(extra)
        user_logs_col.insert_one(entry)
    except Exception as e:
        logger.error(f"_api_log error: {e}")

@app.route('/api/log', methods=['POST', 'OPTIONS'])
def log_event():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        r.headers['Access-Control-Allow-Credentials'] = 'true'
        r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if user_logs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    data       = request.json
    event_type = data.get('event')
    if not event_type:
        return jsonify({'error': 'Missing event type'}), 400

    entry = {
        'event':       event_type,
        'ip_address':  get_client_ip(),
        'device_type': parse_device(request.headers.get('User-Agent', '')),
        'user_agent':  request.headers.get('User-Agent', 'Unknown'),
        'page':        data.get('page', 'Unknown'),
        'timestamp':   now_ist()
    }
    if event_type in ('login', 'login_failed'):
        entry['username'] = data.get('username', 'Unknown')
    elif event_type == 'message':
        entry['username'] = data.get('username', 'Unknown')
        entry['message']  = data.get('message', '')
    elif event_type == 'file_send':
        entry['username']  = data.get('username', 'Unknown')
        entry['file_name'] = data.get('file_name', 'Unknown')
        entry['file_type'] = data.get('file_type', 'Unknown')
        entry['file_size'] = data.get('file_size', 0)

    user_logs_col.insert_one(entry)
    return jsonify({'status': 'logged'})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if user_logs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    token = request.headers.get('X-Admin-Token') or request.args.get('token')
    if token != app.secret_key:
        return jsonify({'error': 'Unauthorized'}), 401
    event_filter = request.args.get('event')
    limit        = int(request.args.get('limit', 100))
    query        = {'event': event_filter} if event_filter else {}
    logs         = list(user_logs_col.find(query, {'_id': 0}).sort('timestamp', -1).limit(limit))
    for log in logs:
        if 'timestamp' in log and hasattr(log['timestamp'], 'strftime'):
            log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'logs': logs, 'total': len(logs)})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    if user_logs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    if not require_password(request.json):
        return jsonify({'error': 'Unauthorized'}), 401
    result = user_logs_col.delete_many({})
    return jsonify({'status': 'cleared', 'deleted': result.deleted_count})

# ============ DB TEST ============
@app.route('/api/test_db')
def test_db():
    if visitors_col is not None:
        try:
            return jsonify({
                'status':        'connected',
                'visitor_count': visitors_col.count_documents({}),
                'message_count': messages_col.count_documents({}),
                'log_count':     user_logs_col.count_documents({}),
                'message':       '✅ MongoDB is working!'
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'error', 'message': '❌ MongoDB not connected'}), 500

# ============ KILL SWITCH (persisted in MongoDB) ============
@app.route('/api/netlify/kill-status', methods=['GET', 'OPTIONS'])
def netlify_kill_status():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    try:
        killed, updated_at = False, None
        if config_col is not None:
            doc = config_col.find_one({'_id': 'kill_switch'})
            logger.debug(f"kill-status doc: {doc}")
            if doc:
                killed     = doc.get('killed', False)
                updated_at = doc.get('updated_at')
    except Exception as e:
        logger.error(f"kill-status error: {e}")
    r = make_response(jsonify({'killed': killed, 'updated_at': updated_at}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    r.headers['Cache-Control'] = 'no-store'
    return r

@app.route('/api/netlify/kill', methods=['POST', 'OPTIONS'])
def netlify_kill():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        return r
    if config_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data = request.get_json() or {}
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    updated_at = now_ist().isoformat()
    result = config_col.update_one(
        {'_id': 'kill_switch'},
        {'$set': {'killed': True, 'updated_at': updated_at}},
        upsert=True
    )
    logger.info(f"kill update result: matched={result.matched_count} modified={result.modified_count} upserted={result.upserted_id}")
    _api_log('kill_switch_on')
    return jsonify({'success': True, 'activated_at': updated_at})

@app.route('/api/netlify/restore', methods=['POST', 'OPTIONS'])
def netlify_restore():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        return r
    if config_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data = request.get_json() or {}
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    updated_at = now_ist().isoformat()
    result = config_col.update_one(
        {'_id': 'kill_switch'},
        {'$set': {'killed': False, 'updated_at': updated_at}},
        upsert=True
    )
    logger.info(f"restore update result: matched={result.matched_count} modified={result.modified_count} upserted={result.upserted_id}")
    _api_log('kill_switch_off')
    return jsonify({'success': True, 'deactivated_at': updated_at})

# ============ SKILL SCORES ============
@app.route('/api/scores', methods=['GET', 'OPTIONS'])
def get_scores():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if scores_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    doc = scores_col.find_one({'_id': 'skills'}, {'_id': 0})
    r = make_response(jsonify(doc or {}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/api/scores', methods=['POST', 'OPTIONS'])
def set_scores():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if scores_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data    = request.json or {}
    skill   = data.get('skill')
    value   = data.get('value')
    if skill not in ('F', 'SM', 'TM', 'PS', 'DM', 'C') or not isinstance(value, int) or not (0 <= value <= 100):
        return jsonify({'error': 'Invalid skill or value'}), 400
    scores_col.update_one({'_id': 'skills'},
        {'$set': {skill: value, 'updated_at': now_ist().strftime('%d %b %Y, %I:%M %p')}},
        upsert=True)
    r = make_response(jsonify({'status': 'updated', 'skill': skill, 'value': value}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

# ============ RATING ============
@app.route('/api/rating', methods=['GET', 'OPTIONS'])
def get_rating():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if rating_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    doc = rating_col.find_one({'_id': 'portfolio'})
    total = doc.get('total', 0)
    count = doc.get('count', 0)
    avg   = round(total / count, 1) if count else 0
    r = make_response(jsonify({'average': avg, 'count': count}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/api/rating', methods=['POST'])
def submit_rating():
    if rating_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    stars = (request.json or {}).get('stars')
    if stars not in (1, 2, 3, 4, 5):
        return jsonify({'error': 'stars must be 1-5'}), 400
    rating_col.update_one(
        {'_id': 'portfolio'},
        {'$inc': {'total': stars, 'count': 1}},
        upsert=True
    )
    doc = rating_col.find_one({'_id': 'portfolio'})
    avg = round(doc['total'] / doc['count'], 1)
    r = make_response(jsonify({'average': avg, 'count': doc['count']}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

# ============ MUSIC VOTE ============
@app.route('/api/songs', methods=['GET', 'OPTIONS'])
def get_songs():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if songs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    songs = list(songs_col.find({}, {'_id': 1, 'title': 1, 'artist': 1, 'youtube_id': 1, 'votes': 1}).sort('votes', -1))
    for s in songs:
        s['id'] = str(s.pop('_id'))
    r = make_response(jsonify({'songs': songs}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/api/songs/add', methods=['POST'])
def add_song():
    if songs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.json
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    title      = data.get('title', '').strip()
    artist     = data.get('artist', '').strip()
    youtube_id = data.get('youtube_id', '').strip()
    if not title or not youtube_id:
        return jsonify({'error': 'title and youtube_id are required'}), 400
    song_id = str(uuid.uuid4())
    songs_col.insert_one({'_id': song_id, 'title': title, 'artist': artist, 'youtube_id': youtube_id, 'votes': 0, 'created_at': now_ist()})
    return jsonify({'status': 'added', 'id': song_id})

@app.route('/api/songs/vote', methods=['POST', 'OPTIONS'])
def vote_song():
    if request.method == 'OPTIONS':
        r = make_response()
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if songs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    song_id = (request.json or {}).get('id')
    if not song_id:
        return jsonify({'error': 'id required'}), 400
    result = songs_col.update_one({'_id': song_id}, {'$inc': {'votes': 1}})
    if result.matched_count == 0:
        return jsonify({'error': 'Song not found'}), 404
    song = songs_col.find_one({'_id': song_id})
    r = make_response(jsonify({'status': 'voted', 'votes': song['votes']}))
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/api/songs/delete', methods=['POST'])
def delete_song():
    if songs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.json
    if not require_password(data):
        return jsonify({'error': 'Unauthorized'}), 401
    song_id = data.get('id')
    songs_col.delete_one({'_id': song_id})
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
