import pytest
import re
from web.app import app as flask_app

sent_emails = []

class DummyMailer:
    def __init__(self):
        pass
    def send_email(self, to_address, subject, body):
        sent_emails.append({'to': to_address, 'subject': subject, 'body': body})

@pytest.fixture(autouse=True)
def patch_mailer(monkeypatch):
    # patch web.mailer.send_email
    import web
    monkeypatch.setattr('web.mailer.send_email', lambda to, s, b: sent_emails.append({'to': to, 'subject': s, 'body': b}))
    sent_emails.clear()
    yield

@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / 'test_users.db'
    monkeypatch.setenv('RICAI_DB_PATH', str(db_file))
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def test_verification_and_reset_flow(client):
    # register with email
    r = client.post('/auth/register', json={'username':'eve','password':'pw','email':'eve@example.com'})
    assert r.status_code == 200
    # an email should have been 'sent'
    assert any('Verify your Ric AI account' in e['subject'] for e in sent_emails)
    v = [e for e in sent_emails if 'Verify your Ric AI account' in e['subject']][0]
    m = re.search(r'token=([A-Za-z0-9_\-]+)', v['body'])
    assert m
    token = m.group(1)
    # New link should point to the in-app verify page
    assert '/static/verify.html?token=' in v['body']
    # verify via token (server endpoint)
    r = client.get(f'/auth/verify?token={token}')
    assert r.status_code == 200
    # request password reset
    r = client.post('/auth/request_reset', json={'identifier':'eve'})
    assert r.status_code == 200
    assert any('Ric AI password reset' in e['subject'] for e in sent_emails)
    reset = [e for e in sent_emails if 'Ric AI password reset' in e['subject']][0]
    m = re.search(r'token=([A-Za-z0-9_\-]+)', reset['body'])
    assert m
    token2 = m.group(1)
    # New link should point to the in-app reset page
    assert '/static/reset.html?token=' in reset['body']
    # reset password
    r = client.post('/auth/reset', json={'token': token2, 'password': 'newpw'})
    assert r.status_code == 200
    # login with new password
    r = client.post('/auth/login', json={'username':'eve','password':'newpw'})
    assert r.status_code == 200