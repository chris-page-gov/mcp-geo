from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_ons_query_requires_dataset_params():
    resp = client.post("/tools/call", json={"tool": "ons_data.query"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "INVALID_INPUT"


def test_ons_query_live_disabled(monkeypatch):
    from server import config

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False)
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_data.query", "dataset": "gdp", "edition": "time-series", "version": "1"},
    )
    assert resp.status_code == 501
    assert resp.json()["code"] == "LIVE_DISABLED"


def test_ons_query_live_success(monkeypatch):
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [{"time": "2024 Q1", "value": 123.4}], "total": 10}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_data.query", "dataset": "gdp", "edition": "time-series", "version": "1", "limit": 1, "page": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["results"][0]["value"] == 123.4


def test_ons_query_time_range_range_invalid(monkeypatch):
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [], "total": 0}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "timeRange": "2023 Q1-2023 Q2",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"
