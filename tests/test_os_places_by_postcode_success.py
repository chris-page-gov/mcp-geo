import tools.os_places as os_places
from fastapi.testclient import TestClient

from server.main import app


def test_os_places_by_postcode_success(monkeypatch):
    fake_raw = {
        "results": [
            {"DPA": {
                "UPRN": "100",
                "ADDRESS": "10 High St",
                "LAT": 51.0,
                "LNG": -0.1,
                "CLASS": "R",
                "LOCAL_CUSTODIAN_CODE": 123,
            }},
            {"DPA": {
                "UPRN": "101",
                "ADDRESS": "11 High St",
                "LAT": 52.0,
                "LNG": -0.2,
                "CLASS": "C",
                "LOCAL_CUSTODIAN_CODE": 456,
            }},
        ],
        "epoch": 1234567890,
    }

    captured = {}
    def fake_get_json(url, params=None):  # noqa: ARG001
        captured.update(params or {})
        return 200, fake_raw

    monkeypatch.setattr(os_places.client, "get_json", fake_get_json)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A1AA"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uprns"]) == 2
    assert {d["uprn"] for d in data["uprns"]} == {"100", "101"}
    assert captured["output_srs"] == "WGS84"


def test_os_places_by_postcode_skips_invalid(monkeypatch):
    fake_raw = {
        "results": [
            "not-a-dict",
            {"DPA": "not-a-dict"},
            {"DPA": {"UPRN": "102", "ADDRESS": "12 High St", "LAT": "bad", "LNG": "bad"}},
        ]
    }

    def fake_get_json(url, params=None):  # noqa: ARG001
        return 200, fake_raw

    monkeypatch.setattr(os_places.client, "get_json", fake_get_json)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A1AA"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uprns"]) == 1
    assert data["uprns"][0]["lat"] == 0.0
    assert data["uprns"][0]["lon"] == 0.0


def test_os_places_by_postcode_empty_results_returns_invalid_input(monkeypatch):
    def fake_get_json(url, params=None):  # noqa: ARG001
        return 200, {"results": []}

    monkeypatch.setattr(os_places.client, "get_json", fake_get_json)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "ZZ99ZZ"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["isError"] is True
    assert body["code"] == "INVALID_INPUT"
