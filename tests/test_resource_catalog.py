from __future__ import annotations

import json

from _pytest.monkeypatch import MonkeyPatch

from server.mcp import resource_catalog


def test_boundary_latest_report_missing(monkeypatch: MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(resource_catalog, "BOUNDARY_RUNS_DIR", tmp_path)
    entry = resource_catalog.resolve_data_resource("boundary-latest-report")
    assert entry is not None
    content, etag, meta = resource_catalog.load_data_content(entry)
    payload = json.loads(content)
    assert payload.get("code") == "NOT_FOUND"
    assert etag
    assert meta is None


def test_boundary_latest_report_present(monkeypatch: MonkeyPatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    report_dir = runs_dir / "20260101T000000Z"
    report_dir.mkdir(parents=True)
    report_path = report_dir / "run_report.json"
    report_path.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "BOUNDARY_RUNS_DIR", runs_dir)
    entry = resource_catalog.resolve_data_resource("boundary-latest-report")
    assert entry is not None
    content, etag, meta = resource_catalog.load_data_content(entry)
    payload = json.loads(content)
    assert payload.get("ok") is True
    assert etag
    assert meta is not None


def test_ons_cache_index_and_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "ons"
    cache_dir.mkdir()
    cache_file = cache_dir / "demo.json"
    cache_file.write_text("{\"ok\":true}", encoding="utf-8")

    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", cache_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-cache-index"})
    payload = json.loads(content)
    assert payload["items"][0]["name"] == "demo.json"
    assert etag
    assert meta is not None

    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-cache/demo.json"})
    payload = json.loads(content)
    assert payload["ok"] is True
    assert etag


def test_ons_cache_missing_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "ons"
    cache_dir.mkdir()
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", cache_dir)
    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-cache/missing.json"})
    payload = json.loads(content)
    assert payload.get("code") == "NOT_FOUND"
    assert etag
    assert meta is None


def test_list_data_resources_skips_missing_manifest(monkeypatch: MonkeyPatch, tmp_path) -> None:
    missing_manifest = tmp_path / "missing.json"
    monkeypatch.setattr(
        resource_catalog,
        "DATA_RESOURCE_DEFS",
        [
            {
                "slug": "boundary-manifest",
                "name": "data_boundary_manifest",
                "title": "Boundary Manifest",
                "description": "Boundary dataset manifest driving the ingestion pipeline.",
                "path": missing_manifest,
                "mimeType": "application/json",
                "annotations": {"type": "dataset", "domain": "boundaries"},
            }
        ],
    )
    resources = resource_catalog.list_data_resources()
    uris = {entry.get("uri") for entry in resources if isinstance(entry, dict)}
    assert resource_catalog.data_resource_uri("boundary-manifest") not in uris


def test_resolve_ons_cache_resources(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "ons"
    cache_dir.mkdir()
    cache_file = cache_dir / "demo.json"
    cache_file.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", cache_dir)
    entry = resource_catalog.resolve_data_resource("resource://mcp-geo/ons-cache-index")
    assert entry is not None and entry.get("slug") == "ons-cache-index"
    entry = resource_catalog.resolve_data_resource("resource://mcp-geo/ons-cache/demo.json")
    assert entry is not None and "ons-cache" in entry.get("slug", "")


def test_build_ui_meta_includes_widget_domain(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        resource_catalog.settings,
        "OPENAI_WIDGET_DOMAIN",
        "widgets.example",
        raising=False,
    )
    meta = resource_catalog._build_ui_meta(
        "Example widget",
        {"connectDomains": ["self"]},
        {"sameOrigin": True},
    )
    assert meta["ui"]["domain"] == "widgets.example"
    assert meta["openai/widgetDomain"] == "widgets.example"
    assert meta["openai/widgetCSP"]["connect_domains"] == ["self"]


def test_latest_run_report_path_missing_dir(monkeypatch: MonkeyPatch, tmp_path) -> None:
    missing_dir = tmp_path / "missing"
    monkeypatch.setattr(resource_catalog, "BOUNDARY_RUNS_DIR", missing_dir)
    assert resource_catalog._latest_run_report_path() is None


def test_ons_cache_files_missing_dir(monkeypatch: MonkeyPatch, tmp_path) -> None:
    missing_dir = tmp_path / "missing-cache"
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", missing_dir)
    assert resource_catalog._ons_cache_files() == []


def test_ons_catalog_missing_and_present(monkeypatch: MonkeyPatch, tmp_path) -> None:
    missing = tmp_path / "ons_catalog.json"
    monkeypatch.setattr(resource_catalog, "ONS_CATALOG_PATH", missing)
    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-catalog"})
    payload = json.loads(content)
    assert payload.get("code") == "NOT_FOUND"
    assert etag
    assert meta is None

    present = tmp_path / "ons_catalog_present.json"
    present.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "ONS_CATALOG_PATH", present)
    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-catalog"})
    payload = json.loads(content)
    assert payload.get("ok") is True
    assert etag
    assert meta is None


def test_boundary_cache_status_handles_exception(monkeypatch: MonkeyPatch) -> None:
    import server.boundary_cache as boundary_cache

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(boundary_cache, "get_boundary_cache", _boom)
    content, etag, meta = resource_catalog.load_data_content({"slug": "boundary-cache-status"})
    payload = json.loads(content)
    assert payload.get("enabled") is False
    assert payload.get("configured") is False
    assert payload.get("dsnSet") is False
    assert payload.get("reloadHint")
    assert etag
    assert meta is not None and meta.get("generatedAt")


def test_ons_cache_slug_without_slash(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "ons"
    cache_dir.mkdir()
    cache_file = cache_dir / "foo.json"
    cache_file.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", cache_dir)
    content, etag, meta = resource_catalog.load_data_content({"slug": "ons-cachefoo.json"})
    payload = json.loads(content)
    assert payload.get("ok") is True
    assert etag
    assert meta is None


def test_load_data_content_unknown_slug_returns_not_found() -> None:
    content, etag, meta = resource_catalog.load_data_content({"slug": "does-not-exist"})
    payload = json.loads(content)
    assert payload.get("code") == "NOT_FOUND"
    assert etag
    assert meta is None
