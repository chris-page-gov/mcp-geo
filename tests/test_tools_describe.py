from fastapi.testclient import TestClient

from server.main import app
from server.mcp import tools as tools_api

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


def test_tools_list_starter_default_includes_harold_wood_recovery_tools(monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "starter")
    resp = client.get("/tools/list", params={"limit": 100})
    assert resp.status_code == 200
    names = set(resp.json()["tools"])
    assert "admin_lookup_area_geometry" in names
    assert "os_linked_ids_get" in names
    assert "os_resources_get" in names


def test_tools_list_handles_filter_validation_error(monkeypatch):
    monkeypatch.setattr(
        tools_api,
        "filter_tool_names_by_toolsets",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad filter")),
    )
    resp = client.get("/tools/list")
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_skips_non_dict_entries_and_normalizes_annotations(monkeypatch):
    monkeypatch.setattr(
        tools_api,
        "search_tools",
        lambda *_args, **_kwargs: [123, {"name": "os_places.by_postcode", "annotations": "bad"}],
    )
    resp = client.post("/tools/search", json={"query": "postcode"})
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "os_places_by_postcode"
    assert tools[0]["annotations"]["originalName"] == "os_places.by_postcode"


def test_tools_describe_handles_filter_validation_error(monkeypatch):
    monkeypatch.setattr(
        tools_api,
        "filter_tool_names_by_toolsets",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad filter")),
    )
    resp = client.get("/tools/describe")
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_describe_returns_unknown_when_tool_missing_after_resolution(monkeypatch):
    original_get = tools_api.get
    monkeypatch.setattr(
        tools_api,
        "get",
        lambda name: None if name == "os_places.by_postcode" else original_get(name),
    )
    resp = client.get("/tools/describe", params={"name": "os_places.by_postcode"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "UNKNOWN_TOOL"


def _assert_os_map_layers_schema(layers: dict) -> None:
    assert "oneOf" in layers
    assert layers["description"].startswith("Requested layers")
    array_option = next(option for option in layers["oneOf"] if option.get("type") == "array")
    string_option = next(option for option in layers["oneOf"] if option.get("type") == "string")
    null_option = next(option for option in layers["oneOf"] if option.get("type") == "null")
    assert array_option["items"] == {"type": "string"}
    assert array_option["minItems"] == 1
    assert string_option["minLength"] == 1
    assert null_option == {"type": "null"}


def test_os_map_inventory_layers_schema_uses_explicit_union() -> None:
    resp = client.get("/tools/describe", params={"name": "os_map.inventory"})
    assert resp.status_code == 200
    tool = resp.json()["tools"][0]
    layers = tool["inputSchema"]["properties"]["layers"]
    _assert_os_map_layers_schema(layers)


def test_os_map_export_layers_schema_uses_explicit_union() -> None:
    resp = client.get("/tools/describe", params={"name": "os_map.export"})
    assert resp.status_code == 200
    tool = resp.json()["tools"][0]
    layers = tool["inputSchema"]["properties"]["layers"]
    _assert_os_map_layers_schema(layers)


def test_select_toolsets_schema_uses_explicit_union_with_array_items() -> None:
    resp = client.get("/tools/describe", params={"name": "os_mcp.select_toolsets"})
    assert resp.status_code == 200
    tool = resp.json()["tools"][0]
    props = tool["inputSchema"]["properties"]

    include = props["includeToolsets"]
    exclude = props["excludeToolsets"]

    assert "oneOf" in include
    assert "oneOf" in exclude

    include_array = next(option for option in include["oneOf"] if option.get("type") == "array")
    include_string = next(option for option in include["oneOf"] if option.get("type") == "string")
    exclude_array = next(option for option in exclude["oneOf"] if option.get("type") == "array")
    exclude_string = next(option for option in exclude["oneOf"] if option.get("type") == "string")

    assert include_array["items"] == {"type": "string"}
    assert exclude_array["items"] == {"type": "string"}
    assert include_string["type"] == "string"
    assert exclude_string["type"] == "string"
