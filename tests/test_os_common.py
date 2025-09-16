import json
import types
import requests
from fastapi.testclient import TestClient
from server.main import app
from tools.os_common import OSClient

client = TestClient(app)

class DummyResp:
    def __init__(self, status_code=200, json_data=None, text="OK"):
        self.status_code = status_code
        self._json_data = json_data or {"ok": True}
        self.text = text
    def json(self):
        return self._json_data


def test_retry_then_success(monkeypatch):
    calls = {"n": 0}
    def fake_get(url, params=None, timeout=5):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.exceptions.ConnectionError("first")
        return DummyResp(200, {"done": True})
    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=3)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 200
    assert payload["done"] is True
    assert calls["n"] == 2  # one retry


def test_non_200_os_api(monkeypatch):
    def fake_get(url, params=None, timeout=5):
        return DummyResp(500, json_data={"error": "bad"}, text="Internal Error Body")
    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 500
    assert payload["code"] == "OS_API_ERROR"


def test_integration_error(monkeypatch):
    class Weird:
        def json(self):
            raise ValueError("boom json parse")
        status_code = 200
        text = "should not matter"
    def fake_get(url, params=None, timeout=5):
        return Weird()
    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    # General exception branch returns 500 INTEGRATION_ERROR
    assert code == 500
    assert payload["code"] == "INTEGRATION_ERROR"
