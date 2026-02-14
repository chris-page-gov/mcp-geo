from server.tool_naming import resolve_tool_name


def test_resolve_tool_name_accepts_display_style_aliases():
    originals = {"os_names.find", "os_places.nearest", "os_mcp.descriptor"}
    assert resolve_tool_name("Os names find", originals) == "os_names.find"
    assert resolve_tool_name("OS_PLACES_NEAREST", originals) == "os_places.nearest"
    assert resolve_tool_name(" os mcp descriptor ", originals) == "os_mcp.descriptor"


def test_resolve_tool_name_unknown_returns_input():
    originals = {"os_names.find"}
    assert resolve_tool_name("does not exist", originals) == "does not exist"
