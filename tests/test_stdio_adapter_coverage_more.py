import io
import json
import sys

import pytest

from server import stdio_adapter
from tools.registry import Tool, register, get as get_tool


def test_handle_get_resource_error_paths():
    with pytest.raises(ValueError):
        stdio_adapter.handle_get_resource({})
    with pytest.raises(LookupError):
        stdio_adapter.handle_get_resource({"uri": "resource://mcp-geo/something"})
    with pytest.raises(LookupError):
        stdio_adapter.handle_get_resource({"uri": "ui://mcp-geo/unknown"})
    with pytest.raises(ValueError):
        stdio_adapter.handle_get_resource({"name": 123})
    with pytest.raises(LookupError):
        stdio_adapter.handle_get_resource({"name": "ui://mcp-geo/unknown"})


def test_sanitize_tool_name_edge_cases():
    assert stdio_adapter._sanitize_tool_name("", {}) == "tool"
    long_name = "a" * 200
    sanitized = stdio_adapter._sanitize_tool_name(long_name, {})
    assert len(sanitized) <= 64
    assert sanitized != long_name
    # Collision branch (same sanitized candidate maps to a different original name).
    collided = stdio_adapter._sanitize_tool_name("same", {"same": "different"})
    assert collided != "same"


def test_rewrite_tool_schema_defensive_returns():
    assert stdio_adapter._rewrite_tool_schema([], sanitized_name="x", original_name="y") == []
    schema = {"type": "object", "properties": []}
    assert stdio_adapter._rewrite_tool_schema(schema, sanitized_name="x", original_name="y") == schema
    schema = {"type": "object", "properties": {"tool": []}}
    assert stdio_adapter._rewrite_tool_schema(schema, sanitized_name="x", original_name="y") == schema


def test_resp_error_includes_data():
    payload = stdio_adapter._resp_error("x", 123, "nope", {"detail": "x"})
    assert payload["error"]["data"]["detail"] == "x"


def test_client_supports_elicitation_form_invalid_types():
    assert stdio_adapter._client_supports_elicitation_form(123) is False  # type: ignore[arg-type]
    assert stdio_adapter._client_supports_elicitation_form({"elicitation": "bad"}) is False


def test_apply_stats_routing_elicitation_choices_accept_missing_content_returns_ok():
    payload = {}
    ok, error = stdio_adapter._apply_stats_routing_elicitation_choices(payload, {"action": "accept"})
    assert ok is True
    assert error is None


def test_maybe_elicit_stats_routing_early_exit_paths(monkeypatch):
    payload = {"query": "Compare A and B"}
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "0")
    ok, error = stdio_adapter._maybe_elicit_stats_routing(dict(payload))
    assert ok is True and error is None

    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {})
    ok, error = stdio_adapter._maybe_elicit_stats_routing(dict(payload))
    assert ok is True and error is None

    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(None)
    ok, error = stdio_adapter._maybe_elicit_stats_routing(dict(payload))
    assert ok is True and error is None

    stdio_adapter._set_elicitation_handler(lambda _params: {"action": "accept"})
    try:
        ok, error = stdio_adapter._maybe_elicit_stats_routing({"query": ""})
        assert ok is True and error is None

        ok, error = stdio_adapter._maybe_elicit_stats_routing({"query": "Tell me about GDP"})
        assert ok is True and error is None

        ok, error = stdio_adapter._maybe_elicit_stats_routing(
            {"query": "Compare A and B", "comparisonLevel": "WARD", "providerPreference": "AUTO"}
        )
        assert ok is True and error is None
    finally:
        stdio_adapter._set_elicitation_handler(None)


def test_maybe_elicit_ons_select_skips_when_not_needed(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(lambda _params: "bad")  # type: ignore[return-value]
    try:
        changed = stdio_adapter._maybe_elicit_ons_select(
            {"query": "inflation"},
            {"query": "inflation", "needsElicitation": True, "elicitationQuestions": []},
        )
        assert changed is False
    finally:
        stdio_adapter._set_elicitation_handler(None)


def test_tool_content_from_data_non_serializable_uses_str():
    content = stdio_adapter._tool_content_from_data(set([1, 2, 3]))
    assert content and content[0]["type"] == "text"
    assert "{" in content[0]["text"] or "set" in content[0]["text"]


def test_extract_initial_view_invalid_lat_lng_returns_none():
    lat, lng, zoom = stdio_adapter._extract_initial_view({"initialLat": "nope", "initialLng": "nope"}, {})
    assert lat is None and lng is None and zoom is None


def test_extract_initial_view_invalid_zoom_returns_none_zoom():
    lat, lng, zoom = stdio_adapter._extract_initial_view(
        {"initialLat": 52.0, "initialLng": -1.0, "initialZoom": "nope"},
        {},
    )
    assert lat == 52.0 and lng == -1.0 and zoom is None


def test_fallback_bbox_invalid_span_env_uses_default(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FALLBACK_BBOX_DEG", "nope")
    bbox = stdio_adapter._fallback_bbox(52.0, -1.0, 16)
    assert len(bbox) == 4


def test_static_map_fallback_includes_map_error_on_render_failure(monkeypatch):
    maps_tool = get_tool("os_maps.render")
    assert maps_tool is not None
    original = maps_tool.handler
    maps_tool.handler = lambda _payload: (500, {"isError": True, "code": "NOPE", "message": "nope"})
    try:
        fallback = stdio_adapter._build_static_map_fallback(
            {"initialLat": 52.0, "initialLng": -1.0, "initialZoom": 16},
            {},
        )
    finally:
        maps_tool.handler = original
    assert isinstance(fallback, dict)
    assert fallback.get("mapError", {}).get("status") == 500


def test_search_tools_validation_and_rewrite_skips_bad_entries(monkeypatch):
    def fake_search_tools(_query, **_kwargs):
        return [
            {"name": None},
            {
                "name": "os_places.by_postcode",
                "inputSchema": {"type": "object", "properties": {"tool": {"const": "os_places.by_postcode"}}},
                "annotations": {},
            },
        ]

    monkeypatch.setattr(stdio_adapter, "search_tools", fake_search_tools)
    with pytest.raises(ValueError):
        stdio_adapter.handle_search_tools({"query": "x", "mode": 123})
    with pytest.raises(ValueError):
        stdio_adapter.handle_search_tools({"query": "x", "limit": 0})
    with pytest.raises(ValueError):
        stdio_adapter.handle_search_tools({"query": "x", "category": 123})
    with pytest.raises(ValueError):
        stdio_adapter.handle_search_tools({"query": "x", "includeSchemas": "bad"})

    ok = stdio_adapter.handle_search_tools({"query": "postcode", "includeSchemas": True})
    assert ok.get("count") == 2


def test_handle_call_tool_payload_not_object_and_non_dict_result():
    with pytest.raises(TypeError):
        stdio_adapter.handle_call_tool({"name": "os_mcp.descriptor", "arguments": "bad"})

    def _handler(_payload):
        return 500, "nope"

    register(
        Tool(
            name="test.non_dict",
            description="test",
            handler=_handler,
        )
    )
    call = stdio_adapter.handle_call_tool({"name": "test.non_dict", "arguments": {}})
    assert call.get("ok") is False
    assert call.get("isError") is True
    assert call.get("content")


def test_read_headers_eof_and_missing_content_length():
    length, error = stdio_adapter._read_headers(io.StringIO(""))
    assert length is None and error is None
    length, error = stdio_adapter._read_headers(io.StringIO("\r\n"))
    assert length is None and error == "Missing Content-Length"


def test_main_defaults_use_sys_streams_line_framing(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "exit"}),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    stdio_adapter.main()
    lines = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    assert any(item.get("id") == 1 and "result" in item for item in lines)


def test_main_emits_startup_and_exit_logs(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    monkeypatch.setenv("MCP_STDIO_LOG_STARTUP", "1")
    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "exit"}),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    logs = [m for m in messages if m.get("method") == "log"]
    assert any("starting" in (m.get("params", {}).get("message") or "") for m in logs)
    assert any("exiting" in (m.get("params", {}).get("message") or "") for m in logs)


def test_main_elicitation_eof_cancels_prompt(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    # No elicitation response provided -> stdin hits EOF while waiting.
    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"capabilities": {"elicitation": {"form": {}}}},
                    }
                ),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "tool": "os_mcp.stats_routing",
                            "args": {"query": "Compare life in Leamington Spa and Warwick"},
                        },
                    }
                ),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    assert any(m.get("method") == "elicitation/create" for m in messages)
    tool_response = next(m for m in messages if m.get("id") == 2 and isinstance(m.get("result"), dict))
    result = tool_response["result"]
    assert result.get("ok") is False
    assert result.get("data", {}).get("code") == "ELICITATION_CANCELLED"


def test_handle_get_resource_success_paths():
    ui = stdio_adapter.handle_get_resource({"uri": "ui://mcp-geo/geography-selector"})
    assert ui.get("contents") and ui["contents"][0]["mimeType"].startswith("text/html")
    skills = stdio_adapter.handle_get_resource({"uri": "skills://mcp-geo/getting-started"})
    assert skills.get("contents") and skills["contents"][0]["mimeType"] == "text/markdown"
    data = stdio_adapter.handle_get_resource({"uri": "resource://mcp-geo/os-exports-index"})
    assert data.get("contents") and data["contents"][0]["mimeType"] == "application/json"
    by_name = stdio_adapter.handle_get_resource({"name": "ui://mcp-geo/geography-selector"})
    assert by_name.get("contents") and by_name["contents"][0]["uri"].startswith("ui://mcp-geo/")


def test_tool_content_from_data_none_returns_empty():
    assert stdio_adapter._tool_content_from_data(None) == []


def test_stats_dashboard_fallback_area_codes_invalid_type_sets_empty_list():
    fallback = stdio_adapter._build_stats_dashboard_fallback({"areaCodes": "nope"})
    assert fallback and fallback.get("areaCodes") == []


def test_misc_handlers_cover_resource_templates_prompts_shutdown():
    assert stdio_adapter.handle_list_resource_templates({}) == {"resourceTemplates": []}
    prompts = stdio_adapter.handle_list_prompts({})
    assert isinstance(prompts.get("prompts"), list)
    assert stdio_adapter.handle_shutdown({}) is None


def test_handle_get_prompt_errors():
    with pytest.raises(ValueError):
        stdio_adapter.handle_get_prompt({})
    with pytest.raises(LookupError):
        stdio_adapter.handle_get_prompt({"name": "does-not-exist"})


def test_handle_call_tool_unknown_tool_raises():
    with pytest.raises(LookupError):
        stdio_adapter.handle_call_tool({"name": "unknown.tool", "arguments": {}})


def test_read_message_line_parse_error_and_skip_blank_line():
    msg, framing, error = stdio_adapter._read_message(io.StringIO("\n{bad}\n"), "line")
    assert msg is None
    assert framing == "line"
    assert error == "Parse error"


def test_read_message_content_length_parse_error():
    body = "{bad}"
    stdin = io.StringIO(f"Content-Length: {len(body)}\r\n\r\n{body}")
    msg, framing, error = stdio_adapter._read_message(stdin, "content-length")
    assert msg is None
    assert framing == "content-length"
    assert error == "Parse error"
