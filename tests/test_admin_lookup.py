from fastapi.testclient import TestClient
from server.main import app

def test_admin_lookup_success():
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "admin_lookup.containing_areas", "lat": 51.5005, "lon": -0.1390})
    assert resp.status_code == 200
    data = resp.json()
    # Expect at least OA upward chain present (using realistic codes)
    ids = [r["id"] for r in data["results"]]
    assert "E00023939" in ids and "E92000001" in ids


def test_admin_lookup_invalid_input():
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "admin_lookup.containing_areas", "lat": "abc", "lon": 1})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_admin_lookup_no_match():
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "admin_lookup.containing_areas", "lat": 60.0, "lon": -3.0})
    assert resp.status_code == 200
    assert resp.json()["results"] == []
