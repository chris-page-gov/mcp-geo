import pytest
from fastapi.testclient import TestClient
from server.config import settings
from server.main import app


@pytest.fixture(autouse=True)
def _enable_admin_lookup_live(monkeypatch):
    from tools import admin_lookup

    def fake_arcgis_get_json(url: str, params):  # noqa: ARG001
        attrs = {}
        for source in admin_lookup.ADMIN_SOURCES:
            attrs[source.id_field] = f"{source.level}_ID"
            attrs[source.name_field] = f"{source.level} Name"
        return 200, {"features": [{"attributes": attrs}]}

    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(admin_lookup._ARCGIS_CLIENT, "get_json", fake_arcgis_get_json)

def test_admin_lookup_success():
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "admin_lookup.containing_areas",
            "lat": 51.5005,
            "lon": -0.1390,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"]


def test_admin_lookup_invalid_input():
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "admin_lookup.containing_areas",
            "lat": "abc",
            "lon": 1,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_admin_lookup_no_match(monkeypatch):
    from tools import admin_lookup

    def empty_arcgis_get_json(url: str, params):  # noqa: ARG001
        return 200, {"features": []}

    monkeypatch.setattr(admin_lookup._ARCGIS_CLIENT, "get_json", empty_arcgis_get_json)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "admin_lookup.containing_areas",
            "lat": 60.0,
            "lon": -3.0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []
