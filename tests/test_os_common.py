from typing import ClassVar

import requests
from fastapi.testclient import TestClient

from server.main import app
from tools import os_common
from tools.os_common import (
    OSClient,
    _normalize_auth_mode,
    classify_os_api_key_error,
    features_request_policy,
)

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
    assert classify_os_api_key_error(403, "something else")[0] == "OS_API_KEY_INVALID"
    assert classify_os_api_key_error(500, "forbidden") is None


def test_auth_mode_normalization_and_features_policy_bounds(monkeypatch):
    assert _normalize_auth_mode("query-param") == "query"
    assert _normalize_auth_mode("key_header") == "header"
    assert _normalize_auth_mode("oauth2-bearer") == "bearer"
    assert _normalize_auth_mode("unexpected") == "query"

    monkeypatch.setattr(
        os_common.settings,
        "OS_FEATURES_TIMEOUT_CONNECT_SECONDS",
        "bad",
        raising=False,
    )
    monkeypatch.setattr(
        os_common.settings,
        "OS_FEATURES_TIMEOUT_READ_SECONDS",
        "-1",
        raising=False,
    )
    monkeypatch.setattr(os_common.settings, "OS_FEATURES_RETRIES", "99", raising=False)
    monkeypatch.setattr(
        os_common.settings,
        "OS_FEATURES_TIMEOUT_DEGRADED_LIMIT",
        "0",
        raising=False,
    )
    policy = features_request_policy()
    assert policy == {
        "connectTimeoutSeconds": 2.0,
        "readTimeoutSeconds": 12.0,
        "retries": 10,
        "degradedLimit": 1,
    }

    monkeypatch.setattr(
        os_common.settings,
        "OS_FEATURES_RETRIES",
        "not-an-int",
        raising=False,
    )
    monkeypatch.setattr(
        os_common.settings,
        "OS_FEATURES_TIMEOUT_DEGRADED_LIMIT",
        "999",
        raising=False,
    )
    policy = features_request_policy()
    assert policy["retries"] == 3
    assert policy["degradedLimit"] == 100


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


def test_missing_requests_dependency_for_all_methods(monkeypatch):
    monkeypatch.setattr(os_common, "requests", None)
    client_obj = OSClient(api_key="abc", retries=1)

    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "MISSING_DEPENDENCY"

    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 501
    assert payload["code"] == "MISSING_DEPENDENCY"

    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "MISSING_DEPENDENCY"


def test_client_timeout_and_retry_overrides_are_bounded():
    client_obj = OSClient(api_key="abc", retries=2, connect_timeout=1, read_timeout=2)

    assert client_obj._effective_timeout(3) == 3.0
    assert client_obj._effective_timeout((-1, 4)) == (5.0, 4.0)
    assert client_obj._effective_timeout(("bad", 4)) == client_obj.timeout
    assert client_obj._effective_retries(0) == 1
    assert client_obj._effective_retries(99) == 10
    assert client_obj._effective_retries("bad") == client_obj.retries


def test_get_json_auth_error_classification(monkeypatch):
    def fake_get(_url, params=None, timeout=5):
        return DummyResp(401, json_data={"error": "missing"}, text="API key required")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 401
    assert payload["code"] == "NO_API_KEY"


def test_post_json_non_200_os_api_and_connect_error(monkeypatch):
    def fake_post_non_200(_url, params=None, json=None, timeout=5):
        return DummyResp(500, text="Internal Error Body")

    monkeypatch.setattr(requests, "post", fake_post_non_200)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 500
    assert payload["code"] == "OS_API_ERROR"

    def fake_post_conn(_url, params=None, json=None, timeout=5):
        raise requests.exceptions.ConnectionError("post boom")

    monkeypatch.setattr(requests, "post", fake_post_conn)
    code, payload = client_obj.post_json("https://api.os.uk/test", {"x": 1}, {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_CONNECT_ERROR"


def test_get_bytes_auth_error_classification(monkeypatch):
    def fake_get(_url, params=None, timeout=5):
        return DummyResp(401, text="api key expired")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 401
    assert payload["code"] == "OS_API_KEY_EXPIRED"


def test_get_bytes_unexpected_exception(monkeypatch):
    def fake_get(_url, params=None, timeout=5):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="abc", retries=1)
    code, payload = client_obj.get_bytes("https://api.os.uk/test", {})
    assert code == 500
    assert payload["code"] == "INTEGRATION_ERROR"


def test_query_auth_mode_uses_key_param(monkeypatch):
    seen: dict[str, object] = {}

    def fake_get(_url, params=None, timeout=5):
        seen["params"] = dict(params or {})
        seen["timeout"] = timeout
        return DummyResp(200, {"done": True})

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="query-key", auth_mode="query", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {"x": 1})
    assert code == 200
    assert payload["done"] is True
    assert seen["params"] == {"x": 1, "key": "query-key"}


def test_header_auth_mode_uses_key_header(monkeypatch):
    seen: dict[str, object] = {}

    def fake_get(_url, params=None, headers=None, timeout=5):
        seen["params"] = dict(params or {})
        seen["headers"] = dict(headers or {})
        return DummyResp(200, {"done": True})

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="header-key", auth_mode="header", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {"x": 1})
    assert code == 200
    assert payload["done"] is True
    assert seen["params"] == {"x": 1}
    assert seen["headers"] == {"key": "header-key"}


def test_os_client_disables_redirects_and_masks_secret_error_text(monkeypatch):
    seen: dict[str, object] = {}

    def fake_get(_url, params=None, headers=None, timeout=5, allow_redirects=True):
        seen["allow_redirects"] = allow_redirects
        seen["headers"] = dict(headers or {})
        return DummyResp(302, text="redirected with header-secret in body")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="header-secret", auth_mode="header", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 302
    assert payload["code"] == "OS_API_ERROR"
    assert seen["allow_redirects"] is False
    assert seen["headers"] == {"key": "header-secret"}
    assert "header-secret" not in payload["message"]
    assert "[REDACTED]" in payload["message"]


def test_os_client_masks_exception_secret_text(monkeypatch):
    def fake_get(_url, params=None, timeout=5, allow_redirects=True):
        raise requests.exceptions.ConnectionError("failed for query-secret")

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="query-secret", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "UPSTREAM_CONNECT_ERROR"
    assert "query-secret" not in payload["message"]
    assert "[REDACTED]" in payload["message"]


def test_bearer_auth_mode_uses_authorization_header_for_all_methods(monkeypatch):
    seen_gets: list[tuple[dict[str, object], dict[str, str]]] = []
    seen_posts: list[tuple[dict[str, object], dict[str, str], dict[str, object]]] = []

    def fake_get(_url, params=None, headers=None, timeout=5):
        seen_gets.append((dict(params or {}), dict(headers or {})))
        return DummyResp(200, {"done": True}, headers={"Content-Type": "application/octet-stream"})

    def fake_post(_url, params=None, headers=None, json=None, timeout=5):
        seen_posts.append((dict(params or {}), dict(headers or {}), dict(json or {})))
        return DummyResp(200, {"posted": True})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
    client_obj = OSClient(
        api_key="unused-key",
        access_token="bearer-token",
        auth_mode="oauth2",
        retries=1,
    )

    assert client_obj.get_json("https://api.os.uk/test", {"x": 1})[0] == 200
    assert client_obj.post_json("https://api.os.uk/test", {"payload": True}, {"x": 2})[0] == 200
    assert client_obj.get_bytes("https://api.os.uk/test", {"x": 3})[0] == 200

    assert seen_gets == [
        ({"x": 1}, {"Authorization": "Bearer bearer-token"}),
        ({"x": 3}, {"Authorization": "Bearer bearer-token"}),
    ]
    assert seen_posts == [
        ({"x": 2}, {"Authorization": "Bearer bearer-token"}, {"payload": True})
    ]


def test_bearer_auth_mode_requires_access_token(monkeypatch):
    calls = {"get": 0}

    def fake_get(*args, **kwargs):
        calls["get"] += 1
        return DummyResp(200, {"done": True})

    monkeypatch.setattr(requests, "get", fake_get)
    client_obj = OSClient(api_key="api-key", access_token="", auth_mode="bearer", retries=1)
    code, payload = client_obj.get_json("https://api.os.uk/test", {})
    assert code == 501
    assert payload["code"] == "NO_API_KEY"
    assert calls["get"] == 0
