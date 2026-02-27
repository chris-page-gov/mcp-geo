from __future__ import annotations

from typing import Any


def test_ons_data_editions_and_versions_validation(monkeypatch) -> None:
    from server import config
    from tools import ons_data

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False, raising=False)
    status, body = ons_data._editions({"dataset": "gdp"})
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    status, body = ons_data._editions({})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_all_pages",
        lambda *_args, **_kwargs: (502, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    status, body = ons_data._editions({"dataset": "gdp"})
    assert status == 502
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(ons_data.ons_client, "get_all_pages", lambda *_args, **_kwargs: (200, {}), raising=True)
    status, body = ons_data._editions({"dataset": "gdp"})
    assert status == 500
    assert body["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_all_pages",
        lambda *_args, **_kwargs: (
            200,
            [{"edition": "time-series", "state": "published"}, {"id": 2, "state": "draft"}, "skip"],
        ),
        raising=True,
    )
    status, body = ons_data._editions({"dataset": "gdp"})
    assert status == 200
    assert body["dataset"] == "gdp-to-four-decimal-places"
    assert [entry["id"] for entry in body["editions"]] == ["time-series", "2"]

    status, body = ons_data._versions({"dataset": "gdp"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(ons_data.ons_client, "get_all_pages", lambda *_args, **_kwargs: (200, {}), raising=True)
    status, body = ons_data._versions({"dataset": "gdp", "edition": "time-series"})
    assert status == 500
    assert body["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_all_pages",
        lambda *_args, **_kwargs: (
            200,
            [{"version": "1", "state": "published"}, {"id": 2, "release_date": "2026-01-01"}, "skip"],
        ),
        raising=True,
    )
    status, body = ons_data._versions({"dataset": "gdp", "edition": "time-series"})
    assert status == 200
    assert [entry["id"] for entry in body["versions"]] == ["1", "2"]


def test_ons_data_get_observation_and_create_filter_errors(monkeypatch) -> None:
    from server import config
    from tools import ons_data

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)

    status, body = ons_data._get_observation({"geography": "K02000001", "measure": "GDPV", "time": "2024 Q1"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        ons_data,
        "_query",
        lambda payload: (200, {"results": []}),  # noqa: ARG005
        raising=True,
    )
    status, body = ons_data._get_observation(
        {
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "K02000001",
            "measure": "GDPV",
            "time": "2024 Q1",
        }
    )
    assert status == 404
    assert body["code"] == "NO_OBSERVATION"

    status, body = ons_data._create_filter({"dataset": "", "edition": "time-series", "version": "1"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_ons_data_get_filter_output_branches(monkeypatch, tmp_path) -> None:
    from tools import ons_data

    monkeypatch.setattr(ons_data, "_ONS_EXPORTS_DIR", tmp_path / "ons_exports", raising=True)
    monkeypatch.setattr(ons_data, "_FILTER_STORE", {"f0001": {"dataset": "gdp"}}, raising=True)
    monkeypatch.setattr(
        ons_data,
        "_query",
        lambda payload: (200, {"results": [{"time": "2024 Q1", "value": 1}], "live": True}),  # noqa: ARG005
        raising=True,
    )

    status, body = ons_data._get_filter_output({"filterId": "f0001", "delivery": "invalid"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = ons_data._get_filter_output({"filterId": "f0001", "inlineMaxBytes": 0})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = ons_data._get_filter_output({"filterId": "unknown"})
    assert status == 404
    assert body["code"] == "UNKNOWN_FILTER"

    status, body = ons_data._get_filter_output({"filterId": "f0001", "format": "XML"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    # Force JSON resource delivery branch.
    status, body = ons_data._get_filter_output(
        {"filterId": "f0001", "format": "JSON", "delivery": "auto", "inlineMaxBytes": 1}
    )
    assert status == 200
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/ons-exports/")

    # CSV inline branch.
    status, body = ons_data._get_filter_output({"filterId": "f0001", "format": "CSV", "delivery": "inline"})
    assert status == 200
    assert body["delivery"] == "inline"
    assert body["contentType"] == "text/csv"
    assert "dataBase64" in body

    # CSV resource branch.
    status, body = ons_data._get_filter_output({"filterId": "f0001", "format": "CSV", "delivery": "resource"})
    assert status == 200
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/ons-exports/")


def test_ons_data_helper_time_parsing_and_resolution(monkeypatch) -> None:
    from tools import ons_data

    assert ons_data._parse_time_token("2024") == 202412
    assert ons_data._parse_time_token("2024 Q1") == 202403
    assert ons_data._parse_time_token("2024-02") == 202402
    assert ons_data._parse_time_token("2024 Sep") == 202409
    assert ons_data._parse_time_token("Jan-24") == 202401
    assert ons_data._parse_time_token("not-a-time") is None

    assert ons_data._parse_range_bound("2024 Q3", is_end=False) == 202407
    assert ons_data._parse_range_bound("2024", is_end=True) == 202412
    assert ons_data._expand_range_end_token("2024 Q1", "Q2") == "2024 Q2"

    monkeypatch.setattr(
        ons_data,
        "_resolve_time_options",
        lambda *_args, **_kwargs: (["2024 Q1", "2024 Q2", "2024 Q3"], None),
        raising=True,
    )
    values, err = ons_data._resolve_time_values(
        "dataset",
        "edition",
        "version",
        start_text="2024 Q1",
        end_text="2024 Q2",
    )
    assert err is None
    assert values == ["2024 Q1", "2024 Q2"]

    monkeypatch.setattr(
        ons_data,
        "_resolve_time_options",
        lambda *_args, **_kwargs: (None, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    values, err = ons_data._resolve_time_values(
        "dataset",
        "edition",
        "version",
        start_text="2024 Q1",
        end_text="2024 Q2",
    )
    assert values is None
    assert err == {"isError": True, "code": "UPSTREAM"}


def test_ons_data_resolve_latest_version_and_option_helpers(monkeypatch) -> None:
    from tools import ons_data

    def fake_pages(url: str, params: dict[str, Any] | None = None):
        if url.endswith("/editions"):
            return 200, [{"edition": "time-series", "state": "published"}]
        if url.endswith("/versions"):
            return 200, [{"version": "1"}, {"version": "3", "state": "published"}]
        raise AssertionError(url)

    monkeypatch.setattr(ons_data.ons_client, "get_all_pages", fake_pages, raising=True)
    assert ons_data._resolve_latest_version("gdp") == ("time-series", "3")

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_all_pages",
        lambda *_args, **_kwargs: (500, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    status, body = ons_data._resolve_latest_version("gdp")  # type: ignore[misc]
    assert status == 500
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_all_pages",
        lambda *_args, **_kwargs: (200, {"bad": "shape"}),
        raising=True,
    )
    assert ons_data._resolve_latest_version("gdp") == (None, None)

    call_index = {"value": 0}

    def fake_options(url: str, params: dict[str, Any] | None = None):
        call_index["value"] += 1
        if call_index["value"] == 1:
            return 404, {"isError": True, "message": "missing"}
        if call_index["value"] == 2:
            return 200, {"bad": "shape"}
        return 200, [{"option": "2024 Q1"}]

    monkeypatch.setattr(ons_data.ons_client, "get_all_pages", fake_options, raising=True)
    options, err = ons_data._load_dimension_options(
        "dataset",
        "edition",
        "version",
        {"name": "time", "id": "time-id", "key": "time-key"},
    )
    assert options == ["2024 Q1"]
    assert err is None


def test_ons_data_resolve_time_options_error_paths(monkeypatch) -> None:
    from tools import ons_data

    monkeypatch.setattr(
        ons_data,
        "_load_version_metadata",
        lambda *_args, **_kwargs: (None, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    options, err = ons_data._resolve_time_options("dataset", "edition", "version")
    assert options is None
    assert err == {"isError": True, "code": "UPSTREAM"}

    monkeypatch.setattr(
        ons_data,
        "_load_version_metadata",
        lambda *_args, **_kwargs: (None, None),
        raising=True,
    )
    options, err = ons_data._resolve_time_options("dataset", "edition", "version")
    assert options is None
    assert err and err["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        ons_data,
        "_load_version_metadata",
        lambda *_args, **_kwargs: ({"dimensions": [{"name": "Date of measure", "id": "date-id"}]}, None),
        raising=True,
    )
    monkeypatch.setattr(
        ons_data,
        "_load_dimension_options",
        lambda *_args, **_kwargs: (None, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    options, err = ons_data._resolve_time_options("dataset", "edition", "version")
    assert options is None
    assert err and err["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_data,
        "_load_version_metadata",
        lambda *_args, **_kwargs: ({"dimensions": [{"name": "geography", "id": "geo"}]}, None),
        raising=True,
    )
    options, err = ons_data._resolve_time_options("dataset", "edition", "version")
    assert options is None
    assert err and err["code"] == "INVALID_INPUT"


def test_ons_data_fetch_observations_additional_branches(monkeypatch) -> None:
    from tools import ons_data

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_json",
        lambda *_args, **_kwargs: (500, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    status, body = ons_data._fetch_observations_paged(
        url="https://example.test/observations",
        filters={"time": "*"},
    )
    assert status == 500
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_json",
        lambda *_args, **_kwargs: (200, {"observations": "bad"}),
        raising=True,
    )
    status, body = ons_data._fetch_observations_paged(
        url="https://example.test/observations",
        filters={"time": "*"},
    )
    assert status == 500
    assert body["code"] == "INTEGRATION_ERROR"

    calls = {"count": 0}

    def fake_paging(url: str, params: dict[str, Any] | None = None):
        calls["count"] += 1
        if calls["count"] == 1:
            return 200, {"observations": [{"id": 1}, {"id": 2}], "total": 4}
        if calls["count"] == 2:
            return 200, {"observations": [{"id": 3}, {"id": 4}], "total": 4}
        return 200, {"observations": [{"id": 5}], "total": 5}

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_paging, raising=True)
    monkeypatch.setattr(ons_data, "_OBSERVATIONS_FETCH_PAGE_LIMIT", 2, raising=False)
    status, body = ons_data._fetch_observations_paged(
        url="https://example.test/observations",
        filters={"time": "*"},
    )
    assert status == 200
    assert [row["id"] for row in body["observations"]] == [3, 4, 5]


def test_ons_data_resolve_from_term_and_metadata(monkeypatch) -> None:
    from tools import ons_data

    def fake_search(url: str, params: dict[str, Any] | None = None):
        return 200, {"items": [{"id": "gdp", "links": {"latest_version": {"href": "/datasets/gdp/editions/time-series/versions/5"}}}]}

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_search, raising=True)
    dataset, edition, version, items = ons_data._resolve_from_term("gdp")  # type: ignore[misc]
    assert dataset == "gdp-to-four-decimal-places"
    assert edition == "time-series"
    assert version == "5"
    assert isinstance(items, list)

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_json",
        lambda *_args, **_kwargs: (200, {"items": []}),
        raising=True,
    )
    assert ons_data._resolve_from_term("missing") == (None, None, None, [])

    monkeypatch.setattr(
        ons_data.ons_client,
        "get_json",
        lambda *_args, **_kwargs: (503, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    status, body = ons_data._resolve_from_term("bad")  # type: ignore[misc]
    assert status == 503
    assert body["code"] == "UPSTREAM"


def test_ons_data_query_validation_and_retry_paths(monkeypatch) -> None:
    from server import config
    from tools import ons_data

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)

    status, body = ons_data._query(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "filters": []}
    )
    assert status == 400 and body["code"] == "INVALID_INPUT"

    status, body = ons_data._query({"dataset": "gdp", "edition": "time-series", "version": "1", "limit": 0})
    assert status == 400 and body["code"] == "INVALID_INPUT"

    status, body = ons_data._query({"dataset": "gdp", "edition": "time-series", "version": "1", "page": 0})
    assert status == 400 and body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        ons_data,
        "_resolve_from_term",
        lambda term: (503, {"isError": True, "code": "UPSTREAM"}),  # noqa: ARG005
        raising=True,
    )
    status, body = ons_data._query({"term": "gdp"})  # type: ignore[misc]
    assert status == 503
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_data,
        "_resolve_from_term",
        lambda term: ("gdp-to-four-decimal-places", None, None, []),  # noqa: ARG005
        raising=True,
    )
    status, body = ons_data._query({"term": "gdp"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        ons_data,
        "_resolve_latest_version",
        lambda dataset: ("time-series", "2"),  # noqa: ARG005
        raising=True,
    )

    state = {"calls": 0}

    def fake_metadata(dataset: str, edition: str, version: str):
        state["calls"] += 1
        if state["calls"] == 1:
            return None, {"isError": True, "message": "invalid version requested"}
        return {"dimensions": []}, None

    monkeypatch.setattr(ons_data, "_load_version_metadata", fake_metadata, raising=True)
    monkeypatch.setattr(
        ons_data.ons_client,
        "get_json",
        lambda *_args, **_kwargs: (200, {"observations": [{"value": 1}], "total": 1}),
        raising=True,
    )
    status, body = ons_data._query({"dataset": "gdp", "edition": "time-series", "version": "1"})
    assert status == 200
    assert body["dataset"] == "gdp-to-four-decimal-places"
    assert body["version"] == "2"
