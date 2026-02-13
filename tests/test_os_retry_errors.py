import requests
import tools.os_common as os_common
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


class FakeSSLError(requests.exceptions.SSLError):
    pass


def test_postcode_tls_error(monkeypatch: MonkeyPatch):
    # Ensure the shared OS client takes the "key present" path.
    os_common.client.api_key = "dummy"

    def fake_get(url: str, params=None, timeout: int = 5):  # noqa: ARG001
        raise FakeSSLError("TLS fail")

    monkeypatch.setattr(os_common.requests, "get", fake_get)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"})
    assert resp.status_code == 501
    assert resp.json()["code"] == "UPSTREAM_TLS_ERROR"


def test_postcode_connect_retry_exhaust(monkeypatch: MonkeyPatch):
    os_common.client.api_key = "dummy"
    calls = {"n": 0}

    def fake_get(url: str, params=None, timeout: int = 5):  # noqa: ARG001
        calls["n"] += 1
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(os_common.requests, "get", fake_get)
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"})
    assert resp.status_code == 501
    body = resp.json()
    assert body["code"] == "UPSTREAM_CONNECT_ERROR"
    assert calls["n"] == os_common.client.retries
