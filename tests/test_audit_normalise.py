from __future__ import annotations

import json
from pathlib import Path

from server.audit.normalise import build_event_ledger, load_event_schema, write_event_ledger


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_build_event_ledger_normalizes_trace_artifacts_and_redacts_secrets(tmp_path: Path) -> None:
    base_ts = 1773136800.0
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "sessionId": "dsap-session",
                "startedAt": "2026-03-10T10:00:00Z",
                "endedAt": "2026-03-10T10:00:09Z",
                "mode": "stdio",
                "source": "codex",
                "surface": "cli",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {
                "ts": base_ts + 1.0,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"capabilities": {"tools": {"listChanged": True}}},
                },
            },
            {
                "ts": base_ts + 1.1,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"protocolVersion": "2025-11-25"},
                },
            },
            {
                "ts": base_ts + 1.2,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {"query": "postcode"},
                },
            },
            {
                "ts": base_ts + 1.3,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "os_places.by_postcode",
                        "arguments": {"postcode": "SW1A 1AA", "api_key": "secret-value"},
                    },
                },
            },
            {
                "ts": base_ts + 1.4,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {"data": {"results": [{"postcode": "SW1A 1AA"}]}},
                },
            },
            {
                "ts": base_ts + 1.5,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "resources/read",
                    "params": {"uri": "ui://mcp-geo/geography-selector"},
                },
            },
        ],
    )
    _write_jsonl(
        session_dir / "ui-events.jsonl",
        [
            {
                "eventId": "ui-1",
                "eventType": "select_result",
                "timestamp": base_ts + 1.6,
                "source": "geography-selector",
                "payload": {"label": "Westminster", "token": "secret-token"},
                "context": {"mode": "area"},
            }
        ],
    )

    events = build_event_ledger(session_dir)
    schema = load_event_schema()
    schema_event_types = set(schema["properties"]["eventType"]["enum"])

    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert events[0]["eventType"] == "conversation.started"
    assert events[-1]["eventType"] == "conversation.closed"
    assert {event["eventType"] for event in events} >= {
        "conversation.started",
        "mcp.session.initialized",
        "mcp.tools.list",
        "mcp.tool.call",
        "mcp.tool.result",
        "mcp.resource.read",
        "ui.choice.made",
        "conversation.closed",
    }
    assert all(event["eventType"] in schema_event_types for event in events)
    assert all(event["conversationId"] == "dsap-session" for event in events)

    tool_call = next(event for event in events if event["eventType"] == "mcp.tool.call")
    assert tool_call["data"]["arguments"]["api_key"] == "[REDACTED]"

    ui_choice = next(event for event in events if event["eventType"] == "ui.choice.made")
    assert ui_choice["data"]["payload"]["token"] == "[REDACTED]"

    ledger_path = write_event_ledger(session_dir)
    assert ledger_path.exists()
    written_lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert len(written_lines) == len(events)


def test_build_event_ledger_does_not_invent_conversation_closed_without_end_marker(
    tmp_path: Path,
) -> None:
    base_ts = 1773136800.0
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"sessionId": "partial-session", "startedAt": "2026-03-10T10:00:00Z"}, indent=2),
        encoding="utf-8",
    )
    _write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {
                "ts": base_ts + 1.0,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {"query": "postcode"},
                },
            }
        ],
    )

    events = build_event_ledger(session_dir)

    assert any(event["eventType"] == "conversation.started" for event in events)
    assert all(event["eventType"] != "conversation.closed" for event in events)
