import requests
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)

def test_postcode_timeout(monkeypatch: MonkeyPatch):
    def fake_get(url: str, timeout: int = 5):
        raise requests.exceptions.ReadTimeout("rt")
    monkeypatch.setattr(requests, "get", fake_get)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"},
    )
    # Expect upstream OS API error mapping (configured as OS_API_ERROR or INTEGRATION
    # depending on code) - here using generic timeout classification
    assert resp.status_code in (500, 501)
    data = resp.json()
    assert data["isError"] is True
