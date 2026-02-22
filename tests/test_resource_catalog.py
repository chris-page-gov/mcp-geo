from __future__ import annotations

import base64
import json
from pathlib import Path

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


def test_ui_resources_include_maplibre_fallback_csp_domains() -> None:
    ui_resources = resource_catalog.list_ui_resources()
    by_uri = {entry["uri"]: entry for entry in ui_resources}
    for uri in (
        "ui://mcp-geo/geography-selector",
        "ui://mcp-geo/boundary-explorer",
    ):
        entry = by_uri[uri]
        meta = entry.get("_meta", {}).get("ui", {})
        csp = meta.get("csp", {})
        connect_domains = set(csp.get("connectDomains", []))
        resource_domains = set(csp.get("resourceDomains", []))
        assert "https://unpkg.com" in connect_domains
        assert "https://cdn.jsdelivr.net" in connect_domains
        assert "https://tile.openstreetmap.org" in connect_domains
        assert "https://unpkg.com" in resource_domains
        assert "https://cdn.jsdelivr.net" in resource_domains


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
    assert payload.get("maturity", {}).get("state") == "disabled"
    assert "staleness" in payload
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


def test_os_exports_index_and_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    exports_dir = tmp_path / "os_exports"
    exports_dir.mkdir()
    export_file = exports_dir / "sample.json"
    export_file.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", exports_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "os-exports-index"})
    payload = json.loads(content)
    assert payload["items"][0]["name"] == "sample.json"
    assert etag
    assert meta is not None

    content, etag, meta = resource_catalog.load_data_content({"slug": "os-exports/sample.json"})
    payload = json.loads(content)
    assert payload["ok"] is True
    assert etag
    assert meta is not None


def test_os_cache_index_and_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "os_cache"
    cache_dir.mkdir()
    cache_file = cache_dir / "cached.json"
    cache_file.write_text("{\"cached\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", cache_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "os-cache-index"})
    payload = json.loads(content)
    assert payload["items"][0]["name"] == "cached.json"
    assert etag
    assert meta is not None

    content, etag, meta = resource_catalog.load_data_content({"slug": "os-cache/cached.json"})
    payload = json.loads(content)
    assert payload["cached"] is True
    assert etag
    assert meta is None


def test_map_scenario_pack_index_and_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    packs_dir = tmp_path / "map_scenario_packs"
    packs_dir.mkdir()
    pack_file = packs_dir / "demo.json"
    pack_file.write_text('{"packId":"demo","scenarios":[]}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "MAP_SCENARIO_PACKS_DIR", packs_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "map-scenario-packs-index"})
    payload = json.loads(content)
    assert payload["items"][0]["name"] == "demo.json"
    assert etag
    assert meta is not None

    content, etag, meta = resource_catalog.load_data_content({"slug": "map-scenario-packs/demo.json"})
    payload = json.loads(content)
    assert payload["packId"] == "demo"
    assert etag
    assert meta is not None


def test_offline_pack_index_and_file(monkeypatch: MonkeyPatch, tmp_path) -> None:
    packs_dir = tmp_path / "offline_packs"
    packs_dir.mkdir()
    pack_file = packs_dir / "demo.pmtiles"
    pack_file.write_text("PMTILES", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", packs_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "offline-packs-index"})
    payload = json.loads(content)
    assert payload["items"][0]["name"] == "demo.pmtiles"
    assert etag
    assert meta is not None

    content, etag, meta = resource_catalog.load_data_content({"slug": "offline-packs/demo.pmtiles"})
    payload = json.loads(content)
    assert payload["encoding"] == "base64"
    assert payload["mediaType"] == "application/vnd.pmtiles"
    assert payload["downloadUrl"].startswith("/resources/download?uri=")
    assert b"PMTILES" in base64.b64decode(payload["blob"])
    assert etag
    assert meta is not None


def test_offline_pack_large_file_omits_inline_blob(monkeypatch: MonkeyPatch, tmp_path) -> None:
    packs_dir = tmp_path / "offline_packs"
    packs_dir.mkdir()
    pack_file = packs_dir / "large.pmtiles"
    pack_file.write_bytes(b"P" * (resource_catalog.OFFLINE_PACK_INLINE_MAX_BYTES + 1))
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", packs_dir)

    content, etag, meta = resource_catalog.load_data_content({"slug": "offline-packs/large.pmtiles"})
    payload = json.loads(content)
    assert payload["encoding"] == "external"
    assert payload["blobOmitted"] is True
    assert payload["inlineMaxBytes"] == resource_catalog.OFFLINE_PACK_INLINE_MAX_BYTES
    assert payload["downloadUrl"].startswith("/resources/download?uri=")
    assert "blob" not in payload
    assert etag
    assert meta is not None


def test_resolve_offline_pack_download(monkeypatch: MonkeyPatch, tmp_path) -> None:
    packs_dir = tmp_path / "offline_packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_file = packs_dir / "demo.pmtiles"
    pack_file.write_bytes(b"PMTILES")
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", packs_dir)
    resolved = resource_catalog.resolve_offline_pack_download(
        "resource://mcp-geo/offline-packs/demo.pmtiles"
    )
    assert resolved is not None
    path, media_type = resolved
    assert path == pack_file.resolve()
    assert media_type == "application/vnd.pmtiles"


def test_offline_pack_media_type_variants(tmp_path) -> None:
    assert resource_catalog._offline_pack_media_type(tmp_path / "demo.mbtiles") == "application/vnd.sqlite3"
    assert resource_catalog._offline_pack_media_type(tmp_path / "demo.bin") == "application/octet-stream"


def test_resolve_offline_pack_download_rejects_invalid(monkeypatch: MonkeyPatch, tmp_path) -> None:
    packs_dir = tmp_path / "offline_packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", packs_dir)

    assert resource_catalog.resolve_offline_pack_download("resource://mcp-geo/offline-packs/") is None
    assert resource_catalog.resolve_offline_pack_download("resource://mcp-geo/not-offline/demo.pmtiles") is None
    assert (
        resource_catalog.resolve_offline_pack_download(
            "resource://mcp-geo/offline-packs/../../etc/passwd"
        )
        is None
    )
    assert (
        resource_catalog.resolve_offline_pack_download(
            "resource://mcp-geo/offline-packs/missing.pmtiles"
        )
        is None
    )


def test_pack_file_helpers_missing_dirs(monkeypatch: MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", tmp_path / "missing-offline")
    monkeypatch.setattr(resource_catalog, "MAP_SCENARIO_PACKS_DIR", tmp_path / "missing-scenario")
    assert resource_catalog._offline_pack_files() == []
    assert resource_catalog._map_scenario_pack_files() == []


def test_load_data_content_unknown_slug_returns_not_found() -> None:
    content, etag, meta = resource_catalog.load_data_content({"slug": "does-not-exist"})
    payload = json.loads(content)
    assert payload.get("code") == "NOT_FOUND"
    assert etag
    assert meta is None


def test_os_file_helpers_missing_dirs(monkeypatch: MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", tmp_path / "missing-cache")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", tmp_path / "missing-exports")
    assert resource_catalog._os_cache_files() == []
    assert resource_catalog._os_export_files() == []


def test_list_data_resources_includes_os_cache_index(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "os_cache"
    cache_dir.mkdir()
    (cache_dir / "cached.json").write_text('{"ok":true}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", cache_dir)
    resources = resource_catalog.list_data_resources()
    uris = {entry.get("uri") for entry in resources if isinstance(entry, dict)}
    assert "resource://mcp-geo/os-cache-index" in uris


def test_resolve_data_resource_additional_os_prefixes() -> None:
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-cache-index") == {
        "slug": "os-cache-index"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-exports-index") == {
        "slug": "os-exports-index"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-cache/demo.json") == {
        "slug": "os-cache/demo.json"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-exports/demo.json") == {
        "slug": "os-exports/demo.json"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/map-scenario-packs-index") == {
        "slug": "map-scenario-packs-index"
    }
    assert resource_catalog.resolve_data_resource(
        "resource://mcp-geo/map-scenario-packs/demo.json"
    ) == {"slug": "map-scenario-packs/demo.json"}
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/offline-packs-index") == {
        "slug": "offline-packs-index"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/offline-packs/demo.pmtiles") == {
        "slug": "offline-packs/demo.pmtiles"
    }
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/ons-exports") is None
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-cache") is None
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/os-exports") is None
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/offline-packs") is None
    assert resource_catalog.resolve_data_resource("resource://mcp-geo/map-scenario-packs") is None


def test_load_data_content_missing_catalog_files(monkeypatch: MonkeyPatch, tmp_path) -> None:
    missing = tmp_path / "missing.json"
    cases: list[tuple[str, str]] = [
        ("OS_CATALOG_PATH", "os-catalog"),
        ("LAYERS_CATALOG_PATH", "layers-catalog"),
        ("OFFLINE_MAP_CATALOG_PATH", "offline-map-catalog"),
        ("MAP_EMBEDDING_STYLE_PROFILES_PATH", "map-embedding-style-profiles"),
        ("NOMIS_WORKFLOWS_PATH", "nomis-workflows"),
        ("BOUNDARY_PACK_SOURCES_PATH", "boundary-pack-sources"),
        ("CODE_LIST_PACK_SOURCES_PATH", "code-list-pack-sources"),
        ("BOUNDARY_PACKS_INDEX_PATH", "boundary-packs-index"),
        ("CODE_LIST_PACKS_INDEX_PATH", "code-list-packs-index"),
    ]
    for attr, slug in cases:
        monkeypatch.setattr(resource_catalog, attr, missing)
        content, etag, meta = resource_catalog.load_data_content({"slug": slug})
        payload = json.loads(content)
        assert payload.get("code") == "NOT_FOUND"
        assert etag
        assert meta is None


def test_load_data_content_path_traversal_guards(monkeypatch: MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", tmp_path / "ons_cache")
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", tmp_path / "ons_exports")
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", tmp_path / "os_cache")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", tmp_path / "os_exports")
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", tmp_path / "offline_packs")
    monkeypatch.setattr(resource_catalog, "MAP_SCENARIO_PACKS_DIR", tmp_path / "map_scenario_packs")
    monkeypatch.setattr(resource_catalog, "EXPORTS_DIR", tmp_path / "exports")

    # Ensure base directories exist for deterministic root resolution.
    Path(resource_catalog.ONS_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.ONS_EXPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.OS_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.OS_EXPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.OFFLINE_PACKS_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.MAP_SCENARIO_PACKS_DIR).mkdir(parents=True, exist_ok=True)
    Path(resource_catalog.EXPORTS_DIR).mkdir(parents=True, exist_ok=True)

    evil_ons_cache = tmp_path / "ons_cache_evil"
    evil_ons_cache.mkdir(parents=True, exist_ok=True)
    (evil_ons_cache / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")
    evil_ons_exports = tmp_path / "ons_exports_evil"
    evil_ons_exports.mkdir(parents=True, exist_ok=True)
    (evil_ons_exports / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")
    evil_os_cache = tmp_path / "os_cache_evil"
    evil_os_cache.mkdir(parents=True, exist_ok=True)
    (evil_os_cache / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")
    evil_os_exports = tmp_path / "os_exports_evil"
    evil_os_exports.mkdir(parents=True, exist_ok=True)
    (evil_os_exports / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")
    evil_offline = tmp_path / "offline_packs_evil"
    evil_offline.mkdir(parents=True, exist_ok=True)
    (evil_offline / "secret.pmtiles").write_text("SECRET", encoding="utf-8")
    evil_scenario = tmp_path / "map_scenario_packs_evil"
    evil_scenario.mkdir(parents=True, exist_ok=True)
    (evil_scenario / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")
    evil_exports = tmp_path / "exports_evil"
    evil_exports.mkdir(parents=True, exist_ok=True)
    (evil_exports / "secret.json").write_text("{\"secret\":true}", encoding="utf-8")

    content, _, _ = resource_catalog.load_data_content({"slug": "ons-cache/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "ons-cache/../ons_cache_evil/secret.json"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "ons-cache/%2e%2e%2fetc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "ons-exports/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "ons-exports/../ons_exports_evil/secret.json"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "ons-exports/..\\..\\etc\\passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "os-cache/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "os-cache/../os_cache_evil/secret.json"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "os-cache/%2e%2e%2fetc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "os-exports/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "os-exports/../os_exports_evil/secret.json"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "os-exports/..\\..\\etc\\passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "offline-packs/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content(
        {"slug": "offline-packs/../offline_packs_evil/secret.pmtiles"}
    )
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "map-scenario-packs/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content(
        {"slug": "map-scenario-packs/../map_scenario_packs_evil/secret.json"}
    )
    assert json.loads(content).get("code") == "INVALID_INPUT"

    content, _, _ = resource_catalog.load_data_content({"slug": "exports/../../etc/passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "exports/../exports_evil/secret.json"})
    assert json.loads(content).get("code") == "INVALID_INPUT"
    content, _, _ = resource_catalog.load_data_content({"slug": "exports/..\\..\\etc\\passwd"})
    assert json.loads(content).get("code") == "INVALID_INPUT"


def test_load_data_content_not_found_export_and_cache_files(
    monkeypatch: MonkeyPatch, tmp_path
) -> None:
    ons_exports = tmp_path / "ons_exports"
    os_cache = tmp_path / "os_cache"
    os_exports = tmp_path / "os_exports"
    offline_packs = tmp_path / "offline_packs"
    scenario_packs = tmp_path / "map_scenario_packs"
    exports = tmp_path / "exports"
    ons_exports.mkdir()
    os_cache.mkdir()
    os_exports.mkdir()
    offline_packs.mkdir()
    scenario_packs.mkdir()
    exports.mkdir()

    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", ons_exports)
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", os_cache)
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports)
    monkeypatch.setattr(resource_catalog, "OFFLINE_PACKS_DIR", offline_packs)
    monkeypatch.setattr(resource_catalog, "MAP_SCENARIO_PACKS_DIR", scenario_packs)
    monkeypatch.setattr(resource_catalog, "EXPORTS_DIR", exports)

    content, _, _ = resource_catalog.load_data_content({"slug": "ons-exports/missing.json"})
    assert json.loads(content).get("code") == "NOT_FOUND"

    content, _, _ = resource_catalog.load_data_content({"slug": "os-cache/missing.json"})
    assert json.loads(content).get("code") == "NOT_FOUND"

    content, _, _ = resource_catalog.load_data_content({"slug": "os-exports/missing.json"})
    assert json.loads(content).get("code") == "NOT_FOUND"

    content, _, _ = resource_catalog.load_data_content({"slug": "offline-packs/missing.pmtiles"})
    assert json.loads(content).get("code") == "NOT_FOUND"

    content, _, _ = resource_catalog.load_data_content({"slug": "map-scenario-packs/missing.json"})
    assert json.loads(content).get("code") == "NOT_FOUND"

    content, _, _ = resource_catalog.load_data_content({"slug": "exports/missing.json"})
    assert json.loads(content).get("code") == "NOT_FOUND"


def test_resource_catalog_path_and_download_helpers(tmp_path) -> None:
    assert resource_catalog._is_path_within(tmp_path / "inside", tmp_path) is True
    assert resource_catalog._is_path_within(tmp_path / "outside", tmp_path / "other") is False
    assert resource_catalog._has_disallowed_path_tokens("") is True
    assert resource_catalog._has_disallowed_path_tokens("/tmp/demo.json") is True
    assert resource_catalog._offline_pack_media_type(tmp_path / "demo.pmtiles") == "application/vnd.pmtiles"
    assert resource_catalog._offline_pack_download_url(
        "resource://mcp-geo/offline-packs/demo.pmtiles"
    ).startswith("/resources/download?uri=")
    assert resource_catalog._resolve_scoped_path(tmp_path, "../escape.json") is None


def test_list_data_resources_dynamic_indexes(monkeypatch: MonkeyPatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    report_dir = runs_dir / "20260101T000000Z"
    report_dir.mkdir(parents=True)
    (report_dir / "run_report.json").write_text("{\"ok\":true}", encoding="utf-8")
    ons_cache = tmp_path / "ons_cache"
    ons_cache.mkdir()
    (ons_cache / "demo.json").write_text("{\"ok\":true}", encoding="utf-8")
    ons_exports = tmp_path / "ons_exports"
    ons_exports.mkdir()
    (ons_exports / "demo.json").write_text("{\"ok\":true}", encoding="utf-8")
    os_cache = tmp_path / "os_cache"
    os_cache.mkdir()
    (os_cache / "demo.json").write_text("{\"ok\":true}", encoding="utf-8")
    os_exports = tmp_path / "os_exports"
    os_exports.mkdir()
    (os_exports / "demo.json").write_text("{\"ok\":true}", encoding="utf-8")

    monkeypatch.setattr(resource_catalog, "BOUNDARY_RUNS_DIR", runs_dir)
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", ons_cache)
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", ons_exports)
    monkeypatch.setattr(resource_catalog, "OS_CACHE_DIR", os_cache)
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports)

    resources = resource_catalog.list_data_resources()
    uris = {entry["uri"] for entry in resources}
    assert "resource://mcp-geo/boundary-latest-report" in uris
    assert "resource://mcp-geo/ons-cache-index" in uris
    assert "resource://mcp-geo/ons-cache/demo.json" in uris
    assert "resource://mcp-geo/ons-exports-index" in uris
    assert "resource://mcp-geo/os-cache-index" in uris
    assert "resource://mcp-geo/os-exports-index" in uris


def test_resolve_helpers_and_content_loaders() -> None:
    ui_entry = resource_catalog.resolve_ui_resource("ui://mcp-geo/geography-selector")
    assert ui_entry is not None
    assert resource_catalog.resolve_ui_resource("ui://mcp-geo/unknown") is None
    skill_entry = resource_catalog.resolve_skill_resource("skills://mcp-geo/getting-started")
    assert skill_entry is not None
    assert resource_catalog.resolve_skill_resource("skills://mcp-geo/unknown") is None
    ui_content, ui_etag = resource_catalog.load_ui_content(ui_entry)
    assert "html" in ui_content.lower()
    assert ui_etag.startswith('W/"')
    skill_content, skill_etag = resource_catalog.load_skill_content()
    assert "MCP Geo Skills" in skill_content
    assert skill_etag.startswith('W/"')

    assert resource_catalog.resolve_data_resource("boundary-manifest") == {
        **resource_catalog.DATA_RESOURCE_DEFS[0],
        "slug": "boundary-manifest",
    }
    assert resource_catalog.resolve_data_resource("boundary-cache-status") == {"slug": "boundary-cache-status"}
    assert resource_catalog.resolve_data_resource("ons-exports-index") == {"slug": "ons-exports-index"}
    assert resource_catalog.resolve_data_resource("exports/demo.json") == {"slug": "exports/demo.json"}
    assert resource_catalog.resolve_data_resource("ons-exports/demo.json") == {
        "slug": "ons-exports/demo.json"
    }


def test_load_data_content_present_catalog_branches(monkeypatch: MonkeyPatch, tmp_path) -> None:
    present = tmp_path / "present.json"
    present.write_text("{\"ok\":true}", encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "BOUNDARY_MANIFEST_PATH", present)
    monkeypatch.setattr(resource_catalog, "OS_CATALOG_PATH", present)
    monkeypatch.setattr(resource_catalog, "LAYERS_CATALOG_PATH", present)
    monkeypatch.setattr(resource_catalog, "OFFLINE_MAP_CATALOG_PATH", present)
    monkeypatch.setattr(resource_catalog, "BOUNDARY_PACK_SOURCES_PATH", present)
    monkeypatch.setattr(resource_catalog, "CODE_LIST_PACK_SOURCES_PATH", present)
    monkeypatch.setattr(resource_catalog, "BOUNDARY_PACKS_INDEX_PATH", present)
    monkeypatch.setattr(resource_catalog, "CODE_LIST_PACKS_INDEX_PATH", present)

    for slug in (
        "boundary-manifest",
        "os-catalog",
        "layers-catalog",
        "offline-map-catalog",
        "boundary-pack-sources",
        "code-list-pack-sources",
        "boundary-packs-index",
        "code-list-packs-index",
    ):
        content, etag, meta = resource_catalog.load_data_content({"slug": slug})
        assert json.loads(content)["ok"] is True
        assert etag
        assert meta is None


def test_load_data_content_boundary_cache_status_enabled_branch(monkeypatch: MonkeyPatch) -> None:
    import server.boundary_cache as boundary_cache

    class _Cache:
        def status(self):
            return {"fresh": True}

    monkeypatch.setattr(boundary_cache, "get_boundary_cache", lambda: _Cache())
    monkeypatch.setattr(resource_catalog.settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(resource_catalog.settings, "BOUNDARY_CACHE_DSN", "postgresql://test", raising=False)
    content, etag, meta = resource_catalog.load_data_content({"slug": "boundary-cache-status"})
    payload = json.loads(content)
    assert payload["enabled"] is True
    assert payload["configured"] is True
    assert payload["dsnSet"] is True
    assert payload["reloadHint"]
    assert etag
    assert meta is not None and meta.get("generatedAt")


def test_ons_cache_fallback_slug_rejects_invalid_path(monkeypatch: MonkeyPatch, tmp_path) -> None:
    cache_dir = tmp_path / "ons"
    cache_dir.mkdir()
    monkeypatch.setattr(resource_catalog, "ONS_CACHE_DIR", cache_dir)
    content, _, _ = resource_catalog.load_data_content({"slug": "ons-cache..%2fetc/passwd"})
    payload = json.loads(content)
    assert payload.get("code") == "INVALID_INPUT"


def test_resolve_scoped_path_rejects_symlink_escape(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "secret.json"
    target.write_text("{\"secret\":true}", encoding="utf-8")
    link = root / "link"
    link.symlink_to(outside, target_is_directory=True)
    assert resource_catalog._resolve_scoped_path(root, "link/secret.json") is None
