from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def _fake_poi_payload() -> dict:
    return {
        "results": [
            {
                "POI": {
                    "ID": "poi-1",
                    "NAME": "Cafe Example",
                    "CLASSIFICATION": "cafe",
                    "ADDRESS": "1 High Street",
                    "LAT": 51.501,
                    "LNG": -0.141,
                },
                "DISTANCE": 120,
            }
        ]
    }


def test_os_poi_search_success(monkeypatch):
    from tools import os_poi

    captured: dict = {}

    def fake_get_json(url, params):
        captured["url"] = url
        captured["params"] = dict(params)
        return 200, _fake_poi_payload()

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", fake_client)

    resp = client.post("/tools/call", json={"tool": "os_poi.search", "text": "cafe", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["name"] == "Cafe Example"
    assert captured["url"].endswith("/find")
    assert captured["params"]["dataset"] == "POI"
    assert captured["params"]["maxresults"] == 5
    assert captured["params"]["output_srs"] == "WGS84"


def test_os_poi_nearest_success(monkeypatch):
    from tools import os_poi

    captured: dict = {}

    def fake_get_json(url, params):
        captured["url"] = url
        captured["params"] = dict(params)
        return 200, _fake_poi_payload()

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", fake_client)

    resp = client.post(
        "/tools/call",
        json={"tool": "os_poi.nearest", "lat": 51.5, "lon": -0.1, "maxDistanceMeters": 500},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert captured["url"].endswith("/nearest")
    assert captured["params"]["dataset"] == "POI"
    assert captured["params"]["point"] == "51.5,-0.1"
    assert captured["params"]["radius"] == 500


def test_os_poi_within_success(monkeypatch):
    from tools import os_poi

    captured: dict = {}

    def fake_get_json(url, params):
        captured["url"] = url
        captured["params"] = dict(params)
        return 200, _fake_poi_payload()

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", fake_client)

    resp = client.post(
        "/tools/call",
        json={"tool": "os_poi.within", "bbox": [-0.2, 51.4, -0.1, 51.6], "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert captured["url"].endswith("/bbox")
    assert captured["params"]["dataset"] == "POI"
    assert captured["params"]["bbox"] == "51.4,-0.2,51.6,-0.1"


def test_os_poi_entitlement_error_passthrough(monkeypatch):
    from tools import os_poi

    def fake_get_json(_url, _params):
        return 501, {"isError": True, "code": "NO_API_KEY", "message": "OS API key missing."}

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", fake_client)

    resp = client.post("/tools/call", json={"tool": "os_poi.search", "text": "cafe"})
    assert resp.status_code == 501
    body = resp.json()
    assert body["code"] == "NO_API_KEY"


def test_os_poi_validation_errors():
    bad_search = client.post("/tools/call", json={"tool": "os_poi.search", "text": "", "limit": 500})
    assert bad_search.status_code == 400

    bad_nearest = client.post("/tools/call", json={"tool": "os_poi.nearest", "lat": "a", "lon": "b"})
    assert bad_nearest.status_code == 400

    bad_within = client.post("/tools/call", json={"tool": "os_poi.within", "bbox": [1, 2, 3]})
    assert bad_within.status_code == 400
