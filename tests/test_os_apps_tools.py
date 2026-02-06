from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_apps_render_geography_selector():
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
