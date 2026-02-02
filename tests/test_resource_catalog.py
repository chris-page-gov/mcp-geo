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
