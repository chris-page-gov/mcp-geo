import io, json
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