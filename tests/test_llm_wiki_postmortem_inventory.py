from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

from scripts import llm_wiki_postmortem_inventory as inventory


def _candidate(prompt: str, *, source_path: Path | None = None) -> inventory.Candidate:
    return inventory.Candidate(
        session_id="session-1",
        start_timestamp="2026-05-14T09:00:00",
        updated_at="2026-05-14T09:01:00Z",
        cwd="/Users/example/repos/mcp-geo",
        title="Example",
        source_path=source_path or Path("/tmp/session.jsonl"),
        source_sha256="abc123",
        line_count=1,
        byte_count=10,
        messages=[
            inventory.Message(
                role="user",
                timestamp="2026-05-14T09:00:00Z",
                text=prompt,
            )
        ],
    )


def test_session_kind_matches_pr_as_whole_term_only() -> None:
    assert _candidate("improve caching logic").session_kind == "interactive"
    assert _candidate("Please check PR #78").session_kind == "github_workflow"
    assert _candidate("Review the pull request checks").session_kind == "github_workflow"


def test_session_kind_matches_review_as_whole_term_only() -> None:
    assert _candidate("track preview spec updates").session_kind == "interactive"
    assert _candidate("Please review this transcript").session_kind == "review"


def test_status_monitor_detection_matches_terms_not_substrings() -> None:
    assert inventory.looks_like_status_monitor("improve caching logic") is False
    assert inventory.looks_like_status_monitor("please check pr status") is True

    profile = inventory.repetition_profile(_candidate("improve caching logic"))
    assert profile is not None
    assert profile.category == "repeated_prompt"


def test_pr_status_signatures_keep_distinct_pr_numbers() -> None:
    pr_78_profile = inventory.repetition_profile(_candidate("Please review PR #78"))
    pr_91_profile = inventory.repetition_profile(_candidate("Please review PR #91"))
    pr_78_status_profile = inventory.repetition_profile(_candidate("Please check PR 78 status"))

    assert pr_78_profile is not None
    assert pr_91_profile is not None
    assert pr_78_status_profile is not None
    assert pr_78_profile.signature == "status:pr-checks:78"
    assert pr_78_status_profile.signature == "status:pr-checks:78"
    assert pr_91_profile.signature == "status:pr-checks:91"


def test_sanitize_text_redacts_bearer_tokens() -> None:
    text = "\n".join(
        [
            "Authorization: Bearer sk-secret-token",
            '{"Authorization": "Bearer sk-json-auth"}',
            'headers={"authorization":"Bearer sk-compact-json-auth"}',
            "OS_API_KEY=abc123",
            "OPENAI_API_KEY=sk-openai-secret",
            '{"OPENAI_API_KEY": "sk-json-secret"}',
            "{'GITHUB_TOKEN': 'ghp_json_secret'}",
            "GITHUB_TOKEN=ghp_secret",
            "MCP_HTTP_JWT_HS256_SECRET=jwt-secret",
        ]
    )
    redacted = inventory.sanitize_text(text)

    assert "sk-secret-token" not in redacted
    assert "sk-json-auth" not in redacted
    assert "sk-compact-json-auth" not in redacted
    assert "abc123" not in redacted
    assert "sk-openai-secret" not in redacted
    assert "sk-json-secret" not in redacted
    assert "ghp_json_secret" not in redacted
    assert "ghp_secret" not in redacted
    assert "jwt-secret" not in redacted
    assert "Authorization: [REDACTED]" in redacted
    assert '"Authorization": "[REDACTED]"' in redacted
    assert 'headers={"authorization":"[REDACTED]"}' in redacted
    assert "OS_API_KEY=[REDACTED]" in redacted
    assert "OPENAI_API_KEY=[REDACTED]" in redacted
    assert '"OPENAI_API_KEY": "[REDACTED]"' in redacted
    assert "'GITHUB_TOKEN': '[REDACTED]'" in redacted
    assert "GITHUB_TOKEN=[REDACTED]" in redacted
    assert "MCP_HTTP_JWT_HS256_SECRET=[REDACTED]" in redacted


def test_sanitize_text_redacts_credentials_embedded_in_urls() -> None:
    text = "remote=https://ghp_secret-token@github.com/chris-page-gov/mcp-geo.git"

    redacted = inventory.sanitize_text(text)

    assert "ghp_secret-token" not in redacted
    assert "https://github.com/chris-page-gov/mcp-geo.git" in redacted


def test_parse_timestamp_normalizes_naive_values_to_utc() -> None:
    parsed = inventory.parse_timestamp("2026-05-14T09:00:00")

    assert parsed is not None
    assert parsed.tzinfo == UTC
    assert parsed.isoformat() == "2026-05-14T09:00:00+00:00"


def test_candidate_record_uses_repo_relative_source_path(tmp_path: Path) -> None:
    source_path = tmp_path / "postmortem" / "candidate.jsonl"
    source_path.parent.mkdir()
    source_path.write_text("{}", encoding="utf-8")

    record = inventory.candidate_record(
        _candidate("Summarize this", source_path=source_path),
        tmp_path,
    )

    assert record["sourceJsonlPath"] == "postmortem/candidate.jsonl"


def test_candidate_record_redacts_repository_url_credentials(tmp_path: Path) -> None:
    candidate = _candidate("Summarize this")
    candidate.repository_url = "https://ghp_secret-token@github.com/chris-page-gov/mcp-geo.git"

    record = inventory.candidate_record(candidate, tmp_path)

    assert record["repositoryUrl"] == "https://github.com/chris-page-gov/mcp-geo.git"
    assert "ghp_secret-token" not in json_dump(record)


def test_repo_matches_accepts_repo_subdirectories(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"cwd": str(repo_root / "server" / "mcp"), "git": {}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is True


def test_repo_matches_accepts_codex_worktree_subdirectories(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"cwd": "/Users/example/.codex/worktrees/mcp-geo/server", "git": {}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is True


def test_repo_matches_accepts_other_checkout_with_exact_repo_segment(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"cwd": "/Users/example/repos/mcp-geo/server", "git": {}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is True


def test_repo_matches_rejects_partial_repo_name_segment(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"cwd": "/Users/example/repos/mcp-geology/server", "git": {}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is False


def test_repo_matches_rejects_missing_cwd_without_matching_remote(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    assert inventory.repo_matches({"git": {}}, repo_root, "mcp-geo") is False

    meta = {"git": {"repository_url": "https://github.com/chris-page-gov/mcp-geo.git"}}
    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is True


def test_repo_matches_accepts_ssh_remote_when_cwd_is_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"git": {"repository_url": "git@github.com:chris-page-gov/mcp-geo.git"}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is True


def test_repo_matches_rejects_nonmatching_ssh_remote_when_cwd_is_missing(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "mcp-geo"
    meta = {"git": {"repository_url": "git@github.com:chris-page-gov/other-repo.git"}}

    assert inventory.repo_matches(meta, repo_root, "mcp-geo") is False


def test_parse_candidate_counts_custom_tool_calls(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    repo_root.mkdir()
    source_path = tmp_path / "session.jsonl"
    records = [
        {
            "type": "session_meta",
            "payload": {
                "id": "session-1",
                "timestamp": "2026-05-14T09:00:00Z",
                "cwd": str(repo_root),
                "git": {},
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Create a patch"}],
            },
        },
        {
            "type": "response_item",
            "payload": {"type": "function_call", "name": "exec_command"},
        },
        {
            "type": "response_item",
            "payload": {"type": "custom_tool_call", "name": "apply_patch"},
        },
        {
            "type": "response_item",
            "payload": {"type": "web_search_call", "query": "mcp geo"},
        },
    ]
    source_path.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    candidate = inventory.parse_candidate(source_path, {}, repo_root)

    assert candidate is not None
    assert candidate.tool_counts == {
        "exec_command": 1,
        "apply_patch": 1,
        "web_search_call": 1,
    }
    assert inventory.candidate_record(candidate, repo_root)["toolCalls"] == 3


def test_session_paths_recurses_into_archived_sessions(tmp_path: Path) -> None:
    active = tmp_path / "sessions" / "2026" / "06" / "active.jsonl"
    archived = tmp_path / "archived_sessions" / "2026" / "06" / "archived.jsonl"
    top_level_archive = tmp_path / "archived_sessions" / "top-level.jsonl"
    active.parent.mkdir(parents=True)
    archived.parent.mkdir(parents=True)
    active.write_text("{}", encoding="utf-8")
    archived.write_text("{}", encoding="utf-8")
    top_level_archive.write_text("{}", encoding="utf-8")

    paths = inventory.session_paths(tmp_path)

    assert paths == sorted([active, archived, top_level_archive])


def test_markdown_rows_escape_table_pipes_once() -> None:
    candidate_row = inventory.markdown_table_row(
        {
            "startTimestamp": "2026-05-14T09:00:00Z",
            "sessionId": "session-123456",
            "title": "Run a|b",
            "kind": "interactive",
            "effortBand": "tiny",
            "estimatedVisibleTokens": 1234,
            "userMessages": 1,
            "assistantMessages": 2,
            "toolCalls": 3,
            "promptExcerpt": "Use x|y",
        }
    )
    repetition_row = inventory.repetition_table_row(
        {
            "groupId": "repeat-001",
            "type": "status_monitor",
            "label": "PR|checks",
            "curationTreatment": "merge|summaries",
            "startTimestamp": "2026-05-14T09:00:00Z",
            "endTimestamp": "2026-05-14T09:10:00Z",
            "sessionCount": 2,
            "estimatedVisibleTokens": 4321,
            "toolCalls": 4,
            "sessionIdRange": "abc..def",
        }
    )

    assert "Run a\\|b" in candidate_row
    assert "Use x\\|y" in candidate_row
    assert "Run a\\\\|b" not in candidate_row
    assert "PR\\|checks" in repetition_row
    assert "merge\\|summaries" in repetition_row
    assert "PR\\\\|checks" not in repetition_row


def test_injected_agents_context_preserves_following_prompt() -> None:
    text = "\n".join(
        [
            "# AGENTS.md instructions for /workspace/mcp-geo",
            "",
            "<INSTRUCTIONS>",
            "Repository guidance.",
            "</INSTRUCTIONS>",
            "<environment_context>",
            "<cwd>/workspace/mcp-geo</cwd>",
            "</environment_context>",
            "Please review PR #78",
        ]
    )
    candidate = _candidate(text)

    assert candidate.first_user_prompt == "Please review PR #78"
    assert candidate.session_kind == "github_workflow"
    assert inventory.infer_title(candidate.messages, "Fallback") == "Please review PR #78"


def test_parse_candidate_skips_standalone_agents_context_message(tmp_path: Path) -> None:
    repo_root = tmp_path / "mcp-geo"
    repo_root.mkdir()
    source_path = tmp_path / "session.jsonl"
    agents_context = "\n".join(
        [
            "# AGENTS.md instructions for /workspace/mcp-geo",
            "",
            "<INSTRUCTIONS>",
            "Repository guidance.",
            "</INSTRUCTIONS>",
            "<environment_context>",
            "<cwd>/workspace/mcp-geo</cwd>",
            "</environment_context>",
        ]
    )
    records = [
        {
            "type": "session_meta",
            "payload": {
                "id": "session-1",
                "timestamp": "2026-05-14T09:00:00Z",
                "cwd": str(repo_root),
                "git": {},
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-05-14T09:00:01Z",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": agents_context}],
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-05-14T09:00:02Z",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Please review PR #78"}],
            },
        },
    ]
    source_path.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    candidate = inventory.parse_candidate(source_path, {}, repo_root)

    assert candidate is not None
    assert candidate.user_message_count == 1
    assert candidate.first_user_prompt == "Please review PR #78"
    assert "Repository guidance" not in json_dump(inventory.candidate_record(candidate, repo_root))


def json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True)
