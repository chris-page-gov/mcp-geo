import tools.os_places as os_places
from fastapi.testclient import TestClient

from server.main import app


def test_os_places_enrichment(monkeypatch):
    fake_raw = {
        "results": [
            {"DPA": {
                "UPRN": "100",
                "ADDRESS": "10 High St",
                "LAT": 51.0,
                "LNG": -0.1,
                "CLASS": "RD",
                "LOCAL_CUSTODIAN_CODE": 5990,
            }},
            {"DPA": {
                "UPRN": "101",
                "ADDRESS": "11 High St",
                "LAT": 52.0,
                "LNG": -0.2,
                "CLASS": "CM",
                "LOCAL_CUSTODIAN_CODE": 1705,
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
    codes = {d["classification"] for d in data["uprns"]}
    assert codes == {"RD", "CM"}
    desc_map = {d["classification"]: d.get("classificationDescription") for d in data["uprns"]}
    assert desc_map["RD"] is None
    assert desc_map["CM"] is None
    names = {d.get("localCustodianName") for d in data["uprns"]}
    assert names == {None}
