from fastapi.testclient import TestClient
from server.main import app
from _pytest.monkeypatch import MonkeyPatch
from typing import Any, Dict, Tuple

client = TestClient(app)


def test_ons_dimensions_live_all(monkeypatch: MonkeyPatch):
    from server import config
    monkeypatch.setattr(config.settings, 'ONS_LIVE_ENABLED', True)
    # Mock client
    from tools import ons_common
    calls: dict[str, Any] = {"meta": 0, "opts": []}

    def fake_get_json(url: str, params=None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # type: ignore[override]
        if url.endswith('/version/1'):
            calls["meta"] += 1
            return 200, {"dimensions": [
                {"id": "geography"},
                {"id": "time"},
            ]}
        if '/dimensions/' in url:
            dim = url.rsplit('/', 2)[-2]
            if dim == 'geography':
                payload = {"items": [{"id": "K02000001"}, {"id": "E92000001"}]}
            else:
                payload = {"items": [{"id": "2024 Q1"}, {"id": "2024 Q2"}]}
            calls["opts"].append(dim)
            return 200, payload
        return 500, {"isError": True, "code": "UNEXPECTED", "message": "Unexpected URL"}

    monkeypatch.setattr(ons_common.client, 'get_json', fake_get_json)
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions', 'dataset': 'gdp', 'edition': 'time-series', 'version': '1'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['live'] is True
    assert body['dimensions']['geography'] == ['K02000001', 'E92000001']
    assert body['dimensions']['time'] == ['2024 Q1', '2024 Q2']
    assert calls['meta'] == 1
    assert set(calls['opts']) == {'geography', 'time'}


def test_ons_dimensions_live_single(monkeypatch: MonkeyPatch):
    from server import config
    monkeypatch.setattr(config.settings, 'ONS_LIVE_ENABLED', True)
    from tools import ons_common
    calls: dict[str, Any] = {"meta": 0, "opts": []}

    def fake_get_json(url: str, params=None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # type: ignore[override]
        if url.endswith('/version/1'):
            calls["meta"] += 1
            return 200, {"dimensions": [
                {"id": "geography"},
                {"id": "time"},
            ]}
        if '/dimensions/' in url:
            dim = url.rsplit('/', 2)[-2]
            calls['opts'].append(dim)
            if dim == 'time':
                return 200, {"items": [{"id": "2024 Q1"}, {"id": "2024 Q2"}]}
            return 200, {"items": []}
        return 500, {"isError": True, "code": "UNEXPECTED", "message": "Unexpected URL"}

    monkeypatch.setattr(ons_common.client, 'get_json', fake_get_json)
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions', 'dataset': 'gdp', 'edition': 'time-series', 'version': '1', 'dimension': 'time'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['live'] is True
    assert list(body['dimensions'].keys()) == ['time']
    assert body['dimensions']['time'] == ['2024 Q1', '2024 Q2']
    assert calls['meta'] == 1
    assert calls['opts'] == ['time']
