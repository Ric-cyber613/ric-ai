import sqlite3
import os
import secrets
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

bp = Blueprint('auth', __name__)

DB_PATH = os.environ.get('RICAI_DB_PATH', os.path.join(os.path.dirname(__file__), 'data', 'users.db'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            is_verified INTEGER DEFAULT 0,
            verification_token TEXT,
            reset_token TEXT,
            reset_expires TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # ensure columns exist for older DBs (simple migration)
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    if 'email' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN email TEXT')
    if 'is_verified' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0')
    if 'verification_token' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN verification_token TEXT')
    if 'reset_token' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
    if 'reset_expires' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN reset_expires TEXT')
    conn.commit()
    conn.close()


init_db()


@bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    email = (data.get('email') or '').strip() or None
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        verification_token = None
        is_verified = 0
        if email:
            # generate a verification token
            import secrets
            verification_token = secrets.token_urlsafe(24)
            is_verified = 0
        cur.execute('INSERT INTO users (username, password_hash, email, is_verified, verification_token, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (username, generate_password_hash(password), email, is_verified, verification_token, datetime.utcnow().isoformat()))
        conn.commit()
        # send verification email if email provided
        if email and verification_token:
            from .mailer import send_email
            url = os.environ.get('RICAI_PUBLIC_URL', 'http://localhost:8000') + f"/static/verify.html?token={verification_token}"
            body = f"Hello {username},\n\nPlease verify your email by visiting:\n{url}\n\nIf you didn't request this, ignore this email."
            try:
                send_email(email, 'Verify your Ric AI account', body)
            except Exception:
                # don't fail the registration on email send errors
                pass
        return jsonify({'ok': True, 'username': username})
    except sqlite3.IntegrityError:
        return jsonify({'ok': False, 'error': 'username already exists'}), 400
    finally:
        conn.close()


@bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password_hash, is_verified, email FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401

    # if email exists and not verified, warn the user (but still allow login)
    session['user_id'] = row['id']
    session['username'] = row['username']
    session['csrf_token'] = secrets.token_urlsafe(32)
    resp = {'ok': True, 'username': row['username'], 'csrf': session['csrf_token']}
    if row['email'] and not row['is_verified']:
        resp['warning'] = 'email not verified'
    return jsonify(resp)


@bp.route('/logout', methods=['POST'])
@csrf_required
def logout():
    # protect with CSRF
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('csrf_token', None)
    return jsonify({'ok': True})


@bp.route('/status', methods=['GET'])
def status():
    user = session.get('username')
    # ensure there's a CSRF token for the session (even anonymous)
    if not session.get('csrf_token'):
        session['csrf_token'] = secrets.token_urlsafe(32)
    return jsonify({'ok': True, 'username': user, 'csrf': session.get('csrf_token')})


@bp.route('/verify', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({'ok': False, 'error': 'token required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM users WHERE verification_token = ?', (token,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'ok': False, 'error': 'invalid token'}), 400
    cur.execute('UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?', (row['id'],))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'message': f"Email verified for {row['username']}"})


@bp.route('/request_reset', methods=['POST'])
def request_reset():
    data = request.json or {}
    identifier = (data.get('identifier') or '').strip()
    if not identifier:
        return jsonify({'ok': False, 'error': 'email or username required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email FROM users WHERE username = ? OR email = ?', (identifier, identifier))
    row = cur.fetchone()
    if not row:
        conn.close()
        # Do not reveal user existence; respond OK
        return jsonify({'ok': True})
    import secrets, datetime
    token = secrets.token_urlsafe(24)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    cur.execute('UPDATE users SET reset_token = ?, reset_expires = ? WHERE id = ?', (token, expires, row['id']))
    conn.commit()
    conn.close()
    # send email with the token
    from .mailer import send_email
    try:
        url = os.environ.get('RICAI_PUBLIC_URL', 'http://localhost:8000') + f"/static/reset.html?token={token}"
        body = f"Hello {row['username']},\n\nA password reset was requested for your account. Use the following link to reset your password (valid 1 hour):\n{url}\n\nIf you didn't request this, ignore this email."
        send_email(row['email'] or identifier, 'Ric AI password reset', body)
    except Exception:
        pass
    return jsonify({'ok': True})


@bp.route('/reset', methods=['POST'])
def reset_password():
    data = request.json or {}
    token = (data.get('token') or '').strip()
    new_password = data.get('password') or ''
    if not token or not new_password:
        return jsonify({'ok': False, 'error': 'token and new password required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, reset_expires FROM users WHERE reset_token = ?', (token,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'ok': False, 'error': 'invalid token'}), 400
    import datetime
    expires = datetime.datetime.fromisoformat(row['reset_expires']) if row['reset_expires'] else None
    if not expires or datetime.datetime.utcnow() > expires:
        conn.close()
        return jsonify({'ok': False, 'error': 'token expired'}), 400
    cur.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_expires = NULL WHERE id = ?', (generate_password_hash(new_password), row['id']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# Helper decorator
from functools import wraps

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'ok': False, 'error': 'authentication required'}), 401
        return f(*args, **kwargs)
    return wrapped


def csrf_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # For JSON POSTs, expect token in X-CSRF-Token header
        token = request.headers.get('X-CSRF-Token') or request.json.get('csrf') if request.json else None
        if not token or token != session.get('csrf_token'):
            return jsonify({'ok': False, 'error': 'csrf token missing or invalid'}), 400
        return f(*args, **kwargs)
    return wrapped
