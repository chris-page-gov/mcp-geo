from typing import Any, Dict
from tools.ons_common import ONSClient, TTLCache

class DummyResp:
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] | None = None, text: str = 'ok') -> None:
        self.status_code: int = status_code
        self._json: Dict[str, Any] = json_data or {"value": 1}
        self.text: str = text
    def json(self) -> Dict[str, Any]:  # type: ignore[override]
        return self._json


def test_ons_client_caching(monkeypatch):
    calls = {"n": 0}
    def fake_get(url: str, params: Dict[str, Any] | None = None, timeout: float | None = None):
        calls["n"] += 1
        return DummyResp(json_data={"url": url, "params": params})
    import requests
    monkeypatch.setattr(requests, 'get', fake_get)
    c = ONSClient(cache_ttl=60.0, cache_size=4)
    status1, data1 = c.get_json('https://api.ons.gov.uk/test', {"a":1})
    status2, data2 = c.get_json('https://api.ons.gov.uk/test', {"a":1})
    assert status1 == 200 and status2 == 200
    assert calls["n"] == 1  # second hit cached
    assert data1 == data2


def test_ons_client_pagination_helper():
    c = ONSClient(cache_ttl=1.0)
    params = c.build_paged_params(50, 3, {"q": "gdp"})
    assert params == {"limit": 50, "page": 3, "q": "gdp"}


def test_ttlcache_expires_entries():
    cache = TTLCache(maxsize=2, ttl=0.0)
    cache.set("a", 1)
    assert cache.get("a") is None


def test_ttlcache_eviction_on_maxsize():
    cache = TTLCache(maxsize=1, ttl=60.0)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("b") == 2


def test_ttlcache_eviction_prefers_expired(monkeypatch):
    cache = TTLCache(maxsize=1, ttl=1.0)
    times = iter([0.0, 2.0, 2.0, 2.0])
    monkeypatch.setattr("tools.ons_common.time.time", lambda: next(times))
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("b") == 2


def test_ons_client_timeout_returns_error(monkeypatch):
    import requests
    from tools import ons_common

    def fake_get(url: str, params: Dict[str, Any] | None = None, timeout: float | None = None):
        raise ons_common.req_exc.Timeout("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    c = ONSClient(retries=1, cache_ttl=1.0)
    status, data = c.get_json("https://api.ons.gov.uk/test", {"a": 1})
    assert status == 501
    assert data["code"] == "UPSTREAM_CONNECT_ERROR"


def test_ons_client_invalid_json_returns_error(monkeypatch):
    import requests

    class BadResp:
        status_code = 200
        text = "not-json"
        def json(self):  # type: ignore[override]
            raise ValueError("boom json parse")

    def fake_get(url: str, params: Dict[str, Any] | None = None, timeout: float | None = None):
        return BadResp()

    monkeypatch.setattr(requests, "get", fake_get)
    c = ONSClient(retries=1, cache_ttl=1.0)
    status, data = c.get_json("https://api.ons.gov.uk/test", {"a": 1})
    assert status == 502
    assert data["code"] == "UPSTREAM_INVALID_RESPONSE"
