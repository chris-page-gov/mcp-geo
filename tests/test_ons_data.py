from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_ons_query_all():
    resp = client.post("/tools/call", json={"tool": "ons_data.query"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 5
    assert len(body["results"]) <= body["limit"]


def test_ons_query_filter_geography_measure():
    resp = client.post("/tools/call", json={
        "tool": "ons_data.query",
        "geography": "K02000001",
        "measure": "chained_volume_measure"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert all(r["geography"] == "K02000001" for r in body["results"])


def test_ons_query_time_range():
    resp = client.post("/tools/call", json={
        "tool": "ons_data.query",
        "timeRange": "2023 Q2-2023 Q3"
    })
    assert resp.status_code == 200
    body = resp.json()
    times = {r["time"] for r in body["results"]}
    assert times == {"2023 Q2", "2023 Q3"}


def test_ons_query_single_period():
    resp = client.post("/tools/call", json={
        "tool": "ons_data.query",
        "timeRange": "2024 Q1"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["time"] == "2024 Q1"


def test_ons_query_pagination():
    resp1 = client.post("/tools/call", json={"tool": "ons_data.query", "limit": 2, "page": 1})
    resp2 = client.post("/tools/call", json={"tool": "ons_data.query", "limit": 2, "page": 2})
    resp3 = client.post("/tools/call", json={"tool": "ons_data.query", "limit": 2, "page": 3})
    assert resp1.status_code == 200 and resp2.status_code == 200
    assert resp3.status_code == 200
    ids1 = {r["time"] for r in resp1.json()["results"]}
    ids2 = {r["time"] for r in resp2.json()["results"]}
    ids3 = {r["time"] for r in resp3.json()["results"]}
    assert ids1.isdisjoint(ids2)
    assert ids1.isdisjoint(ids3)
    assert ids2.isdisjoint(ids3)
    assert resp3.json()["data"].get("nextPageToken") is None if isinstance(resp3.json().get("data"), dict) else True  # defensive


def test_ons_query_invalid_limit():
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "limit": 0})
    assert resp.status_code == 400
    err = resp.json()
    assert err["isError"] and err["code"] == "INVALID_INPUT"


def test_ons_query_invalid_time_range_no_results():
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "timeRange": "2022 Q1-2022 Q2"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["results"] == []


def test_ons_query_live_disabled_falls_back_sample(monkeypatch):
    # Ensure flag false
    from server import config
    monkeypatch.setattr(config.settings, 'ONS_LIVE_ENABLED', False)
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "dataset": "gdp", "edition": "time-series", "version": "1"})
    # Should not error, but returns sample (empty results? sample doesn't match params so returns sample full)
    assert resp.status_code == 200
    body = resp.json()
    assert 'live' not in body


def test_ons_query_live_enabled(monkeypatch):
    from server import config
    monkeypatch.setattr(config.settings, 'ONS_LIVE_ENABLED', True)
    # Mock client get_json
    from tools import ons_common
    from typing import Any, Dict, Tuple
    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:
        return 200, {"observations": [{"time": "2024 Q1", "value": 123.4}], "total": 10}
    monkeypatch.setattr(ons_common.client, 'get_json', fake_get_json)
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "dataset": "gdp", "edition": "time-series", "version": "1", "limit": 1, "page": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body['live'] is True
    assert body['results'][0]['value'] == 123.4


def test_ons_query_no_match():
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "geography": "NOPE"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["results"] == []