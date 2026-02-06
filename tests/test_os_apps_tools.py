from fastapi.testclient import TestClient

from server.config import settings
from server.main import app

client = TestClient(app)


def test_os_apps_render_geography_selector(monkeypatch):
    monkeypatch.setattr(settings, "MCP_APPS_RESOURCE_LINK", True, raising=False)
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
