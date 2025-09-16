from fastapi.testclient import TestClient
from server.main import app
import importlib
import tools.os_places as os_places
from server.config import settings

class DummyResp:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self._json = {
            "results": [
                {"DPA": {"UPRN": "100", "ADDRESS": "10 High St", "LAT": 51.0, "LNG": -0.1, "CLASS": "R", "LOCAL_CUSTODIAN_CODE": 123}},
                {"DPA": {"UPRN": "101", "ADDRESS": "11 High St", "LAT": 52.0, "LNG": -0.2, "CLASS": "C", "LOCAL_CUSTODIAN_CODE": 456}},
            ],
            "epoch": 1234567890,
        }
        self.text = "OK"
    def json(self):
        return self._json

def test_os_places_by_postcode_success(monkeypatch):
    def fake_get(url, timeout):  # noqa: ARG001 - signature shape only
        return DummyResp()
    # Ensure settings reflects an API key at runtime
    monkeypatch.setattr(settings, "OS_API_KEY", "dummy", raising=False)
    # Reload modules so any module-level client picks up updated settings
    import tools.os_common as os_common
    importlib.reload(os_common)  # refresh client
    importlib.reload(os_places)
    monkeypatch.setattr(os_places.requests, "get", fake_get)
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A1AA"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uprns"]) == 2
    assert {d["uprn"] for d in data["uprns"]} == {"100", "101"}
