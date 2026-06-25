"""Europe PMC client: cursorMark pagination, partial-failure, and normalization.
Fully offline — monkeypatches urlopen + sleep; the real search_paged logic runs."""
import json
import urllib.error

import pytest

import europepmc_client as epmc


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, *a):
        return self._b


def _urlopen_serving(pages):
    it = iter(pages)

    def fake(_req, timeout=None):
        item = next(it)
        if isinstance(item, Exception):
            raise item
        return _Resp(item)

    return fake


def _page(results, cursor):
    return {"resultList": {"result": results}, "nextCursorMark": cursor}


def test_pagination_stops_on_unchanged_cursor(monkeypatch):
    pages = [_page([{"id": "1"}, {"id": "2"}], "c1"), _page([{"id": "3"}], "c1")]  # cursor repeats -> stop
    monkeypatch.setattr(epmc.urllib.request, "urlopen", _urlopen_serving(pages))
    monkeypatch.setattr(epmc.time, "sleep", lambda *_a: None)
    out = epmc.search_paged("q", target=100, page_size=2)
    assert [r["id"] for r in out] == ["1", "2", "3"]


def test_partial_failure_returns_accumulated(monkeypatch):
    pages = [_page([{"id": "1"}], "c1"), urllib.error.URLError("boom")]  # 2nd page fails
    monkeypatch.setattr(epmc.urllib.request, "urlopen", _urlopen_serving(pages))
    monkeypatch.setattr(epmc.time, "sleep", lambda *_a: None)
    out = epmc.search_paged("q", target=100, page_size=1)
    assert [r["id"] for r in out] == ["1"]  # first page kept, not lost


def test_first_page_failure_raises_runtimeerror(monkeypatch):
    monkeypatch.setattr(epmc.urllib.request, "urlopen", _urlopen_serving([urllib.error.URLError("down")]))
    monkeypatch.setattr(epmc.time, "sleep", lambda *_a: None)
    with pytest.raises(RuntimeError):
        epmc.search_paged("q", target=10)


def test_normalize_resolvable_url():
    d = epmc.normalize({"source": "MED", "id": "42", "title": "X", "pubYear": "2025"}, "cond")
    assert d["url"] == "https://europepmc.org/article/MED/42"
    assert d["is_trial"] is False and d["condition"] == "cond"
