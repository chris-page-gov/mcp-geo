import importlib
import re
import time


def _initialize_payload():
    return {"jsonrpc": "2.0", "id": "init-1", "method": "initialize", "params": {}}


def _call_payload(msg_id: str, method: str, params: dict):
    return {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}


def test_mcp_http_initialize_sets_session_header(client):
    resp = client.post("/mcp", json=_initialize_payload())
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["result"]["server"] == "mcp-geo"
    assert "mcp-session-id" in resp.headers


def test_mcp_http_list_tools_sanitized(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("list-1", "tools/list", {}),
    )
    payload = resp.json()
    names = [tool["name"] for tool in payload["result"]["tools"]]
    assert any(name == "os_places_by_postcode" for name in names)
    assert all(re.match(r"^[A-Za-z0-9_-]{1,64}$", name) for name in names)


def test_mcp_http_call_tool_accepts_arguments(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "call-1",
            "tools/call",
            {"name": "ons_data_dimensions", "arguments": {}},
        ),
    )
    payload = resp.json()
    assert payload["result"]["ok"] is True
    assert payload["result"]["content"]


def test_mcp_http_resources_get_ui(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "resource-1",
            "resources/get",
            {"uri": "ui://mcp-geo/geography-selector"},
        ),
    )
    payload = resp.json()
    result = payload["result"]
    assert result["mimeType"] == "text/html;profile=mcp-app"
    assert result["uri"].startswith("ui://mcp-geo/")


def test_http_transport_env_parsing(monkeypatch):
    from server.mcp import http_transport

    monkeypatch.setenv("MCP_HTTP_SESSION_TTL", "nope")
    reloaded = importlib.reload(http_transport)
    assert reloaded._SESSION_TTL_SECONDS == 0.0
    monkeypatch.delenv("MCP_HTTP_SESSION_TTL", raising=False)
    importlib.reload(http_transport)


def test_http_transport_session_cleanup(monkeypatch):
    from server.mcp import http_transport

    http_transport._SESSION_STATE.clear()
    monkeypatch.setattr(http_transport, "_SESSION_TTL_SECONDS", 1.0)
    http_transport._SESSION_STATE["old"] = {"last_seen": time.time() - 5}
    http_transport._cleanup_sessions(time.time())
    assert "old" not in http_transport._SESSION_STATE


def test_http_transport_bool_helpers(monkeypatch):
    from server.mcp import http_transport

    monkeypatch.setenv("MCP_HTTP_UI_SUPPORTED", "true")
    assert http_transport._read_bool_env("MCP_HTTP_UI_SUPPORTED") is True
    monkeypatch.setenv("MCP_HTTP_RESOURCE_CONTENT", "yes")
    assert http_transport._bool_env("MCP_HTTP_RESOURCE_CONTENT", default=False) is True


def test_http_transport_client_supports_ui_override(monkeypatch):
    from server.mcp import http_transport

    monkeypatch.setenv("MCP_HTTP_UI_SUPPORTED", "0")
    assert http_transport._client_supports_ui({"uiResources": {"render": True}}) is False
    monkeypatch.delenv("MCP_HTTP_UI_SUPPORTED", raising=False)
    assert http_transport._client_supports_ui({"uiResources": {"render": True}}) is True

def test_http_transport_client_supports_ui_nested(monkeypatch):
    from server.mcp import http_transport

    monkeypatch.delenv("MCP_HTTP_UI_SUPPORTED", raising=False)
    capabilities = {"capabilities": {"ui": {"enabled": True}}}
    assert http_transport._client_supports_ui(capabilities) is True


def test_http_transport_resp_error_with_data():
    from server.mcp import http_transport

    payload = http_transport._resp_error("x", 123, "nope", {"detail": "x"})
    assert payload["error"]["data"]["detail"] == "x"


def test_mcp_http_invalid_json_returns_parse_error(client):
    resp = client.post("/mcp", data=b"{bad", headers={"content-type": "application/json"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32700


def test_mcp_http_invalid_request_shapes(client):
    resp = client.post("/mcp", json=["nope"])
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32600
    resp = client.post("/mcp", json={"id": "x", "method": "tools/list", "params": {}})
    assert resp.json()["error"]["code"] == -32600
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "x", "method": 123, "params": {}},
    )
    assert resp.json()["error"]["code"] == -32600
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list", "params": "nope"},
    )
    assert resp.json()["error"]["code"] == -32602


def test_mcp_http_method_not_found(client):
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "x", "method": "unknown/method", "params": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == -32601


def test_mcp_http_notification_returns_no_content(client):
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 204


def test_mcp_http_call_tool_errors(client):
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/call", "params": {}},
    )
    assert resp.json()["error"]["code"] == 1002
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "x",
            "method": "tools/call",
            "params": {"name": "unknown.tool", "arguments": {}},
        },
    )
    assert resp.json()["error"]["code"] == 1001
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "x",
            "method": "tools/call",
            "params": {"name": "ons_data_dimensions", "arguments": "bad"},
        },
    )
    assert resp.json()["error"]["code"] == 1003


def test_mcp_http_dispatch_resources_and_search(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("search-1", "tools/search", {"query": "postcode"}),
    )
    assert resp.json()["result"]["count"] >= 1
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("resources-1", "resources/list", {}),
    )
    assert resp.json()["result"]["resources"]
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("resources-2", "resources/describe", {}),
    )
    assert resp.json()["result"]["resources"]
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("shutdown-1", "shutdown", {}),
    )
    assert resp.json()["result"] is None


def test_mcp_http_ui_tool_fallback_and_meta(client, monkeypatch):
    monkeypatch.setenv("MCP_HTTP_UI_SUPPORTED", "0")
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "ui-1",
            "tools/call",
            {
                "name": "os_apps_render_geography_selector",
                "arguments": {"initialLat": 52.0, "initialLng": -1.0, "initialZoom": 16},
            },
        ),
    )
    result = resp.json()["result"]
    assert result["data"]["fallback"]["type"] == "static_map"
    assert result["uiResourceUris"]
    assert result["_meta"]["uiResourceUris"]
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "ui-2",
            "tools/call",
            {"name": "os_apps_render_geography_selector", "arguments": {"level": 123}},
        ),
    )
    assert resp.json()["result"]["isError"] is True
