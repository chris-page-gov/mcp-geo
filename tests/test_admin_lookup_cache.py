from types import SimpleNamespace

from fastapi.testclient import TestClient

from server.main import app


def _client():
    return TestClient(app)


def test_admin_lookup_area_geometry_uses_cache(monkeypatch):
    from tools import admin_lookup

    stub = SimpleNamespace(
        bbox=[-0.2, 51.4, -0.1, 51.6],
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [-0.2, 51.4],
                    [-0.1, 51.4],
                    [-0.1, 51.6],
                    [-0.2, 51.6],
                    [-0.2, 51.4],
                ]
            ],
        },
        meta={"source": "cache"},
        name="Test Ward",
        level="WARD",
    )

    class StubCache:
        def area_geometry(self, area_id, *, include_geometry, zoom=None):  # noqa: ARG002
            return stub

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: StubCache())
    monkeypatch.setattr(admin_lookup, "_live_enabled", lambda: False)

    c = _client()
    resp = c.post(
        "/tools/call",
        json={"tool": "admin_lookup.area_geometry", "id": "E00000001", "includeGeometry": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is False
    assert body["meta"]["source"] == "cache"
    assert body["geometry"]["type"] == "Polygon"


def test_admin_lookup_containing_areas_uses_cache(monkeypatch):
    from tools import admin_lookup

    class StubCache:
        def containing_areas(self, lat, lon):  # noqa: ARG002
            return [{"id": "E00000001", "level": "WARD", "name": "Test Ward"}]

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: StubCache())
    monkeypatch.setattr(admin_lookup, "_live_enabled", lambda: False)

    c = _client()
    resp = c.post(
        "/tools/call",
        json={"tool": "admin_lookup.containing_areas", "lat": 51.5, "lon": -0.1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is False
    assert body["results"]


def test_admin_lookup_cache_status(monkeypatch):
    from tools import admin_lookup

    class StubCache:
        def status(self):
            return {
                "enabled": True,
                "total": 10,
                "geomCount": 10,
                "maturity": {"state": "ready"},
                "staleness": {"staleDatasetIds": [], "freshDatasetIds": []},
            }

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: StubCache())
    c = _client()
    resp = c.post("/tools/call", json={"tool": "admin_lookup.get_cache_status"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert body["total"] == 10
    assert body["maturity"]["state"] == "ready"
    assert body["performance"]["degraded"] is False


def test_admin_lookup_cache_search(monkeypatch):
    from tools import admin_lookup

    class StubCache:
        def search(self, *, query=None, level=None, limit=25, include_geometry=False):  # noqa: ARG002
            return [{"id": "E00000001", "name": "Test", "level": "OA", "bbox": [0, 0, 1, 1]}]

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: StubCache())
    c = _client()
    resp = c.post(
        "/tools/call",
        json={"tool": "admin_lookup.search_cache", "query": "Test", "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1


def test_admin_lookup_cache_search_fallback_live_when_disabled(monkeypatch):
    from tools import admin_lookup

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: None)
    monkeypatch.setattr(admin_lookup, "_live_enabled", lambda: True)
    monkeypatch.setattr(
        admin_lookup,
        "_live_find_by_name",
        lambda query, limit, **kwargs: [  # noqa: ARG005
            {"id": "E00000001", "name": "Example Ward", "level": "WARD"}
        ],
    )
    c = _client()
    resp = c.post(
        "/tools/call",
        json={"tool": "admin_lookup.search_cache", "query": "Example", "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["meta"]["fallback"] is True
    assert body["meta"]["fallbackReason"] == "cache_disabled"
    assert body["meta"]["cache"] == "disabled"
    assert body["meta"]["cacheMaturity"]["state"] == "disabled"


def test_admin_lookup_cache_search_fallback_live_when_error(monkeypatch):
    from tools import admin_lookup

    class StubCache:
        def search(self, *, query=None, level=None, limit=25, include_geometry=False):  # noqa: ARG002
            return None

    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: StubCache())
    monkeypatch.setattr(admin_lookup, "_live_enabled", lambda: True)
    monkeypatch.setattr(
        admin_lookup,
        "_live_find_by_name",
        lambda query, limit, **kwargs: [  # noqa: ARG005
            {"id": "E00000002", "name": "Example District", "level": "DISTRICT"}
        ],
    )
    c = _client()
    resp = c.post(
        "/tools/call",
        json={"tool": "admin_lookup.search_cache", "query": "Example", "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["meta"]["fallback"] is True
    assert body["meta"]["fallbackReason"] == "cache_error"
    assert body["meta"]["cacheError"] is True
