from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_tools_list_basic():
    resp = client.get("/tools/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert any(t == "os_places_by_postcode" for t in data["tools"]) or data.get("nextPageToken")


def test_tools_describe_all():
    resp = client.get("/tools/describe")
    assert resp.status_code == 200
    data = resp.json()
    names = [t["name"] for t in data["tools"]]
    assert "os_places_by_postcode" in names
    assert "ons_data_create_filter" in names
    # Ensure schemas present
    bp = next(t for t in data["tools"] if t["name"] == "os_places_by_postcode")
    assert "inputSchema" in bp and "outputSchema" in bp
    assert "annotations" in bp
    assert bp["annotations"].get("readOnlyHint") is True
    assert bp["annotations"].get("openWorldHint") is True
    assert bp["annotations"].get("originalName") == "os_places.by_postcode"
    meta = bp.get("_meta", {}).get("mcp-geo", {})
    assert "deferLoading" in meta
    assert "category" in meta
    create_filter = next(t for t in data["tools"] if t["name"] == "ons_data_create_filter")
    assert create_filter["annotations"].get("readOnlyHint") is not True


def test_tools_describe_single():
    resp = client.get("/tools/describe", params={"name": "os_places.by_postcode"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "os_places_by_postcode"
    assert data["tools"][0]["annotations"]["originalName"] == "os_places.by_postcode"


def test_tools_describe_single_sanitized_alias():
    resp = client.get("/tools/describe", params={"name": "os_places_by_postcode"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "os_places_by_postcode"
    assert data["tools"][0]["annotations"]["originalName"] == "os_places.by_postcode"


def test_tools_describe_unknown():
    resp = client.get("/tools/describe", params={"name": "unknown.tool"})
    assert resp.status_code == 404
    body = resp.json()
    assert body.get("isError")
    assert body.get("code") == "UNKNOWN_TOOL"


def test_tools_list_toolset_filter():
    resp = client.get("/tools/list", params={"toolset": "maps_tiles"})
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert tools
    assert all(name in {"os_maps_render", "os_vector_tiles_descriptor"} for name in tools)


def test_tools_describe_toolset_filter():
    resp = client.get("/tools/describe", params={"toolset": "maps_tiles"})
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert tools
    names = {tool["name"] for tool in tools}
    assert names == {"os_maps_render", "os_vector_tiles_descriptor"}


def test_tools_list_uses_default_toolset_env(monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "maps_tiles")
    resp = client.get("/tools/list")
    assert resp.status_code == 200
    names = set(resp.json()["tools"])
    assert names == {"os_maps_render", "os_vector_tiles_descriptor"}


def test_tools_describe_uses_default_toolset_env(monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "maps_tiles")
    resp = client.get("/tools/describe")
    assert resp.status_code == 200
    names = {tool["name"] for tool in resp.json()["tools"]}
    assert names == {"os_maps_render", "os_vector_tiles_descriptor"}
