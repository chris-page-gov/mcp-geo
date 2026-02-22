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


def test_ons_query_observations_include_paged_params_non_range(monkeypatch):
    from tools import ons_common

    observation_params: list[Dict[str, Any]] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if "/versions/1" in url and "observations" not in url and "dimensions/" not in url:
            return 200, {"dimensions": [{"id": "time"}]}
        if "observations" in url:
            if isinstance(params, dict):
                observation_params.append(dict(params))
            return 200, {"dimensions": {"time": {"id": "time"}}, "observations": [{"value": 1}], "total": 1}
        return 200, {"items": []}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "limit": 5,
            "page": 2,
        },
    )
    assert resp.status_code == 200
    assert observation_params
    first = observation_params[0]
    assert "limit" not in first and "page" not in first
    assert first.get("time") == "*"


def test_ons_query_links_next_exact_total_avoids_duplicate_fetch(monkeypatch):
    from tools import ons_data

    calls: list[tuple[str, Dict[str, Any] | None]] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        captured = dict(params) if isinstance(params, dict) else None
        calls.append((url, captured))
        if len(calls) == 1:
            assert captured == {"time": "*"}
            return 200, {
                "observations": [{"id": "page-1-a"}, {"id": "page-1-b"}],
                "links": [{"rel": "next", "href": "?page=2&limit=2"}],
                "total": 4,
            }
        if len(calls) == 2:
            assert captured is None
            assert "page=2" in url
            return 200, {"observations": [{"id": "page-2-a"}, {"id": "page-2-b"}], "total": 4}
        raise AssertionError("Unexpected extra observations fetch")

    monkeypatch.setattr(ons_data, "_OBSERVATIONS_FETCH_PAGE_LIMIT", 2)
    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json)

    status, body = ons_data._fetch_observations_paged(
        url="https://api.beta.ons.gov.uk/v1/datasets/gdp/editions/time-series/versions/1/observations",
        filters={"time": "*"},
    )

    assert status == 200
    assert [row["id"] for row in body["observations"]] == [
        "page-1-a",
        "page-1-b",
        "page-2-a",
        "page-2-b",
    ]
    assert len(calls) == 2


def test_ons_query_retries_observations_without_limit_page(monkeypatch):
    from tools import ons_data

    calls: list[Dict[str, Any] | None] = []
    implicit_pages: list[int] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True):  # noqa: ARG001
        if "observations" not in url:
            return 500, {"isError": True, "code": "UNEXPECTED", "message": "unexpected URL"}
        captured = dict(params) if isinstance(params, dict) else None
        calls.append(captured)
        if isinstance(captured, dict) and "limit" not in captured and "page" not in captured:
            implicit_pages.append(len(implicit_pages) + 1)
            if len(implicit_pages) == 1:
                return 200, {"observations": [{"id": "implicit"}], "total": 2}
            return 200, {"observations": [{"id": "fallback"}], "total": 1}
        if isinstance(captured, dict) and ("limit" in captured or "page" in captured):
            return 400, {
                "isError": True,
                "code": "ONS_API_ERROR",
                "message": "incorrect selection of query parameters: [limit page], these dimensions do not exist for this version of the dataset",  # noqa: E501
            }
        return 500, {"isError": True, "code": "UNEXPECTED", "message": "unexpected params"}

    monkeypatch.setattr(ons_data, "_OBSERVATIONS_FETCH_PAGE_LIMIT", 1)
    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json)

    status, body = ons_data._fetch_observations_paged(
        url="https://api.beta.ons.gov.uk/v1/datasets/gdp/editions/time-series/versions/1/observations",
        filters={"time": "Jan-24"},
    )

    assert status == 200
    assert body["observations"] == [{"id": "fallback"}]
    assert len(calls) == 3
    assert calls[0] == {"time": "Jan-24"}
    assert calls[1] == {"limit": 1, "page": 1, "time": "Jan-24"}
    assert calls[2] == {"time": "Jan-24"}


def test_ons_query_handles_null_observations_payload(monkeypatch):
    from tools import ons_data

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True):  # noqa: ARG001
        return 200, {"observations": None, "total": 0}

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json)
    status, body = ons_data._fetch_observations_paged(
        url="https://api.beta.ons.gov.uk/v1/datasets/gdp/editions/time-series/versions/1/observations",
        filters={"time": "2023 Q1"},
    )
    assert status == 200
    assert body["observations"] == []


def test_ons_query_time_range_handles_links_code_ids_and_observation_retry(monkeypatch):
    from tools import ons_common

    observation_params: list[Dict[str, Any]] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if "/versions/1" in url and "dimensions/" not in url and "observations" not in url:
            return 200, {
                "dimensions": [
                    {"name": "time", "id": "mmm-yy"},
                    {"name": "geography", "id": "uk-only"},
                    {
                        "name": "unofficialstandardindustrialclassification",
                        "id": "sic-unofficial",
                    },
                ]
            }
        if "dimensions/time/options" in url:
            return 200, {
                "items": [
                    {"label": "Jan-24", "links": {"code": {"id": "Jan-24"}}},
                    {"label": "Feb-24", "links": {"code": {"id": "Feb-24"}}},
                    {"label": "Mar-24", "links": {"code": {"id": "Mar-24"}}},
                    {"label": "Apr-24", "links": {"code": {"id": "Apr-24"}}},
                ],
                "links": [],
            }
        if "observations" in url:
            if isinstance(params, dict):
                if "limit" in params or "page" in params:
                    return 400, {
                        "isError": True,
                        "code": "ONS_API_ERROR",
                        "message": "incorrect selection of query parameters: [limit page], these dimensions do not exist for this version of the dataset",  # noqa: E501
                    }
                observation_params.append(dict(params))
            return 200, {"observations": [{"time": params.get("time"), "value": 1}], "total": 1}
        return 200, {"items": []}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "GDPV",
            "timeRange": "2024 Q1-2024 Q2",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 4
    assert body["timeValues"] == ["Jan-24", "Feb-24", "Mar-24", "Apr-24"]
    assert {entry.get("time") for entry in observation_params} == {
        "Jan-24",
        "Feb-24",
        "Mar-24",
        "Apr-24",
    }
    for entry in observation_params:
        assert "limit" not in entry
        assert "page" not in entry


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


def test_ons_query_time_range_observations_include_paged_params(monkeypatch):
    from tools import ons_common

    observation_params: list[Dict[str, Any]] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if "/versions/1" in url and "dimensions/time/options" not in url and "observations" not in url:
            return 200, {"dimensions": [{"id": "time"}]}
        if "dimensions/time/options" in url:
            return 200, {"items": [{"option": "2024 Q1"}, {"option": "2024 Q2"}], "links": []}
        if "observations" in url:
            if isinstance(params, dict):
                observation_params.append(dict(params))
            return 200, {"observations": [{"time": params.get("time"), "value": 1}], "total": 1}
        return 200, {"items": []}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "timeRange": "2024 Q1-2024 Q2",
        },
    )
    assert resp.status_code == 200
    assert observation_params
    assert {entry.get("time") for entry in observation_params} == {"2024 Q1", "2024 Q2"}
    for entry in observation_params:
        assert "limit" not in entry
        assert "page" not in entry


def test_ons_query_time_range_expands_with_shorthand_end(monkeypatch):
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        if "/versions/1" in url and "dimensions/time/options" not in url and "observations" not in url:
            return 200, {"dimensions": [{"id": "time"}]}
        if "dimensions/time/options" in url:
            return 200, {"items": [{"option": "2024 Q1"}, {"option": "2024 Q2"}], "links": []}
        return 200, {"observations": [{"time": params.get("time"), "value": 1}], "total": 1}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "timeRange": "2024 Q1-Q2",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["timeValues"] == ["2024 Q1", "2024 Q2"]


def test_get_observation_expands_single_quarter_token(monkeypatch):
    from tools import ons_common

    observed_times: list[str] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True):  # noqa: ARG001
        if "/versions/1" in url and "dimensions/" not in url and "observations" not in url:
            return 200, {
                "dimensions": [
                    {"name": "time", "id": "mmm-yy"},
                    {"name": "geography", "id": "uk-only"},
                    {
                        "name": "unofficialstandardindustrialclassification",
                        "id": "sic-unofficial",
                    },
                ]
            }
        if "dimensions/time/options" in url:
            return 200, {
                "items": [
                    {"option": "Mar-23"},
                    {"option": "Feb-23"},
                    {"option": "Jan-23"},
                ],
                "links": [],
            }
        if "dimensions/geography/options" in url:
            return 200, {"items": [{"option": "K02000001"}], "links": []}
        if "dimensions/unofficialstandardindustrialclassification/options" in url:
            return 200, {"items": [{"option": "A--T"}], "links": []}
        if "observations" in url:
            if isinstance(params, dict):
                observed_times.append(str(params.get("time")))
            return 200, {
                "observations": [
                    {
                        "dimensions": {
                            "Time": {"id": params.get("time")},
                        },
                        "observation": "1.0",
                    }
                ],
                "total": 1,
            }
        return 200, {"items": []}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "chained_volume_measure",
            "time": "2023 Q1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["observation"]["dimensions"]["Time"]["id"] == "Mar-23"
    assert observed_times == ["Mar-23", "Feb-23", "Jan-23"]


def test_get_observation_single_token_retries_latest_alias_version(monkeypatch):
    from tools import ons_common, ons_data

    observed_times: list[str] = []
    metadata_versions: list[str] = []

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True):  # noqa: ARG001
        if "/versions/" in url and "dimensions/" not in url and "observations" not in url:
            if "/versions/1" in url:
                metadata_versions.append("1")
                return 200, {
                    "dimensions": [
                        {"name": "time", "id": "mmm-yy"},
                        {"name": "geography", "id": "uk-only"},
                        {
                            "name": "unofficialstandardindustrialclassification",
                            "id": "sic-unofficial",
                        },
                    ]
                }
            metadata_versions.append("65")
            return 200, {
                "dimensions": [
                    {"name": "time", "id": "mmm-yy"},
                    {"name": "geography", "id": "uk-only"},
                    {
                        "name": "unofficialstandardindustrialclassification",
                        "id": "sic-unofficial",
                    },
                ]
            }
        if "versions/1/dimensions/time/options" in url:
            return 200, {"items": [], "links": []}
        if "versions/65/dimensions/time/options" in url:
            return 200, {"items": [{"option": "Mar-23"}], "links": []}
        if "dimensions/geography/options" in url:
            return 200, {"items": [{"option": "K02000001"}], "links": []}
        if "dimensions/unofficialstandardindustrialclassification/options" in url:
            return 200, {"items": [{"option": "A--T"}], "links": []}
        if "observations" in url:
            if isinstance(params, dict):
                observed_times.append(str(params.get("time")))
            return 200, {
                "observations": [
                    {
                        "dimensions": {
                            "Time": {"id": params.get("time")},
                        },
                        "observation": "1.0",
                    }
                ],
                "total": 1,
            }
        return 200, {"items": []}

    monkeypatch.setattr(ons_data, "_resolve_latest_version", lambda dataset: ("time-series", "65"))
    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "chained_volume_measure",
            "time": "2023 Q1",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["observation"]["dimensions"]["Time"]["id"] == "Mar-23"
    assert "1" in metadata_versions
    assert "65" in metadata_versions
    assert observed_times == ["Mar-23"]


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
    assert body["dataset"] == "gdp-to-four-decimal-places"
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
