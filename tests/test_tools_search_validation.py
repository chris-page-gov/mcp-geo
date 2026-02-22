def test_tools_search_invalid_mode(client):
    resp = client.post("/tools/search", json={"query": "os", "mode": 123})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_invalid_limit(client):
    resp = client.post("/tools/search", json={"query": "os", "limit": 0})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_invalid_category(client):
    resp = client.post("/tools/search", json={"query": "os", "category": 123})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_invalid_include_schemas(client):
    resp = client.post("/tools/search", json={"query": "os", "includeSchemas": "no"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_invalid_toolset_type(client):
    resp = client.post("/tools/search", json={"query": "os", "toolset": 123})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_invalid_include_toolsets_type(client):
    resp = client.post("/tools/search", json={"query": "os", "includeToolsets": 123})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_unknown_toolset(client):
    resp = client.post("/tools/search", json={"query": "os", "toolset": "not-a-toolset"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_tools_search_rejects_non_object_payload(client):
    resp = client.post("/tools/search", json=["not", "an", "object"])
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["code"] == "INVALID_INPUT"


def test_tools_call_unknown_prefixed_tool(client):
    resp = client.post("/tools/call", json={"tool": "os_places.missing"})
    assert resp.status_code == 501
    payload = resp.json()
    assert payload["code"] in ("TOOL_NOT_REGISTERED", "TOOL_IMPORT_FAILED")


def test_tools_call_rejects_non_object_payload(client):
    resp = client.post("/tools/call", json=["not", "an", "object"])
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["code"] == "INVALID_INPUT"


def test_tools_call_rejects_malformed_json(client):
    resp = client.post(
        "/tools/call",
        data="{bad",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["code"] == "INVALID_INPUT"
    assert payload["message"] == "Malformed JSON request body"


def test_tools_search_rejects_malformed_json(client):
    resp = client.post(
        "/tools/search",
        data="{bad",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["code"] == "INVALID_INPUT"
    assert payload["message"] == "Malformed JSON request body"


def test_tools_call_accepts_display_style_tool_name(client):
    resp = client.post("/tools/call", json={"tool": "Os mcp descriptor"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("server") == "mcp-geo"


def test_tools_call_accepts_namespaced_tool_name(client):
    resp = client.post("/tools/call", json={"tool": "mcp-geo:os_mcp_descriptor"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("server") == "mcp-geo"
