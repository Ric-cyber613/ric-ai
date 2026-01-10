def test_api_status_endpoint():
    # Ensure the /api/status endpoint returns a valid JSON and ok=True
    import importlib
    m = importlib.import_module('web.app')
    app = getattr(m, 'app')
    client = app.test_client()
    resp = client.get('/api/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('ok') is True
    assert 'mode' in data
    assert 'transformer' in data
    # research_cache may be None or a dict
    assert 'research_cache' in data
