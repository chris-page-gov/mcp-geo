import requests

from tools.os_common import OSClient


class DummyResponse:
    def __init__(self, status_code: int, text: str, url: str = "https://api.os.uk/test"):
        self.status_code = status_code
        self.text = text
        self.url = url


def test_invalid_key_classified(monkeypatch):
    resp = DummyResponse(401, "Invalid API key")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: resp)
    client = OSClient(api_key="bad-key", retries=1)
    status, payload = client.get_json("https://api.os.uk/search/places/v1/postcode", {})
    assert status == 401
    assert payload["code"] == "OS_API_KEY_INVALID"


def test_expired_key_classified(monkeypatch):
    resp = DummyResponse(403, "API key expired")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: resp)
    client = OSClient(api_key="expired-key", retries=1)
    status, payload = client.get_json("https://api.os.uk/search/places/v1/postcode", {})
    assert status == 403
    assert payload["code"] == "OS_API_KEY_EXPIRED"


def test_missing_key_classified(monkeypatch):
    resp = DummyResponse(401, "API key required")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: resp)
    client = OSClient(api_key="missing-key", retries=1)
    status, payload = client.get_json("https://api.os.uk/search/places/v1/postcode", {})
    assert status == 401
    assert payload["code"] == "NO_API_KEY"
