#!/usr/bin/env python3
"""Probe MCP-Apps UI content modes over STDIO.

Examples:
  python3 scripts/mcp_ui_mode_probe.py
  python3 scripts/mcp_ui_mode_probe.py --save logs/ui-probe.json -- \
    /Users/crpage/repos/mcp-geo/scripts/claude-mcp-local
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


MCP_APPS_MIME = "text/html;profile=mcp-app"
DEFAULT_MODES = ("resource_link", "embedded", "text")
DEFAULT_RESOURCE_URI = "ui://mcp-geo/statistics-dashboard"


def _frame_line(message: dict[str, Any]) -> bytes:
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


def _send_line(proc: subprocess.Popen[Any], message: dict[str, Any]) -> None:
    if proc.stdin is None:
        raise RuntimeError("Missing stdin pipe")
    proc.stdin.write(_frame_line(message))
    proc.stdin.flush()


def _read_for_id(
    proc: subprocess.Popen[Any],
    expected_id: int,
    timeout_s: float,
) -> dict[str, Any]:
    if proc.stdout is None:
        raise RuntimeError("Missing stdout pipe")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("EOF while waiting for response")
        text = line.decode("utf-8", errors="replace").strip()
        if not text:
            continue
        try:
            message = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        if message.get("id") == expected_id:
            return message
    raise TimeoutError(f"Timed out waiting for id={expected_id}")


def _build_initialize(ui_capability: bool) -> dict[str, Any]:
    capabilities: dict[str, Any] = {}
    if ui_capability:
        capabilities = {
            "extensions": {
                "io.modelcontextprotocol/ui": {
                    "mimeTypes": [MCP_APPS_MIME],
                }
            }
        }
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": capabilities,
            "clientInfo": {"name": "mcp-ui-mode-probe", "version": "0.1.0"},
        },
    }


def _extract_content_types(result: dict[str, Any]) -> list[str]:
    content = result.get("content")
    if not isinstance(content, list):
        return []
    content_types: list[str] = []
    for block in content:
        if isinstance(block, dict):
            value = block.get("type")
            if isinstance(value, str):
                content_types.append(value)
    return content_types


def _select_probe_tool_name(tools_response: dict[str, Any]) -> str | None:
    result = tools_response.get("result")
    if not isinstance(result, dict):
        return None
    tools = result.get("tools")
    if not isinstance(tools, list):
        return None
    names = {
        item.get("name")
        for item in tools
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if "os_apps_render_ui_probe" in names:
        return "os_apps_render_ui_probe"
    if "os_apps.render_ui_probe" in names:
        return "os_apps.render_ui_probe"
    return None


def _default_command(repo_root: Path) -> list[str]:
    return [str(repo_root / "scripts" / "claude-mcp-local")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe MCP-Apps UI content modes over STDIO.")
    parser.add_argument(
        "--modes",
        default=",".join(DEFAULT_MODES),
        help="Comma-separated modes to test (default: resource_link,embedded,text).",
    )
    parser.add_argument(
        "--resource-uri",
        default=DEFAULT_RESOURCE_URI,
        help="UI resource URI for os_apps.render_ui_probe.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--no-ui-capability",
        action="store_true",
        help="Do not advertise MCP-Apps UI capability in initialize.",
    )
    parser.add_argument(
        "--save",
        help="Optional path to write full JSON response payloads.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional server command (prefix with --).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        command = _default_command(repo_root)

    modes = [item.strip() for item in args.modes.split(",") if item.strip()]
    if not modes:
        modes = list(DEFAULT_MODES)

    env = dict(os.environ)
    env.setdefault("MCP_STDIO_FRAMING", "line")

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    payload_log: dict[str, Any] = {
        "command": command,
        "modes": modes,
        "resourceUri": args.resource_uri,
        "results": [],
    }
    exit_code = 0
    try:
        _send_line(proc, _build_initialize(ui_capability=not args.no_ui_capability))
        init_response = _read_for_id(proc, expected_id=1, timeout_s=args.timeout)
        payload_log["initialize"] = init_response

        _send_line(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        tools_response = _read_for_id(proc, expected_id=2, timeout_s=args.timeout)
        payload_log["toolsList"] = tools_response
        probe_tool_name = _select_probe_tool_name(tools_response)
        next_id = 3
        if probe_tool_name is None:
            print("probe tool not found: os_apps.render_ui_probe", file=sys.stderr)
            print(
                "hint: rebuild/update the runtime image "
                "(for claude-mcp-local, set MCP_GEO_DOCKER_BUILD=always once).",
                file=sys.stderr,
            )
            exit_code = 2
        else:
            for mode in modes:
                _send_line(
                    proc,
                    {
                        "jsonrpc": "2.0",
                        "id": next_id,
                        "method": "tools/call",
                        "params": {
                            "name": probe_tool_name,
                            "arguments": {
                                "contentMode": mode,
                                "resourceUri": args.resource_uri,
                            },
                        },
                    },
                )
                call_response = _read_for_id(proc, expected_id=next_id, timeout_s=args.timeout)
                payload_log["results"].append({"mode": mode, "response": call_response})
                error = call_response.get("error")
                if isinstance(error, dict):
                    message = error.get("message", "unknown error")
                    print(f"{mode:>13}: rpc_error={message}")
                else:
                    result = call_response.get("result", {})
                    if not isinstance(result, dict):
                        print(f"{mode:>13}: invalid result payload")
                        next_id += 1
                        continue
                    ok = bool(result.get("ok"))
                    types = _extract_content_types(result)
                    print(f"{mode:>13}: ok={ok} content_types={types}")
                next_id += 1

        _send_line(
            proc,
            {"jsonrpc": "2.0", "id": next_id, "method": "shutdown", "params": {}},
        )
        _read_for_id(proc, expected_id=next_id, timeout_s=args.timeout)
        _send_line(proc, {"jsonrpc": "2.0", "method": "exit"})
    finally:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(payload_log, indent=2), encoding="utf-8")
        print(f"saved: {save_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
