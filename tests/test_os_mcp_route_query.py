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


def test_route_query_address_search():
    body = _route("Find address 10 Downing Street")
    assert body["intent"] == "address_lookup"
    assert body["recommended_tool"] == "os_places.search"


def test_route_query_unknown():
    body = _route("asdfghjkl qwertyuiop")
    assert body["intent"] == "unknown"
    assert body["recommended_tool"] == "os_mcp.descriptor"
