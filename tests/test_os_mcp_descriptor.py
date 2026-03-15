from fastapi.testclient import TestClient

from server.mcp.resource_catalog import MCP_APPS_MIME
from server.protocol import MCP_APPS_PROTOCOL_VERSION, PROTOCOL_VERSION, SUPPORTED_PROTOCOL_VERSIONS

from server.main import app

client = TestClient(app)


def test_os_mcp_descriptor_tool():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("server") == "mcp-geo"
    assert body.get("protocolVersion") == PROTOCOL_VERSION
    assert body.get("supportedProtocolVersions") == list(SUPPORTED_PROTOCOL_VERSIONS)
    assert body.get("mcpAppsProtocolVersion") == MCP_APPS_PROTOCOL_VERSION
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


def test_os_mcp_descriptor_accepts_stats_category_alias():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor", "category": "stats"})
    assert resp.status_code == 200
    body = resp.json()
    tool_search = body.get("toolSearch", {})
    assert "error" not in tool_search
    assert tool_search.get("filtered_category") == "statistics"


def test_os_mcp_descriptor_accepts_map_category_alias():
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor", "category": "map"})
    assert resp.status_code == 200
    body = resp.json()
    tool_search = body.get("toolSearch", {})
    assert "error" not in tool_search
    assert tool_search.get("filtered_category") == "maps"
