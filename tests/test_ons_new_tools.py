from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_get_observation_live_disabled(monkeypatch):
    from server import config

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "growth",
            "time": "2024 Q1",
        },
    )
    assert resp.status_code == 501
    assert resp.json()["code"] == "LIVE_DISABLED"


def test_get_observation_missing_params():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_get_observation_live_success(monkeypatch):
    from tools import ons_data

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [{"value": 42, "time": "2024 Q1"}]}

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "growth",
            "time": "2024 Q1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["observation"]["value"] == 42


def test_filter_lifecycle_json(monkeypatch):
    from tools import ons_data

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [{"time": "2024 Q1", "value": 1.5}], "total": 1}

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json)
    create_resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.create_filter",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
        },
    )
    assert create_resp.status_code == 201
    filter_id = create_resp.json()["filterId"]

    output_resp = client.post(
        "/tools/call",
        json={"tool": "ons_data.get_filter_output", "filterId": filter_id, "format": "JSON"},
    )
    assert output_resp.status_code == 200
    output = output_resp.json()
    assert output["format"] == "JSON"
    assert output["data"]["results"][0]["value"] == 1.5


def test_filter_output_unknown_filter():
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_data.get_filter_output", "filterId": "unknown", "format": "JSON"},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "UNKNOWN_FILTER"
