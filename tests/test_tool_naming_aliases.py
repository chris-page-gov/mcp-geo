from server.tool_naming import resolve_tool_name


def test_resolve_tool_name_accepts_display_style_aliases():
    originals = {"os_names.find", "os_places.nearest", "os_mcp.descriptor"}
    assert resolve_tool_name("Os names find", originals) == "os_names.find"
    assert resolve_tool_name("OS_PLACES_NEAREST", originals) == "os_places.nearest"
    assert resolve_tool_name(" os mcp descriptor ", originals) == "os_mcp.descriptor"


def test_resolve_tool_name_unknown_returns_input():
    originals = {"os_names.find"}
    assert resolve_tool_name("does not exist", originals) == "does not exist"


def test_resolve_tool_name_accepts_server_namespaced_aliases():
    originals = {"os_places.search", "os_maps.render"}
    assert resolve_tool_name("mcp-geo:os_places_search", originals) == "os_places.search"
    assert resolve_tool_name("mcp-geo:os_places.search", originals) == "os_places.search"
    assert resolve_tool_name("mcp-geo/os_maps_render", originals) == "os_maps.render"
