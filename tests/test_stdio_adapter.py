import json, subprocess, sys, textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "os_mcp.py"


def _rpc(msg):
    data = json.dumps(msg)
    return f"Content-Length: {len(data)}\r\n\r\n{data}".encode()


def _read_one(stream):
    # Read headers
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


def test_stdio_initialize_and_list_tools():
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    # initialize (skip initial log notification if present)
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    proc.stdin.flush()
    resp1 = _read_one(proc.stdout)
    if "result" not in resp1 and resp1.get("method") == "log":  # notification first
        resp1 = _read_one(proc.stdout)
    assert resp1.get("result", {}).get("server") == "mcp-geo"
    # list tools
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}))
    proc.stdin.flush()
    resp2 = _read_one(proc.stdout)
    assert "tools" in resp2["result"] and isinstance(resp2["result"]["tools"], list)
    # call a trivial tool (dimensions sample)
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"tool": "ons_data.dimensions", "args": {}}}))
    proc.stdin.flush()
    resp3 = _read_one(proc.stdout)
    assert resp3["result"]["ok"] is True
    # shutdown
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 4, "method": "shutdown", "params": {}}))
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "method": "exit"}))
    proc.stdin.flush()
    proc.terminate()
    proc.wait(timeout=5)
