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


def test_route_query_postcode_geography_lookup():
    body = _route("List all geographies for postcode SW1A 1AA")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "ons_geo.by_postcode"
    assert body["recommended_parameters"]["postcode"] == "SW1A1AA"


def test_route_query_postcode_geography_lookup_best_fit():
    body = _route("Use NSPL best-fit geographies for postcode SW1A 1AA")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "ons_geo.by_postcode"
    assert body["recommended_parameters"]["postcode"] == "SW1A1AA"
    assert body["recommended_parameters"]["derivationMode"] == "best_fit"


def test_route_query_uprn_lookup():
    body = _route("Lookup UPRN 100023336959")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "os_places.by_uprn"
    assert body["recommended_parameters"]["uprn"] == "100023336959"


def test_route_query_uprn_geography_lookup():
    body = _route("Which geographies does UPRN 100023336959 map to in exact mode")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "ons_geo.by_uprn"
    assert body["recommended_parameters"]["uprn"] == "100023336959"
    assert body["recommended_parameters"]["derivationMode"] == "exact"


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


def test_route_query_linked_ids_overrides_uprn_address_mode():
    body = _route("Resolve linked IDs for UPRN 100021892956")
    assert body["intent"] == "linked_ids"
    assert body["recommended_tool"] == "os_linked_ids.get"
    assert body["recommended_parameters"]["identifier"] == "100021892956"


def test_route_query_map_render():
    body = _route("Render a static map image for Westminster")
    assert body["intent"] == "map_render"
    assert body["recommended_tool"] == "os_maps.render"


def test_route_query_sg03_style_prompt_prefers_os_route_tool():
    body = _route(
        "What is the best emergency route from Retford Library, 17 Churchgate, Retford, DN22 6PE "
        "to Goodwin Hall, Chancery Lane, Retford, DN22 6DF and avoid flood-risk-zone reference "
        "167647/3 if possible?"
    )
    assert body["intent"] == "route_planning"
    assert body["recommended_tool"] == "os_route.get"
    params = body["recommended_parameters"]
    assert params["profile"] == "emergency"
    assert params["constraints"]["softAvoid"] is True
    assert params["constraints"]["avoidIds"] == ["167647/3"]
    assert params["stops"][0]["query"].startswith("Retford Library")
    assert params["stops"][1]["query"].startswith("Goodwin Hall")
    assert body["workflow_steps"][:2] == ["os_route.get", "os_apps.render_route_planner"]
    assert body["interactive_companion_tool"] == "os_apps.render_route_planner"


def test_route_query_without_if_possible_preserves_hard_avoid():
    body = _route(
        "What is the best emergency route from Retford Library, 17 Churchgate, Retford, DN22 6PE "
        "to Goodwin Hall, Chancery Lane, Retford, DN22 6DF and avoid flood-risk-zone reference "
        "167647/3?"
    )
    assert body["intent"] == "route_planning"
    assert body["recommended_tool"] == "os_route.get"
    params = body["recommended_parameters"]
    assert params["constraints"]["avoidIds"] == ["167647/3"]
    assert params["constraints"]["softAvoid"] is False


def test_route_query_surfaces_unresolved_avoid_text_without_invalid_parameters():
    body = _route(
        "Plan the best route from Coventry rail station to London Euston and "
        "avoid central cordon if possible"
    )
    assert body["intent"] == "route_planning"
    params = body["recommended_parameters"]
    assert params["constraints"]["avoidAreas"] == []
    assert params["constraints"]["avoidIds"] == []
    assert body["routeHints"]["unresolvedAvoidTexts"] == ["central cordon"]
    assert "routeHints.unresolvedAvoidTexts" in body["guidance"]


def test_route_query_treats_plain_avoid_tokens_as_ids():
    body = _route(
        "Plan the best route from Coventry rail station to London Euston and "
        "avoid edge-1001 if possible"
    )
    assert body["intent"] == "route_planning"
    params = body["recommended_parameters"]
    assert params["constraints"]["avoidIds"] == ["edge-1001"]
    assert params["constraints"]["avoidAreas"] == []


def test_route_query_extracts_coordinate_and_via_route_hints():
    body = _route(
        "Give me walking directions from 51.5034,-0.1276 to Westminster Abbey via Big Ben"
    )
    assert body["intent"] == "route_planning"
    assert body["recommended_tool"] == "os_route.get"
    params = body["recommended_parameters"]
    assert params["profile"] == "walk"
    assert params["stops"][0]["coordinates"] == [-0.1276, 51.5034]
    assert params["stops"][1]["query"] == "Westminster Abbey"
    assert params["via"][0]["query"] == "Big Ben"
    hints = body.get("routeHints", {})
    assert hints.get("startText") == "51.5034,-0.1276"


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


def test_route_query_poi_phrase_routes_to_poi_lookup():
    body = _route("Search points of interest for cafes in Westminster")
    assert body["intent"] == "poi_lookup"
    assert body["recommended_tool"] == "os_poi.search"


def test_route_query_poi_acronym_with_coordinates_routes_to_poi_lookup():
    body = _route("Find nearest POIs to 51.5034,-0.1276")
    assert body["intent"] == "poi_lookup"
    assert body["recommended_tool"] == "os_poi.nearest"


def test_route_query_dataset_discovery_dimensions_phrase():
    body = _route("List available ONS observation dimensions")
    assert body["intent"] == "dataset_discovery"


def test_route_query_dataset_discovery_nomis_concepts():
    body = _route("List NOMIS concepts")
    assert body["intent"] == "dataset_discovery"


def test_route_query_statistics_for_ons_filter_creation():
    body = _route("Create an ONS filter for UK GDPV 2024 Q1-Q2")
    assert body["intent"] == "statistics"


def test_route_query_hierarchy_phrase():
    body = _route("Show the hierarchy for ward E05000644")
    assert body["intent"] == "place_lookup"
    assert body["recommended_tool"] == "admin_lookup.reverse_hierarchy"
    assert body["recommended_parameters"]["id"] == "E05000644"


def test_route_query_hierarchy_phrase_without_code_routes_to_name_lookup():
    body = _route("Show hierarchy for Westminster")
    assert body["intent"] == "place_lookup"
    assert body["recommended_tool"] == "admin_lookup.find_by_name"
    assert body["recommended_parameters"]["text"] == "Westminster"
    assert "admin_lookup.reverse_hierarchy" in body.get("workflow_steps", [])


def test_route_query_tool_discovery_phrase():
    body = _route("Find tools related to postcode search")
    assert body["intent"] == "unknown"
    assert body["confidence"] >= 0.8


def test_route_query_statistics_dashboard_area_comparison():
    body = _route("Open the statistics dashboard for Westminster")
    assert body["intent"] == "area_comparison"
    assert body["recommended_tool"] == "os_apps.render_statistics_dashboard"


def test_route_query_boundary_explorer_widget_phrase():
    body = _route("Open the boundary explorer widget")
    assert body["intent"] == "interactive_selection"
    assert body["recommended_tool"] == "os_apps.render_boundary_explorer"


def test_route_query_ui_probe_phrase():
    body = _route("Probe MCP-Apps UI rendering mode support")
    assert body["intent"] == "interactive_selection"
    assert body["recommended_tool"] == "os_apps.render_ui_probe"


def test_route_query_unknown_skills_guide_request():
    body = _route("Fetch the MCP Geo skills guide")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "resources/read"


def test_route_query_unknown_descriptor_request():
    body = _route("Describe server capabilities and tool search config")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "os_mcp.descriptor"


def test_route_query_unknown_log_event_request():
    body = _route("Log a UI event for analytics")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "os_apps.log_event"


def test_route_query_unknown_cache_status_request():
    body = _route("Show boundary cache status")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "admin_lookup.get_cache_status"


def test_route_query_unknown_cache_search_request():
    body = _route("Search the boundary cache for Westminster")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "admin_lookup.search_cache"
    assert body["recommended_parameters"]["query"] == "Westminster"


def test_route_query_environmental_survey_bowland():
    body = _route("Do a peatland site survey on the forrest of Bowland")
    assert body["intent"] == "environmental_survey"
    assert body["recommended_tool"] == "os_landscape.find"
    assert body["recommended_parameters"]["text"] == "Forest of Bowland"
    plan = body.get("surveyPlan")
    assert isinstance(plan, list)
    assert plan
    assert plan[0]["tool"] == "os_landscape.find"
    assert any(step.get("tool") == "os_peat.evidence_paths" for step in plan)


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
        json={
            "tool": "os_mcp.stats_routing",
            "query": "Compare unemployment between Leeds and Manchester",
        },
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
        step
        for step in next_steps
        if isinstance(step, dict) and step.get("tool") == "admin_lookup.find_by_name"
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


def test_select_toolsets_poi_query_infers_places_names():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_mcp.select_toolsets",
            "query": "Search points of interest for cafes in Westminster",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    inference = body.get("inference", {})
    assert inference.get("intent") == "poi_lookup"
    filters = body.get("effectiveFilters", {})
    include = filters.get("includeToolsets", [])
    assert "places_names" in include
    assert "admin_boundaries" not in include
    matched = body.get("matchedTools", [])
    assert "os_poi.search" in matched


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
