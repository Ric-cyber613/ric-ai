"""Simple web research utilities.

Performs a lightweight search using DuckDuckGo HTML results and fetches page
snippets. This is intentionally minimal and optional. If `requests` or
`beautifulsoup4` are not installed, functions will raise RuntimeError.
"""
from typing import List, Tuple

AVAILABLE = True
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    AVAILABLE = False

import time
import os
from typing import Optional

# Simple in-memory TTL cache for search queries and URL fetches
_CACHE_TTL = int(os.environ.get('RICAI_RESEARCH_CACHE_TTL', 3600))  # seconds
_CACHE_MAX = int(os.environ.get('RICAI_RESEARCH_CACHE_MAX', 512))
_search_cache = {}  # query -> (ts, results)
_fetch_cache = {}   # url -> (ts, text)


def _now():
    return int(time.time())


def _get_from_cache(cache: dict, key: str) -> Optional[object]:
    item = cache.get(key)
    if not item:
        return None
    ts, val = item
    if _now() - ts > _CACHE_TTL:
        try:
            del cache[key]
        except KeyError:
            pass
        return None
    return val


def _set_in_cache(cache: dict, key: str, val: object):
    cache[key] = (_now(), val)
    # eviction: trim to _CACHE_MAX by removing oldest
    if len(cache) > _CACHE_MAX:
        # sort keys by timestamp and remove oldest 10% entries
        items = sorted(cache.items(), key=lambda kv: kv[1][0])
        to_remove = max(1, int(_CACHE_MAX * 0.1))
        for k, _ in items[:to_remove]:
            try:
                del cache[k]
            except KeyError:
                pass


def clear_cache():
    _search_cache.clear()
    _fetch_cache.clear()


def cache_status():
    return {
        'search_entries': len(_search_cache),
        'fetch_entries': len(_fetch_cache),
        'ttl_seconds': _CACHE_TTL,
        'max_entries': _CACHE_MAX,
    }


def ensure_available():
    if not AVAILABLE:
        raise RuntimeError('research dependencies missing (requests, beautifulsoup4)')


def search_duckduckgo(query: str, max_results: int = 3, timeout: int = 5) -> List[Tuple[str, str, str]]:
    """Search DuckDuckGo HTML endpoint and return list of (title, url, snippet).

    We fetch the DDG HTML search and parse links; this avoids requiring an API key.
    """
    ensure_available()
    q = query.strip()
    if not q:
        return []
    url = 'https://html.duckduckgo.com/html/'
    params = {'q': q}
    # Check cache first
    cache_key = f'search:{q}'
    cached = _get_from_cache(_search_cache, cache_key)
    if cached is not None:
        return cached

    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    # try common patterns
    anchors = soup.find_all('a', href=True)
    seen = set()
    for a in anchors:
        href = a['href']
        if href.startswith('http') and href not in seen:
            seen.add(href)
            title = a.get_text(strip=True) or href
            # try to find a nearby snippet
            snippet = ''
            parent = a.parent
            if parent:
                snippet = parent.get_text(separator=' ', strip=True)
            results.append((title, href, snippet))
            if len(results) >= max_results:
                break

    _set_in_cache(_search_cache, cache_key, results)
    return results


def fetch_text_from_url(url: str, max_chars: int = 2000, timeout: int = 6) -> str:
    """Fetch a URL and return a cleaned text snippet up to max_chars."""
    ensure_available()
    # Check cache first
    cache_key = f'fetch:{url}'
    cached = _get_from_cache(_fetch_cache, cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # remove scripts/styles
        for s in soup(['script', 'style', 'noscript', 'header', 'footer', 'form']):
            s.decompose()
        text = ' '.join(soup.stripped_strings)
        short = text[:max_chars]
        _set_in_cache(_fetch_cache, cache_key, short)
        return short
    except Exception:
        return ''
