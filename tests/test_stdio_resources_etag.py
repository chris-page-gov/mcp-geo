import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "os_mcp.py"

def _rpc(msg):
    data = json.dumps(msg)
    return f"Content-Length: {len(data)}\r\n\r\n{data}".encode()

def _read(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError("EOF")
        if line in (b"\r\n", b"\n"):
            break
        k,v = line.decode().split(":",1)
        headers[k.lower()] = v.strip()
    length = int(headers.get("content-length",0))
    body = stream.read(length)
    return json.loads(body.decode())

def test_stdio_etag_not_modified():
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}))
    proc.stdin.flush()
    first = _read(proc.stdout)
    if "result" not in first:
        first = _read(proc.stdout)
    # First resource fetch
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"name":"skills_getting_started"}}))
    proc.stdin.flush()
    res1 = _read(proc.stdout)
    contents1 = res1["result"]["contents"]
    assert contents1[0]["uri"] == "skills://mcp-geo/getting-started"
    # Second fetch with If-None-Match
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"name":"skills_getting_started","ifNoneMatch":"W/\\\"ignored\\\""}}))
    proc.stdin.flush()
    res2 = _read(proc.stdout)
    contents2 = res2["result"]["contents"]
    assert contents2[0]["uri"] == "skills://mcp-geo/getting-started"
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":4,"method":"shutdown","params":{}}))
    proc.stdin.write(_rpc({"jsonrpc":"2.0","method":"exit"}))
    proc.stdin.flush()
    proc.terminate()
    proc.wait(timeout=5)

def test_stdio_resources_describe():
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}))
    proc.stdin.flush()
    init_resp = _read(proc.stdout)
    if "result" not in init_resp:
        init_resp = _read(proc.stdout)
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":2,"method":"resources/describe","params":{}}))
    proc.stdin.flush()
    desc = _read(proc.stdout)
    if "result" not in desc and desc.get("method") == "log":
        desc = _read(proc.stdout)
    assert "resources" in desc.get("result", {})
    assert any(r.get("name") == "skills_getting_started" for r in desc["result"]["resources"])
    proc.stdin.write(_rpc({"jsonrpc":"2.0","id":3,"method":"shutdown","params":{}}))
    proc.stdin.write(_rpc({"jsonrpc":"2.0","method":"exit"}))
    proc.stdin.flush()
    proc.terminate()
    proc.wait(timeout=5)
