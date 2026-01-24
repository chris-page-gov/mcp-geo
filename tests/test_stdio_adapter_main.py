import io, json
from server import stdio_adapter

def frame(msg):
    body = json.dumps(msg, separators=(",", ":")).encode()
    return f"Content-Length: {len(body)}\r\n\r\n".encode() + body

def read_all(buf: io.BytesIO):
    messages = []
    while buf.tell() < len(buf.getvalue()):
        # parse headers
        headers = {}
        while True:
            line = buf.readline()
            if not line:
                return messages
            if line in (b"\r\n", b"\n"):
                break
            k, v = line.decode().split(":", 1)
            headers[k.lower()] = v.strip()
        length = int(headers.get("content-length", 0))
        body = buf.read(length)
        if not body:
            break
        messages.append(json.loads(body.decode()))
    return messages

def test_adapter_full_sequence():
    # Build a sequence of JSON-RPC requests: initialize, list tools, call tool, get resource, unknown method, exit
    stdin_bytes = b"".join([
        frame({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}),
        frame({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}),
        frame({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"tool":"ons_data.dimensions","args":{}}}),
        frame({"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"name":"admin_boundaries","limit":1}}),
        frame({"jsonrpc":"2.0","id":5,"method":"no_such_method","params":{}}),
        frame({"jsonrpc":"2.0","method":"exit"}),
    ])
    stdin = io.StringIO(stdin_bytes.decode())
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    buf = io.BytesIO(stdout.getvalue().encode())
    msgs = read_all(buf)
    # Filter out log notifications
    results = [m for m in msgs if "result" in m]
    # Expect at least initialize result and tools list
    init = next(m for m in results if m.get("id") == 1)
    assert init["result"]["server"] == "mcp-geo"
    tools_list = next(m for m in results if m.get("id") == 2)
    assert isinstance(tools_list["result"].get("tools"), list)
    tool_call = next(m for m in results if m.get("id") == 3)
    assert tool_call["result"].get("ok") is True
    resource_get = next(m for m in results if m.get("id") == 4)
    payload = json.loads(resource_get["result"]["contents"][0]["text"])
    assert payload.get("name") == "admin_boundaries"
    # Error response for unknown method should have error
    error_msg = next(m for m in msgs if m.get("id") == 5 and "error" in m)
    assert error_msg["error"]["code"] == -32601
