import io, json, re
from server import stdio_adapter

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


def test_tool_names_sanitized_and_resolvable():
    result = stdio_adapter.handle_list_tools({})
    names = [t["name"] for t in result["tools"]]
    assert any(name == "os_places_by_postcode" for name in names)
    assert all(re.match(r"^[A-Za-z0-9_-]{1,64}$", name) for name in names)
    call = stdio_adapter.handle_call_tool({"tool": "ons_data_dimensions", "args": {}})
    assert call.get("ok") is True


def test_call_tool_accepts_arguments_payload():
    call = stdio_adapter.handle_call_tool({"name": "ons_data_dimensions", "arguments": {}})
    assert call.get("ok") is True
    assert call.get("content")
    assert call["content"][0]["type"] == "text"


def test_ui_tools_emit_resource_content(monkeypatch):
    monkeypatch.setenv("MCP_STDIO_RESOURCE_CONTENT", "1")
    call = stdio_adapter.handle_call_tool({"name": "os_apps_render_geography_selector", "arguments": {}})
    assert call.get("ok") is True
    resources = [item for item in call.get("content", []) if item.get("type") == "resource"]
    assert resources
    assert resources[0]["resource"]["uri"].startswith("ui://")


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
