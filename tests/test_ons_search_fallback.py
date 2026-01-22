from fastapi.testclient import TestClient

from server.config import settings
from server.main import app


def test_ons_search_sample_fallback(monkeypatch):
    from tools import ons_search

    monkeypatch.setattr(settings, "ONS_SEARCH_LIVE_ENABLED", False, raising=False)
    monkeypatch.setattr(
        ons_search,
        "_load",
        lambda: {"dimensions": {"geo": ["abc", "def"]}},
    )
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "ons_search.query", "term": "ab"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is False
    assert any(r["code"] == "abc" for r in body["results"])


def test_ons_search_load_failure_returns_empty(monkeypatch):
    from tools import ons_search

    def boom(self):  # noqa: ARG001
        raise OSError("nope")

    monkeypatch.setattr(ons_search.Path, "read_text", boom)
    assert ons_search._load() == {}


def test_ons_search_invalid_limit_offset(client):
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_search.query", "term": "test", "limit": 0},
    )
    assert resp.status_code == 400
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_search.query", "term": "test", "offset": -1},
    )
    assert resp.status_code == 400


def test_ons_search_live_error_passthrough(monkeypatch):
    from tools import ons_search

    def fake_get_json(url, params):  # noqa: ARG001
        return 500, {"error": "nope"}

    monkeypatch.setattr(ons_search._SEARCH_CLIENT, "get_json", fake_get_json)
    status, data = ons_search._live_search("gdp", 10, 0)
    assert status == 500
    assert data["error"] == "nope"


def test_ons_search_live_skips_non_dict_items(monkeypatch):
    from tools import ons_search

    def fake_get_json(url, params):  # noqa: ARG001
        return 200, {
            "items": ["bad", {"id": "x", "title": "Good"}],
            "count": 2,
            "offset": 0,
            "limit": 1,
            "total_count": 2,
        }

    monkeypatch.setattr(ons_search._SEARCH_CLIENT, "get_json", fake_get_json)
    status, data = ons_search._live_search("gdp", 1, 0)
    assert status == 200
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "x"
