from fastapi.testclient import TestClient
from server.main import app
from server.config import settings
import importlib
import tools.os_places as os_places

class DummyResp:
    def __init__(self):
        self.status_code = 200
        self._json = {
            "results": [
                {"DPA": {"UPRN": "100", "ADDRESS": "10 High St", "LAT": 51.0, "LNG": -0.1, "CLASS": "RD", "LOCAL_CUSTODIAN_CODE": 5990}},
                {"DPA": {"UPRN": "101", "ADDRESS": "11 High St", "LAT": 52.0, "LNG": -0.2, "CLASS": "CM", "LOCAL_CUSTODIAN_CODE": 1705}},
            ],
            "epoch": 1234567890,
        }
        self.text = "OK"
    def json(self):
        return self._json


def test_os_places_enrichment(monkeypatch):
    monkeypatch.setattr(settings, "OS_API_KEY", "dummy", raising=False)
    import tools.os_common as os_common
    importlib.reload(os_common)
    importlib.reload(os_places)

    def fake_get(url, timeout):  # noqa: ARG001
        return DummyResp()

    monkeypatch.setattr(os_places.requests, "get", fake_get)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A1AA"})
    assert resp.status_code == 200
    data = resp.json()
    codes = {d["classification"] for d in data["uprns"]}
    assert codes == {"RD", "CM"}
    desc_map = {d["classification"]: d.get("classificationDescription") for d in data["uprns"]}
    assert desc_map["RD"].lower().startswith("residential")
    assert desc_map["CM"].lower().startswith("commercial")
    names = {d.get("localCustodianName") for d in data["uprns"]}
    assert "Westminster City Council" in names
    assert "Coventry City Council" in names
