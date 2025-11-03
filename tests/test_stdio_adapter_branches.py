import io, json
from server import stdio_adapter

def frame(raw: bytes) -> bytes:
    return f"Content-Length: {len(raw)}\r\n\r\n".encode() + raw

def make(msg: dict) -> bytes:
    return frame(json.dumps(msg, separators=(",", ":")).encode())

def read_messages(buf: io.BytesIO):
    out = []
    while buf.tell() < len(buf.getvalue()):
        headers = {}
        while True:
            line = buf.readline()
            if not line:
                return out
            if line in (b"\r\n", b"\n"):
                break
            k, v = line.decode().split(":", 1)
            headers[k.lower()] = v.strip()
        length = int(headers.get("content-length", 0))
        body = buf.read(length)
        if not body:
            break
        out.append(json.loads(body.decode()))
    return out

def test_parse_error_branch():
    # First message is invalid JSON, second is exit
    stdin_bytes = frame(b"{invalid") + make({"jsonrpc":"2.0","method":"exit"})
    stdin = io.StringIO(stdin_bytes.decode(errors="ignore"))
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    msgs = read_messages(io.BytesIO(stdout.getvalue().encode()))
    err = next(m for m in msgs if m.get("error") and m["error"]["code"] == -32700)
    assert err["error"]["message"] == "Parse error"

def test_invalid_version_branch():
    stdin_bytes = make({"jsonrpc":"1.0","id":1,"method":"initialize","params":{}}) + make({"jsonrpc":"2.0","method":"exit"})
    stdin = io.StringIO(stdin_bytes.decode())
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    msgs = read_messages(io.BytesIO(stdout.getvalue().encode()))
    invalid = next(m for m in msgs if m.get("id") == 1 and m.get("error"))
    assert invalid["error"]["code"] == -32600

def test_invalid_params_type_branch():
    # Use a handler that expects dict params; pass list to trigger -32602
    stdin_bytes = make({"jsonrpc":"2.0","id":1,"method":"tools/list","params":[]}) + make({"jsonrpc":"2.0","method":"exit"})
    stdin = io.StringIO(stdin_bytes.decode())
    stdout = io.StringIO()
    stdio_adapter.main(stdin=stdin, stdout=stdout)
    msgs = read_messages(io.BytesIO(stdout.getvalue().encode()))
    invalid = next(m for m in msgs if m.get("id") == 1 and m.get("error"))
    assert invalid["error"]["code"] == -32602

def test_resources_get_not_modified_etag():
    # First fetch resource, second with ifNoneMatch
    req1 = {"jsonrpc":"2.0","id":1,"method":"resources/get","params":{"name":"admin_boundaries","limit":1}}
    req2 = {"jsonrpc":"2.0","id":2,"method":"resources/get","params":{"name":"admin_boundaries","limit":1}}  # will patch etag after first response
    exit_msg = {"jsonrpc":"2.0","method":"exit"}
    # Build combined stdin after first run to capture etag
    stdin1 = io.StringIO((make(req1)+make(exit_msg)).decode())
    stdout1 = io.StringIO()
    stdio_adapter.main(stdin=stdin1, stdout=stdout1)
    msgs1 = read_messages(io.BytesIO(stdout1.getvalue().encode()))
    res1 = next(m for m in msgs1 if m.get("id") == 1 and m.get("result"))
    etag = res1["result"].get("etag")
    assert etag
    # Second sequence with ifNoneMatch
    req2_with_etag = {"jsonrpc":"2.0","id":1,"method":"resources/get","params":{"name":"admin_boundaries","limit":1,"ifNoneMatch":etag}}
    stdin2 = io.StringIO((make(req2_with_etag)+make(exit_msg)).decode())
    stdout2 = io.StringIO()
    stdio_adapter.main(stdin=stdin2, stdout=stdout2)
    msgs2 = read_messages(io.BytesIO(stdout2.getvalue().encode()))
    res2 = next(m for m in msgs2 if m.get("id") == 1 and m.get("result"))
    assert res2["result"].get("notModified") is True