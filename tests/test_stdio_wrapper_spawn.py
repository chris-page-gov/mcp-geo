import json, subprocess, sys
from pathlib import Path

LEGACY_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "os-mcp"

def _rpc(msg):
    data = json.dumps(msg, separators=(",", ":"))
    return f"Content-Length: {len(data)}\r\n\r\n{data}".encode()

def _read(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError("EOF before headers complete")
        if line in (b"\r\n", b"\n"):
            break
        k, v = line.decode().split(":", 1)
        headers[k.lower()] = v.strip()
    length = int(headers.get("content-length", 0))
    body = stream.read(length)
    return json.loads(body.decode())

def test_legacy_wrapper_initialize():
    assert LEGACY_SCRIPT.exists(), "Legacy wrapper script missing"
    proc = subprocess.Popen([sys.executable, str(LEGACY_SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    proc.stdin.flush()
    first = _read(proc.stdout)
    if "result" not in first and first.get("method") == "log":
        first = _read(proc.stdout)
    assert first.get("result", {}).get("server") == "mcp-geo"
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": {}}))
    proc.stdin.write(_rpc({"jsonrpc": "2.0", "method": "exit"}))
    proc.stdin.flush()
    proc.wait(timeout=5)
