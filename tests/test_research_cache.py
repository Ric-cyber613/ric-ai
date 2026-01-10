import pytest
from src.ric_ai import research


def test_search_cache(monkeypatch):
    # Mock requests.get to assert single network call
    calls = {'count': 0}

    class DummyResp:
        text = '<html><body><a href="http://example.com">Example</a></body></html>'
        def raise_for_status(self):
            return
    def fake_get(*a, **k):
        calls['count'] += 1
        return DummyResp()

    monkeypatch.setattr(research, 'AVAILABLE', True)
    monkeypatch.setattr(research, 'requests', type('R', (), {'get': fake_get}))
    # first call should call network
    r1 = research.search_duckduckgo('foo', max_results=1)
    assert calls['count'] == 1
    # second call (same query) should be served from cache
    r2 = research.search_duckduckgo('foo', max_results=1)
    assert calls['count'] == 1
    assert r1 == r2


def test_fetch_cache(monkeypatch):
    calls = {'count': 0}
    class DummyResp:
        text = '<html><body><p>Hello world</p></body></html>'
        def raise_for_status(self):
            return
    def fake_get(*a, **k):
        calls['count'] += 1
        return DummyResp()
    monkeypatch.setattr(research, 'AVAILABLE', True)
    monkeypatch.setattr(research, 'requests', type('R', (), {'get': fake_get}))
    t1 = research.fetch_text_from_url('http://example.com')
    assert calls['count'] == 1
    t2 = research.fetch_text_from_url('http://example.com')
    assert calls['count'] == 1
    assert t1 == t2


def test_cache_clear(monkeypatch):
    monkeypatch.setattr(research, 'AVAILABLE', True)
    research.clear_cache()
    # populate cache
    class DummyResp:
        text = '<html><body><a href="http://example.com">Example</a></body></html>'
        def raise_for_status(self):
            return
    monkeypatch.setattr(research, 'requests', type('R', (), {'get': lambda *a, **k: DummyResp()}))
    research.search_duckduckgo('bar', max_results=1)
    assert research.cache_status()['search_entries'] >= 1
    research.clear_cache()
    assert research.cache_status()['search_entries'] == 0
    assert research.cache_status()['fetch_entries'] == 0
