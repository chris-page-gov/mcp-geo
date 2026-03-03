import importlib
import json
import queue
import re
import threading
import time

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app
from server.mcp.resource_catalog import MCP_APPS_MIME


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


def test_mcp_http_initialize_records_capability_summary(client):
    from server.mcp import http_transport

    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "init-summary",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}, "elicitation": {"form": {}}},
            },
        },
    )
    assert resp.status_code == 200
    session_id = resp.headers.get("mcp-session-id")
    assert session_id
    state = http_transport._SESSION_STATE.get(session_id, {})
    summary = state.get("capabilitySummary", {})
    assert summary.get("requestedProtocolVersion") == "2025-03-26"
    assert summary.get("supports", {}).get("tools") is True
    assert summary.get("supports", {}).get("elicitationForm") is True


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


def test_mcp_http_list_tools_toolset_filter(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("list-toolset-1", "tools/list", {"toolset": "ons_selection"}),
    )
    payload = resp.json()
    tools = payload["result"]["tools"]
    assert tools
    names = [tool["name"] for tool in tools]
    assert all(name.startswith("ons_") for name in names)
    assert "toolsets" in payload["result"]


def test_mcp_http_list_tools_uses_default_toolset_env(client, monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "maps_tiles")
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload("list-default-toolset-1", "tools/list", {}),
    )
    payload = resp.json()
    names = {tool["name"] for tool in payload["result"]["tools"]}
    assert names == {"os_maps_render", "os_vector_tiles_descriptor"}


def test_mcp_http_list_tools_query_filters_and_limits(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "list-query-1",
            "tools/list",
            {"query": "postcode", "limit": 5},
        ),
    )
    payload = resp.json()
    tools = payload["result"]["tools"]
    assert 1 <= len(tools) <= 5
    original_names = [tool.get("annotations", {}).get("originalName") for tool in tools]
    assert "os_places.by_postcode" in original_names


def test_mcp_http_search_tools_toolset_filters(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "search-toolset-1",
            "tools/search",
            {"query": "dataset", "toolset": "ons_selection"},
        ),
    )
    payload = resp.json()
    tools = payload["result"]["tools"]
    assert tools
    original_names = [tool.get("annotations", {}).get("originalName") for tool in tools]
    assert all(
        isinstance(name, str)
        and (name.startswith("ons_select.") or name.startswith("ons_search.") or name.startswith("ons_codes."))
        for name in original_names
    )


def test_mcp_http_call_tool_accepts_arguments(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "call-1",
            "tools/call",
            {"name": "os_mcp_descriptor", "arguments": {}},
        ),
    )
    payload = resp.json()
    assert payload["result"]["ok"] is True
    assert payload["result"]["content"]
    assert isinstance(payload["result"].get("structuredContent"), dict)


def test_mcp_http_resources_get_ui(client):
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "resource-1",
            "resources/read",
            {"uri": "ui://mcp-geo/geography-selector"},
        ),
    )
    payload = resp.json()
    result = payload["result"]
    contents = result["contents"]
    assert contents[0]["mimeType"] == "text/html;profile=mcp-app"
    assert contents[0]["uri"].startswith("ui://mcp-geo/")


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
    capabilities = {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": [MCP_APPS_MIME]}}}
    assert http_transport._client_supports_ui(capabilities) is False
    monkeypatch.delenv("MCP_HTTP_UI_SUPPORTED", raising=False)
    assert http_transport._client_supports_ui(capabilities) is True

def test_http_transport_client_supports_ui_nested(monkeypatch):
    from server.mcp import http_transport

    monkeypatch.delenv("MCP_HTTP_UI_SUPPORTED", raising=False)
    capabilities = {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": [MCP_APPS_MIME]}}}
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
    assert resp.status_code == 202


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
            "params": {"name": "os_mcp_descriptor", "arguments": "bad"},
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
    fallback = result["data"]["fallback"]
    assert fallback["type"] == "static_map"
    assert fallback["fallbackOrder"] == ["map_card", "overlay_bundle", "export_handoff"]
    assert fallback["map_card"]["type"] == "map_card"
    assert fallback["overlay_bundle"]["type"] == "overlay_bundle"
    assert fallback["export_handoff"]["type"] == "export_handoff"
    assert fallback["export_handoff"]["resourceUri"]
    assert str(fallback["export_handoff"]["hash"]).startswith("sha256:")
    assert fallback["widgetUnsupported"] is True
    assert fallback["widgetUnsupportedReason"] == "ui_extension_not_advertised"
    assert fallback["guidance"]["degradationMode"] == "no_ui"
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


def test_mcp_http_ui_stats_dashboard_fallback(client, monkeypatch):
    monkeypatch.setenv("MCP_HTTP_UI_SUPPORTED", "0")
    init_resp = client.post("/mcp", json=_initialize_payload())
    session_id = init_resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=_call_payload(
            "ui-stats-1",
            "tools/call",
            {
                "name": "os_apps_render_statistics_dashboard",
                "arguments": {"areaCodes": ["E09000033"], "dataset": "gdp", "measure": "GDPV"},
            },
        ),
    )
    result = resp.json()["result"]
    fallback = result["data"]["fallback"]
    assert fallback["type"] == "statistics_dashboard"
    assert "nomis.query" in fallback.get("suggestedTools", [])
    assert fallback["widgetUnsupported"] is True
    assert fallback["guidance"]["degradationMode"] == "no_ui"


def _write_catalog(tmp_path, items):
    path = tmp_path / "ons_catalog.json"
    payload = {
        "generatedAt": "2026-02-07T00:00:00Z",
        "source": "test",
        "placeholder": False,
        "items": items,
    }
    path.write_text(json.dumps(payload))
    return path


def test_mcp_http_ons_select_elicitation_stream(monkeypatch, tmp_path):
    catalog = _write_catalog(
        tmp_path,
        [
            {
                "id": "inflation-prices",
                "title": "Inflation and prices",
                "description": "Price indices over time.",
                "keywords": ["inflation", "prices"],
                "geography": {"levels": ["nation"]},
                "time": {"granularity": "month"},
                "state": "published",
            }
        ],
    )
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(catalog), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)
    monkeypatch.setenv("MCP_HTTP_ELICITATION_ENABLED", "1")
    monkeypatch.setenv("MCP_HTTP_ELICITATION_TIMEOUT_SECONDS", "5")

    main_client = TestClient(app)
    init_resp = main_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {"capabilities": {"elicitation": {"form": {}}}},
        },
    )
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    tool_call = {
        "jsonrpc": "2.0",
        "id": "call-1",
        "method": "tools/call",
        "params": {"name": "ons_select.search", "arguments": {"query": "inflation"}},
    }

    events = queue.Queue()
    captured = {}

    def _stream():
        stream_client = TestClient(app)
        with stream_client.stream(
            "POST",
            "/mcp",
            headers={
                "mcp-session-id": session_id,
                "accept": "text/event-stream, application/json",
            },
            json=tool_call,
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers.get("content-type", "").startswith("text/event-stream")
            for raw in resp.iter_lines():
                if raw is None:
                    continue
                line = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
                if not isinstance(line, str) or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if not data:
                    continue
                msg = json.loads(data)
                if msg.get("method") == "elicitation/create":
                    captured["elicitation"] = msg
                if msg.get("id") == "call-1" and isinstance(msg.get("result"), dict):
                    captured["tool_response"] = msg
                    events.put(("tool_response", msg.get("id")))

    t = threading.Thread(target=_stream, daemon=True)
    t.start()
    elicitation_id = "elicitation-1"
    accepted = False
    for _ in range(20):
        resp = main_client.post(
            "/mcp",
            headers={"mcp-session-id": session_id},
            json={
                "jsonrpc": "2.0",
                "id": elicitation_id,
                "result": {
                    "action": "accept",
                    "content": {"geographyLevel": "nation", "timeGranularity": "month"},
                },
            },
        )
        if resp.status_code == 202:
            accepted = True
            break
        time.sleep(0.05)
    assert accepted is True

    kind, _ = events.get(timeout=5)
    assert kind == "tool_response"
    t.join(timeout=5)

    elicitation = captured.get("elicitation", {})
    params = elicitation.get("params", {})
    schema = params.get("requestedSchema", {})
    props = schema.get("properties", {})
    assert "geographyLevel" in props
    assert "timeGranularity" in props

    tool_response = captured.get("tool_response", {})
    result = tool_response.get("result", {})
    assert result.get("ok") is True
    data = result.get("data", {})
    assert data.get("needsElicitation") is False


def test_mcp_http_select_toolsets_elicitation_stream(monkeypatch):
    monkeypatch.setenv("MCP_HTTP_ELICITATION_ENABLED", "1")
    monkeypatch.setenv("MCP_HTTP_ELICITATION_TIMEOUT_SECONDS", "5")

    main_client = TestClient(app)
    init_resp = main_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {"capabilities": {"elicitation": {"form": {}}}},
        },
    )
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    tool_call = {
        "jsonrpc": "2.0",
        "id": "call-toolsets-1",
        "method": "tools/call",
        "params": {"name": "os_mcp.select_toolsets", "arguments": {}},
    }

    events = queue.Queue()
    captured = {}

    def _stream():
        stream_client = TestClient(app)
        with stream_client.stream(
            "POST",
            "/mcp",
            headers={
                "mcp-session-id": session_id,
                "accept": "text/event-stream, application/json",
            },
            json=tool_call,
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers.get("content-type", "").startswith("text/event-stream")
            for raw in resp.iter_lines():
                if raw is None:
                    continue
                line = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
                if not isinstance(line, str) or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if not data:
                    continue
                msg = json.loads(data)
                if msg.get("method") == "elicitation/create":
                    captured["elicitation"] = msg
                if msg.get("id") == "call-toolsets-1" and isinstance(msg.get("result"), dict):
                    captured["tool_response"] = msg
                    events.put(("tool_response", msg.get("id")))

    t = threading.Thread(target=_stream, daemon=True)
    t.start()
    elicitation_id = "elicitation-1"
    accepted = False
    for _ in range(20):
        resp = main_client.post(
            "/mcp",
            headers={"mcp-session-id": session_id},
            json={
                "jsonrpc": "2.0",
                "id": elicitation_id,
                "result": {
                    "action": "accept",
                    "content": {"includeToolsets": ["core_router", "maps_tiles"]},
                },
            },
        )
        if resp.status_code == 202:
            accepted = True
            break
        time.sleep(0.05)
    assert accepted is True

    kind, _ = events.get(timeout=5)
    assert kind == "tool_response"
    t.join(timeout=5)

    elicitation = captured.get("elicitation", {})
    params = elicitation.get("params", {})
    schema = params.get("requestedSchema", {})
    props = schema.get("properties", {})
    assert "includeToolsets" in props
    assert "excludeToolsets" in props

    tool_response = captured.get("tool_response", {})
    result = tool_response.get("result", {})
    assert result.get("ok") is True
    data = result.get("data", {})
    assert data.get("effectiveFilters", {}).get("includeToolsets") == [
        "core_router",
        "maps_tiles",
    ]
