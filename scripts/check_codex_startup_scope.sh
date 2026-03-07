#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="${MCP_CODEX_WRAPPER:-$REPO_ROOT/scripts/codex-mcp-local}"
BUILD_MODE="${MCP_GEO_DOCKER_BUILD:-never}"
TIMEOUT_SEC="${MCP_CODEX_SCOPE_TIMEOUT_SEC:-45}"
EXPECT_TOOLSET="${MCP_TOOLS_DEFAULT_TOOLSET_EXPECT:-starter}"
EXPECT_INCLUDE="${MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS_EXPECT:-features_layers}"

if [[ ! -x "$WRAPPER" ]]; then
  echo "ERROR: wrapper is not executable: $WRAPPER" >&2
  exit 2
fi

python3 - "$WRAPPER" "$BUILD_MODE" "$TIMEOUT_SEC" "$EXPECT_TOOLSET" "$EXPECT_INCLUDE" <<'PY'
import json
import os
import subprocess
import sys
from typing import Any

wrapper, build_mode, timeout_s, expect_toolset, expect_include = sys.argv[1:6]
timeout = int(timeout_s)
request = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n'


def run_count(toolset: str | None, include: str | None) -> tuple[int, list[str]]:
    env = dict(os.environ)
    env["MCP_GEO_DOCKER_BUILD"] = build_mode
    for key in (
        "MCP_TOOLS_DEFAULT_TOOLSET",
        "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS",
        "MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS",
    ):
        env.pop(key, None)
    if toolset:
        env["MCP_TOOLS_DEFAULT_TOOLSET"] = toolset
    if include:
        env["MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS"] = include

    proc = subprocess.run(
        [wrapper],
        input=request,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )
    stderr_tail = proc.stderr.splitlines()[-8:]
    if proc.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "error": "wrapper_nonzero",
                    "returncode": proc.returncode,
                    "stderrTail": stderr_tail,
                }
            )
        )
    line = next((ln for ln in proc.stdout.splitlines() if ln.strip()), "")
    if not line:
        raise RuntimeError(
            json.dumps({"error": "empty_stdout", "stderrTail": stderr_tail})
        )
    try:
        payload: dict[str, Any] = json.loads(line)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            json.dumps(
                {
                    "error": "bad_json",
                    "detail": str(exc),
                    "linePrefix": line[:400],
                }
            )
        ) from exc
    tools = payload.get("result", {}).get("tools")
    if not isinstance(tools, list):
        raise RuntimeError(
            json.dumps(
                {
                    "error": "missing_tools",
                    "payloadKeys": list(payload.keys()),
                    "stderrTail": stderr_tail,
                }
            )
        )
    return len(tools), stderr_tail


try:
    baseline_count, baseline_stderr = run_count(None, None)
    scoped_count, scoped_stderr = run_count(expect_toolset, expect_include)
except Exception as exc:  # noqa: BLE001
    print(f"FAIL: {exc}")
    sys.exit(1)

print(f"wrapper={wrapper}")
print(f"build_mode={build_mode}")
print(f"expected_scope={expect_toolset}+{expect_include}")
print(f"baseline_tools={baseline_count}")
print(f"scoped_tools={scoped_count}")

if scoped_count <= 0:
    print("FAIL: scoped tool count is zero")
    sys.exit(1)
if scoped_count >= baseline_count:
    print("FAIL: scoped tool count is not lower than baseline")
    sys.exit(1)

print("PASS: scoped startup discovery is active")
if baseline_stderr:
    print(f"baseline_stderr_tail={baseline_stderr[-1]}")
if scoped_stderr:
    print(f"scoped_stderr_tail={scoped_stderr[-1]}")
PY
