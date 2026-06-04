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


def test_status_monitor_detection_matches_terms_not_substrings() -> None:
    assert inventory.looks_like_status_monitor("improve caching logic") is False
    assert inventory.looks_like_status_monitor("please check pr status") is True

    profile = inventory.repetition_profile(_candidate("improve caching logic"))
    assert profile is not None
    assert profile.category == "repeated_prompt"


def test_sanitize_text_redacts_bearer_tokens() -> None:
    text = "Authorization: Bearer sk-secret-token\nOS_API_KEY=abc123"
    redacted = inventory.sanitize_text(text)

    assert "sk-secret-token" not in redacted
    assert "abc123" not in redacted
    assert "Authorization: [REDACTED]" in redacted
    assert "OS_API_KEY=[REDACTED]" in redacted


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


def json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True)
