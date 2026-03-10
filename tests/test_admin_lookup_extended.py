import pytest
from fastapi.testclient import TestClient
from server.boundary_cache import reset_boundary_cache
from server.config import settings
from server.main import app


@pytest.fixture(autouse=True)
def _enable_admin_lookup_live(monkeypatch):
    from tools import admin_lookup

    def fake_arcgis_get_json(url: str, params):  # noqa: ARG001
        if params.get("returnExtentOnly") == "true":
            where = str(params.get("where", ""))
            if "NOPE" in where:
                return 200, {}
            return 200, {"extent": {"xmin": -0.2, "ymin": 51.4, "xmax": -0.1, "ymax": 51.6}}
        where = params.get("where", "")
        if "UNKNOWN" in str(where) or "NOPEVILLE" in str(where):
            return 200, {"features": []}
        attrs = {}
        for source in admin_lookup.ADMIN_SOURCES:
            attrs[source.id_field] = f"{source.level}_ID"
            attrs[source.name_field] = f"{source.level} Name"
            if source.lat_field:
                attrs[source.lat_field] = 51.5
            if source.lon_field:
                attrs[source.lon_field] = -0.12
        return 200, {"features": [{"attributes": attrs}]}

    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_DSN", "", raising=False)
    reset_boundary_cache()
    monkeypatch.setattr(admin_lookup._ARCGIS_CLIENT, "get_json", fake_arcgis_get_json)


def _client():
    return TestClient(app)


def test_admin_reverse_hierarchy_success():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.reverse_hierarchy", "id": "E00023939"})
    assert resp.status_code == 200
    chain = resp.json()["chain"]
    assert chain


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
    assert results

def test_admin_find_by_name_no_match_hints():
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.find_by_name", "text": "Nopeville"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["count"] == 0
