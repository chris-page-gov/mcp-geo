import json
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


def test_ons_query_time_range_expands(monkeypatch):
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if "/versions/1" in url and "dimensions/time/options" not in url and "observations" not in url:
            return 200, {"dimensions": [{"id": "time"}]}
        if "dimensions/time/options" in url:
            return 200, {"items": [{"option": "2023 Q1"}, {"option": "2023 Q2"}], "links": []}
        return 200, {"observations": [{"time": params.get("time"), "value": 1}], "total": 1}

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
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["timeValues"] == ["2023 Q1", "2023 Q2"]


def test_ons_query_auto_resolve(monkeypatch):
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if url.endswith("/datasets") and params and params.get("search"):
            return 200, {
                "items": [
                    {
                        "id": "gdp",
                        "state": "published",
                        "links": {
                            "latest_version": {
                                "href": "https://api.beta.ons.gov.uk/v1/datasets/gdp/editions/time-series/versions/1"
                            }
                        },
                    }
                ]
            }
        return 200, {"observations": [{"time": "2024 Q1", "value": 99}], "total": 1}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post("/tools/call", json={"tool": "ons_data.query", "term": "gdp"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset"] == "gdp"
    assert body["results"][0]["value"] == 99


def test_filter_output_resource_delivery(monkeypatch, tmp_path):
    from server.mcp import resource_catalog
    from tools import ons_data

    monkeypatch.setattr(ons_data, "_ONS_EXPORTS_DIR", tmp_path / "ons_exports")
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", tmp_path / "ons_exports")

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [{"time": "2024 Q1", "value": 123.4}], "total": 1}

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
        json={
            "tool": "ons_data.get_filter_output",
            "filterId": filter_id,
            "format": "CSV",
            "delivery": "resource",
        },
    )
    assert output_resp.status_code == 200
    body = output_resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/ons-exports/")

    read_resp = client.get("/resources/read", params={"uri": body["resourceUri"]})
    assert read_resp.status_code == 200
    contents = read_resp.json()["contents"]
    payload = json.loads(contents[0]["text"])
    assert payload["filterId"] == filter_id
    assert payload["format"] == "CSV"
    assert payload["encoding"] == "utf-8"
    assert "time,value" in payload["data"]


def test_filter_output_auto_switches_to_resource(monkeypatch, tmp_path):
    from server.mcp import resource_catalog
    from tools import ons_data

    monkeypatch.setattr(ons_data, "_ONS_EXPORTS_DIR", tmp_path / "ons_exports")
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", tmp_path / "ons_exports")

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        observations = [
            {"time": "2024 Q1", "value": 123.4, "geography": "E09000001"},
            {"time": "2024 Q2", "value": 123.9, "geography": "E09000001"},
        ]
        return 200, {"observations": observations, "total": len(observations)}

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
        json={
            "tool": "ons_data.get_filter_output",
            "filterId": filter_id,
            "format": "JSON",
            "delivery": "auto",
            "inlineMaxBytes": 10,
        },
    )
    assert output_resp.status_code == 200
    body = output_resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/ons-exports/")
