from __future__ import annotations

from typing import Any


def test_ons_codes_require_live_and_input_validation(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False, raising=False)
    status, body = ons_codes._require_live("dataset", "edition", "version")  # type: ignore[misc]
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    status, body = ons_codes._require_live("dataset", None, "version")  # type: ignore[misc]
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    assert ons_codes._require_live("dataset", "edition", "version") is None


def test_ons_codes_normalization_and_helpers() -> None:
    from tools import ons_codes

    assert ons_codes._normalize_dataset_id(" gdp ") == "gdp-to-four-decimal-places"
    assert ons_codes._normalize_dataset_id("custom-dataset") == "custom-dataset"
    assert ons_codes._normalize_dataset_id("   ") == ""
    assert ons_codes._is_stale_version_error({"message": "Invalid version requested"}) is True
    assert ons_codes._is_stale_version_error({"message": "upstream timeout"}) is False

    assert ons_codes._pick_latest([], "edition") is None
    assert ons_codes._pick_latest([{"version": 1}], "version") == "1"
    assert ons_codes._pick_latest([{"edition": "v1"}, {"edition": "v2"}], "edition") == "v1"
    assert (
        ons_codes._pick_latest(
            [{"version": "1", "state": "draft"}, {"version": "3", "state": "published"}],
            "version",
        )
        == "3"
    )


def test_ons_codes_helper_empty_inputs_and_alias_error_passthrough(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    assert ons_codes._extract_dim_ids({"dimensions": "bad-shape"}) == []
    assert ons_codes._extract_dim_entries({"dimensions": "bad-shape"}) == []
    assert (
        ons_codes._find_dimension([{"key": "time", "name": "time", "id": "t"}], "   ")
        is None
    )

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: None, raising=True)
    monkeypatch.setattr(
        ons_codes,
        "_resolve_latest_version",
        lambda dataset: (503, {"isError": True, "code": "UPSTREAM"}),  # noqa: ARG005
        raising=True,
    )
    status, body = ons_codes._list({"dataset": "gdp", "edition": " ", "version": " "})  # type: ignore[misc]
    assert status == 503
    assert body["code"] == "UPSTREAM"


def test_ons_codes_dimension_and_code_extractors() -> None:
    from tools import ons_codes

    meta = {
        "dimensions": [
            {"name": "time", "id": "time-id"},
            {"id": "geography-id"},
            {"name": "measure"},
            "ignore-me",
        ]
    }
    assert ons_codes._extract_dim_ids(meta) == ["time", "geography-id", "measure"]

    entries = ons_codes._extract_dim_entries(
        {
            "dimensions": [
                {"name": "time", "id": "t"},
                {"id": "geo"},
                {"name": ""},
                {"id": ""},
                "invalid",
            ]
        }
    )
    assert entries == [{"key": "time", "name": "time", "id": "t"}, {"key": "geo", "name": "", "id": "geo"}]
    assert ons_codes._find_dimension(entries, "TIME") == {"key": "time", "name": "time", "id": "t"}
    assert ons_codes._find_dimension(entries, "missing") is None

    assert ons_codes._extract_codes({"items": [{"option": "A"}, {"id": "B"}, {"links": {"code": {"id": "C"}}}]}) == ["A", "B", "C"]
    assert ons_codes._extract_codes({"options": [{"value": "D"}]}) == ["D"]
    assert ons_codes._extract_codes({"results": [{"code": "E"}]}) == ["E"]
    assert ons_codes._extract_codes({"items": "bad"}) == []


def test_ons_codes_resolve_latest_version_paths(monkeypatch) -> None:
    from tools import ons_codes

    def fake_get_all_pages(url: str, params: dict[str, Any] | None = None):
        if url.endswith("/editions"):
            return 200, [{"edition": "time-series", "state": "published"}]
        if url.endswith("/versions"):
            return 200, [{"version": "1"}, {"version": "2", "state": "published"}]
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_get_all_pages, raising=True)
    assert ons_codes._resolve_latest_version("dataset-id") == ("time-series", "2")

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda *_args, **_kwargs: (503, {"isError": True, "message": "upstream"}),
        raising=True,
    )
    status, body = ons_codes._resolve_latest_version("dataset-id")  # type: ignore[misc]
    assert status == 503
    assert body["isError"] is True


def test_ons_codes_resolve_latest_version_edge_cases(monkeypatch) -> None:
    from tools import ons_codes

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda *_args, **_kwargs: (200, {"not": "a-list"}),
        raising=True,
    )
    assert ons_codes._resolve_latest_version("dataset-id") == (None, None)

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda url, params=None: (200, [{}]) if url.endswith("/editions") else (200, []),
        raising=True,
    )
    assert ons_codes._resolve_latest_version("dataset-id") == (None, None)

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda url, params=None: (
            (200, [{"edition": "time-series"}])
            if url.endswith("/editions")
            else (503, {"isError": True, "code": "UPSTREAM"})
        ),
        raising=True,
    )
    status, body = ons_codes._resolve_latest_version("dataset-id")  # type: ignore[misc]
    assert status == 503
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda url, params=None: (
            (200, [{"edition": "time-series"}]) if url.endswith("/editions") else (200, {"bad": True})
        ),
        raising=True,
    )
    assert ons_codes._resolve_latest_version("dataset-id") == ("time-series", None)


def test_ons_codes_load_dimension_options_paths(monkeypatch) -> None:
    from tools import ons_codes

    calls: list[str] = []

    def fake_get_all_pages(url: str, params: dict[str, Any] | None = None):
        calls.append(url)
        if "/dimensions/time/options" in url:
            return 404, {"isError": True, "message": "not found"}
        if "/dimensions/time-id/options" in url:
            return 200, {"unexpected": "shape"}
        if "/dimensions/time-key/options" in url:
            return 200, [{"id": "2024 Q1"}]
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_get_all_pages, raising=True)
    options, err = ons_codes._load_dimension_options(
        "dataset",
        "edition",
        "version",
        {"name": "time", "id": "time-id", "key": "time-key"},
    )
    assert options == ["2024 Q1"]
    assert err is None
    assert len(calls) == 3

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_all_pages",
        lambda *_args, **_kwargs: (404, {"isError": True, "message": "missing"}),
        raising=True,
    )
    options, err = ons_codes._load_dimension_options(
        "dataset",
        "edition",
        "version",
        {"name": "time", "id": "time-id", "key": "time-key"},
    )
    assert options == []
    assert err == {"isError": True, "message": "missing"}

    calls.clear()

    def fake_duplicate(url: str, params: dict[str, Any] | None = None):
        calls.append(url)
        return 200, []

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_duplicate, raising=True)
    options, err = ons_codes._load_dimension_options(
        "dataset",
        "edition",
        "version",
        {"name": None, "id": "time", "key": "time"},
    )
    assert options == []
    assert err is None
    assert len(calls) == 1


def test_ons_codes_list_cache_hit(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    class FakeCache:
        def read(self, key: str) -> dict[str, Any] | None:
            expected = "ons_codes:dimensions:gdp-to-four-decimal-places:time-series:1"
            assert key == expected
            return {"dimensions": ["time", "geography"]}

        def write(self, key: str, data: dict[str, Any]) -> None:  # pragma: no cover - should not be called
            raise AssertionError((key, data))

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: FakeCache(), raising=True)
    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("get_json should not be called")),
        raising=True,
    )

    status, body = ons_codes._list(
        {"dataset": "gdp", "edition": "time-series", "version": "1"}
    )
    assert status == 200
    assert body["cached"] is True
    assert body["dimensions"] == ["time", "geography"]


def test_ons_codes_list_retries_stale_alias_version(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: None, raising=True)
    monkeypatch.setattr(
        ons_codes,
        "_resolve_latest_version",
        lambda dataset: ("time-series", "2"),
        raising=True,
    )

    calls: list[str] = []

    def fake_get_json(url: str, params: dict[str, Any] | None = None):
        calls.append(url)
        if url.endswith("/versions/1"):
            return 404, {"isError": True, "message": "invalid version requested"}
        if url.endswith("/versions/2"):
            return 200, {"dimensions": [{"id": "time"}, {"name": "geography"}]}
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_get_json, raising=True)
    status, body = ons_codes._list(
        {"dataset": "gdp", "edition": "time-series", "version": "1"}
    )
    assert status == 200
    assert body["dimensions"] == ["time", "geography"]
    assert len(calls) == 2


def test_ons_codes_list_live_disabled_and_alias_resolution(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False, raising=False)
    status, body = ons_codes._list({"dataset": "gdp", "edition": "time-series", "version": "1"})
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: None, raising=True)
    monkeypatch.setattr(
        ons_codes,
        "_resolve_latest_version",
        lambda dataset: ("time-series", "7"),
        raising=True,
    )

    seen_urls: list[str] = []

    def fake_get_json(url: str, params: dict[str, Any] | None = None):
        seen_urls.append(url)
        return 200, {"dimensions": [{"id": "time"}]}

    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_get_json, raising=True)
    status, body = ons_codes._list({"dataset": "gdp", "edition": " ", "version": " "})
    assert status == 200
    assert body["dimensions"] == ["time"]
    assert any("/versions/7" in url for url in seen_urls)

    monkeypatch.setattr(
        ons_codes._CLIENT,
        "get_json",
        lambda *_args, **_kwargs: (404, {"message": "invalid version requested"}),
        raising=True,
    )
    monkeypatch.setattr(
        ons_codes,
        "_resolve_latest_version",
        lambda dataset: (504, {"isError": True, "code": "UPSTREAM"}),
        raising=True,
    )
    status, body = ons_codes._list({"dataset": "gdp", "edition": "time-series", "version": "1"})  # type: ignore[misc]
    assert status == 504
    assert body["code"] == "UPSTREAM"


def test_ons_codes_options_paths(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: None, raising=True)

    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": ""}
    )
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    def fake_direct(url: str, params: dict[str, Any] | None = None):
        if "/dimensions/time/options" in url:
            return 200, [{"option": "2024 Q1"}, {"links": {"code": {"id": "2024 Q2"}}}]
        return 500, {"isError": True, "message": "unexpected"}

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_direct, raising=True)
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"}
    )
    assert status == 200
    assert body["options"] == ["2024 Q1", "2024 Q2"]

    def fake_fallback(url: str, params: dict[str, Any] | None = None):
        if "/dimensions/" in url and url.endswith("/options"):
            return 404, {"isError": True, "message": "forbidden"}
        if url.endswith("/versions/1"):
            return 200, {"dimensions": [{"name": "time", "id": "time-id"}]}
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_fallback, raising=True)
    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_fallback, raising=True)
    monkeypatch.setattr(
        ons_codes,
        "_load_dimension_options",
        lambda *_args, **_kwargs: (None, {"isError": True, "code": "UPSTREAM", "message": "bad"}),
        raising=True,
    )
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"}
    )
    assert status == 400
    assert body["code"] == "UPSTREAM"

    monkeypatch.setattr(
        ons_codes,
        "_load_dimension_options",
        lambda *_args, **_kwargs: (["2024 Q1"], None),
        raising=True,
    )
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "unknown"}
    )
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_ons_codes_options_stale_retry_paths(monkeypatch) -> None:
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", False, raising=False)
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"}
    )
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"

    monkeypatch.setattr(config.settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(ons_codes, "_dataset_cache", lambda: None, raising=True)

    calls: list[str] = []

    def fake_retry(url: str, params: dict[str, Any] | None = None):
        calls.append(url)
        if "/versions/1/dimensions/time/options" in url:
            return 404, {"isError": True, "message": "invalid version requested"}
        if "/versions/2/dimensions/time/options" in url:
            return 200, [{"id": "2024 Q1"}]
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_retry, raising=True)
    monkeypatch.setattr(
        ons_codes,
        "_resolve_latest_version",
        lambda dataset: ("time-series", "2"),
        raising=True,
    )
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"}
    )
    assert status == 200
    assert body["options"] == ["2024 Q1"]
    assert any("/versions/1/" in url for url in calls)
    assert any("/versions/2/" in url for url in calls)

    def fake_meta(url: str, params: dict[str, Any] | None = None):
        if "/dimensions/time/options" in url:
            return 404, {"isError": True, "message": "forbidden"}
        if url.endswith("/versions/1"):
            return 404, {"isError": True, "message": "invalid version requested"}
        if url.endswith("/versions/2"):
            return 503, {"isError": True, "code": "UPSTREAM"}
        raise AssertionError(url)

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_meta, raising=True)
    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_meta, raising=True)
    status, body = ons_codes._options(
        {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"}
    )
    assert status == 503
    assert body["code"] == "UPSTREAM"
