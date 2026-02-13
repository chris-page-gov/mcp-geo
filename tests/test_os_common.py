from typing import ClassVar

import requests
from fastapi.testclient import TestClient

from server.main import app
from tools.os_common import OSClient, classify_os_api_key_error

client = TestClient(app)

class DummyResp:
    def __init__(self, status_code=200, json_data=None, text="OK", headers=None, content=b"{}"):
        self.status_code = status_code
        self._json_data = json_data or {"ok": True}
        self.text = text
        self.headers = headers or {"Content-Type": "application/json"}
        self.content = content
        self.url = "https://api.os.uk/test"
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
    assert code == 502
    assert payload["code"] == "UPSTREAM_INVALID_RESPONSE"


def test_post_json_retry_then_success(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=5):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.exceptions.ConnectionError("first")
        return DummyResp(200, {"posted": True})

    monkeypatch.setattr(requests, "post", fake_post)
    client_obj = OSClient(api_key="abc", retries=3)
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 200
    assert payload["posted"] is True
    assert calls["n"] == 2


def test_post_json_non_200_auth(monkeypatch):
    def fake_post(url, params=None, json=None, timeout=5):
        return DummyResp(403, text="forbidden invalid api key")

    monkeypatch.setattr(requests, "post", fake_post)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 403
    assert payload["code"] == "OS_API_KEY_INVALID"


def test_post_json_invalid_json(monkeypatch):
    class Weird:
        status_code = 200
        text = "not-json"
        url = "https://api.os.uk/test"
        headers: ClassVar[dict[str, str]] = {"Content-Type": "application/json"}

        def json(self):
            raise ValueError("bad json")

    def fake_post(url, params=None, json=None, timeout=5):
        return Weird()

    monkeypatch.setattr(requests, "post", fake_post)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 502
    assert payload["code"] == "UPSTREAM_INVALID_RESPONSE"


def test_get_bytes_success(monkeypatch):
    def fake_get(url, params=None, timeout=5):
        return DummyResp(
            200,
            json_data={"unused": True},
            headers={"Content-Type": "application/xml"},
            content=b"<xml/>",
        )

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 200
    assert payload["contentType"] == "application/xml"
    assert payload["content"] == b"<xml/>"


def test_get_bytes_non_200_and_connect_error(monkeypatch):
    def fake_get_non_200(url, params=None, timeout=5):
        return DummyResp(500, text="Internal Error")

    monkeypatch.setattr(requests, "get", fake_get_non_200)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 500
    assert payload["code"] == "OS_API_ERROR"

    def fake_get_conn(url, params=None, timeout=5):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", fake_get_conn)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_CONNECT_ERROR"


def test_classify_os_api_key_error_variants():
    assert classify_os_api_key_error(401, "api key expired")[0] == "OS_API_KEY_EXPIRED"
    assert classify_os_api_key_error(401, "api key required")[0] == "NO_API_KEY"
    assert classify_os_api_key_error(403, "forbidden")[0] == "OS_API_KEY_INVALID"
    assert classify_os_api_key_error(500, "forbidden") is None


def test_no_api_key_for_all_methods():
    client_obj = OSClient(api_key="", retries=1)
    client_obj.api_key = ""
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "NO_API_KEY"
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 501
    assert payload["code"] == "NO_API_KEY"
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "NO_API_KEY"


def test_circuit_open_for_all_methods():
    class OpenBreaker:
        @staticmethod
        def allow():
            return False

    client_obj = OSClient(api_key="abc", retries=1)
    client_obj._breaker = OpenBreaker()
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 503
    assert payload["code"] == "CIRCUIT_OPEN"
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 503
    assert payload["code"] == "CIRCUIT_OPEN"
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 503
    assert payload["code"] == "CIRCUIT_OPEN"


def test_tls_error_paths(monkeypatch):
    def fake_get_tls(_url, params=None, timeout=5):
        raise requests.exceptions.SSLError("tls")

    def fake_post_tls(_url, params=None, json=None, timeout=5):
        raise requests.exceptions.SSLError("tls")

    monkeypatch.setattr(requests, "get", fake_get_tls)
    monkeypatch.setattr(requests, "post", fake_post_tls)
    client_obj = OSClient(api_key="abc", retries=1)

    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_TLS_ERROR"

    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_TLS_ERROR"

    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_TLS_ERROR"


def test_get_json_auth_error_classification(monkeypatch):
    def fake_get(_url, params=None, timeout=5):
        return DummyResp(401, json_data={"error": "missing"}, text="API key required")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 401
    assert payload["code"] == "NO_API_KEY"
