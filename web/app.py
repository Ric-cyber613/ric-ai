from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from src.ric_ai.ai import RicAI
try:
    # Prefer absolute import when running as module or installed package
    from web.auth import bp as auth_bp, login_required, csrf_required
except Exception:
    try:
        # Fallback to relative import when running as a package
        from .auth import bp as auth_bp, login_required, csrf_required  # type: ignore
    except Exception:
        # Last resort: provide no-op placeholders so the app can still run for local testing
        auth_bp = None
        def login_required(f):
            return f
        def csrf_required(f):
            return f

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)
# Secret key for sessions (override in production via FLASK_SECRET env var)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
# Secure session cookie settings (recommended for production behind HTTPS)
app.config.update({
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600 * 24,  # 1 day
})

# Use environment variable to pick KB path and default mode
KB_PATH = os.environ.get('RICAI_KB_PATH', os.path.join(os.getcwd(), '..', 'kb.json'))
DEFAULT_MODE = os.environ.get('RICAI_MODE', 'offline')  # 'offline' or 'online'

# Initialize RicAI safely so import-time failures don't break tests or simple imports
try:
    ric = RicAI(kb_path=KB_PATH)
    ric.set_mode(DEFAULT_MODE)
except Exception as e:
    app.logger.exception('Failed to initialize RicAI; using fallback stub')
    class _StubTransformer:
        def is_available(self):
            return False
        def is_loaded(self):
            return False

    class _StubRic:
        mode = DEFAULT_MODE
        transformer = _StubTransformer()
        kb = []
        def set_mode(self, m):
            self.mode = m
        def respond(self, *args, **kwargs):
            return 'Service temporarily unavailable'
        def add_kb_entry(self, q, a):
            return {'id': None, 'question': q, 'answer': a}

    ric = _StubRic()

# register auth blueprint (optional)
if auth_bp is not None:
    app.register_blueprint(auth_bp, url_prefix='/auth')
else:
    app.logger.warning('Auth blueprint not available; running without auth')


@app.route('/')
def index():
    # Use configured static folder to avoid relying on CWD
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/robots.txt')
def robots_txt():
    # Serve a minimal robots.txt. Use environment variable RICAI_PUBLIC_URL to include sitemap location.
    public = os.environ.get('RICAI_PUBLIC_URL', 'https://ricai.com')
    content = f"""User-agent: *
Allow: /
Sitemap: {public.rstrip('/')}/sitemap.xml
"""
    return app.response_class(content, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    # Dynamically generate a small sitemap from known public endpoints.
    public = os.environ.get('RICAI_PUBLIC_URL') or request.host_url.rstrip('/')
    urls = [
        f"{public}/",
        f"{public}/static/index.html",
        f"{public}/auth/login",
        f"{public}/auth/register",
        f"{public}/api/status",
    ]
    urlset = "\n".join([
        f"  <url>\n    <loc>{u}</loc>\n  </url>" for u in urls
    ])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urlset}
</urlset>"""
    return app.response_class(xml, mimetype='application/xml')


# Google Search verification helpers
# - If GOOGLE_SITE_VERIFICATION_FILENAME is set, serve that filename at root with the provided content
# - If GOOGLE_SITE_VERIFICATION_META is set, inject the meta tag into the served index.html
GOOGLE_SITE_VERIFICATION_FILENAME = os.environ.get('GOOGLE_SITE_VERIFICATION_FILENAME')
GOOGLE_SITE_VERIFICATION_FILE_CONTENT = os.environ.get('GOOGLE_SITE_VERIFICATION_FILE_CONTENT')
GOOGLE_SITE_VERIFICATION_META = os.environ.get('GOOGLE_SITE_VERIFICATION_META')

if GOOGLE_SITE_VERIFICATION_FILENAME:
    filename = GOOGLE_SITE_VERIFICATION_FILENAME
    def _serve_google_verification_file():
        content = GOOGLE_SITE_VERIFICATION_FILE_CONTENT or f"{filename}"
        # Google expects the file to be served from root path
        return app.response_class(content, mimetype='text/html')
    app.add_url_rule(f'/{filename}', endpoint='google_verify_file', view_func=_serve_google_verification_file)


# Update index route to optionally inject meta verification tag
@app.route('/')
def index():
    # Use configured static folder to avoid relying on CWD
    if GOOGLE_SITE_VERIFICATION_META:
        try:
            path = os.path.join(app.static_folder, 'index.html')
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            if 'google-site-verification' not in html:
                meta = f'<meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION_META}" />'
                html = html.replace('<head>', '<head>\n    ' + meta, 1)
            return html, 200, {'Content-Type': 'text/html'}
        except Exception:
            app.logger.exception('Failed to inject Google verification meta tag; falling back to static serve')
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/respond', methods=['POST'])
def api_respond():
    data = request.json or {}
    text = data.get('text', '')
    creativity = float(data.get('creativity', 0.8))
    mode = data.get('mode') or DEFAULT_MODE
    use_research = bool(data.get('use_research', False))
    ric.set_mode(mode)
    try:
        out = ric.respond(text, creativity=creativity, use_research=use_research)
        return jsonify({'ok': True, 'response': out})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/kb', methods=['GET', 'POST'])
def api_kb():
    if request.method == 'GET':
        return jsonify({'ok': True, 'kb': ric.kb})
    # require auth + CSRF to add KB entries

    @login_required
    @csrf_required
    def add_entry():
        data = request.json or {}
        q = data.get('question')
        a = data.get('answer')
        if not q or a is None:
            return jsonify({'ok': False, 'error': 'question and answer required'}), 400
        entry = ric.add_kb_entry(q, a)
        return jsonify({'ok': True, 'entry': entry})

    return add_entry()


@app.route('/api/mode', methods=['POST'])
def api_mode():
    data = request.json or {}
    mode = data.get('mode')
    if mode not in ('offline', 'online'):
        return jsonify({'ok': False, 'error': 'invalid mode'}), 400
    ric.set_mode(mode)
    return jsonify({'ok': True, 'mode': mode})


@app.route('/api/load_model', methods=['POST'])
@login_required
@csrf_required
def api_load_model():
    data = request.json or {}
    model = data.get('model')
    device = data.get('device', 'cpu')
    try:
        ric.load_transformer_model(model_name=model, device=device)
        return jsonify({'ok': True, 'model': model})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    t = getattr(ric, 'transformer', None)
    try:
        transformer_status = {
            'available': False,
            'loaded': False,
            'model': None,
            'device': None,
        }
        if t is not None:
            try:
                transformer_status = {
                    'available': t.is_available(),
                    'loaded': t.is_loaded(),
                    'model': getattr(t, 'model_name', None),
                    'device': getattr(t, 'device', None),
                }
            except Exception:
                app.logger.exception('Error getting transformer status')

        status = {
            'ok': True,
            'mode': ric.mode,
            'transformer': transformer_status,
        }
        # include research cache info if research module is present
        try:
            from src.ric_ai import research
            status['research_cache'] = research.cache_status()
        except Exception:
            status['research_cache'] = None
        return jsonify(status)
    except Exception as e:
        app.logger.exception('Error in /api/status')
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/cache/clear', methods=['POST'])
@login_required
@csrf_required
def api_research_cache_clear():
    try:
        from src.ric_ai import research
        research.clear_cache()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/cache/status', methods=['GET'])
def api_research_cache_status():
    try:
        from src.ric_ai import research
        return jsonify({'ok': True, 'status': research.cache_status()})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
