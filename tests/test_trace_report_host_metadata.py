from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_trace_report_writes_host_metadata_summary(tmp_path: Path) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "sessionId": "host-meta",
                "mode": "stdio",
                "source": "codex",
                "surface": "cli",
                "hostProfile": "codex_cli_stdio",
                "clientVersion": "codex-cli 0.104.0",
                "model": "gpt-5.4",
                "scenarioPack": "codex_vs_claude_host_v1",
                "scenarioId": "tool_search_postcode",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {"ts": 1.0, "direction": "client->server", "json": {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}}},
            {"ts": 1.1, "direction": "server->client", "json": {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-11-25"}}},
            {"ts": 1.2, "direction": "client->server", "json": {"jsonrpc": "2.0", "id": 2, "method": "tools/search", "params": {"query": "postcode"}}},
            {"ts": 1.3, "direction": "server->client", "json": {"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "os_places_by_postcode"}]}}},
        ],
    )

    subprocess.run(
        [sys.executable, "scripts/trace_report.py", str(session_dir)],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    report_text = (session_dir / "report.md").read_text(encoding="utf-8")
    summary = json.loads((session_dir / "summary.json").read_text(encoding="utf-8"))

    assert "Source: codex" in report_text
    assert "Surface: cli" in report_text
    assert "Host profile: codex_cli_stdio" in report_text
    assert summary["session"]["model"] == "gpt-5.4"
    assert summary["hostSignals"]["toolSearchUsage"] == "used"
