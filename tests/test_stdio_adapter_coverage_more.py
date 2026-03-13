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


def test_tool_content_from_data_truncates_large_payload(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_TOOL_CONTENT_MAX_BYTES", "1024")
    payload = {"items": [{"i": idx, "value": "x" * 120} for idx in range(100)]}
    content = stdio_adapter._tool_content_from_data(payload)
    assert content and content[0]["type"] == "text"
    text = content[0]["text"]
    assert "content truncated by stdio adapter" in text
    assert "result.data" in text


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
    assert fallback.get("guidance", {}).get("widgetUnsupported") is True
    assert fallback.get("guidance", {}).get("preferredNextTools")


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


def test_main_sanitizes_internal_errors(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    monkeypatch.setitem(
        stdio_adapter.HANDLERS,
        "test/boom",
        lambda _params: (_ for _ in ()).throw(RuntimeError("secret-stdio-error")),
    )
    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "test/boom", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "exit"}),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    error_msg = next(item["error"] for item in messages if item.get("id") == 2)
    assert error_msg["code"] == -32603
    assert error_msg["message"] == "Internal error"
    assert "secret-stdio-error" not in json.dumps(error_msg)
    assert isinstance(error_msg.get("data", {}).get("correlationId"), str)


def test_internal_error_logs_exception_type_only(monkeypatch):
    captured: dict[str, object] = {}

    def fake_error(message: str, *args: object) -> None:
        captured["message"] = message
        captured["args"] = args

    monkeypatch.setattr(stdio_adapter.logger, "error", fake_error)
    payload = stdio_adapter._internal_error(
        "id-1", "tools/list", RuntimeError("secret-stdio-token")
    )
    assert payload["error"]["message"] == "Internal error"
    assert isinstance(payload.get("error", {}).get("data", {}).get("correlationId"), str)

    serialized = json.dumps(captured)
    assert "secret-stdio-token" not in serialized
    assert "RuntimeError" in serialized


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
    ui_html = ui["contents"][0]["text"]
    assert 'src="vendor/maplibre-gl.js"' in ui_html
    assert 'href="vendor/maplibre-gl.css"' in ui_html
    assert 'src="/ui/vendor/maplibre-gl.js"' not in ui_html
    assert 'href="/ui/vendor/maplibre-gl.css"' not in ui_html
    skills = stdio_adapter.handle_get_resource({"uri": "skills://mcp-geo/getting-started"})
    assert skills.get("contents") and skills["contents"][0]["mimeType"] == "text/markdown"
    data = stdio_adapter.handle_get_resource({"uri": "resource://mcp-geo/os-exports-index"})
    assert data.get("contents") and data["contents"][0]["mimeType"] == "application/json"
    by_name = stdio_adapter.handle_get_resource({"name": "ui://mcp-geo/geography-selector"})
    assert by_name.get("contents") and by_name["contents"][0]["uri"].startswith("ui://mcp-geo/")
    by_data_name = stdio_adapter.handle_get_resource({"name": "resource://mcp-geo/os-exports-index"})
    assert by_data_name.get("contents") and by_data_name["contents"][0]["mimeType"] == "application/json"


def test_tool_content_from_data_none_returns_empty():
    assert stdio_adapter._tool_content_from_data(None) == []


def test_stats_dashboard_fallback_area_codes_invalid_type_sets_empty_list():
    fallback = stdio_adapter._build_stats_dashboard_fallback({"areaCodes": "nope"})
    assert fallback and fallback.get("areaCodes") == []
    assert fallback.get("guidance", {}).get("widgetUnsupported") is True


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


def test_read_message_autodetect_line_mode_success_and_parse_error():
    msg, framing, error = stdio_adapter._read_message(
        io.StringIO('{"jsonrpc":"2.0","id":1}\n'),
        None,
    )
    assert isinstance(msg, dict)
    assert framing == "line"
    assert error is None

    msg, framing, error = stdio_adapter._read_message(io.StringIO("{bad}\n"), None)
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


def test_read_message_content_length_error_and_eof_paths():
    msg, framing, error = stdio_adapter._read_message(
        io.StringIO("Content-Length: nope\r\n\r\n"),
        "content-length",
    )
    assert msg is None
    assert framing == "content-length"
    assert error == "Invalid Content-Length"

    msg, framing, error = stdio_adapter._read_message(io.StringIO(""), "content-length")
    assert msg is None
    assert framing == "content-length"
    assert error is None

    msg, framing, error = stdio_adapter._read_message(
        io.StringIO("Content-Length: 5\r\n\r\n"),
        "content-length",
    )
    assert msg is None
    assert framing == "content-length"
    assert error is None


def test_read_message_autodetect_content_length_error_paths():
    msg, framing, error = stdio_adapter._read_message(io.StringIO("\n"), None)
    assert msg is None
    assert framing is None
    assert error is None

    msg, framing, error = stdio_adapter._read_message(
        io.StringIO("Content-Length: nope\r\n\r\n"),
        None,
    )
    assert msg is None
    assert framing == "content-length"
    assert error == "Invalid Content-Length"

    msg, framing, error = stdio_adapter._read_message(
        io.StringIO("Content-Length: 5\r\n\r\n"),
        None,
    )
    assert msg is None
    assert framing == "content-length"
    assert error is None


def test_main_handles_parse_error_and_missing_params_branch(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    stdin = io.StringIO(
        "\n".join(
            [
                "{bad}",
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                json.dumps({"jsonrpc": "2.0", "method": "exit"}),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    parse_error = next(item for item in messages if item.get("error", {}).get("code") == -32700)
    assert parse_error["error"]["message"] == "Parse error"
    tools_list = next(item for item in messages if item.get("id") == 2 and "result" in item)
    assert "tools" in tools_list["result"]


def test_main_maps_lookup_value_and_type_errors(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_FRAMING", "line")
    monkeypatch.setitem(stdio_adapter.HANDLERS, "test/lookup", lambda _params: (_ for _ in ()).throw(LookupError("missing")))
    monkeypatch.setitem(stdio_adapter.HANDLERS, "test/value", lambda _params: (_ for _ in ()).throw(ValueError("bad value")))
    monkeypatch.setitem(stdio_adapter.HANDLERS, "test/type", lambda _params: (_ for _ in ()).throw(TypeError("bad type")))

    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "test/lookup", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 3, "method": "test/value", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "id": 4, "method": "test/type", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "exit"}),
                "",
            ]
        )
    )
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    by_id = {item.get("id"): item for item in messages if item.get("id") in {2, 3, 4}}
    assert by_id[2]["error"]["code"] == 1001
    assert by_id[3]["error"]["code"] == 1002
    assert by_id[4]["error"]["code"] == 1003


def test_helper_functions_cover_bool_env_and_modes(monkeypatch):
    monkeypatch.setenv("STDIO_TEST_BOOL", "1")
    assert stdio_adapter._read_bool_env("STDIO_TEST_BOOL") is True
    assert stdio_adapter._bool_env("STDIO_TEST_BOOL", default=False) is True
    monkeypatch.setattr(stdio_adapter, "CLIENT_INFO", {"name": "Claude Desktop"})
    assert stdio_adapter._is_claude_client() is True
    monkeypatch.setattr(stdio_adapter, "CLIENT_INFO", {"name": 123})
    assert stdio_adapter._is_claude_client() is False
    assert stdio_adapter._normalize_apps_content_mode("text") == "text"
    assert stdio_adapter._normalize_apps_content_mode("resource_link") == "resource_link"
    assert stdio_adapter._normalize_apps_content_mode("embedded") == "embedded"


def test_elicitation_early_return_branches(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "0")
    changed = stdio_adapter._maybe_elicit_ons_select({}, {"needsElicitation": True, "query": "x"})
    assert changed is False

    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {})
    changed = stdio_adapter._maybe_elicit_ons_select({}, {"needsElicitation": True, "query": "x"})
    assert changed is False

    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(None)
    changed = stdio_adapter._maybe_elicit_ons_select({}, {"needsElicitation": True, "query": "x"})
    assert changed is False

    stdio_adapter._set_elicitation_handler(lambda _params: {"action": "accept"})
    try:
        changed = stdio_adapter._maybe_elicit_ons_select({}, {"needsElicitation": False, "query": "x"})
        assert changed is False
        changed = stdio_adapter._maybe_elicit_ons_select({}, {"needsElicitation": True, "query": ""})
        assert changed is False
    finally:
        stdio_adapter._set_elicitation_handler(None)


def test_select_toolset_elicitation_guard_branches(monkeypatch):
    payload = {"query": "maps"}
    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "0")
    ok, error = stdio_adapter._maybe_elicit_select_toolsets(dict(payload))
    assert ok is True and error is None

    monkeypatch.setenv("MCP_STDIO_ELICITATION_ENABLED", "1")
    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {})
    ok, error = stdio_adapter._maybe_elicit_select_toolsets(dict(payload))
    assert ok is True and error is None

    monkeypatch.setattr(stdio_adapter, "CLIENT_CAPABILITIES", {"elicitation": {"form": {}}})
    stdio_adapter._set_elicitation_handler(None)
    ok, error = stdio_adapter._maybe_elicit_select_toolsets(dict(payload))
    assert ok is True and error is None

    ok, error = stdio_adapter._maybe_elicit_select_toolsets({"skipElicitation": True})
    assert ok is True and error is None

    ok, error = stdio_adapter._maybe_elicit_select_toolsets({"toolset": "maps_tiles"})
    assert ok is True and error is None

    stdio_adapter._set_elicitation_handler(lambda _params: "bad")  # type: ignore[return-value]
    try:
        ok, error = stdio_adapter._maybe_elicit_select_toolsets(dict(payload))
        assert ok is False
        assert error and error.get("code") == "ELICITATION_UNAVAILABLE"
    finally:
        stdio_adapter._set_elicitation_handler(None)


def test_tool_content_limit_bytes_invalid_env(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_TOOL_CONTENT_MAX_BYTES", "bad-value")
    assert stdio_adapter._tool_content_limit_bytes() == stdio_adapter._STDIO_TOOL_CONTENT_MAX_BYTES_DEFAULT


def test_stdio_validation_branches_for_toolset_and_prompt_success(monkeypatch):
    with pytest.raises(ValueError):
        stdio_adapter.handle_list_tools({"toolset": 123})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        stdio_adapter.handle_search_tools({"query": "x", "toolset": 123})  # type: ignore[arg-type]
    monkeypatch.setattr(stdio_adapter, "list_prompt_defs", lambda: [{"name": "demo"}])
    monkeypatch.setattr(stdio_adapter, "get_prompt_def", lambda _name: {"messages": [{"role": "user"}]})
    prompts = stdio_adapter.handle_list_prompts({}).get("prompts", [])
    assert prompts[0]["name"] == "demo"
    prompt = stdio_adapter.handle_get_prompt({"name": "demo"})
    assert "messages" in prompt
