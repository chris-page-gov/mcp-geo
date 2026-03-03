import io, json, re

from server import stdio_adapter
from server.config import settings
from server.mcp.resource_catalog import MCP_APPS_MIME
from server.protocol import PROTOCOL_VERSION

def frame(msg: dict) -> bytes:
    body = json.dumps(msg, separators=(",", ":")).encode()
    return f"Content-Length: {len(body)}\r\n\r\n".encode() + body

def read_one(buf: io.BytesIO) -> dict:
    # read headers
    headers = {}
    while True:
        line = buf.readline()
        if not line:
            raise RuntimeError("EOF before headers")
        if line in (b"\r\n", b"\n"):
            break
        k, v = line.decode().split(":", 1)
        headers[k.lower()] = v.strip()
    length = int(headers.get("content-length", 0))
    body = buf.read(length)
    return json.loads(body.decode())


def read_all(buf: io.BytesIO) -> list[dict]:
    messages: list[dict] = []
    while buf.tell() < len(buf.getvalue()):
        headers = {}
        while True:
            line = buf.readline()
            if not line:
                return messages
            if line in (b"\r\n", b"\n"):
                break
            key, value = line.decode().split(":", 1)
            headers[key.lower()] = value.strip()
        length = int(headers.get("content-length", 0))
        body = buf.read(length)
        if not body:
            break
        messages.append(json.loads(body.decode()))
    return messages

def test_direct_main_initialize_and_exit():
    stdin_bytes = frame({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}) + frame({"jsonrpc":"2.0","method":"exit"})
    stdin = io.StringIO(stdin_bytes.decode())  # use text for readline compatibility
    # Need a binary-capable stdout; we'll capture writes via a custom wrapper
    class StdoutCapture(io.StringIO):
        pass
    stdout = StdoutCapture()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    out_bytes = stdout.getvalue().encode()
    buf = io.BytesIO(out_bytes)
    first = read_one(buf)
    if 'result' not in first and first.get('method') == 'log':  # skip log notification
        first = read_one(buf)
    assert first.get('result', {}).get('server') == 'mcp-geo'


def test_stdio_initialize_negotiates_supported_protocol():
    result = stdio_adapter.handle_initialize({"protocolVersion": "2025-03-26", "capabilities": {}})
    assert result.get("protocolVersion") == "2025-03-26"


def test_stdio_initialize_falls_back_to_latest_protocol():
    result = stdio_adapter.handle_initialize({"protocolVersion": "1999-01-01", "capabilities": {}})
    assert result.get("protocolVersion") == PROTOCOL_VERSION


def test_stdio_initialize_records_capability_summary():
    stdio_adapter.handle_initialize(
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}, "elicitation": {"form": {}}},
        }
    )
    summary = stdio_adapter.CLIENT_CAPABILITY_SUMMARY
    assert summary.get("requestedProtocolVersion") == "2025-03-26"
    assert summary.get("supports", {}).get("tools") is True
    assert summary.get("supports", {}).get("elicitationForm") is True


def test_tool_names_sanitized_and_resolvable():
    result = stdio_adapter.handle_list_tools({})
    names = [t["name"] for t in result["tools"]]
    assert any(name == "os_places_by_postcode" for name in names)
    assert all(re.match(r"^[A-Za-z0-9_-]{1,64}$", name) for name in names)
    call = stdio_adapter.handle_call_tool({"tool": "os_mcp_descriptor", "args": {}})
    assert call.get("ok") is True


def test_call_tool_accepts_arguments_payload():
    call = stdio_adapter.handle_call_tool({"name": "os_mcp_descriptor", "arguments": {}})
    assert call.get("ok") is True
    assert call.get("content")
    assert call["content"][0]["type"] == "text"
    assert isinstance(call.get("structuredContent"), dict)


def test_call_tool_accepts_display_style_name_alias():
    call = stdio_adapter.handle_call_tool({"name": "Os mcp descriptor", "arguments": {}})
    assert call.get("ok") is True
    assert call.get("content")


def test_call_tool_accepts_namespaced_name_alias():
    call = stdio_adapter.handle_call_tool({"name": "mcp-geo:os_mcp_descriptor", "arguments": {}})
    assert call.get("ok") is True
    assert call.get("content")


def test_call_tool_display_style_alias_routes_to_os_tool(monkeypatch):
    from tools import os_common

    monkeypatch.setattr(settings, "OS_API_KEY", "", raising=False)
    monkeypatch.setattr(os_common.client, "api_key", "")
    call = stdio_adapter.handle_call_tool(
        {"name": "Os names find", "arguments": {"text": "Village Hotel Coventry"}}
    )
    assert call.get("isError") is True
    data = call.get("data", {})
    assert data.get("code") == "NO_API_KEY"
    structured = call.get("structuredContent", {})
    assert structured.get("code") == "NO_API_KEY"


def test_ui_tools_emit_resource_content(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_RESOURCE_CONTENT", "1")
    call = stdio_adapter.handle_call_tool({"name": "os_apps_render_geography_selector", "arguments": {}})
    assert call.get("ok") is True
    content = call.get("content", [])
    assert content
    assert content[0]["type"] == "text"
    assert "Open the geography selector" in content[0]["text"]

def test_ui_tools_include_resource_content_by_default(monkeypatch):
    monkeypatch.delenv("MCP_STDIO_RESOURCE_CONTENT", raising=False)
    monkeypatch.setenv("MCP_STDIO_UI_SUPPORTED", "1")
    call = stdio_adapter.handle_call_tool({"name": "os_apps_render_geography_selector", "arguments": {}})
    assert call.get("ok") is True
    content = call.get("content", [])
    assert content
    assert content[0]["type"] == "text"
    assert "Open the geography selector" in content[0]["text"]


def test_claude_defaults_ui_tool_content_mode_to_resource_link(monkeypatch):
    monkeypatch.delenv("MCP_STDIO_CLAUDE_APPS_CONTENT_MODE", raising=False)
    monkeypatch.setenv("MCP_APPS_CONTENT_MODE", "embedded")
    monkeypatch.setattr(stdio_adapter, "CLIENT_INFO", {"name": "claude-ai"})
    call = stdio_adapter.handle_call_tool({"name": "os_apps_render_boundary_explorer", "arguments": {}})
    assert call.get("ok") is True
    content = call.get("content", [])
    assert content
    assert any(block.get("type") == "resource_link" for block in content if isinstance(block, dict))
    assert not any(block.get("type") == "resource" for block in content if isinstance(block, dict))


def test_claude_ui_content_mode_respects_explicit_override(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_CLAUDE_APPS_CONTENT_MODE", "text")
    monkeypatch.setattr(stdio_adapter, "CLIENT_INFO", {"name": "claude-ai"})
    call = stdio_adapter.handle_call_tool(
        {
            "name": "os_apps_render_geography_selector",
            "arguments": {"contentMode": "embedded"},
        }
    )
    assert call.get("ok") is True
    content = call.get("content", [])
    assert any(block.get("type") == "resource" for block in content if isinstance(block, dict))

def test_stdio_client_supports_ui_nested(monkeypatch):
    monkeypatch.delenv("MCP_STDIO_UI_SUPPORTED", raising=False)
    capabilities = {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": [MCP_APPS_MIME]}}}
    assert stdio_adapter._client_supports_ui(capabilities) is True


def test_ui_tools_fallback_to_static_map(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_UI_SUPPORTED", "0")
    call = stdio_adapter.handle_call_tool(
        {
            "name": "os_apps_render_geography_selector",
            "arguments": {"initialLat": 52.0, "initialLng": -1.0, "initialZoom": 16},
        }
    )
    assert call.get("ok") is True
    data = call.get("data", {})
    assert isinstance(data, dict)
    fallback = data.get("fallback")
    assert isinstance(fallback, dict)
    assert fallback.get("type") == "static_map"
    assert "render" in fallback
    assert fallback.get("fallbackOrder") == ["map_card", "overlay_bundle", "export_handoff"]
    assert fallback.get("map_card", {}).get("type") == "map_card"
    assert fallback.get("overlay_bundle", {}).get("type") == "overlay_bundle"
    assert fallback.get("export_handoff", {}).get("type") == "export_handoff"
    assert fallback.get("export_handoff", {}).get("resourceUri")
    assert str(fallback.get("export_handoff", {}).get("hash", "")).startswith("sha256:")
    assert fallback.get("widgetUnsupported") is True
    assert fallback.get("widgetUnsupportedReason") == "ui_extension_not_advertised"
    assert fallback.get("guidance", {}).get("degradationMode") == "no_ui"


def test_ui_tools_fallback_stats_dashboard(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_UI_SUPPORTED", "0")
    call = stdio_adapter.handle_call_tool(
        {
            "name": "os_apps_render_statistics_dashboard",
            "arguments": {
                "areaCodes": ["E09000033"],
                "dataset": "gdp",
                "measure": "GDPV",
            },
        }
    )
    assert call.get("ok") is True
    data = call.get("data", {})
    fallback = data.get("fallback")
    assert isinstance(fallback, dict)
    assert fallback.get("type") == "statistics_dashboard"
    assert "nomis.query" in fallback.get("suggestedTools", [])
    assert fallback.get("widgetUnsupported") is True
    assert fallback.get("guidance", {}).get("preferredNextTools")


def test_tool_schema_const_is_sanitized():
    result = stdio_adapter.handle_list_tools({})
    tool = next(t for t in result["tools"] if t["name"] == "os_places_by_postcode")
    const = tool.get("inputSchema", {}).get("properties", {}).get("tool", {}).get("const")
    assert const == "os_places_by_postcode"


def test_tools_list_uses_default_toolset_from_env(monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "maps_tiles")
    result = stdio_adapter.handle_list_tools({})
    names = {tool["name"] for tool in result["tools"]}
    assert names == {"os_maps_render", "os_vector_tiles_descriptor"}


def test_tools_list_explicit_toolset_overrides_default(monkeypatch):
    monkeypatch.setenv("MCP_TOOLS_DEFAULT_TOOLSET", "maps_tiles")
    result = stdio_adapter.handle_list_tools({"toolset": "ons_selection"})
    names = {tool["name"] for tool in result["tools"]}
    assert names
    assert all(name.startswith("ons_") for name in names)


def test_tools_list_query_filters_and_limits_results():
    result = stdio_adapter.handle_list_tools({"query": "postcode", "limit": 5})
    tools = result["tools"]
    assert 1 <= len(tools) <= 5
    original_names = [tool.get("annotations", {}).get("originalName") for tool in tools]
    assert "os_places.by_postcode" in original_names


def test_read_headers_invalid_content_length():
    buf = io.StringIO("Content-Length: nope\r\n\r\n")
    length, error = stdio_adapter._read_headers(buf)
    assert length is None
    assert error == "Invalid Content-Length"


def test_resolve_framing_env(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    assert stdio_adapter._resolve_framing() == "line"
    monkeypatch.setenv("MCP_STDIO_FRAMING", "content-length")
    assert stdio_adapter._resolve_framing() == "content-length"
    monkeypatch.delenv("MCP_STDIO_FRAMING", raising=False)
    assert stdio_adapter._resolve_framing() is None


def test_stdio_main_reports_errors_line(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "unknown/method", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": "bad"},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/search", "params": {"query": ""}},
        {"jsonrpc": "2.0", "method": "exit"},
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    output = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    error_codes = [item.get("error", {}).get("code") for item in output if "error" in item]
    assert 1002 in error_codes
    assert -32601 in error_codes
    assert -32602 in error_codes


def test_stats_routing_elicitation_applies_choices(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(
        lambda _params: {
            "action": "accept",
            "content": {"comparisonLevel": "msoa", "providerPreference": "ons"},
        }
    )
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "os_mcp.stats_routing",
                "arguments": {"query": "Compare life in Leamington Spa and Warwick"},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)
    assert call.get("ok") is True
    data = call.get("data", {})
    assert data.get("provider") == "ons"
    selections = data.get("userSelections", {})
    assert selections.get("comparisonLevel") == "MSOA"
    assert selections.get("providerPreference") == "ONS"


def test_stats_routing_elicitation_cancel_returns_error(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(lambda _params: {"action": "cancel"})
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "os_mcp.stats_routing",
                "arguments": {"query": "Compare life in Leamington Spa and Warwick"},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)
    assert call.get("ok") is False
    assert call.get("status") == 409
    data = call.get("data", {})
    assert data.get("code") == "ELICITATION_CANCELLED"


def test_select_toolsets_elicitation_applies_choices(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(
        lambda _params: {
            "action": "accept",
            "content": {"includeToolsets": ["core_router", "maps_tiles"]},
        }
    )
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "os_mcp.select_toolsets",
                "arguments": {},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)
    assert call.get("ok") is True
    data = call.get("data", {})
    filters = data.get("effectiveFilters", {})
    assert filters.get("includeToolsets") == ["core_router", "maps_tiles"]


def test_select_toolsets_elicitation_cancel_returns_error(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(lambda _params: {"action": "cancel"})
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "os_mcp.select_toolsets",
                "arguments": {},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)
    assert call.get("ok") is False
    data = call.get("data", {})
    assert data.get("code") == "ELICITATION_CANCELLED"


def test_client_supports_elicitation_form_variants():
    assert stdio_adapter._client_supports_elicitation_form({}) is False
    assert stdio_adapter._client_supports_elicitation_form({"elicitation": {}}) is True
    assert stdio_adapter._client_supports_elicitation_form({"elicitation": {"form": {}}}) is True
    assert stdio_adapter._client_supports_elicitation_form({"elicitation": {"url": {}}}) is False


def test_build_stats_routing_elicitation_defaults_from_payload():
    params = stdio_adapter._build_stats_routing_elicitation_params(
        "Compare life in Leamington Spa and Warwick",
        {"comparisonLevel": "msoa", "providerPreference": "ons"},
    )
    properties = params["requestedSchema"]["properties"]
    assert properties["comparisonLevel"]["default"] == "MSOA"
    assert properties["providerPreference"]["default"] == "ONS"


def test_apply_stats_routing_elicitation_invalid_action():
    payload = {}
    ok, error = stdio_adapter._apply_stats_routing_elicitation_choices(payload, {"action": "unexpected"})
    assert ok is False
    assert error and error.get("code") == "ELICITATION_INVALID_RESULT"


def test_is_stats_comparison_query_between_keyword():
    assert stdio_adapter._is_stats_comparison_query(
        "Difference between Leamington Spa and Warwick"
    ) is True


def test_maybe_elicit_stats_routing_unavailable_response(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(lambda _params: None)
    try:
        ok, error = stdio_adapter._maybe_elicit_stats_routing(
            {"query": "Compare life in Leamington Spa and Warwick"}
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)
    assert ok is False
    assert error and error.get("code") == "ELICITATION_UNAVAILABLE"


def test_stdio_main_round_trip_with_elicitation(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"capabilities": {"elicitation": {"form": {}}}},
    }
    tool_call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "tool": "os_mcp.stats_routing",
            "args": {"query": "Compare life in Leamington Spa and Warwick"},
        },
    }
    interleaved_request = {
        "jsonrpc": "2.0",
        "id": 77,
        "method": "tools/list",
        "params": {},
    }
    elicitation_result = {
        "jsonrpc": "2.0",
        "id": "elicitation-1",
        "result": {
            "action": "accept",
            "content": {"comparisonLevel": "LSOA", "providerPreference": "NOMIS"},
        },
    }
    exit_msg = {"jsonrpc": "2.0", "method": "exit"}
    stdin_bytes = (
        frame(initialize)
        + frame(tool_call)
        + frame(interleaved_request)
        + frame(elicitation_result)
        + frame(exit_msg)
    )
    stdin = io.StringIO(stdin_bytes.decode())
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)

    messages = read_all(io.BytesIO(stdout.getvalue().encode()))
    elicitation = next(m for m in messages if m.get("method") == "elicitation/create")
    assert elicitation.get("id") == "elicitation-1"
    params = elicitation.get("params", {})
    assert params.get("mode") == "form"
    schema = params.get("requestedSchema", {})
    properties = schema.get("properties", {})
    assert "comparisonLevel" in properties
    assert "providerPreference" in properties

    tool_response = next(
        m for m in messages if m.get("id") == 2 and isinstance(m.get("result"), dict)
    )
    result = tool_response["result"]
    assert result.get("ok") is True
    data = result.get("data", {})
    assert data.get("provider") == "nomis"
    assert data.get("userSelections", {}).get("comparisonLevel") == "LSOA"
    busy_error = next(m for m in messages if m.get("id") == 77 and isinstance(m.get("error"), dict))
    assert busy_error["error"]["code"] == -32001


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


def test_ons_select_elicitation_applies_choices(monkeypatch, tmp_path):
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
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    captured = {}

    def _handler(params):
        captured["params"] = params
        return {
            "action": "accept",
            "content": {"geographyLevel": "nation", "timeGranularity": "month"},
        }

    stdio_adapter._set_elicitation_handler(_handler)
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "ons_select.search",
                "arguments": {"query": "inflation"},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)

    assert call.get("ok") is True
    params = captured.get("params", {})
    schema = params.get("requestedSchema", {})
    props = schema.get("properties", {})
    assert "geographyLevel" in props
    assert "timeGranularity" in props
    data = call.get("data", {})
    assert isinstance(data, dict)
    assert data.get("needsElicitation") is False


def test_ons_select_elicitation_cancel_returns_original(monkeypatch, tmp_path):
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
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(lambda _params: {"action": "cancel"})
    try:
        call = stdio_adapter.handle_call_tool(
            {
                "name": "ons_select.search",
                "arguments": {"query": "inflation"},
            }
        )
    finally:
        stdio_adapter._set_elicitation_handler(None)

    assert call.get("ok") is True
    data = call.get("data", {})
    assert isinstance(data, dict)
    assert data.get("needsElicitation") is True


def test_stdio_main_round_trip_with_ons_select_elicitation(monkeypatch, tmp_path):
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
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"capabilities": {"elicitation": {"form": {}}}},
    }
    tool_call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "tool": "ons_select.search",
            "args": {"query": "inflation"},
        },
    }
    interleaved_request = {
        "jsonrpc": "2.0",
        "id": 77,
        "method": "tools/list",
        "params": {},
    }
    elicitation_result = {
        "jsonrpc": "2.0",
        "id": "elicitation-1",
        "result": {
            "action": "accept",
            "content": {"geographyLevel": "nation", "timeGranularity": "month"},
        },
    }
    exit_msg = {"jsonrpc": "2.0", "method": "exit"}
    stdin_bytes = (
        frame(initialize)
        + frame(tool_call)
        + frame(interleaved_request)
        + frame(elicitation_result)
        + frame(exit_msg)
    )
    stdin = io.StringIO(stdin_bytes.decode())
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)

    messages = read_all(io.BytesIO(stdout.getvalue().encode()))
    elicitation = next(m for m in messages if m.get("method") == "elicitation/create")
    assert elicitation.get("id") == "elicitation-1"
    params = elicitation.get("params", {})
    assert params.get("mode") == "form"
    schema = params.get("requestedSchema", {})
    properties = schema.get("properties", {})
    assert "geographyLevel" in properties
    assert "timeGranularity" in properties

    tool_response = next(
        m for m in messages if m.get("id") == 2 and isinstance(m.get("result"), dict)
    )
    result = tool_response["result"]
    assert result.get("ok") is True
    data = result.get("data", {})
    assert data.get("needsElicitation") is False
    busy_error = next(m for m in messages if m.get("id") == 77 and isinstance(m.get("error"), dict))
    assert busy_error["error"]["code"] == -32001
