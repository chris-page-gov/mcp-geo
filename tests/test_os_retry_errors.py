import requests
from fastapi.testclient import TestClient
from server.main import app
from server.config import settings

client = TestClient(app)

class Boom(Exception):
    pass

class FakeSSLError(requests.exceptions.SSLError):
    pass


def test_postcode_tls_error(monkeypatch):
    try:
        settings.OS_API_KEY = "dummy"  # type: ignore
    except Exception:
        pass
    def fake_get(url, timeout=5):
        raise FakeSSLError("TLS fail")
    monkeypatch.setattr(requests, "get", fake_get)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"})
    assert resp.status_code == 501
    assert resp.json()["code"] == "UPSTREAM_TLS_ERROR"


def test_postcode_connect_retry_exhaust(monkeypatch):
    calls = {"n": 0}
    def fake_get(url, timeout=5):
        calls["n"] += 1
        raise requests.exceptions.ConnectionError("boom")
    monkeypatch.setattr(requests, "get", fake_get)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"})
    assert resp.status_code == 501
    body = resp.json()
    assert body["code"] == "UPSTREAM_CONNECT_ERROR"
    assert calls["n"] == 3  # retried 3 times
