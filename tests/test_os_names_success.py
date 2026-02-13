from fastapi.testclient import TestClient
from server.main import app

def test_os_names_nearest_success(monkeypatch):
    from tools import os_names
    captured = {}
    def fake_get_json(url, params):
        captured.update(params)
        return 200, {
            "results": [
                {
                    "GAZETTEER_ENTRY": {
                        "ID": "1",
                        "NAME1": "Foo",
                        "TYPE": "T",
                        "DISTANCE": 12.3,
                    }
                },
                {
                    "GAZETTEER_ENTRY": {
                        "ID": "2",
                        "NAME1": "Bar",
                        "TYPE": "U",
                        "DISTANCE": 4.5,
                    }
                },
            ]
        }
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_names.nearest", "lat": 51.5, "lon": -0.1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    ids = {r["id"] for r in data["results"]}
    assert ids == {"1", "2"}
    assert "output_srs" not in captured


def test_os_names_find_requests_wgs84(monkeypatch):
    from tools import os_names
    captured = {}
    def fake_get_json(url, params):
        captured.update(params)
        return 200, {"results": []}
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_names.find", "text": "London"})
    assert resp.status_code == 200
    assert "output_srs" not in captured
    assert captured["maxresults"] == 25


def test_os_names_find_respects_limit(monkeypatch):
    from tools import os_names

    captured = {}

    def fake_get_json(url, params):
        captured.update(params)
        return 200, {"results": []}

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_names.find", "text": "London", "limit": 40})
    assert resp.status_code == 200
    assert captured["maxresults"] == 40


def test_os_names_nearest_bng_coords(monkeypatch):
    from tools import os_names
    captured = {}

    def fake_get_json(url, params):
        captured.update(params)
        return 200, {"results": []}

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_names.nearest", "lat": 530000, "lon": 180000, "coordSystem": "EPSG:27700"},
    )
    assert resp.status_code == 200
    assert captured["point"] == "180000.00,530000.00"


def test_os_names_nearest_invalid_coord_system(monkeypatch):
    from tools import os_names

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(lambda url, params: (200, {"results": []})),  # noqa: ARG005
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_names.nearest", "lat": 51.5, "lon": -0.1, "coordSystem": "EPSG:9999"},
    )
    assert resp.status_code == 400


def test_os_names_extract_lat_lon_variants():
    from tools import os_names

    lat, lon = os_names._extract_lat_lon({"LAT": "51.5", "LNG": "-0.1"})
    assert lat == 51.5
    assert lon == -0.1
    lat, lon = os_names._extract_lat_lon({"X": -0.1, "Y": 51.5})
    assert lat == 51.5
    assert lon == -0.1
    lat, lon = os_names._extract_lat_lon([-0.1, 51.5])
    assert lat == 51.5
    assert lon == -0.1


def test_os_names_nearest_missing_pyproj(monkeypatch):
    from tools import os_names

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(lambda url, params: (200, {"results": []})),  # noqa: ARG005
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    monkeypatch.setattr(os_names, "Transformer", None)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_names.nearest", "lat": 51.5, "lon": -0.1},
    )
    assert resp.status_code == 501
    assert resp.json()["code"] == "MISSING_DEPENDENCY"


def test_os_names_find_upstream_error(monkeypatch):
    from tools import os_names

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(lambda url, params: (500, {"isError": True})),  # noqa: ARG005
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_names.find", "text": "London"})
    assert resp.status_code == 501


def test_os_names_normalize_coord_system():
    from tools import os_names

    assert os_names._normalize_coord_system("WGS84") == "EPSG:4326"


def test_os_names_wgs84_transform_error(monkeypatch):
    from tools import os_names

    class BadTransformer:
        def transform(self, lon, lat):  # noqa: ARG002
            raise RuntimeError("boom")

    monkeypatch.setattr(os_names, "_BNG_TRANSFORMER", BadTransformer())
    monkeypatch.setattr(os_names, "Transformer", object())
    assert os_names._wgs84_to_bng(51.5, -0.1) is None


def test_os_names_nearest_upstream_error(monkeypatch):
    from tools import os_names

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(lambda url, params: (500, {"isError": True})),  # noqa: ARG005
            "base_names": "http://example",
        },
    )()
    monkeypatch.setattr(os_names, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_names.nearest", "lat": 530000, "lon": 180000, "coordSystem": "EPSG:27700"},
    )
    assert resp.status_code == 501
