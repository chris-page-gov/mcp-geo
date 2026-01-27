import io, json, re, os

from server import stdio_adapter
from server.mcp.resource_catalog import MCP_APPS_MIME

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
    call = stdio_adapter.handle_call_tool({"tool": "os_mcp_descriptor", "args": {}})
    assert call.get("ok") is True


def test_call_tool_accepts_arguments_payload():
    call = stdio_adapter.handle_call_tool({"name": "os_mcp_descriptor", "arguments": {}})
    assert call.get("ok") is True
    assert call.get("content")
    assert call["content"][0]["type"] == "text"


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
