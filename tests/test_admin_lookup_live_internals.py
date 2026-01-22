from typing import Any

from tools import admin_lookup


class DummyResp:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


def _patch_admin_sources(monkeypatch):
    source = admin_lookup.AdminSource(
        level="TEST",
        service="ExampleService",
        id_field="TEST_ID",
        name_field="TEST_NAME",
        lat_field="LAT",
        lon_field="LON",
    )
    monkeypatch.setattr(admin_lookup, "ADMIN_SOURCES", [source])
    monkeypatch.setattr(admin_lookup, "LEVEL_ORDER", [source.level])
    monkeypatch.setattr(admin_lookup, "LEVEL_INDEX", {source.level: 0})
    return source


def test_arcgis_client_caches_success(monkeypatch):
    client = admin_lookup._ArcGisClient()
    calls = {"count": 0}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        return DummyResp(200, {"features": []})

    monkeypatch.setattr(admin_lookup.requests, "get", fake_get)
    status1, data1 = client.get_json("http://example", {"q": "x"})
    status2, data2 = client.get_json("http://example", {"q": "x"})
    assert status1 == 200 and data1 == {"features": []}
    assert status2 == 200 and data2 == {"features": []}
    assert calls["count"] == 1


def test_arcgis_client_retries_on_timeout(monkeypatch):
    client = admin_lookup._ArcGisClient()
    calls = {"count": 0}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] == 1:
            raise admin_lookup.req_exc.Timeout("boom")
        return DummyResp(200, {"features": []})

    monkeypatch.setattr(admin_lookup.requests, "get", fake_get)
    status, data = client.get_json("http://example", {"q": "y"})
    assert status == 200
    assert data == {"features": []}
    assert calls["count"] == 2


def test_live_find_by_name_builds_results(monkeypatch):
    _patch_admin_sources(monkeypatch)
    captured = {}

    def fake_fetch(url, params):
        captured["where"] = params.get("where")
        return {
            "features": [
                {"attributes": {"TEST_ID": "X1", "TEST_NAME": "Example Name"}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_find_by_name("Example", limit=5)
    assert results == [{"id": "X1", "level": "TEST", "name": "Example Name"}]
    assert "UPPER(TEST_NAME) LIKE '%EXAMPLE%'" in captured["where"]


def test_live_containing_areas_builds_chain(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):
        assert params["geometry"] == "-0.1,51.5"
        return {
            "features": [
                {"attributes": {"TEST_ID": "X2", "TEST_NAME": "Example Area"}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_containing_areas(51.5, -0.1)
    assert results == [{"id": "X2", "level": "TEST", "name": "Example Area"}]


def test_live_area_geometry_returns_bbox(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return {"extent": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3}}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    bbox, meta = admin_lookup._live_area_geometry("X3")
    assert bbox == [0.0, 1.0, 2.0, 3.0]
    assert meta == {"level": "TEST", "source": "arcgis"}


def test_live_find_by_id_returns_match(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return {
            "features": [
                {"attributes": {"TEST_ID": "X4", "TEST_NAME": "Example", "LAT": 10, "LON": -1}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    hit, err = admin_lookup._live_find_by_id("X4")
    assert err is None
    assert hit == {"id": "X4", "level": "TEST", "name": "Example", "lat": 10, "lon": -1}
