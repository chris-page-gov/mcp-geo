from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def _route(query: str):
    resp = client.post("/tools/call", json={"tool": "os_mcp.route_query", "query": query})
    assert resp.status_code == 200
    return resp.json()


def test_route_query_requires_query():
    resp = client.post("/tools/call", json={"tool": "os_mcp.route_query"})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_route_query_place_lookup():
    body = _route("Find Westminster")
    assert body["intent"] == "place_lookup"
    assert body["recommended_tool"] == "admin_lookup.find_by_name"
    assert body["recommended_parameters"]["text"] == "Westminster"


def test_route_query_postcode_lookup():
    body = _route("UPRNs for SW1A 1AA")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "os_places.by_postcode"
    assert body["recommended_parameters"]["postcode"] == "SW1A1AA"


def test_route_query_uprn_lookup():
    body = _route("Lookup UPRN 100023336959")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "os_places.by_uprn"
    assert body["recommended_parameters"]["uprn"] == "100023336959"


def test_route_query_boundary_fetch():
    body = _route("Get the boundary of Westminster")
    assert body["intent"] == "boundary_fetch"
    assert body["recommended_tool"] == "admin_lookup.area_geometry"


def test_route_query_interactive_selection():
    body = _route("Select an OA from Coventry West")
    assert body["intent"] == "interactive_selection"
    assert body["recommended_tool"] == "os_apps.render_geography_selector"
    params = body["recommended_parameters"]
    assert params["level"] == "oa"
    assert params.get("focusName") == "Coventry West"


def test_route_query_boundary_explorer_for_layer_inventory():
    body = _route("Show me buildings and road links within Westminster ward")
    assert body["intent"] == "interactive_selection"
    assert body["recommended_tool"] == "os_apps.render_boundary_explorer"
    params = body["recommended_parameters"]
    assert params["level"] == "WARD"
    assert params.get("searchTerm") == "Westminster"


def test_route_query_vector_tiles():
    body = _route("Show me the vector tiles descriptor")
    assert body["intent"] == "vector_tiles"
    assert body["recommended_tool"] == "os_vector_tiles.descriptor"


def test_route_query_linked_ids():
    body = _route("Resolve USRN 12345678")
    assert body["intent"] == "linked_ids"
    assert body["recommended_tool"] == "os_linked_ids.get"


def test_route_query_map_render():
    body = _route("Render a static map image for Westminster")
    assert body["intent"] == "map_render"
    assert body["recommended_tool"] == "os_maps.render"


def test_route_query_statistics_nomis():
    body = _route("Unemployment rate for LSOA in Warwick")
    assert body["intent"] == "statistics"
    assert body["recommended_tool"] == "nomis.query"
    assert body["workflow_profile_uri"] == "resource://mcp-geo/nomis-workflows"
    assert "nomis-workflows" in body["guidance"]


def test_route_query_address_search():
    body = _route("Find address 10 Downing Street")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "os_places.search"


def test_route_query_poi_search():
    body = _route("Find nearby cafes in Westminster")
    assert body["intent"] == "poi_lookup"
    assert body["recommended_tool"] == "os_poi.search"


def test_route_query_unknown():
    body = _route("asdfghjkl qwertyuiop")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "os_mcp.descriptor"
    assert body["workflow_profile_uri"] is None


def test_stats_routing_tool():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_mcp.stats_routing", "query": "Employment rate for LSOA in Leeds"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "nomis"
    assert body["recommendedTool"] == "nomis.query"


def test_stats_routing_comparison_recommendations():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_mcp.stats_routing", "query": "Compare unemployment between Leeds and Manchester"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comparisonRecommended"] is True
    assert body["nextSteps"]
    step_tools = [step.get("tool") for step in body["nextSteps"] if isinstance(step, dict)]
    assert "admin_lookup.find_by_name" in step_tools
    assert "os_apps.render_statistics_dashboard" in step_tools
    assert "nomis.query" in step_tools
    assert any("q and limit" in note for note in body.get("notes", []))


def test_stats_routing_respects_provider_preference_and_level():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_mcp.stats_routing",
            "query": "Compare life in Leamington Spa and Warwick",
            "providerPreference": "ONS",
            "comparisonLevel": "LSOA",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "ons"
    assert body["recommendedTool"] == "ons_data.query"
    assert body["userSelections"]["comparisonLevel"] == "LSOA"
    assert body["userSelections"]["providerPreference"] == "ONS"
    next_steps = body.get("nextSteps", [])
    admin_step = next(
        step for step in next_steps if isinstance(step, dict) and step.get("tool") == "admin_lookup.find_by_name"
    )
    assert "level=LSOA" in admin_step.get("note", "")


def test_stats_routing_rejects_invalid_provider_preference():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_mcp.stats_routing",
            "query": "Compare life in Leamington Spa and Warwick",
            "providerPreference": "BAD_PROVIDER",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_stats_routing_rejects_invalid_comparison_level():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_mcp.stats_routing",
            "query": "Compare life in Leamington Spa and Warwick",
            "comparisonLevel": "TOWN",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_select_toolsets_infers_from_query():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_mcp.select_toolsets", "query": "Render a static map for Coventry"},
    )
    assert resp.status_code == 200
    body = resp.json()
    filters = body.get("effectiveFilters", {})
    include = filters.get("includeToolsets", [])
    assert "core_router" in include
    assert "maps_tiles" in include
    assert body.get("matchedToolCount", 0) >= 1


def test_select_toolsets_explicit_filters():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_mcp.select_toolsets",
            "includeToolsets": ["core_router"],
            "excludeToolsets": ["apps_ui"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    filters = body.get("effectiveFilters", {})
    assert filters.get("includeToolsets") == ["core_router"]
    assert filters.get("excludeToolsets") == ["apps_ui"]


def test_select_toolsets_rejects_invalid_max_tools():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_mcp.select_toolsets", "maxTools": 0},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"
