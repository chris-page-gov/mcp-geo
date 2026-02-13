import json

import pytest

from server.config import settings
from tools import nomis_common


class DummyResponse:
    def __init__(self, status_code: int, payload: dict, *, text: str | None = None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else json.dumps(payload)
        self.url = "http://example"

    def json(self) -> dict:
        return self._payload


def _skip_if_no_requests():
    if nomis_common.requests is None:
        pytest.skip("requests not installed")


def test_nomis_client_success_caches_and_auth(monkeypatch):
    _skip_if_no_requests()
    calls = {"count": 0, "params": None}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        calls["params"] = params
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    monkeypatch.setattr(settings, "NOMIS_UID", "uid-test", raising=False)
    monkeypatch.setattr(settings, "NOMIS_SIGNATURE", "sig-test", raising=False)
    client = nomis_common.NomisClient(retries=1, cache_ttl=60, cache_size=4)

    status, data = client.get_json("http://example", {"q": 1})
    assert status == 200
    assert data["ok"] is True
    assert calls["params"]["uid"] == "uid-test"
    assert calls["params"]["signature"] == "sig-test"

    status2, data2 = client.get_json("http://example", {"q": 1})
    assert status2 == 200
    assert data2["ok"] is True
    assert calls["count"] == 1


def test_nomis_client_invalid_json(monkeypatch):
    _skip_if_no_requests()

    class BadResponse(DummyResponse):
        def json(self):  # noqa: D401
            raise ValueError("bad json")

    def fake_get(url, params, timeout):  # noqa: ARG001
        return BadResponse(200, {}, text="not-json")

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 502
    assert data["code"] == "UPSTREAM_INVALID_RESPONSE"


def test_nomis_client_non_200(monkeypatch):
    _skip_if_no_requests()

    def fake_get(url, params, timeout):  # noqa: ARG001
        return DummyResponse(500, {"error": "boom"}, text="boom")

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 500
    assert data["code"] == "NOMIS_API_ERROR"


def test_nomis_client_connection_error(monkeypatch):
    _skip_if_no_requests()

    def fake_get(url, params, timeout):  # noqa: ARG001
        raise nomis_common.req_exc.ConnectionError("boom")

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 501
    assert data["code"] == "UPSTREAM_CONNECT_ERROR"


def test_nomis_client_tls_error(monkeypatch):
    _skip_if_no_requests()

    def fake_get(url, params, timeout):  # noqa: ARG001
        raise nomis_common.req_exc.SSLError("tls")

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 501
    assert data["code"] == "UPSTREAM_TLS_ERROR"


def test_ttlcache_evicts_expired():
    cache = nomis_common.TTLCache(maxsize=1, ttl=-1)
    cache.set("a", 1)
    assert cache.get("a") is None


def test_ttlcache_evicts_oldest():
    cache = nomis_common.TTLCache(maxsize=1, ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_ttlcache_evicts_invalid_entry_first():
    cache = nomis_common.TTLCache(maxsize=1, ttl=60)
    cache.ttl = -1
    cache.set("a", 1)
    cache.ttl = 60
    cache.set("b", 2)
    assert cache.get("b") == 2


def test_nomis_client_requests_missing(monkeypatch):
    monkeypatch.setattr(nomis_common, "requests", None)
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 501
    assert data["code"] == "MISSING_DEPENDENCY"


def test_nomis_client_circuit_breaker_open(monkeypatch):
    _skip_if_no_requests()
    client = nomis_common.NomisClient(retries=1, cache_ttl=0, cache_size=1)
    monkeypatch.setattr(client._breaker, "allow", lambda: False)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 503
    assert data["code"] == "CIRCUIT_OPEN"


def test_nomis_client_retries_then_success(monkeypatch):
    _skip_if_no_requests()
    calls = {"count": 0, "slept": False}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] == 1:
            raise nomis_common.req_exc.ConnectionError("boom")
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr(nomis_common.requests, "get", fake_get)
    monkeypatch.setattr(nomis_common, "_sleep_with_jitter", lambda *args, **kwargs: calls.update({"slept": True}))
    client = nomis_common.NomisClient(retries=2, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 200
    assert data["ok"] is True
    assert calls["slept"] is True


def test_nomis_client_zero_retries_returns_failure(monkeypatch):
    _skip_if_no_requests()
    client = nomis_common.NomisClient(retries=0, cache_ttl=0, cache_size=1)
    status, data = client.get_json("http://example", {"q": 1})
    assert status == 501
    assert data["code"] == "UPSTREAM_CONNECT_ERROR"


def test_sleep_with_jitter(monkeypatch):
    calls = {"slept": 0}

    monkeypatch.setattr(nomis_common.time, "sleep", lambda _: calls.update({"slept": calls["slept"] + 1}))
    monkeypatch.setattr(nomis_common.random, "uniform", lambda *_: 0)
    nomis_common._sleep_with_jitter(1, base=0.0, cap=0.0)
    assert calls["slept"] == 1
