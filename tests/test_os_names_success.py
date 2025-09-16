from fastapi.testclient import TestClient
from server.main import app

def test_os_names_nearest_success(monkeypatch):
    from tools import os_names
    def fake_get_json(url, params):
        return 200, {
            "results": [
                {"GAZETTEER_ENTRY": {"ID": "1", "NAME1": "Foo", "TYPE": "T", "DISTANCE": 12.3}},
                {"GAZETTEER_ENTRY": {"ID": "2", "NAME1": "Bar", "TYPE": "U", "DISTANCE": 4.5}},
            ]
        }
    monkeypatch.setattr(os_names, "client", type("C", (), {"get_json": staticmethod(fake_get_json), "base_names": "http://example"})())
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_names.nearest", "lat": 51.5, "lon": -0.1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    ids = {r["id"] for r in data["results"]}
    assert ids == {"1", "2"}
