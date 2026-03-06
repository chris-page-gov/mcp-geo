#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.trace_utils import DOCKER_LOCAL_WRAPPER_NAMES


DEFAULT_SESSION_ROOT = REPO_ROOT / "logs" / "sessions"
SENSITIVE_ENV = {"OS_API_KEY", "ONS_API_KEY", "STDIO_KEY", "BEARER_TOKENS"}
ENV_SNAPSHOT_KEYS = [
    "OS_API_KEY",
    "ONS_API_KEY",
    "STDIO_KEY",
    "BEARER_TOKENS",
    "ONS_LIVE_ENABLED",
    "ADMIN_LOOKUP_LIVE_ENABLED",
    "MCP_STDIO_FRAMING",
    "MCP_STDIO_UI_SUPPORTED",
    "LOG_JSON",
    "DEBUG_ERRORS",
]


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _session_id() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def _git_info() -> dict[str, str]:
    info: dict[str, str] = {}
    try:
        info["commit"] = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
            .decode("utf-8")
            .strip()
        )
        info["branch"] = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT)
            .decode("utf-8")
            .strip()
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return info
    return info


def _read_version() -> str:
    version_file = REPO_ROOT / "server" / "__init__.py"
    if not version_file.exists():
        return ""
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip("\"'")
    return ""


def _write_latest(session_root: Path, session_dir: Path) -> None:
    marker = session_root / ".latest"
    marker.write_text(str(session_dir), encoding="utf-8")


def _snapshot_env() -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in ENV_SNAPSHOT_KEYS:
        value = os.getenv(key)
        if value is None:
            continue
        if key in SENSITIVE_ENV:
            snapshot[key] = "set" if value else "unset"
        else:
            snapshot[key] = value
    return snapshot


def _is_docker_local_command(cmd: list[str]) -> bool:
    if not cmd:
        return False
    command = Path(cmd[0]).name
    if command in DOCKER_LOCAL_WRAPPER_NAMES:
        return True
    return any(str(cmd[0]).endswith(name) for name in DOCKER_LOCAL_WRAPPER_NAMES)


def _infer_source(cmd: list[str]) -> str:
    if not cmd:
        return "unknown"
    name = Path(cmd[0]).name
    if "codex" in name:
        return "codex"
    if "claude" in name:
        return "claude"
    if "vscode" in name:
        return "vscode"
    return "unknown"


def _default_surface(source: str) -> str:
    if source == "codex":
        return "cli"
    if source == "claude":
        return "desktop"
    if source == "vscode":
        return "ide"
    return "unknown"


def _pick_session_dir(session_root: Path, name: str | None) -> Path:
    session_root.mkdir(parents=True, exist_ok=True)
    base = name or _session_id()
    candidate = session_root / base
    counter = 1
    while candidate.exists():
        candidate = session_root / f"{base}-{counter}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=True)
    _write_latest(session_root, candidate)
    return candidate


def _default_command(mode: str, source: str) -> list[str]:
    if mode == "stdio":
        if source == "codex":
            return [str(REPO_ROOT / "scripts" / "codex-mcp-local")]
        return [str(REPO_ROOT / "scripts" / "claude-mcp-local")]
    if mode == "http":
        return [str(REPO_ROOT / "scripts" / "start_https_proxy.sh")]
    raise ValueError(f"Unknown mode: {mode}")


def _build_command(mode: str, cmd: list[str], session_dir: Path) -> list[str]:
    if mode == "stdio":
        proxy = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "mcp_stdio_trace_proxy.py"),
            "--log",
            str(session_dir / "mcp-stdio-trace.jsonl"),
            "--",
        ]
        return proxy + cmd
    if mode == "http":
        return cmd
    raise ValueError(f"Unknown mode: {mode}")


def _write_session_metadata(
    session_dir: Path,
    mode: str,
    command: list[str],
    ui_event_path: str,
    http_trace_path: str,
    upstream_log_path: str,
    *,
    source: str,
    surface: str,
    host_profile: str | None,
    client_version: str | None,
    model: str | None,
    scenario_pack: str | None,
    scenario_id: str | None,
) -> None:
    payload = {
        "sessionId": session_dir.name,
        "startedAt": _utc_now(),
        "mode": mode,
        "source": source,
        "surface": surface,
        "hostProfile": host_profile,
        "clientVersion": client_version,
        "model": model,
        "scenarioPack": scenario_pack,
        "scenarioId": scenario_id,
        "cwd": str(Path.cwd()),
        "repoRoot": str(REPO_ROOT),
        "command": command,
        "version": _read_version(),
        "git": _git_info(),
        "paths": {
            "sessionDir": str(session_dir),
            "mcpStdioTrace": str(session_dir / "mcp-stdio-trace.jsonl"),
            "mcpHttpTrace": http_trace_path,
            "uiEvents": ui_event_path,
            "upstreamLog": upstream_log_path,
        },
        "env": _snapshot_env(),
    }
    (session_dir / "session.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a traceable MCP Geo session.")
    parser.add_argument("mode", choices=["stdio", "http"], help="Which transport to run.")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional command to run (prefix with --).",
    )
    parser.add_argument(
        "--session-root",
        default=str(DEFAULT_SESSION_ROOT),
        help="Directory to store session artifacts.",
    )
    parser.add_argument("--name", help="Override the session directory name.")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation.")
    parser.add_argument("--source", help="Host source (for example: codex, claude, vscode).")
    parser.add_argument("--surface", help="Host surface (for example: cli, ide, desktop).")
    parser.add_argument("--host-profile", help="Benchmark host profile identifier.")
    parser.add_argument("--client-version", help="Client version recorded in session metadata.")
    parser.add_argument("--model", help="Model recorded in session metadata.")
    parser.add_argument("--scenario-pack", help="Scenario pack identifier recorded in metadata.")
    parser.add_argument("--scenario-id", help="Scenario identifier recorded in metadata.")
    parser.add_argument(
        "--debug-errors",
        action="store_true",
        help="Enable DEBUG_ERRORS for richer stack traces.",
    )
    args = parser.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    session_root = Path(args.session_root).resolve()
    session_dir = _pick_session_dir(session_root, args.name)

    env = os.environ.copy()
    env["TRACE_SESSION_DIR"] = str(session_dir)
    env["MCP_HTTP_TRACE_LOG"] = str(session_dir / "mcp-http-trace.jsonl")
    env["MCP_UPSTREAM_LOG"] = str(session_dir / "upstream.log")
    if args.debug_errors:
        env["DEBUG_ERRORS"] = "true"

    base_cmd = cmd if cmd else _default_command(args.mode, args.source or "unknown")
    source = args.source or _infer_source(base_cmd)
    surface = args.surface or _default_surface(source)
    if args.mode == "stdio" and _is_docker_local_command(base_cmd):
        ui_event_path = f"/logs/sessions/{session_dir.name}/ui-events.jsonl"
    else:
        ui_event_path = str(session_dir / "ui-events.jsonl")
    env["UI_EVENT_LOG_PATH"] = ui_event_path

    command = _build_command(args.mode, base_cmd, session_dir)
    _write_session_metadata(
        session_dir,
        args.mode,
        command,
        ui_event_path,
        env["MCP_HTTP_TRACE_LOG"],
        env["MCP_UPSTREAM_LOG"],
        source=source,
        surface=surface,
        host_profile=args.host_profile,
        client_version=args.client_version,
        model=args.model,
        scenario_pack=args.scenario_pack,
        scenario_id=args.scenario_id,
    )

    print(f"[mcp-geo] session: {session_dir}", file=sys.stderr)
    print(f"[mcp-geo] command: {' '.join(command)}", file=sys.stderr)
    print(f"[mcp-geo] ui events: {ui_event_path}", file=sys.stderr)

    proc = subprocess.run(command, env=env, check=False)

    if not args.no_report:
        report_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "trace_report.py"),
            str(session_dir),
        ]
        subprocess.run(report_cmd, env=env, check=False)

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
