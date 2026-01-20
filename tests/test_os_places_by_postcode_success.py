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

    def fake_get_json(url, params=None):  # noqa: ARG001
        return 200, fake_raw

    monkeypatch.setattr(os_places.client, "get_json", fake_get_json)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A1AA"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uprns"]) == 2
    assert {d["uprn"] for d in data["uprns"]} == {"100", "101"}
