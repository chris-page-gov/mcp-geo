from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_trace_report_writes_event_ledger_artifact(tmp_path: Path) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "sessionId": "ledger-session",
                "mode": "stdio",
                "source": "codex",
                "surface": "cli",
                "startedAt": "2026-03-10T10:00:00Z",
                "endedAt": "2026-03-10T10:00:02Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {
                "ts": 1.0,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"capabilities": {}},
                },
            },
            {
                "ts": 1.1,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"protocolVersion": "2025-11-25"},
                },
            },
        ],
    )

    subprocess.run(
        [sys.executable, "scripts/trace_report.py", str(session_dir)],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    ledger_path = session_dir / "event-ledger.jsonl"
    assert ledger_path.exists()

    summary = json.loads((session_dir / "summary.json").read_text(encoding="utf-8"))
    assert "eventLedger" in summary["artifacts"]

    event_types = [
        json.loads(line)["eventType"]
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert "mcp.session.initialized" in event_types

