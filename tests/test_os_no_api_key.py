import requests

from server.config import settings
from tools.os_common import OSClient


def test_no_api_key_return(monkeypatch):
    # Ensure no env key leaks
    try:
        settings.OS_API_KEY = ""
    except Exception:
        pass
    monkeypatch.delenv("OS_API_KEY", raising=False)
    called = {"n":0}
    def fake_get(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("should not be called when no API key")
    monkeypatch.setattr(requests, "get", fake_get)
    c = OSClient(api_key="", retries=1)
    code, payload = c.get_json("https://ignore.example.com", {})
    assert code == 501
    assert payload["code"] == "NO_API_KEY"
    assert called["n"] == 0
