from fastapi.testclient import TestClient
from server.main import app


def _client():
    return TestClient(app)


def test_admin_reverse_hierarchy_success():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.reverse_hierarchy", "id": "E00023939"})
    assert resp.status_code == 200
    chain = resp.json()["chain"]
    assert chain[0]["id"] == "E00023939"
    assert any(x["id"] == "E92000001" for x in chain)


def test_admin_reverse_hierarchy_not_found():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.reverse_hierarchy", "id": "UNKNOWN"})
    assert resp.status_code == 404


def test_admin_area_geometry_success():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.area_geometry", "id": "E05000644"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "E05000644"
    assert len(body["bbox"]) == 4


def test_admin_area_geometry_not_found():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.area_geometry", "id": "NOPE"})
    assert resp.status_code == 404


def test_admin_find_by_name_success():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.find_by_name", "text": "Westminster"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any(r["id"] == "E09000033" for r in results)


def test_resource_get_admin_boundaries():
    c = _client()
    resp = c.get("/resources/get", params={"name": "admin_boundaries"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "admin_boundaries"
    assert data["count"] > 0