from typing import Any, Dict
from tools.ons_common import ONSClient

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
