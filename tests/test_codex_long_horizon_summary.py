from __future__ import annotations

import json
from pathlib import Path

from scripts.codex_long_horizon_summary import (
    build_summary,
    render_markdown,
    render_summary_card_svg,
)


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def test_build_summary_filters_repo_and_computes_metrics(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"

    included_records = [
        {
            "timestamp": "2026-02-10T10:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "id": "session-1",
                "timestamp": "2026-02-10T10:00:00.000Z",
                "cwd": "/Users/example/repos/mcp-geo",
            },
        },
        {
            "timestamp": "2026-02-10T10:00:01.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "# AGENTS.md instructions for /repo"}],
            },
        },
        {
            "timestamp": "2026-02-10T10:00:02.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Build a long horizon summary"}],
            },
        },
        {
            "timestamp": "2026-02-10T10:01:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": "{\"cmd\":\"ls\"}",
            },
        },
        {
            "timestamp": "2026-02-10T10:01:30.000Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "apply_patch",
                "input": "*** Begin Patch\n*** Add File: a.txt\n+alpha\n+beta\n*** End Patch\n",
            },
        },
        {
            "timestamp": "2026-02-10T10:02:00.000Z",
            "type": "response_item",
            "payload": {"type": "web_search_call", "query": "mcp geo"},
        },
        {
            "timestamp": "2026-02-10T10:02:30.000Z",
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "total_token_usage": {
                        "total_tokens": 1200,
                        "input_tokens": 700,
                        "output_tokens": 500,
                        "cached_input_tokens": 2000,
                        "reasoning_output_tokens": 300,
                    },
                    "last_token_usage": {"total_tokens": 345},
                },
            },
        },
        {
            "timestamp": "2026-02-10T10:03:00.000Z",
            "type": "event_msg",
            "payload": {"type": "context_compacted"},
        },
        {"timestamp": "2026-02-10T10:03:10.000Z", "type": "compacted", "payload": {}},
        {
            "timestamp": "2026-02-10T10:04:00.000Z",
            "type": "event_msg",
            "payload": {"type": "agent_message", "message": "done"},
        },
    ]

    excluded_records = [
        {
            "timestamp": "2026-02-11T10:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "id": "session-2",
                "timestamp": "2026-02-11T10:00:00.000Z",
                "cwd": "/Users/example/repos/other-repo",
            },
        },
        {
            "timestamp": "2026-02-11T10:01:00.000Z",
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "total_token_usage": {
                        "total_tokens": 9999,
                        "input_tokens": 5000,
                        "output_tokens": 4999,
                    },
                    "last_token_usage": {"total_tokens": 9999},
                },
            },
        },
    ]

    _write_jsonl(codex_home / "sessions" / "2026" / "02" / "a.jsonl", included_records)
    _write_jsonl(codex_home / "archived_sessions" / "b.jsonl", excluded_records)

    summary = build_summary(codex_home=codex_home, repo_filter="mcp-geo")
    stats = summary["summary"]

    assert stats["session_count"] == 1
    assert stats["interactive_sessions"] == 1
    assert stats["automation_sessions"] == 0
    assert stats["sessions_with_tokens"] == 1

    assert stats["total_tokens"] == 1200
    assert stats["input_tokens"] == 700
    assert stats["output_tokens"] == 500
    assert stats["cached_input_tokens"] == 2000
    assert stats["reasoning_output_tokens"] == 300

    assert stats["tool_calls"] == 3
    assert stats["function_calls"] == 1
    assert stats["custom_tool_calls"] == 1
    assert stats["web_search_calls"] == 1
    assert stats["shell_calls"] == 1
    assert stats["patch_calls"] == 1
    assert stats["apply_patch_lines_added"] == 2
    assert stats["context_compactions"] == 2
    assert stats["peak_single_step_tokens"] == 345

    session = summary["sessions"][0]
    assert session["first_prompt"] == "Build a long horizon summary"

    markdown = render_markdown(summary)
    assert "# MCP Geo Codex Session Summary" in markdown
    assert "Long Horizon-style Metrics" in markdown
    assert "`1,200`" in markdown

    markdown_with_image = render_markdown(
        summary,
        summary_image_path="mcp_geo_codex_long_horizon_summary_2026-02-10.svg",
        summary_image_title="Codex MCP-Geo Summary",
    )
    assert markdown_with_image.startswith(
        "![Codex MCP-Geo Summary](mcp_geo_codex_long_horizon_summary_2026-02-10.svg)"
    )

    template_path = tmp_path / "summary_card.svg.tmpl"
    template_path.write_text(
        (
            "<svg><text>$title</text><text>$active_runtime</text>"
            "<text>$token_usage</text><text>$tool_calls</text></svg>"
        ),
        encoding="utf-8",
    )
    svg = render_summary_card_svg(
        summary,
        title="Codex MCP-Geo Summary",
        template_path=template_path,
    )
    assert "<text>Codex MCP-Geo Summary</text>" in svg
    assert "<text>0.1h</text>" in svg
    assert "<text>1.2k</text>" in svg
    assert "<text>3</text>" in svg
