# Ric AI (local)

Ric AI is a small self-contained local AI assistant implemented in Python. It uses a local knowledge base and a simple Markov chain generator to produce replies—no external APIs or services required.

Features:
- Tkinter GUI with chat window
- Local knowledge base (`kb.json`) editable via the GUI
- Simple retrieval (cosine similarity) to answer queries from the KB
- Markov-chain fallback generator for creative replies

How to run:

1. Ensure you have Python 3.8+ installed (Tkinter should be available).
2. From the repository root, run:

   ```bash
   python main.py
   ```

Files:
- `src/ric_ai/` - package with AI modules and GUI
- `main.py` - application entry point (desktop GUI)
- `kb.json` - knowledge base file (created on first run or prepopulated)
- `web/` - Flask web app and static frontend for deploying Ric AI as a web app
- `scripts/` - utility scripts (e.g., `predownload_model.py`)
Design notes:
- All code runs locally. No external APIs are used.
- The implementation is intentionally simple so you can extend it easily.

Optional: Online (local transformer) mode 🔧
- This app supports an *optional* online-style research mode that uses a local generative transformer model (no external API). This requires installing extra Python packages and downloading a model to your machine.

Install (recommended virtualenv):

```bash
pip install transformers torch
```

Pre-download a small model (e.g. `gpt2`) so the app can load it quickly:

```bash
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('gpt2'); AutoModelForCausalLM.from_pretrained('gpt2')"
```

Using online mode (desktop GUI):
- Start the GUI, go to Settings → Mode → Online
- Click "Load Model" and enter the model name (e.g. `gpt2`)
- Once loaded, Ric AI will attempt to use the local model to answer research-style queries.

Using online mode (web app):
- By default the web app runs in `offline` mode. You can enable online mode by setting environment variable `RICAI_MODE=online`.
- The web app supports optional *web research* that performs a light DuckDuckGo search and fetches top pages to provide context for answers. Enable it in the UI (Use web research) or send `use_research=true` to the `/api/respond` endpoint.
- To load a model at runtime, use the web UI's Mode selector and call the `/api/load_model` endpoint (or use the predownload CLI then set `RICAI_MODE=online`).

Notes & caution:
- Web research uses live HTTP requests to gather context. Respect site terms and robots; consider the legal and ethical implications for scraping before enabling widely.
- If `requests` and `beautifulsoup4` are not installed, the web research option will be disabled and the app will fall back to KB/transformer-only behavior.
Pre-download models (CLI)
- You can pre-download model/tokenizer files to the local cache to speed up first load and avoid downloads during runtime.

Run the CLI script:

```bash
python scripts/predownload_model.py --model gpt2
```

Deploying the web app (quick):
- Build and run with docker-compose:

```bash
docker-compose up --build
```

- Visit http://localhost:8000 to use the web app (chat UI).

Authentication
- The web app supports user registration and login. Users are stored in a simple local SQLite DB at `web/data/users.db` (or the path set via `RICAI_DB_PATH`).
- Initialize the DB explicitly (optional):

```bash
python web/init_db.py
```

- In the web UI, use the Account box to register or log in. Adding KB entries and loading models require an authenticated account.

Security notes
- This is a simple auth implementation intended for local or internal deployments. For public-facing production deployments, consider adding HTTPS (Nginx + Let's Encrypt), stronger password policies, email verification, rate-limiting, and a proper user management system.

Session & CSRF protection (recommended)
- The web app now enables more secure session cookie defaults: `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, and `SESSION_COOKIE_SAMESITE=Lax`. In production you must serve the app over HTTPS for `SESSION_COOKIE_SECURE` to be effective.
- A per-session CSRF token is generated and returned by `/auth/status` (and on login). Clients must include the token in the `X-CSRF-Token` header for state-changing requests (POST endpoints such as `/api/kb`, `/api/load_model`, and `/auth/logout`).
- In the web GUI this header is added automatically after sign-in.
- Make sure to set `FLASK_SECRET` to a strong secret in production to protect session cookies.

Email verification & password reset
- Optional flows for email verification and password reset are available:
  - During registration provide an `email` field to send a verification link.
  - `/auth/verify?token=...` verifies a user when they visit the link sent to email.
  - `/auth/request_reset` accepts `{identifier: username|email}` to send a reset email containing a tokenized link (valid 1 hour by default).
  - `/auth/reset` accepts `{token, password}` to set a new password.
- The app uses SMTP if configured via env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, and `EMAIL_FROM`. If not configured emails are printed to the console for local development/testing.
- Set `RICAI_PUBLIC_URL` to the public base URL (e.g., https://ricai.com) so emails contain working links.


Running integration tests (optional)

The repository includes an optional integration test that will attempt to download a tiny transformer model and run a short generation. This test is skipped by default to avoid unexpected downloads during normal testing.

To run the integration test:

1. Install the optional dependencies:

```bash
pip install transformers torch
```

2. Set the environment variable to enable HF integration tests and run pytest:

```bash
export RUN_HF_INTEGRATION_TESTS=1
pytest tests/test_transformer_integration.py -q
```

Note: The integration test uses `sshleifer/tiny-gpt2` by default to minimize download size and memory usage. If you have limited bandwidth or disk space, consider not running this test.

Notes:
- If `transformers` or the model is not present, the app will continue to work in offline mode (greetings, KB lookup, Markov fallback).
- Large models require more disk space and memory; for modest machines use small models like `gpt2`.

Enjoy!