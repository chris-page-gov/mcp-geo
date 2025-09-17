import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "os-mcp"


def _rpc(msg):
    data = json.dumps(msg)
    return f"Content-Length: {len(data)}\r\n\r\n{data}".encode()


def _read_one(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError("EOF before headers complete")
        if line in (b"\r\n", b"\n"):
            break
        key, val = line.decode().split(":", 1)
        headers[key.lower()] = val.strip()
    length = int(headers.get("content-length", 0))
    body = stream.read(length)
    return json.loads(body.decode())


def test_stdio_resources_get_admin_boundaries():
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    proc.stdin.flush()
    first = _read_one(proc.stdout)
    if "result" not in first and first.get("method") == "log":
        first = _read_one(proc.stdout)
    # Get resource
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 2, "method": "resources/get", "params": {"name": "admin_boundaries", "limit": 1, "page": 1}}))
    proc.stdin.flush()
    resp = _read_one(proc.stdout)
    assert resp["result"]["name"] == "admin_boundaries"
    assert resp["result"]["data"]["limit"] == 1
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": {}}))
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "method": "exit"}))
    proc.stdin.flush()
    proc.terminate()
    proc.wait(timeout=5)
