from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from server.main import app
from tests.helpers import resource_contents


client = TestClient(app)


def test_resources_list_includes_data_catalog_entries() -> None:
    resp = client.get("/resources/list", params={"limit": 200, "page": 1})
    assert resp.status_code == 200
    resources = resp.json().get("resources", [])
    uris = {entry.get("uri") for entry in resources if isinstance(entry, dict)}
    assert "resource://mcp-geo/boundary-manifest" in uris
    assert "resource://mcp-geo/boundary-cache-status" in uris
    assert "resource://mcp-geo/ons-catalog" in uris
    assert "resource://mcp-geo/os-catalog" in uris
    assert "resource://mcp-geo/layers-catalog" in uris
    assert "resource://mcp-geo/protected-landscapes-england" in uris
    assert "resource://mcp-geo/offline-map-catalog" in uris
    assert "resource://mcp-geo/map-embedding-style-profiles" in uris
    assert "resource://mcp-geo/boundary-pack-sources" in uris
    assert "resource://mcp-geo/code-list-pack-sources" in uris
    assert "resource://mcp-geo/boundary-packs-index" in uris
    assert "resource://mcp-geo/code-list-packs-index" in uris
    assert "resource://mcp-geo/map-scenario-packs-index" in uris
    assert "resource://mcp-geo/offline-packs-index" in uris


def test_resources_read_boundary_manifest() -> None:
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/boundary-manifest"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"] == "application/json"
    payload = json.loads(contents[0]["text"])
    assert "manifest_version" in payload
    assert "boundary_families" in payload


def test_resources_read_map_embedding_style_profiles() -> None:
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/map-embedding-style-profiles"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    payload = json.loads(contents[0]["text"])
    profiles = payload.get("profiles", [])
    assert any(row.get("id") == "compact_static" for row in profiles if isinstance(row, dict))


def test_resources_read_simple_map_lab_ui() -> None:
    resp = client.get("/resources/read", params={"uri": "ui://mcp-geo/simple-map-lab"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"].startswith("text/html")
    assert "Simple Map Lab" in contents[0]["text"]


def test_ui_route_renders_simple_map_lab_html() -> None:
    resp = client.get("/ui/simple-map-lab")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert resp.headers.get("cache-control") == "no-store, max-age=0"
    assert "Simple Map Lab" in resp.text
    assert 'select id="osStyle"' in resp.text
    assert 'value="OS_VTS_3857_Light.json"' in resp.text
    assert 'value="OS_VTS_3857_Open_Road.json"' in resp.text


def test_simple_map_lab_short_route_redirects() -> None:
    resp = client.get("/simple-map-lab", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/ui/simple-map-lab"


def test_resources_read_boundary_cache_status() -> None:
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/boundary-cache-status"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    payload = json.loads(contents[0]["text"])
    assert "enabled" in payload
    assert "performance" in payload
    assert "reloadHint" in payload


def test_resources_read_boundary_manifest_by_name() -> None:
    resp = client.get("/resources/read", params={"name": "data_boundary_manifest"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    payload = json.loads(contents[0]["text"])
    assert "manifest_version" in payload


def test_resources_read_pack_indexes() -> None:
    boundary_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/boundary-packs-index"})
    assert boundary_resp.status_code == 200
    boundary_payload = json.loads(resource_contents(boundary_resp)[0]["text"])
    assert boundary_payload["kind"] == "boundary"
    assert boundary_payload["cacheMode"] == "hybrid_fetch_cache"
    assert isinstance(boundary_payload.get("packs"), list)

    code_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/code-list-packs-index"})
    assert code_resp.status_code == 200
    code_payload = json.loads(resource_contents(code_resp)[0]["text"])
    assert code_payload["kind"] == "code_lists"
    assert code_payload["cacheMode"] == "hybrid_fetch_cache"
    assert isinstance(code_payload.get("packs"), list)


def test_resources_read_map_scenario_pack_index_and_file() -> None:
    index_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/map-scenario-packs-index"})
    assert index_resp.status_code == 200
    index_payload = json.loads(resource_contents(index_resp)[0]["text"])
    items = index_payload.get("items", [])
    assert any(item.get("name") == "map_delivery_option_tracker.sample.json" for item in items if isinstance(item, dict))

    read_resp = client.get(
        "/resources/read",
        params={"uri": "resource://mcp-geo/map-scenario-packs/map_delivery_option_tracker.sample.json"},
    )
    assert read_resp.status_code == 200
    payload = json.loads(resource_contents(read_resp)[0]["text"])
    assert payload["packId"] == "map_delivery_option_tracker.sample"


def test_resources_read_offline_pack_index_and_file() -> None:
    index_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/offline-packs-index"})
    assert index_resp.status_code == 200
    index_payload = json.loads(resource_contents(index_resp)[0]["text"])
    items = index_payload.get("items", [])
    assert any(item.get("name") == "gb_basemap_light_pmtiles.pmtiles" for item in items if isinstance(item, dict))

    read_resp = client.get(
        "/resources/read",
        params={"uri": "resource://mcp-geo/offline-packs/gb_basemap_light_pmtiles.pmtiles"},
    )
    assert read_resp.status_code == 200
    payload = json.loads(resource_contents(read_resp)[0]["text"])
    assert payload["encoding"] == "base64"
    assert payload["mediaType"] == "application/vnd.pmtiles"
    blob = base64.b64decode(payload["blob"])
    assert b"PMTILES_PLACEHOLDER" in blob


def test_resources_download_offline_pack_file() -> None:
    resp = client.get(
        "/resources/download",
        params={"uri": "resource://mcp-geo/offline-packs/gb_basemap_light_pmtiles.pmtiles"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/vnd.pmtiles")
    assert b"PMTILES_PLACEHOLDER" in resp.content


def test_resources_list_includes_ons_exports_index_when_present(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog

    exports_dir = tmp_path / "ons_exports"
    exports_dir.mkdir()
    (exports_dir / "sample-export.json").write_text('{"ok":true}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", exports_dir)

    resp = client.get("/resources/list", params={"limit": 300, "page": 1})
    assert resp.status_code == 200
    uris = {entry.get("uri") for entry in resp.json().get("resources", []) if isinstance(entry, dict)}
    assert "resource://mcp-geo/ons-exports-index" in uris


def test_resources_read_ons_exports_index_and_file(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog

    exports_dir = tmp_path / "ons_exports"
    exports_dir.mkdir()
    export_name = "f0001-123456-json.json"
    export_path = exports_dir / export_name
    export_path.write_text('{"filterId":"f0001","format":"JSON","data":{"results":[]}}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "ONS_EXPORTS_DIR", exports_dir)

    index_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/ons-exports-index"})
    assert index_resp.status_code == 200
    index_payload = json.loads(resource_contents(index_resp)[0]["text"])
    items = index_payload.get("items", [])
    assert any(item.get("name") == export_name for item in items if isinstance(item, dict))

    read_resp = client.get("/resources/read", params={"uri": f"resource://mcp-geo/ons-exports/{export_name}"})
    assert read_resp.status_code == 200
    payload = json.loads(resource_contents(read_resp)[0]["text"])
    assert payload["filterId"] == "f0001"
    assert payload["format"] == "JSON"


def test_resources_list_includes_os_exports_index_when_present(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog

    exports_dir = tmp_path / "os_exports"
    exports_dir.mkdir()
    (exports_dir / "sample-os-export.json").write_text('{"ok":true}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", exports_dir)

    resp = client.get("/resources/list", params={"limit": 300, "page": 1})
    assert resp.status_code == 200
    uris = {entry.get("uri") for entry in resp.json().get("resources", []) if isinstance(entry, dict)}
    assert "resource://mcp-geo/os-exports-index" in uris


def test_resources_read_os_exports_index_and_file(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog

    exports_dir = tmp_path / "os_exports"
    exports_dir.mkdir()
    export_name = "os-downloads-export-demo.json"
    export_path = exports_dir / export_name
    export_path.write_text('{"exportId":"x1","productId":"openroads"}', encoding="utf-8")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", exports_dir)

    index_resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/os-exports-index"})
    assert index_resp.status_code == 200
    index_payload = json.loads(resource_contents(index_resp)[0]["text"])
    items = index_payload.get("items", [])
    assert any(item.get("name") == export_name for item in items if isinstance(item, dict))

    read_resp = client.get("/resources/read", params={"uri": f"resource://mcp-geo/os-exports/{export_name}"})
    assert read_resp.status_code == 200
    payload = json.loads(resource_contents(read_resp)[0]["text"])
    assert payload["exportId"] == "x1"
    assert payload["productId"] == "openroads"
