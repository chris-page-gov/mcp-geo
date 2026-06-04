#!/usr/bin/env python3
"""Inventory local Codex sessions as LLM-wiki postmortem candidates.

Stage 1 of the MCP-Geo conversation postmortem workflow is deliberately
read-only: scan local Codex rollout JSONL logs, identify sessions for this repo,
estimate curation effort, and write a private candidate register under
``postmortem/``. Stage 2 can then promote selected sessions into the tracked
``postmortem-public/`` wiki.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOCAL_PATH_RE = re.compile(r"/Users/[^\s`'\"<>)]*")
EXTSSD_RE = re.compile(r"/Volumes/ExtSSD-Data(?:/Data)?[^\s`'\"<>)]*")
SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(?P<key>OS_API_KEY|api_key|apikey|access_token|token)\b"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?:Bearer\s+)?[^\s,;]+",
    re.IGNORECASE,
)
AUTHORIZATION_HEADER_RE = re.compile(
    r"\b(?P<key>authorization)\b(?P<sep>\s*[:=]\s*)(?:Bearer\s+)?[^\n,;]+",
    re.IGNORECASE,
)
AUTOMATION_TITLE_RE = re.compile(
    r"\bautomation:\s*(.*?)(?:\s+automation id:|\s+automation memory:|\s+last run:|$)",
    re.IGNORECASE,
)
ISO_TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T[\d:.]+Z?\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
LONG_HEX_RE = re.compile(r"\b[0-9a-f]{8,}\b")
NUMBER_RE = re.compile(r"\b\d+\b")
STATUS_MONITOR_WORDS = frozenset(
    {
        "check",
        "checks",
        "ci",
        "failing",
        "failed",
        "green",
        "logs",
        "monitor",
        "passing",
        "pr",
        "pull request",
        "status",
        "waiting",
        "workflow",
    }
)
WORD_RE = re.compile(r"\b[a-z0-9]+\b")
PR_WORKFLOW_RE = re.compile(r"\b(?:pr|pull request)\b", re.IGNORECASE)


@dataclass
class Message:
    role: str
    timestamp: str
    text: str
    phase: str | None = None


@dataclass
class Candidate:
    session_id: str
    start_timestamp: str
    updated_at: str
    cwd: str
    title: str
    source_path: Path
    source_sha256: str
    line_count: int
    byte_count: int
    event_counts: dict[str, int] = field(default_factory=dict)
    tool_counts: dict[str, int] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    git_commit_hash: str | None = None
    repository_url: str | None = None

    @property
    def user_message_count(self) -> int:
        return sum(1 for message in self.messages if message.role == "user")

    @property
    def assistant_message_count(self) -> int:
        return sum(1 for message in self.messages if message.role == "assistant")

    @property
    def visible_char_count(self) -> int:
        return sum(len(message.text) for message in self.messages)

    @property
    def token_estimate(self) -> int:
        # Good enough for triage: English/code-heavy logs average roughly 4 chars/token.
        return max(1, round(self.visible_char_count / 4))

    @property
    def exchange_estimate(self) -> int:
        return self.user_message_count

    @property
    def effort_band(self) -> str:
        tokens = self.token_estimate
        if tokens <= 4_000 and self.exchange_estimate <= 3:
            return "tiny"
        if tokens <= 16_000 and self.exchange_estimate <= 10:
            return "small"
        if tokens <= 64_000 and self.exchange_estimate <= 35:
            return "medium"
        if tokens <= 160_000:
            return "large"
        return "very_large"

    @property
    def effort_note(self) -> str:
        return {
            "tiny": "15-30 min curation",
            "small": "30-60 min curation",
            "medium": "1-2 h curation",
            "large": "2-4 h curation",
            "very_large": "4 h+ or split first",
        }[self.effort_band]

    @property
    def first_user_prompt(self) -> str:
        for message in self.messages:
            if message.role == "user" and not is_context_only(message.text):
                return message.text
        return ""

    @property
    def session_kind(self) -> str:
        prompt = self.first_user_prompt.strip().lower()
        if prompt.startswith("automation:"):
            return "automation"
        if PR_WORKFLOW_RE.search(prompt[:160]):
            return "github_workflow"
        if "review" in prompt[:240]:
            return "review"
        return "interactive"


@dataclass(frozen=True)
class RepetitionProfile:
    category: str
    label: str
    signature: str
    global_group: bool = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_text(text: str) -> str:
    text = EXTSSD_RE.sub("[EXTSSD_DATA_PATH]", text)
    text = LOCAL_PATH_RE.sub("[LOCAL_PATH]", text)
    text = AUTHORIZATION_HEADER_RE.sub(
        lambda match: f"{match.group('key')}{match.group('sep')}[REDACTED]",
        text,
    )
    text = SECRET_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group('key')}{match.group('sep')}[REDACTED]",
        text,
    )
    return text


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def timestamp_sort_key(candidate: Candidate) -> datetime:
    return parse_timestamp(candidate.start_timestamp) or datetime.min.replace(tzinfo=UTC)


def compact_prompt_excerpt(prompt: str, max_chars: int = 240) -> str:
    excerpt = " ".join(prompt.split())
    if len(excerpt) > max_chars:
        return excerpt[: max_chars - 3].rstrip() + "..."
    return excerpt


def normalise_prompt_for_signature(text: str) -> str:
    text = sanitize_text(text).lower()
    text = text.replace("`", "")
    text = ISO_TIMESTAMP_RE.sub("[timestamp]", text)
    text = DATE_RE.sub("[date]", text)
    text = UUID_RE.sub("[uuid]", text)
    text = LONG_HEX_RE.sub("[hex]", text)
    text = NUMBER_RE.sub("[number]", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def automation_title(prompt: str) -> str | None:
    match = AUTOMATION_TITLE_RE.search(" ".join(prompt.split()))
    if not match:
        return None
    title = match.group(1).strip()
    return title or None


def looks_like_status_monitor(normalised_prompt: str) -> bool:
    tokens = set(WORD_RE.findall(normalised_prompt))
    return "pull request" in normalised_prompt or bool(tokens & STATUS_MONITOR_WORDS)


def repetition_profile(candidate: Candidate) -> RepetitionProfile | None:
    prompt = candidate.first_user_prompt.strip()
    if not prompt:
        return None

    title = automation_title(prompt)
    if title:
        signature = f"automation:{normalise_prompt_for_signature(title)}"
        return RepetitionProfile("automation", title, signature, global_group=True)

    normalised = normalise_prompt_for_signature(prompt)
    if not normalised:
        return None

    if normalised.startswith("use the connected mcp-geo mcp server"):
        return RepetitionProfile(
            "retry",
            "MCP server harness prompts",
            "retry:mcp-server-harness",
        )

    if "codex agent history whose request action you are assessing" in normalised:
        return RepetitionProfile(
            "review",
            "Approval-review transcript checks",
            "review:approval-transcript",
        )

    if normalised.startswith("<turn_aborted>"):
        return RepetitionProfile(
            "retry",
            "Interrupted-turn continuations",
            "retry:turn-aborted",
        )

    if looks_like_status_monitor(normalised) and candidate.token_estimate <= 16_000:
        label = "Status/check monitoring"
        signature = f"status:{normalised[:180]}"
        if PR_WORKFLOW_RE.search(normalised):
            label = "PR/check status monitoring"
            signature = "status:pr-checks"
        return RepetitionProfile("status_monitor", label, signature)

    return RepetitionProfile(
        "repeated_prompt",
        candidate.title,
        f"prompt:{normalised[:280]}",
    )


def normalise_content_item(item: dict[str, Any]) -> str:
    item_type = item.get("type", "unknown")
    if item_type in {"input_text", "output_text", "text"}:
        return item.get("text", "")
    if item_type in {"input_image", "image"}:
        image_url = item.get("image_url", "")
        if image_url.startswith("data:"):
            header, _, payload = image_url.partition(",")
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            return (
                f"[image attachment omitted: {header}; base64_chars={len(payload)}; "
                f"sha256={digest}]"
            )
        return f"[image attachment: {sanitize_text(image_url)}]"
    return f"[non-text content omitted: type={item_type}]"


def message_text(content: Any) -> str:
    if isinstance(content, list):
        parts = [normalise_content_item(item) for item in content if isinstance(item, dict)]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(content, str):
        return content.strip()
    return ""


def is_environment_only(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("<environment_context>") and stripped.endswith(
        "</environment_context>"
    )


def is_context_only(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("# AGENTS.md instructions for ")


def session_paths(codex_home: Path) -> list[Path]:
    paths: list[Path] = []
    sessions_root = codex_home / "sessions"
    archived_root = codex_home / "archived_sessions"
    if sessions_root.exists():
        paths.extend(sessions_root.glob("**/*.jsonl"))
    if archived_root.exists():
        paths.extend(archived_root.glob("*.jsonl"))
    return sorted(paths)


def load_session_index(codex_home: Path) -> dict[str, dict[str, Any]]:
    index_path = codex_home / "session_index.jsonl"
    index: dict[str, dict[str, Any]] = {}
    if not index_path.exists():
        return index
    with index_path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = record.get("id")
            if session_id:
                index[session_id] = record
    return index


def repo_matches(meta: dict[str, Any], repo_root: Path, repo_name: str) -> bool:
    cwd = str(meta.get("cwd") or "")
    repo_root_str = str(repo_root)
    if cwd == repo_root_str:
        return True
    if Path(cwd).name == repo_name and "/.codex/worktrees/" in cwd:
        return True
    git_meta = meta.get("git") or {}
    repository_url = str(git_meta.get("repository_url") or "")
    return repository_url.endswith(f"/{repo_name}.git") or repository_url.endswith(f"/{repo_name}")


def infer_title(messages: list[Message], fallback: str) -> str:
    for message in messages:
        if message.role != "user" or is_context_only(message.text):
            continue
        lines = [line.strip("# ").strip() for line in message.text.splitlines() if line.strip()]
        for line in lines:
            if line.startswith("<") or line.startswith("# Files mentioned by the user"):
                continue
            if line.startswith("Automation:"):
                return line.replace("Automation:", "").strip() or fallback
            return line[:96]
    return fallback


def parse_candidate(
    path: Path, index: dict[str, dict[str, Any]], repo_root: Path
) -> Candidate | None:
    session_meta: dict[str, Any] | None = None
    messages: list[Message] = []
    event_counts: dict[str, int] = {}
    tool_counts: dict[str, int] = {}
    line_count = 0

    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line_count += 1
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = record.get("payload", {})
            record_type = record.get("type", "")
            event_counts[record_type] = event_counts.get(record_type, 0) + 1
            if record_type == "session_meta":
                session_meta = payload
            elif record_type == "response_item" and payload.get("type") == "message":
                role = payload.get("role", "")
                if role not in {"user", "assistant"}:
                    continue
                text = message_text(payload.get("content", []))
                if not text or is_environment_only(text):
                    continue
                messages.append(
                    Message(
                        role=role,
                        timestamp=record.get("timestamp", ""),
                        text=sanitize_text(text),
                        phase=payload.get("phase"),
                    )
                )
            elif record_type == "response_item" and payload.get("type") == "function_call":
                name = str(payload.get("name") or "function_call")
                tool_counts[name] = tool_counts.get(name, 0) + 1
            elif record_type == "response_item" and payload.get("type") in {
                "web_search_call",
                "tool_search_call",
            }:
                name = str(payload.get("type") or "tool_call")
                tool_counts[name] = tool_counts.get(name, 0) + 1

    if not session_meta or not repo_matches(session_meta, repo_root, repo_root.name):
        return None

    session_id = str(session_meta.get("id") or path.stem)
    indexed = index.get(session_id, {})
    fallback_title = str(indexed.get("thread_name") or f"Codex session {session_id[:8]}")
    git_meta = session_meta.get("git") or {}
    return Candidate(
        session_id=session_id,
        start_timestamp=str(session_meta.get("timestamp") or ""),
        updated_at=str(indexed.get("updated_at") or ""),
        cwd=str(session_meta.get("cwd") or ""),
        title=infer_title(messages, fallback_title),
        source_path=path,
        source_sha256=sha256_file(path),
        line_count=line_count,
        byte_count=path.stat().st_size,
        event_counts=event_counts,
        tool_counts=tool_counts,
        messages=messages,
        git_commit_hash=git_meta.get("commit_hash"),
        repository_url=git_meta.get("repository_url"),
    )


def candidate_record(candidate: Candidate, repo_root: Path) -> dict[str, Any]:
    prompt = candidate.first_user_prompt
    prompt_excerpt = compact_prompt_excerpt(prompt)
    try:
        source_path = str(candidate.source_path.relative_to(repo_root))
    except ValueError:
        try:
            source_path = str(candidate.source_path.relative_to(Path.home()))
            source_path = f"~/{source_path}"
        except ValueError:
            source_path = str(candidate.source_path)
    return {
        "sessionId": candidate.session_id,
        "startTimestamp": candidate.start_timestamp,
        "updatedAt": candidate.updated_at,
        "title": candidate.title,
        "kind": candidate.session_kind,
        "effortBand": candidate.effort_band,
        "effortNote": candidate.effort_note,
        "estimatedVisibleTokens": candidate.token_estimate,
        "visibleCharacters": candidate.visible_char_count,
        "userMessages": candidate.user_message_count,
        "assistantMessages": candidate.assistant_message_count,
        "exchangeEstimate": candidate.exchange_estimate,
        "toolCalls": sum(candidate.tool_counts.values()),
        "lineCount": candidate.line_count,
        "byteCount": candidate.byte_count,
        "promptExcerpt": prompt_excerpt,
        "cwd": sanitize_text(candidate.cwd),
        "sourceJsonlPath": source_path,
        "sourceJsonlSha256": candidate.source_sha256,
        "gitCommitHash": candidate.git_commit_hash,
        "repositoryUrl": candidate.repository_url,
    }


def split_by_time_window(
    members: list[Candidate],
    window_hours: float,
) -> list[list[Candidate]]:
    clusters: list[list[Candidate]] = []
    current: list[Candidate] = []
    previous_dt: datetime | None = None
    window_seconds = window_hours * 60 * 60

    for member in members:
        current_dt = parse_timestamp(member.start_timestamp)
        if not current:
            current = [member]
            previous_dt = current_dt
            continue
        if (
            previous_dt is not None
            and current_dt is not None
            and (current_dt - previous_dt).total_seconds() <= window_seconds
        ):
            current.append(member)
        else:
            clusters.append(current)
            current = [member]
        previous_dt = current_dt

    if current:
        clusters.append(current)
    return clusters


def repetition_treatment(category: str) -> str:
    return {
        "automation": "Summarize as scheduled rollup; inspect failures or outliers.",
        "retry": "Summarize as retry series; promote only final or representative outcome.",
        "review": "Summarize as review-gate batch; keep decision and notable findings.",
        "status_monitor": "Summarize status cadence; keep final state and transitions.",
        "repeated_prompt": "Summarize duplicate prompt series; inspect first, last, and outliers.",
    }.get(category, "Summarize compactly and inspect outliers.")


def repetition_group_record(
    group_id: str,
    profile: RepetitionProfile,
    members: list[Candidate],
) -> dict[str, Any]:
    ordered = sorted(members, key=timestamp_sort_key)
    newest_first_ids = [member.session_id for member in reversed(ordered)]
    token_total = sum(member.token_estimate for member in ordered)
    tool_total = sum(sum(member.tool_counts.values()) for member in ordered)
    first = ordered[0]
    last = ordered[-1]
    session_id_range = f"{first.session_id[:8]}..{last.session_id[:8]}"
    prompt = first.first_user_prompt or last.first_user_prompt
    return {
        "groupId": group_id,
        "type": profile.category,
        "label": profile.label,
        "signature": profile.signature,
        "startTimestamp": first.start_timestamp,
        "endTimestamp": last.start_timestamp,
        "sessionCount": len(ordered),
        "uniqueSessionCount": len({member.session_id for member in ordered}),
        "sessionIdRange": session_id_range,
        "sessionIdsNewestFirst": newest_first_ids,
        "estimatedVisibleTokens": token_total,
        "visibleCharacters": sum(member.visible_char_count for member in ordered),
        "userMessages": sum(member.user_message_count for member in ordered),
        "assistantMessages": sum(member.assistant_message_count for member in ordered),
        "toolCalls": tool_total,
        "lineCount": sum(member.line_count for member in ordered),
        "byteCount": sum(member.byte_count for member in ordered),
        "maxSessionTokens": max(member.token_estimate for member in ordered),
        "representativePromptExcerpt": compact_prompt_excerpt(prompt),
        "curationTreatment": repetition_treatment(profile.category),
    }


def build_repetition_group_records(
    candidates: list[Candidate],
    repeat_window_hours: float,
    min_count: int,
) -> list[dict[str, Any]]:
    by_signature: dict[str, tuple[RepetitionProfile, list[Candidate]]] = {}
    for candidate in candidates:
        profile = repetition_profile(candidate)
        if profile is None:
            continue
        _, members = by_signature.setdefault(profile.signature, (profile, []))
        members.append(candidate)

    groups: list[tuple[RepetitionProfile, list[Candidate]]] = []
    for profile, members in by_signature.values():
        ordered = sorted(members, key=timestamp_sort_key)
        clusters = [ordered] if profile.global_group else split_by_time_window(
            ordered, repeat_window_hours
        )
        for cluster in clusters:
            if len({member.session_id for member in cluster}) >= min_count:
                groups.append((profile, cluster))

    groups.sort(
        key=lambda item: (
            timestamp_sort_key(max(item[1], key=timestamp_sort_key)),
            len(item[1]),
        ),
        reverse=True,
    )
    return [
        repetition_group_record(f"repeat-{index:03d}", profile, members)
        for index, (profile, members) in enumerate(groups, start=1)
    ]


def write_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def markdown_table_row(record: dict[str, Any]) -> str:
    title = str(record["title"]).replace("|", "\\\\|")
    prompt = str(record["promptExcerpt"]).replace("|", "\\\\|")
    return (
        f"| `{record['startTimestamp'] or 'unknown'}` | `{record['sessionId'][:8]}` | "
        f"{title} | `{record['kind']}` | `{record['effortBand']}` | "
        f"{record['estimatedVisibleTokens']:,} | {record['userMessages']} | "
        f"{record['assistantMessages']} | {record['toolCalls']} | {prompt} |\n"
    )


def repetition_table_row(record: dict[str, Any]) -> str:
    group_type = str(record["type"]).replace("_", " ").title()
    label = str(record["label"]).replace("|", "\\\\|")
    treatment = str(record["curationTreatment"]).replace("|", "\\\\|")
    span = f"{record['startTimestamp'] or 'unknown'} -> {record['endTimestamp'] or 'unknown'}"
    return (
        f"| `{record['groupId']}` | {group_type} | {label} | `{span}` | "
        f"{record['sessionCount']} | {record['estimatedVisibleTokens']:,} | "
        f"{record['toolCalls']} | `{record['sessionIdRange']}` | {treatment} |\n"
    )


def write_repetition_markdown(
    path: Path,
    records: list[dict[str, Any]],
    repo_root: Path,
    codex_home: Path,
    repeat_window_hours: float,
    min_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    parts = [
        "# Codex Repeated Session Rollup\n\n",
        f"- Generated at: `{now}`\n",
        f"- Repository: `{repo_root}`\n",
        f"- Codex home: `{codex_home}`\n",
        f"- Repeated group count: `{len(records)}`\n",
        f"- Non-automation repeat window: `{repeat_window_hours:g}` hours\n",
        f"- Minimum group size: `{min_count}` sessions\n\n",
        "This private rollup collapses repeated local sessions into compact "
        "curation units. Automations are grouped across their full observed span; "
        "other repeated prompts are grouped when adjacent matching sessions fall "
        "inside the repeat window.\n\n",
        "| Group | Type | Label | Time span | Sessions | Est. visible tokens | "
        "Tool calls | Session IDs | Suggested treatment |\n",
        "|---|---|---|---|---:|---:|---:|---|---|\n",
    ]
    if records:
        parts.extend(repetition_table_row(record) for record in records)
    else:
        parts.append("| _none_ |  |  |  |  |  |  |  |  |\n")

    parts.append("\n## Representative Prompts\n\n")
    for record in records:
        prompt = str(record["representativePromptExcerpt"]).replace("\n", " ")
        parts.append(f"- `{record['groupId']}`: {prompt}\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_markdown(
    path: Path,
    records: list[dict[str, Any]],
    repetition_records: list[dict[str, Any]],
    repetition_markdown_name: str,
    repo_root: Path,
    codex_home: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    parts = [
        "# Codex Session Candidate Inventory\n\n",
        f"- Generated at: `{now}`\n",
        f"- Repository: `{repo_root}`\n",
        f"- Codex home: `{codex_home}`\n",
        f"- Candidate count: `{len(records)}`\n",
        f"- Repeated-session group count: `{len(repetition_records)}`\n",
        "- Sort order: newest first by session start timestamp\n",
        "- Scope: local Codex rollout JSONL logs matching this repository name, "
        "repo root, or git remote\n\n",
        "## How To Use\n\n",
        "Pick candidate session IDs from this list for stage 2 promotion. Large and "
        "very large sessions should usually be split or curated with a narrower "
        "publication boundary before adding to `postmortem-public/`.\n\n",
        "Use the repeated-session rollup first when triaging automations, retries, "
        f"and status-watch sessions: [`{repetition_markdown_name}`]"
        f"({repetition_markdown_name}).\n\n",
        "## Effort Bands\n\n",
        "| Band | Meaning |\n",
        "|---|---|\n",
        "| `tiny` | About 15-30 min; one to three exchanges. |\n",
        "| `small` | About 30-60 min; short focused session. |\n",
        "| `medium` | About 1-2 h; multiple exchanges or moderate tool use. |\n",
        "| `large` | About 2-4 h; lengthy curation and redaction. |\n",
        "| `very_large` | More than 4 h or split first. |\n\n",
        "## Candidates\n\n",
        "| Start | Session | Title | Kind | Effort | Est. visible tokens | User msgs | "
        "Codex msgs | Tool calls | Prompt excerpt |\n",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|\n",
    ]
    parts.extend(markdown_table_row(record) for record in records)
    parts.append("\n## Source Paths\n\n")
    for record in records:
        parts.append(
            f"- `{record['sessionId']}`: `{record['sourceJsonlPath']}` "
            f"(sha256 `{record['sourceJsonlSha256']}`)\n"
        )
    path.write_text("".join(parts), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("postmortem/candidates"))
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional maximum number of newest candidates to write.",
    )
    parser.add_argument(
        "--repeat-window-hours",
        type=float,
        default=6.0,
        help="Maximum adjacent-session gap for non-automation repeated-prompt groups.",
    )
    parser.add_argument(
        "--repeat-min-count",
        type=int,
        default=2,
        help="Minimum sessions required for a repeated-session group.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    codex_home = args.codex_home.expanduser().resolve()
    index = load_session_index(codex_home)
    candidates = [
        candidate
        for path in session_paths(codex_home)
        if (candidate := parse_candidate(path, index, repo_root)) is not None
    ]
    candidates.sort(key=lambda item: (item.start_timestamp, item.session_id), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    records = [candidate_record(candidate, repo_root) for candidate in candidates]
    repetition_records = build_repetition_group_records(
        candidates,
        repeat_window_hours=args.repeat_window_hours,
        min_count=args.repeat_min_count,
    )
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    output_dir = (repo_root / args.output_dir).resolve()
    json_path = output_dir / f"codex-session-candidates-{date}.json"
    md_path = output_dir / f"codex-session-candidates-{date}.md"
    repeat_json_path = output_dir / f"codex-session-repeat-groups-{date}.json"
    repeat_md_path = output_dir / f"codex-session-repeat-groups-{date}.md"
    write_json(json_path, records)
    write_json(repeat_json_path, repetition_records)
    write_repetition_markdown(
        repeat_md_path,
        repetition_records,
        repo_root,
        codex_home,
        repeat_window_hours=args.repeat_window_hours,
        min_count=args.repeat_min_count,
    )
    write_markdown(
        md_path,
        records,
        repetition_records,
        repeat_md_path.name,
        repo_root,
        codex_home,
    )
    print(f"wrote {len(records)} candidates")
    print(f"wrote {len(repetition_records)} repeated-session groups")
    print(json_path)
    print(md_path)
    print(repeat_json_path)
    print(repeat_md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
