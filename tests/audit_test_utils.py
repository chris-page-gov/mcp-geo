from __future__ import annotations

import json
from pathlib import Path


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def build_live_style_session(session_dir: Path) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    base_ts = 1773136800.0
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "sessionId": "dsap-live-session",
                "mode": "stdio",
                "source": "codex",
                "surface": "cli",
                "startedAt": "2026-03-10T10:00:00Z",
                "endedAt": "2026-03-10T10:00:30Z",
                "exitCode": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {
                "ts": base_ts + 0.1,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"capabilities": {"tools": {}}},
                },
            },
            {
                "ts": base_ts + 0.2,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"protocolVersion": "2025-11-25"},
                },
            },
            {
                "ts": base_ts + 0.3,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {"query": "postcode"},
                },
            },
            {
                "ts": base_ts + 0.4,
                "direction": "client->server",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "os_places.by_postcode",
                        "arguments": {"postcode": "SW1A 1AA"},
                    },
                },
            },
            {
                "ts": base_ts + 0.5,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {"data": {"results": [{"postcode": "SW1A 1AA"}]}},
                },
            },
        ],
    )
    write_jsonl(
        session_dir / "transcript-visible.jsonl",
        [
            {
                "timestamp": "2026-03-10T10:00:05Z",
                "role": "user",
                "content": "Find the postcode for Westminster.",
            },
            {
                "timestamp": "2026-03-10T10:00:10Z",
                "role": "assistant",
                "content": "I will check the postcode evidence.",
            },
            {
                "timestamp": "2026-03-10T10:00:20Z",
                "role": "assistant",
                "content": "The postcode is SW1A 1AA.",
                "isConclusion": True,
            },
        ],
    )
    write_jsonl(
        session_dir / "decision-log.jsonl",
        [
            {
                "timestamp": "2026-03-10T10:00:12Z",
                "kind": "assumption",
                "content": "The visible transcript is the disclosure-safe conversation surface.",
            },
            {
                "timestamp": "2026-03-10T10:00:13Z",
                "kind": "uncertainty",
                "content": "No HTTP response body was retained for source review.",
            },
            {
                "timestamp": "2026-03-10T10:00:21Z",
                "kind": "conclusion",
                "content": "The assistant concluded with the postcode answer.",
            },
        ],
    )
    write_jsonl(
        session_dir / "source-http-trace.jsonl",
        [
            {
                "timestamp": "2026-03-10T10:00:06Z",
                "direction": "request",
                "sourceAccessId": "src-1",
                "source": "os_places",
                "method": "GET",
                "url": "https://api.os.uk/search/places/v1/postcode?postcode=SW1A1AA",
                "heldStatus": "held",
            },
            {
                "timestamp": "2026-03-10T10:00:07Z",
                "direction": "response",
                "sourceAccessId": "src-1",
                "source": "os_places",
                "statusCode": 200,
                "heldStatus": "held",
            },
        ],
    )
    return session_dir


def build_partial_session(session_dir: Path) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        session_dir / "mcp-stdio-trace.jsonl",
        [
            {
                "ts": 1773136800.0,
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
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "sessionId": "dsap-partial-session",
                "mode": "stdio",
                "source": "codex",
                "surface": "cli",
                "startedAt": "2026-03-10T10:00:00Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return session_dir
