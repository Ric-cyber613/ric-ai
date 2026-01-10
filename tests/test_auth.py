import os
import tempfile
import json
import pytest
from web.app import app as flask_app

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a temporary db for tests
    db_file = tmp_path / 'test_users.db'
    monkeypatch.setenv('RICAI_DB_PATH', str(db_file))
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def test_register_login_logout(client):
    # register
    r = client.post('/auth/register', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok']

    # duplicate register
    r = client.post('/auth/register', json={'username': 'alice', 'password': 'x'})
    assert r.status_code == 400

    # login wrong password
    r = client.post('/auth/login', json={'username': 'alice', 'password': 'wrong'})
    assert r.status_code == 401

    # login correct
    r = client.post('/auth/login', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok']

    # status shows username
    r = client.get('/auth/status')
    assert r.status_code == 200
    data = r.get_json()
    assert data['username'] == 'alice'

    # logout without csrf should fail
    r = client.post('/auth/logout')
    assert r.status_code == 400

    # logout with csrf
    r = client.post('/auth/logout', headers={'X-CSRF-Token': csrf})
    assert r.status_code == 200
    r = client.get('/auth/status')
    data = r.get_json()
    assert data['username'] is None


def test_kb_requires_auth(client):
    # not logged in, adding KB should fail
    r = client.post('/api/kb', json={'question':'q','answer':'a'})
    assert r.status_code == 401

    # register and login
    client.post('/auth/register', json={'username': 'bob', 'password': 'pw'})
    r = client.post('/auth/login', json={'username': 'bob', 'password': 'pw'})
    assert r.status_code == 200

    # fetch csrf token from status
    r = client.get('/auth/status')
    assert r.status_code == 200
    data = r.get_json()
    csrf = data.get('csrf')
    assert csrf

    # missing csrf should fail
    r = client.post('/api/kb', json={'question':'q','answer':'a'})
    assert r.status_code == 400

    # with csrf header should succeed
    r = client.post('/api/kb', headers={'X-CSRF-Token': csrf}, json={'question':'q','answer':'a'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok']
