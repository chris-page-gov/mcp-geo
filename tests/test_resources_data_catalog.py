from __future__ import annotations

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


def test_resources_read_boundary_manifest() -> None:
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/boundary-manifest"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"] == "application/json"
    payload = json.loads(contents[0]["text"])
    assert "manifest_version" in payload
    assert "boundary_families" in payload


def test_resources_read_boundary_cache_status() -> None:
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/boundary-cache-status"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    payload = json.loads(contents[0]["text"])
    assert "enabled" in payload
    assert "reloadHint" in payload


def test_resources_read_boundary_manifest_by_name() -> None:
    resp = client.get("/resources/read", params={"name": "data_boundary_manifest"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    payload = json.loads(contents[0]["text"])
    assert "manifest_version" in payload
