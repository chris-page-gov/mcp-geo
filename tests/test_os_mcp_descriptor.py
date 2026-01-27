from fastapi.testclient import TestClient

from server.mcp.resource_catalog import MCP_APPS_MIME

from server.main import app

client = TestClient(app)


def test_os_mcp_descriptor_tool():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("server") == "mcp-geo"
    assert "toolSearch" in body
    assert body.get("skillsUri") == "skills://mcp-geo/getting-started"
    extensions = body.get("capabilities", {}).get("extensions", {})
    ui_ext = extensions.get("io.modelcontextprotocol/ui", {})
    assert MCP_APPS_MIME in ui_ext.get("mimeTypes", [])


def test_os_mcp_descriptor_invalid_category():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor", "category": 123})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_os_mcp_descriptor_invalid_include_tools():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor", "includeTools": "yes"})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"
