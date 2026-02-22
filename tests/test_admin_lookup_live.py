from fastapi.testclient import TestClient

from server.config import settings
from server.main import app
from tools import admin_lookup


def test_admin_lookup_find_by_name_live(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    captured = {}

    def fake_live(
        text: str,
        limit: int,
        *,
        levels: list[str] | None = None,
        match: str | None = None,
        limit_per_level: int | None = None,
    ):
        captured["text"] = text
        captured["limit"] = limit
        captured["levels"] = levels
        captured["match"] = match
        captured["limit_per_level"] = limit_per_level
        return [{"id": "E00000001", "level": "WARD", "name": "Example Ward"}]

    monkeypatch.setattr(admin_lookup, "_live_find_by_name", fake_live)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "admin_lookup.find_by_name", "text": "Example", "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["count"] == 1
    assert body["results"][0]["id"] == "E00000001"
    assert captured["text"] == "Example"
    assert captured["limit"] == 5
    assert captured["levels"] is None
    assert captured["match"] == "contains"
    assert captured["limit_per_level"] is None


def test_admin_lookup_find_by_name_include_geometry_passthrough(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    captured = {}

    def fake_live(
        text: str,
        limit: int,
        *,
        levels: list[str] | None = None,
        match: str | None = None,
        limit_per_level: int | None = None,
        include_geometry: bool = False,
    ):
        captured["text"] = text
        captured["include_geometry"] = include_geometry
        return [{"id": "E00000001", "level": "WARD", "name": "Example Ward", "bbox": [0, 0, 1, 1]}]

    monkeypatch.setattr(admin_lookup, "_live_find_by_name", fake_live)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "admin_lookup.find_by_name",
            "text": "Example",
            "limit": 5,
            "includeGeometry": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert captured["text"] == "Example"
    assert captured["include_geometry"] is True
    assert body["meta"]["includeGeometry"] is True


def test_admin_lookup_find_by_name_validation(monkeypatch):
    from server.config import settings
    from tools import admin_lookup

    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    client = TestClient(app)

    resp = client.post("/tools/call", json={"tool": "admin_lookup.find_by_name", "text": ""})
    assert resp.status_code == 400

    resp = client.post(
        "/tools/call",
        json={"tool": "admin_lookup.find_by_name", "text": "Test", "limit": 0},
    )
    assert resp.status_code == 400

    resp = client.post(
        "/tools/call",
        json={"tool": "admin_lookup.find_by_name", "text": "Test", "match": 123},
    )
    assert resp.status_code == 400

    resp = client.post(
        "/tools/call",
        json={"tool": "admin_lookup.find_by_name", "text": "Test", "limitPerLevel": 0},
    )
    assert resp.status_code == 400


def test_admin_lookup_find_by_name_live_disabled(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", False, raising=False)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "admin_lookup.find_by_name", "text": "Test"})
    assert resp.status_code == 501
