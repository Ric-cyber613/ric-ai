import importlib
import os


def reload_app_with_env(env):
    # set env and reload module
    for k, v in env.items():
        os.environ[k] = v
    if 'web.app' in importlib.sys.modules:
        importlib.reload(importlib.import_module('web.app'))
    return importlib.import_module('web.app')


def test_google_verification_file(tmp_path, monkeypatch):
    # Set filename and content
    fn = 'google-test-12345.html'
    content = 'google-site-verification: test-12345'
    app_mod = reload_app_with_env({'GOOGLE_SITE_VERIFICATION_FILENAME': fn, 'GOOGLE_SITE_VERIFICATION_FILE_CONTENT': content})
    client = app_mod.app.test_client()
    r = client.get(f'/{fn}')
    assert r.status_code == 200
    assert content in r.get_data(as_text=True)


def test_google_meta_injection(monkeypatch):
    token = 'meta-token-abc'
    app_mod = reload_app_with_env({'GOOGLE_SITE_VERIFICATION_META': token})
    client = app_mod.app.test_client()
    r = client.get('/')
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert f'name="google-site-verification"' in html
    assert token in html
