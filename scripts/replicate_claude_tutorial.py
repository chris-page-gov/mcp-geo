#!/usr/bin/env python3
"""Replicate the Claude tutorial flow against the local mcp-geo STDIO adapter.

Usage:
  ./.venv/bin/python scripts/replicate_claude_tutorial.py
  ./.venv/bin/python scripts/replicate_claude_tutorial.py --skip-area-geometry
  ./.venv/bin/python scripts/replicate_claude_tutorial.py --json-out logs/claude-tutorial.json
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER = REPO_ROOT / "scripts" / "os-mcp"
DEFAULT_JSON_OUT = REPO_ROOT / "logs" / "claude-tutorial-repro.json"


def _frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode()
    return header + body


@dataclass
class RpcResponse:
    message: dict[str, Any]

    @property
    def result(self) -> dict[str, Any]:
        value = self.message.get("result")
        if isinstance(value, dict):
            return value
        return {}


class StdioRpcClient:
    """Minimal Content-Length framed JSON-RPC client for STDIO MCP servers."""

    def __init__(
        self,
        python_exe: str,
        adapter_path: Path,
        command_override: str = "",
    ) -> None:
        self._python_exe = python_exe
        self._adapter_path = adapter_path
        self._command_override = command_override.strip()
        self._proc: subprocess.Popen[Any] | None = None
        self._next_id = 1

    def start(self) -> None:
        if self._command_override:
            command = shlex.split(self._command_override)
        else:
            command = [self._python_exe, str(self._adapter_path)]
        self._proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.poll() is None:
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": self._next_id,
                        "method": "shutdown",
                        "params": {},
                    }
                )
                self._read_response(expected_id=self._next_id)
                self._next_id += 1
                self._send({"jsonrpc": "2.0", "method": "exit"})
        except (BrokenPipeError, RuntimeError, ValueError):
            # Process already exited or failed before graceful shutdown.
            pass
        finally:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            self._proc = None

    def initialize(self) -> RpcResponse:
        return self.call("initialize", {})

    def call(self, method: str, params: dict[str, Any]) -> RpcResponse:
        request_id = self._next_id
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        return RpcResponse(self._read_response(expected_id=request_id))

    def _send(self, message: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("STDIO client is not started.")
        try:
            self._proc.stdin.write(_frame(message))
            self._proc.stdin.flush()
        except BrokenPipeError as exc:
            raise RuntimeError("MCP process closed its stdin pipe.") from exc

    def _read_response(self, expected_id: int) -> dict[str, Any]:
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("STDIO client is not started.")
        while True:
            headers: dict[str, str] = {}
            while True:
                line = self._proc.stdout.readline()
                if not line:
                    raise RuntimeError("EOF while waiting for response headers.")
                if line in (b"\r\n", b"\n"):
                    break
                key, value = line.decode("utf-8").split(":", 1)
                headers[key.strip().lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            body = self._proc.stdout.read(length)
            message = json.loads(body.decode("utf-8"))

            # Ignore JSON-RPC notifications, including server log notifications.
            if "id" not in message:
                continue

            msg_id = message.get("id")
            if msg_id != expected_id:
                raise RuntimeError(f"Unexpected RPC response id {msg_id}, expected {expected_id}.")
            return message


def _is_unknown_tool(result: dict[str, Any]) -> bool:
    if result.get("code") == "UNKNOWN_TOOL":
        return True
    data = result.get("data")
    if isinstance(data, dict) and data.get("code") == "UNKNOWN_TOOL":
        return True
    content = result.get("content")
    if isinstance(content, list):
        text_chunks = [chunk.get("text", "") for chunk in content if isinstance(chunk, dict)]
        joined = " ".join(text_chunks).lower()
        return "unknown_tool" in joined or "tool not found" in joined
    return False


def _call_tool_with_alias(
    client: StdioRpcClient,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    candidates = [tool_name]
    if "." in tool_name:
        candidates.append(tool_name.replace(".", "_"))
    for candidate in candidates:
        response = client.call("tools/call", {"name": candidate, "arguments": arguments})
        result = response.result
        if _is_unknown_tool(result):
            continue
        return response.message
    raise RuntimeError(f"Tool not found (dotted and underscore): {tool_name}")


def _extract_data(message: dict[str, Any]) -> dict[str, Any]:
    result = message.get("result")
    if isinstance(result, dict):
        data = result.get("data")
        if isinstance(data, dict):
            return data
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
    return {}


def _print_step(title: str, payload: dict[str, Any]) -> None:
    print(f"\n[{title}]")
    print(json.dumps(payload, indent=2))


def _default_python() -> str:
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run(args: argparse.Namespace) -> int:
    prompts = [
        "Find tools related to postcode search.",
        "Open a map so I can select wards in Westminster.",
        "Fetch the boundary bbox for the selected ward.",
    ]
    print("Claude tutorial prompts:")
    for idx, prompt in enumerate(prompts, start=1):
        print(f"{idx}. {prompt}")

    client = StdioRpcClient(
        python_exe=args.python,
        adapter_path=args.adapter,
        command_override=args.command,
    )
    transcript: dict[str, Any] = {"steps": {}, "prompts": prompts}

    try:
        client.start()
        init = client.initialize().message
        transcript["initialize"] = init
        _print_step("initialize", init.get("result", {}))

        search = client.call("tools/search", {"query": "postcode search"}).message
        transcript["steps"]["tools_search"] = search
        search_result = search.get("result", {})
        _print_step("tools/search", search_result)

        selector = _call_tool_with_alias(
            client,
            "os_apps.render_geography_selector",
            {"level": "WARD", "focusName": "Westminster", "focusLevel": "local_auth"},
        )
        transcript["steps"]["render_geography_selector"] = selector
        _print_step("tools/call os_apps.render_geography_selector", selector.get("result", {}))

        ward_lookup = _call_tool_with_alias(
            client,
            "admin_lookup.find_by_name",
            {"text": args.ward_name, "levels": ["WARD"], "limit": 1},
        )
        transcript["steps"]["ward_lookup"] = ward_lookup
        ward_data = _extract_data(ward_lookup)
        _print_step("tools/call admin_lookup.find_by_name", ward_lookup.get("result", {}))

        ward_id = ""
        ward_name = args.ward_name
        results = ward_data.get("results")
        if isinstance(results, list) and results and isinstance(results[0], dict):
            ward_id = str(results[0].get("id", ""))
            ward_name = str(results[0].get("name", ward_name))

        if ward_id and not args.skip_area_geometry:
            geometry = _call_tool_with_alias(
                client,
                "admin_lookup.area_geometry",
                {"id": ward_id},
            )
            transcript["steps"]["ward_bbox"] = geometry
            _print_step("tools/call admin_lookup.area_geometry", geometry.get("result", {}))
            bbox_data = _extract_data(geometry)
            bbox = bbox_data.get("bbox")
            print(f"\nSelected ward: {ward_name} ({ward_id})")
            print(f"Boundary bbox: {bbox}")
        elif not ward_id:
            print("\nNo ward id found from ward lookup; skipping bbox step.")
        else:
            print("\nSkipped boundary bbox step (--skip-area-geometry).")

        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        print(f"\nTranscript written to: {args.json_out}")
        return 0
    except RuntimeError as exc:
        print(f"\nMCP tutorial replication failed: {exc}", file=sys.stderr)
        if args.command:
            print(
                "Tip: for scripts/os-mcp, prefer the default launcher or pass "
                "'--command \"<venv-python> /path/to/scripts/os-mcp\"'.",
                file=sys.stderr,
            )
        return 1
    finally:
        client.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replicate the Claude tutorial flow against mcp-geo over STDIO."
    )
    parser.add_argument(
        "--command",
        default="",
        help=(
            "Optional command override used to launch the MCP server over STDIO. "
            "Example: '/Users/crpage/repos/mcp-geo/scripts/claude-mcp-local'."
        ),
    )
    parser.add_argument(
        "--python",
        default=_default_python(),
        help=(
            "Python interpreter used to launch the adapter "
            "(default: .venv/bin/python if present)."
        ),
    )
    parser.add_argument(
        "--adapter",
        type=Path,
        default=DEFAULT_ADAPTER,
        help="Path to the STDIO adapter script (default: scripts/os-mcp).",
    )
    parser.add_argument(
        "--ward-name",
        default="St James's",
        help="Ward name used for the post-selector boundary lookup.",
    )
    parser.add_argument(
        "--skip-area-geometry",
        action="store_true",
        help="Skip the final boundary bbox lookup call.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Where to write the JSON transcript.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.command and not args.adapter.exists():
        print(f"Adapter not found: {args.adapter}", file=sys.stderr)
        return 1
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
