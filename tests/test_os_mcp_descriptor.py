from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_mcp_descriptor_tool():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("server") == "mcp-geo"
    assert "toolSearch" in body
    assert body.get("skillsUri") == "skills://mcp-geo/getting-started"
    assert "ui://mcp-geo/geography-selector" in body.get("uiResources", [])
