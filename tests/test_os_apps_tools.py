from fastapi.testclient import TestClient

from server.config import settings
from server.main import app
from tools import os_apps

client = TestClient(app)


def test_os_apps_render_geography_selector(monkeypatch):
    monkeypatch.setattr(settings, "MCP_APPS_RESOURCE_LINK", True, raising=False)
    monkeypatch.setattr(settings, "MCP_APPS_CONTENT_MODE", "", raising=False)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_geography_selector", "level": "ward"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["uiResourceUris"] == ["ui://mcp-geo/geography-selector"]
    assert body["status"] == "ready"
    assert body["config"]["level"] == "ward"
    assert body["resourceUri"] == "ui://mcp-geo/geography-selector"
    assert body["_meta"]["ui"]["resourceUri"] == "ui://mcp-geo/geography-selector"
    assert body["_meta"]["uiResourceUris"] == ["ui://mcp-geo/geography-selector"]
    resource_links = [
        block
        for block in body.get("content", [])
        if isinstance(block, dict) and block.get("type") == "resource_link"
    ]
    assert resource_links
    assert resource_links[0]["uri"] == "ui://mcp-geo/geography-selector"


def test_os_apps_render_geography_selector_embedded(monkeypatch):
    monkeypatch.setattr(settings, "MCP_APPS_CONTENT_MODE", "embedded", raising=False)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_geography_selector"},
    )
    assert resp.status_code == 200
    body = resp.json()
    resource_blocks = [
        block
        for block in body.get("content", [])
        if isinstance(block, dict) and block.get("type") == "resource"
    ]
    assert resource_blocks
    resource = resource_blocks[0].get("resource", {})
    assert resource.get("uri") == "ui://mcp-geo/geography-selector"
    assert isinstance(resource.get("text"), str)
    assert resource.get("text", "").startswith("<!DOCTYPE html>")


def test_os_apps_render_geography_selector_text_only_override(monkeypatch):
    monkeypatch.setattr(settings, "MCP_APPS_CONTENT_MODE", "resource_link", raising=False)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_geography_selector", "contentMode": "text"},
    )
    assert resp.status_code == 200
    body = resp.json()
    content = body.get("content", [])
    assert content
    assert all(block.get("type") == "text" for block in content if isinstance(block, dict))


def test_os_apps_render_ui_probe_embedded(monkeypatch):
    monkeypatch.setattr(settings, "MCP_APPS_CONTENT_MODE", "text", raising=False)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_apps.render_ui_probe",
            "resourceUri": "ui://mcp-geo/statistics-dashboard",
            "contentMode": "embedded",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    resource_blocks = [
        block
        for block in body.get("content", [])
        if isinstance(block, dict) and block.get("type") == "resource"
    ]
    assert resource_blocks
    assert resource_blocks[0]["resource"]["uri"] == "ui://mcp-geo/statistics-dashboard"


def test_os_apps_content_mode_aliases():
    assert os_apps._normalize_content_mode("link") == "resource_link"
    assert os_apps._normalize_content_mode("inline") == "embedded"
    assert os_apps._normalize_content_mode("plain") == "text"
    assert os_apps._normalize_content_mode("unsupported") is None


def test_os_apps_build_ui_tool_meta_unknown():
    assert os_apps.build_ui_tool_meta("os_apps.render_not_real") is None


def test_os_apps_build_ui_tool_meta_includes_flat_and_nested_uri():
    meta = os_apps.build_ui_tool_meta("os_apps.render_statistics_dashboard")
    assert isinstance(meta, dict)
    assert meta["ui"]["resourceUri"] == "ui://mcp-geo/statistics-dashboard"
    assert meta["ui/resourceUri"] == "ui://mcp-geo/statistics-dashboard"


def test_os_apps_render_ui_probe_validation_errors():
    bad_type = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_ui_probe", "resourceUri": 123},
    )
    assert bad_type.status_code == 400
    assert bad_type.json()["message"] == "resourceUri must be a string"

    bad_uri = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_ui_probe", "resourceUri": "resource://mcp-geo/test"},
    )
    assert bad_uri.status_code == 400
    assert bad_uri.json()["message"] == "resourceUri must be a ui:// URI"

    bad_mode = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_ui_probe", "contentMode": 1},
    )
    assert bad_mode.status_code == 400
    assert bad_mode.json()["message"] == "contentMode must be a string"


def test_os_apps_render_ui_probe_embedded_unknown_resource():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_apps.render_ui_probe",
            "resourceUri": "ui://mcp-geo/does-not-exist",
            "contentMode": "embedded",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    content = body.get("content", [])
    assert len(content) == 1
    assert content[0]["type"] == "text"
