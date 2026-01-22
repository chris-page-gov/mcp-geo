from fastapi.testclient import TestClient

from server.config import settings
from server.main import app
from tools import admin_lookup


def test_admin_lookup_find_by_name_live(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    captured = {}

    def fake_live(text: str, limit: int):
        captured["text"] = text
        captured["limit"] = limit
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
