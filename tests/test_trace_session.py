from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.trace_session as trace_session


def test_trace_session_keeps_host_ui_event_path_for_codex_wrapper(monkeypatch, tmp_path: Path) -> None:
    session_root = tmp_path / "logs" / "sessions"
    captured: list[dict[str, object]] = []

    def fake_run(command: list[str], env: dict[str, str] | None = None, check: bool = False, **_: object):
        captured.append({"command": command, "env": env, "check": check})
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(trace_session.subprocess, "run", fake_run)
    monkeypatch.setattr(trace_session, "_git_info", lambda: {})
    monkeypatch.setenv("MCP_GEO_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trace_session.py",
            "--session-root",
            str(session_root),
            "--name",
            "codex-trace",
            "--no-report",
            "--source",
            "codex",
            "stdio",
            "--",
            str(trace_session.REPO_ROOT / "scripts" / "codex-mcp-local"),
            "--sample-flag",
        ],
    )

    assert trace_session.main() == 0
    assert len(captured) == 1

    env = captured[0]["env"]
    assert isinstance(env, dict)
    session_dir = session_root / "codex-trace"
    host_ui_path = session_dir / "ui-events.jsonl"
    assert env["UI_EVENT_LOG_PATH"] == str(host_ui_path)
    assert env["MCP_GEO_DOCKER_UI_EVENT_LOG_PATH"] == "/logs/sessions/codex-trace/ui-events.jsonl"

    session_meta = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_meta["paths"]["uiEvents"] == str(host_ui_path)
    assert session_meta["exitCode"] == 0
    assert session_meta["endedAt"].endswith("Z")
