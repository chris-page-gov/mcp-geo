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
    assert captured["params"]["dataset"] == "DPA,LPI"
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
    assert captured["params"]["dataset"] == "DPA,LPI"
    assert captured["params"]["point"] == "51.5,-0.1"
    assert captured["params"]["radius"] == 500
    assert "maxresults" not in captured["params"]


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
    assert captured["params"]["dataset"] == "DPA,LPI"
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


def test_os_poi_helper_parsers_and_normalization_edges():
    from tools import os_poi

    assert os_poi._parse_limit(None) == os_poi.DEFAULT_LIMIT
    assert os_poi._parse_limit("bad") is None
    assert os_poi._parse_limit(0) is None
    assert os_poi._parse_limit(os_poi.MAX_LIMIT + 1) is None

    assert os_poi._parse_bbox("bad") is None
    assert os_poi._parse_bbox([1, 2, 3]) is None
    assert os_poi._parse_bbox([1, "x", 3, 4]) is None
    assert os_poi._parse_bbox([1, 2, 1, 4]) is None
    assert os_poi._parse_bbox([1, 4, 3, 4]) is None

    assert os_poi._float_or_none("bad") is None
    assert os_poi._text_or_none(None) is None
    assert os_poi._text_or_none("   ") is None

    assert os_poi._extract_source_entry("bad") is None
    assert os_poi._extract_source_entry({"POI": {"NAME": "x"}}) == {"NAME": "x"}
    assert os_poi._extract_source_entry({"DPA": {"NAME1": "x"}}) == {"NAME1": "x"}

    normalized = os_poi._normalize_results(
        {
            "results": [
                "skip-non-dict",
                {"POI": "skip-non-dict-entry"},
                {
                    "POI": {
                        "ORGANISATION_NAME": "Org Cafe",
                        "CLASS_DESCRIPTION": "Cafe",
                        "DESCRIPTION": "1 High Street",
                        "LAT": "51.5",
                        "LNG": "-0.12",
                        "UPRN": "u-1",
                    },
                    "DISTANCE": "123.4",
                },
                {
                    "NAME1": "Fallback Name",
                    "CLASSIFICATION_CODE": "R",
                    "ADDRESS": "2 High Street",
                    "LAT": 51.6,
                    "LNG": -0.13,
                    "ID": "id-2",
                    "DISTANCE": "not-a-number",
                },
            ]
        }
    )
    assert len(normalized) == 3
    assert normalized[0]["name"] is None
    assert normalized[1]["name"] == "Org Cafe"
    assert normalized[1]["distanceMeters"] == 123.4
    assert normalized[2]["name"] == "Fallback Name"
    assert "distanceMeters" not in normalized[2]
    assert os_poi._normalize_results({"results": "bad"}) == []


def test_os_poi_handlers_cover_error_and_bbox_paths(monkeypatch):
    from tools import os_poi

    assert os_poi._search({"text": ""})[0] == 400
    assert os_poi._search({"text": "x", "limit": "bad"})[0] == 400
    assert os_poi._search({"text": "x", "bbox": [1, 2, 1, 3]})[0] == 400

    captured: dict = {}

    def ok_get_json(url, params):
        captured["url"] = url
        captured["params"] = dict(params)
        return 200, {"results": []}

    ok_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(ok_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", ok_client)
    status, payload = os_poi._search({"text": "cafe", "bbox": [-0.2, 51.4, -0.1, 51.5], "limit": 2})
    assert status == 200
    assert payload["count"] == 0
    assert captured["url"].endswith("/find")
    assert captured["params"]["bbox"] == "51.4,-0.2,51.5,-0.1"
    assert captured["params"]["srs"] == "WGS84"

    assert os_poi._nearest({"lat": "bad", "lon": -0.1})[0] == 400
    assert os_poi._nearest({"lat": 51.5, "lon": -0.1, "limit": 0})[0] == 400
    assert os_poi._nearest({"lat": 51.5, "lon": -0.1, "maxDistanceMeters": "bad"})[0] == 400

    def failing_get_json(_url, _params):
        return 429, {"isError": True, "code": "UPSTREAM_RATE_LIMIT"}

    fail_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(failing_get_json),
            "base_places": "http://example/places/v1",
        },
    )()
    monkeypatch.setattr(os_poi, "client", fail_client)
    nearest_status, nearest_payload = os_poi._nearest({"lat": 51.5, "lon": -0.1, "limit": 5})
    assert nearest_status == 501
    assert nearest_payload["code"] == "UPSTREAM_RATE_LIMIT"

    assert os_poi._within({"bbox": "bad"})[0] == 400
    assert os_poi._within({"bbox": [-0.2, 51.4, -0.1, 51.6], "limit": 0})[0] == 400
    within_status, within_payload = os_poi._within({"bbox": [-0.2, 51.4, -0.1, 51.6], "limit": 5})
    assert within_status == 501
    assert within_payload["code"] == "UPSTREAM_RATE_LIMIT"
