from fastapi.testclient import TestClient
from server.main import app

def _fake_body(uprn: str):
    return {"results": [{"DPA": {"UPRN": uprn, "ADDRESS": f"Addr {uprn}", "LAT": 50.0, "LNG": -1.0, "CLASS": "R"}}]}

def test_os_places_by_uprn_success(monkeypatch):
    from tools import os_places_extra
    def fake_get_json(url, params):
        return 200, _fake_body(params["uprn"])  # echo uprn
    monkeypatch.setattr(os_places_extra, "client", type("C", (), {"get_json": staticmethod(fake_get_json), "base_places": "http://example"})())
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_uprn", "uprn": "12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["uprn"] == "12345"

def test_os_places_nearest_success(monkeypatch):
    from tools import os_places_extra
    def fake_get_json(url, params):
        return 200, _fake_body("N1")
    monkeypatch.setattr(os_places_extra, "client", type("C", (), {"get_json": staticmethod(fake_get_json), "base_places": "http://example"})())
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.nearest", "lat": 51.0, "lon": -0.1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "N1"

def test_os_places_within_success(monkeypatch):
    from tools import os_places_extra
    def fake_get_json(url, params):
        return 200, _fake_body("W1")
    monkeypatch.setattr(os_places_extra, "client", type("C", (), {"get_json": staticmethod(fake_get_json), "base_places": "http://example"})())
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.within", "bbox": [-1.2, 50.1, -1.0, 50.2]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "W1"
