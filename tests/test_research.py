import pytest
from src.ric_ai import research


def test_research_unavailable(monkeypatch):
    # Simulate missing dependencies
    monkeypatch.setattr(research, 'AVAILABLE', False)
    with pytest.raises(RuntimeError):
        research.search_duckduckgo('test')


def test_search_mock(monkeypatch):
    # Mock requests and bs4 behavior
    class DummyResp:
        text = '<html><body><a href="http://example.com">Example</a></body></html>'
        def raise_for_status(self):
            return
    monkeypatch.setattr(research, 'AVAILABLE', True)
    monkeypatch.setattr(research, 'requests', type('R', (), {'get': lambda *a, **k: DummyResp()}))
    monkeypatch.setattr(research, 'BeautifulSoup', lambda t, h: __import__('bs4').BeautifulSoup('<html><body><a href="http://example.com">Example</a></body></html>', 'html.parser'))
    res = research.search_duckduckgo('example', max_results=1)
    assert isinstance(res, list) and len(res) == 1
    title, url, snippet = res[0]
    assert 'http' in url
