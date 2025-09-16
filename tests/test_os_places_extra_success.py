from fastapi.testclient import TestClient
from server.main import app

def test_os_places_search_success(monkeypatch):
    from tools import os_places_extra
    def fake_get_json(url, params):
        return 200, {
            "results": [
                {"DPA": {"UPRN": "1", "ADDRESS": "A St", "LAT": 51.0, "LNG": -0.1, "CLASS": "R"}},
                {"DPA": {"UPRN": "2", "ADDRESS": "B St", "LAT": 52.0, "LNG": -0.2, "CLASS": "C"}},
            ]
        }
    monkeypatch.setattr(os_places_extra, "client", type("C", (), {"get_json": staticmethod(fake_get_json), "base_places": "http://example"})())
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.search", "text": "foo"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["results"]) == 2
