from server.mcp.tool_search import STARTER_TOOLS, get_tool_search_config, search_tools


def test_get_tool_search_config_invalid_category():
    result = get_tool_search_config("nope")
    assert "error" in result


def test_get_tool_search_config_filtered_category():
    result = get_tool_search_config("places")
    assert result.get("filtered_category") == "places"
    tools = result.get("tools", {})
    assert tools
    assert all(meta.get("category") == "places" for meta in tools.values())


def test_get_tool_search_config_stats_alias():
    result = get_tool_search_config("stats")
    assert "error" not in result
    assert result.get("filtered_category") == "statistics"
    alias = result.get("categoryAlias")
    assert alias == {"input": "stats", "normalized": "statistics"}
    tools = result.get("tools", {})
    assert tools
    assert all(meta.get("category") == "statistics" for meta in tools.values())


def test_get_tool_search_config_map_alias():
    result = get_tool_search_config("map")
    assert "error" not in result
    assert result.get("filtered_category") == "maps"
    alias = result.get("categoryAlias")
    assert alias == {"input": "map", "normalized": "maps"}
    tools = result.get("tools", {})
    assert tools
    assert all(meta.get("category") == "maps" for meta in tools.values())


def test_search_tools_regex_mode_and_schemas():
    results = search_tools("postcode", mode="regex", include_schemas=True)
    assert results
    first = results[0]
    assert "inputSchema" in first
    assert "outputSchema" in first


def test_search_tools_invalid_regex():
    try:
        search_tools("(", mode="regex")
    except ValueError as exc:
        assert "Invalid regex" in str(exc)
    else:
        raise AssertionError("Expected invalid regex error")


def test_search_tools_empty_query():
    results = search_tools("  ", mode="token")
    assert results == []


def test_search_tools_finds_ons_geo_keywords():
    results = search_tools("onspd postcode geography", mode="token")
    names = {item.get("name") for item in results}
    assert "ons_geo.by_postcode" in names


def test_search_tools_accepts_stats_alias_category():
    results = search_tools("nomis", mode="token", category="stats")
    assert results
    assert all(item.get("category") == "statistics" for item in results)


def test_starter_toolset_includes_select_toolsets():
    assert "os_mcp.select_toolsets" in STARTER_TOOLS
