#!/usr/bin/env python3
"""Helper client for the mcp-geo STDIO adapter.

Usage examples:
    python scripts/mcp_client.py initialize
    python scripts/mcp_client.py tools/list
    python scripts/mcp_client.py tools/call ons_data.dimensions '{"args":{}}'
    python scripts/mcp_client.py --repl   # interactive mode

This spawns the adapter each run (stateless). For interactive sessions, run the
adapter manually and use a named pipe or another tool.
"""
from __future__ import annotations
import json, subprocess, sys
from typing import Any, Dict
from pathlib import Path

SCRIPT = Path(__file__).parent / "os-mcp"


def frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, separators=(",", ":")).encode()
    return f"Content-Length: {len(body)}\r\n\r\n".encode() + body


def read_response(proc: "subprocess.Popen[Any]", skip_logs: bool = True) -> dict[str, Any]:  # type: ignore[type-arg]
    # Read headers
    headers: Dict[str, str] = {}
    while True:
        line: bytes = proc.stdout.readline()  # type: ignore[attr-defined]
        if not line:
            raise SystemExit("EOF before response headers")
        if line in (b"\r\n", b"\n"):
            break
        key, val = line.decode().split(":", 1)
        headers[key.lower()] = val.strip()
    length = int(headers.get("content-length", "0"))
    body: bytes = proc.stdout.read(length)  # type: ignore[attr-defined]
    msg = json.loads(body.decode())
    if skip_logs and msg.get("method") == "log" and "result" not in msg:
        return read_response(proc, skip_logs=skip_logs)
    return msg


def _start_proc():
    return subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def repl() -> int:
    proc = _start_proc()
    assert proc.stdin and proc.stdout
    proc.stdin.write(frame({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}))
    proc.stdin.flush()
    init = read_response(proc)
    print("Initialized:", json.dumps(init.get("result", init), indent=2))
    next_id = 2
    try:
        while True:
            line = input("mcp> ").strip()
            if not line:
                continue
            if line in {"quit", "exit"}:
                break
            # syntax: method [json]
            parts = line.split(" ", 1)
            method = parts[0]
            params: Dict[str, Any] = {}
            if len(parts) == 2:
                try:
                    params = json.loads(parts[1]) if parts[1].strip() else {}
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}")
                    continue
            proc.stdin.write(frame({"jsonrpc":"2.0","id":next_id,"method":method,"params":params}))
            proc.stdin.flush()
            resp = read_response(proc)
            print(json.dumps(resp, indent=2))
            next_id += 1
    finally:
        proc.stdin.write(frame({"jsonrpc":"2.0","id":next_id,"method":"shutdown","params":{}}))
        proc.stdin.write(frame({"jsonrpc":"2.0","method":"exit"}))
        proc.stdin.flush()
        proc.wait(timeout=5)
    return 0


def main() -> int:
    if not SCRIPT.exists():
        print("Adapter script not found", file=sys.stderr)
        return 1
    if len(sys.argv) >= 2 and sys.argv[1] == "--repl":
        return repl()
    if len(sys.argv) < 2:
        print("Usage: python scripts/mcp_client.py <method> [<toolName>] [<jsonParams>] or --repl")
        return 1
    method = sys.argv[1]
    sys_argv_rest = sys.argv
    params: dict[str, Any] = {}
    # Generic argument parsing: if a second arg and method == tools/call treat it as tool name unless JSON; if third (or second if not tools/call) is JSON parse into params
    arg_index = 2
    if method == "tools/call":
        if len(sys_argv_rest) < 3:
            print("Need tool name", file=sys.stderr)
            return 1
        # If explicit JSON payload provided as second arg starting with '{', assume inline params containing tool field
        if sys_argv_rest[2].startswith('{'):
            try:
                inline = json.loads(sys_argv_rest[2])
                if isinstance(inline, dict):
                    params.update(inline)
            except json.JSONDecodeError:
                print("Invalid JSON params", file=sys.stderr)
                return 1
        else:
            params["tool"] = sys_argv_rest[2]
        arg_index = 3
    if len(sys_argv_rest) >= arg_index + 1:
        candidate = sys_argv_rest[arg_index]
        if candidate.startswith('{'):
            try:
                extra = json.loads(candidate)
                if isinstance(extra, dict):
                    params.update(extra)
            except json.JSONDecodeError:
                print("Invalid JSON params", file=sys.stderr)
                return 1
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    if not proc.stdin or not proc.stdout:
        print("Failed to start adapter", file=sys.stderr)
        return 1
    # initialize first
    proc.stdin.write(frame({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}))
    proc.stdin.flush()
    init_resp = read_response(proc)
    # actual request
    proc.stdin.write(frame({"jsonrpc":"2.0","id":2,"method":method,"params":params}))
    proc.stdin.flush()
    resp = read_response(proc)
    # shutdown politely
    proc.stdin.write(frame({"jsonrpc":"2.0","id":3,"method":"shutdown","params":{}}))
    proc.stdin.write(frame({"jsonrpc":"2.0","method":"exit"}))
    proc.stdin.flush()
    # Print results
    out = {"init": init_resp, "response": resp}
    print(json.dumps(out, indent=2))
    proc.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
