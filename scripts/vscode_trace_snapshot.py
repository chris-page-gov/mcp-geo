#!/usr/bin/env python3
"""Snapshot VS Code MCP trace logs into a trace_session-style directory.

VS Code MCP servers can write long-lived trace files (for example
`logs/vscode-mcp-trace.jsonl`) rather than per-run session directories.

This helper copies the latest VS Code artifacts into a new directory under
`logs/sessions/` using the filenames expected by `scripts/trace_report.py`,
then generates a report.

Usage:
  python scripts/vscode_trace_snapshot.py
  python scripts/vscode_trace_snapshot.py --name my-debug-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_ROOT = REPO_ROOT / "logs" / "sessions"


def _utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _session_id() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-vscode"


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


def _pick_session_dir(session_root: Path, name: str | None) -> Path:
    session_root.mkdir(parents=True, exist_ok=True)
    base = name or _session_id()
    candidate = session_root / base
    counter = 1
    while candidate.exists():
        candidate = session_root / f"{base}-{counter}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=True)
    (session_root / ".latest").write_text(str(candidate), encoding="utf-8")
    return candidate


def _write_session_metadata(session_dir: Path, files: dict[str, str]) -> None:
    payload: dict[str, Any] = {
        "sessionId": session_dir.name,
        "startedAt": _utc_now(),
        "mode": "stdio",
        "source": "vscode",
        "cwd": str(Path.cwd()),
        "repoRoot": str(REPO_ROOT),
        "version": _read_version(),
        "git": _git_info(),
        "paths": files,
        "env": {
            # Snapshot only presence of sensitive keys.
            "OS_API_KEY": "set" if os.getenv("OS_API_KEY") else "unset",
        },
    }
    (session_dir / "session.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot VS Code MCP trace logs into a session dir.")
    parser.add_argument(
        "--session-root",
        default=str(DEFAULT_SESSION_ROOT),
        help="Directory to store session artifacts.",
    )
    parser.add_argument("--name", help="Override the session directory name.")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation.")
    args = parser.parse_args()

    src_trace = REPO_ROOT / "logs" / "vscode-mcp-trace.jsonl"
    if not src_trace.exists():
        print(f"[mcp-geo] missing: {src_trace}", file=sys.stderr)
        return 2

    src_ui = REPO_ROOT / "logs" / "ui-events.vscode-trace.jsonl"

    session_dir = _pick_session_dir(Path(args.session_root).resolve(), args.name)

    dst_trace = session_dir / "mcp-stdio-trace.jsonl"
    shutil.copyfile(src_trace, dst_trace)

    files: dict[str, str] = {
        "sessionDir": str(session_dir),
        "mcpStdioTrace": str(dst_trace),
    }

    if src_ui.exists():
        dst_ui = session_dir / "ui-events.jsonl"
        shutil.copyfile(src_ui, dst_ui)
        files["uiEvents"] = str(dst_ui)

    _write_session_metadata(session_dir, files)

    print(f"[mcp-geo] session: {session_dir}", file=sys.stderr)
    print(f"[mcp-geo] copied: {src_trace} -> {dst_trace}", file=sys.stderr)
    if src_ui.exists():
        print(f"[mcp-geo] copied: {src_ui} -> {session_dir / 'ui-events.jsonl'}", file=sys.stderr)

    if not args.no_report:
        report_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "trace_report.py"),
            str(session_dir),
        ]
        subprocess.run(report_cmd, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

