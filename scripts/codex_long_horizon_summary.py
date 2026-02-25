#!/usr/bin/env python3
"""Generate Long Horizon-style Codex session metrics for a repository filter."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from string import Template
from typing import Any

BOOTSTRAP_PREFIXES = (
    "# AGENTS.md instructions for ",
    "<environment_context>",
    "<permissions instructions>",
    "<collaboration_mode>",
    "<app-context>",
)

SUMMARY_TITLE_DEFAULT = "Codex MCP-Geo Summary"


@dataclass
class SessionMetrics:
    session_id: str
    file_path: str
    cwd: str
    start_iso: str
    end_iso: str
    duration_seconds: float
    first_prompt: str
    is_automation: bool
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    reasoning_output_tokens: int
    peak_step_tokens: int
    tool_calls: int
    function_calls: int
    custom_tool_calls: int
    web_search_calls: int
    shell_calls: int
    patch_calls: int
    apply_patch_lines_added: int
    context_compactions: int
    tool_name_counts: dict[str, int] = field(default_factory=dict)


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _is_bootstrap_message(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if any(stripped.startswith(prefix) for prefix in BOOTSTRAP_PREFIXES):
        return True
    if "<INSTRUCTIONS>" in stripped and "AGENTS.md" in stripped:
        return True
    if "### Available skills" in stripped and "How to use skills" in stripped:
        return True
    return False


def _extract_user_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in payload.get("content") or []:
        text = item.get("text") if isinstance(item, dict) else None
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n".join(parts).strip()


def _count_added_lines_in_patch(patch_text: str) -> int:
    added = 0
    for line in patch_text.splitlines():
        if not line.startswith("+"):
            continue
        if line.startswith("+++"):
            continue
        added += 1
    return added


def _discover_session_files(codex_home: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ("sessions", "archived_sessions"):
        root = codex_home / rel
        if root.exists():
            files.extend(root.rglob("*.jsonl"))
    return sorted(files)


def _sanitize_session_file_path(file_path: str, codex_home: Path) -> str:
    raw = Path(file_path).expanduser()
    try:
        rel = raw.resolve().relative_to(codex_home.expanduser().resolve())
        return f"<codex_home>/{rel.as_posix()}"
    except Exception:
        tail = Path(file_path).as_posix().split("/")[-3:]
        return f"<session_file>/{'/'.join(tail)}"


def _sanitize_session_cwd(cwd: str, repo_filter: str) -> str:
    normalized = cwd.replace("\\", "/")
    if repo_filter and repo_filter in normalized:
        return f"<repo>/{repo_filter}"
    tail = [segment for segment in normalized.split("/") if segment]
    if tail:
        return f"<cwd>/{tail[-1]}"
    return "<cwd>/unknown"


def _serialize_session_metrics(
    metrics: SessionMetrics,
    codex_home: Path,
    repo_filter: str,
) -> dict[str, Any]:
    payload = asdict(metrics)
    payload["file_path"] = _sanitize_session_file_path(metrics.file_path, codex_home)
    payload["cwd"] = _sanitize_session_cwd(metrics.cwd, repo_filter)
    return payload


def _parse_session_file(path: Path, repo_filter: str) -> SessionMetrics | None:
    records: list[dict[str, Any]] = []
    meta: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        records.append(record)
        if record.get("type") != "session_meta":
            continue
        payload = record.get("payload") or {}
        cwd = payload.get("cwd", "")
        if repo_filter in str(cwd):
            meta = payload

    if meta is None:
        return None

    session_id = str(meta.get("id") or "")
    cwd = str(meta.get("cwd") or "")
    session_start = _parse_iso(meta.get("timestamp"))

    first_prompt = ""
    start_ts: datetime | None = session_start
    end_ts: datetime | None = session_start

    total_tokens = 0
    input_tokens = 0
    output_tokens = 0
    cached_input_tokens = 0
    reasoning_output_tokens = 0
    peak_step_tokens = 0

    tool_calls = 0
    function_calls = 0
    custom_tool_calls = 0
    web_search_calls = 0
    shell_calls = 0
    patch_calls = 0
    apply_patch_lines_added = 0
    context_compactions = 0
    tool_name_counts: dict[str, int] = {}

    for record in records:
        event_ts = _parse_iso(record.get("timestamp"))
        if event_ts is not None:
            if start_ts is None or event_ts < start_ts:
                start_ts = event_ts
            if end_ts is None or event_ts > end_ts:
                end_ts = event_ts

        record_type = record.get("type")
        payload = record.get("payload") or {}

        if record_type == "compacted":
            context_compactions += 1

        if record_type == "event_msg":
            event_type = payload.get("type")
            if event_type == "context_compacted":
                context_compactions += 1
            if event_type == "token_count":
                info = payload.get("info") or {}
                if isinstance(info, dict):
                    totals = info.get("total_token_usage") or {}
                    if isinstance(totals, dict):
                        total_tokens = _safe_int(totals.get("total_tokens"))
                        input_tokens = _safe_int(totals.get("input_tokens"))
                        output_tokens = _safe_int(totals.get("output_tokens"))
                        cached_input_tokens = _safe_int(totals.get("cached_input_tokens"))
                        reasoning_output_tokens = _safe_int(
                            totals.get("reasoning_output_tokens")
                        )
                    last_usage = info.get("last_token_usage") or {}
                    if isinstance(last_usage, dict):
                        peak_step_tokens = max(
                            peak_step_tokens,
                            _safe_int(last_usage.get("total_tokens")),
                        )

        if record_type != "response_item":
            continue

        response_type = payload.get("type")

        if response_type == "message" and payload.get("role") == "user":
            text = _extract_user_text(payload)
            if text and not _is_bootstrap_message(text) and not first_prompt:
                first_prompt = _normalize_text(text)
            continue

        if response_type == "function_call":
            function_calls += 1
            tool_calls += 1
            name = str(payload.get("name") or "")
            tool_name_counts[name] = tool_name_counts.get(name, 0) + 1
            if name in {"exec_command", "write_stdin"}:
                shell_calls += 1
            if name == "apply_patch":
                patch_calls += 1
                args = payload.get("arguments")
                if isinstance(args, str):
                    apply_patch_lines_added += _count_added_lines_in_patch(args)
            continue

        if response_type == "custom_tool_call":
            custom_tool_calls += 1
            tool_calls += 1
            name = str(payload.get("name") or "")
            tool_name_counts[name] = tool_name_counts.get(name, 0) + 1
            if name == "apply_patch":
                patch_calls += 1
                patch_input = payload.get("input")
                if isinstance(patch_input, str):
                    apply_patch_lines_added += _count_added_lines_in_patch(patch_input)
            continue

        if response_type == "web_search_call":
            web_search_calls += 1
            tool_calls += 1
            name = "web_search"
            tool_name_counts[name] = tool_name_counts.get(name, 0) + 1

    duration_seconds = 0.0
    if start_ts is not None and end_ts is not None:
        duration_seconds = max((end_ts - start_ts).total_seconds(), 0.0)

    return SessionMetrics(
        session_id=session_id,
        file_path=str(path),
        cwd=cwd,
        start_iso=_iso(start_ts),
        end_iso=_iso(end_ts),
        duration_seconds=duration_seconds,
        first_prompt=first_prompt,
        is_automation=first_prompt.startswith("Automation:"),
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        reasoning_output_tokens=reasoning_output_tokens,
        peak_step_tokens=peak_step_tokens,
        tool_calls=tool_calls,
        function_calls=function_calls,
        custom_tool_calls=custom_tool_calls,
        web_search_calls=web_search_calls,
        shell_calls=shell_calls,
        patch_calls=patch_calls,
        apply_patch_lines_added=apply_patch_lines_added,
        context_compactions=context_compactions,
        tool_name_counts=tool_name_counts,
    )


def build_summary(codex_home: Path, repo_filter: str) -> dict[str, Any]:
    sessions: list[SessionMetrics] = []
    for path in _discover_session_files(codex_home):
        parsed = _parse_session_file(path, repo_filter)
        if parsed is not None:
            sessions.append(parsed)

    sessions.sort(key=lambda item: (item.start_iso, item.session_id))

    start_values = [_parse_iso(item.start_iso) for item in sessions if item.start_iso]
    end_values = [_parse_iso(item.end_iso) for item in sessions if item.end_iso]
    non_null_starts = [value for value in start_values if value is not None]
    non_null_ends = [value for value in end_values if value is not None]

    wall_clock_seconds = 0.0
    if non_null_starts and non_null_ends:
        wall_clock_seconds = max((max(non_null_ends) - min(non_null_starts)).total_seconds(), 0.0)

    active_runtime_seconds = sum(item.duration_seconds for item in sessions)

    totals = {
        "total_tokens": sum(item.total_tokens for item in sessions),
        "input_tokens": sum(item.input_tokens for item in sessions),
        "output_tokens": sum(item.output_tokens for item in sessions),
        "cached_input_tokens": sum(item.cached_input_tokens for item in sessions),
        "reasoning_output_tokens": sum(item.reasoning_output_tokens for item in sessions),
        "tool_calls": sum(item.tool_calls for item in sessions),
        "function_calls": sum(item.function_calls for item in sessions),
        "custom_tool_calls": sum(item.custom_tool_calls for item in sessions),
        "web_search_calls": sum(item.web_search_calls for item in sessions),
        "shell_calls": sum(item.shell_calls for item in sessions),
        "patch_calls": sum(item.patch_calls for item in sessions),
        "apply_patch_lines_added": sum(item.apply_patch_lines_added for item in sessions),
        "context_compactions": sum(item.context_compactions for item in sessions),
    }

    peak_step_tokens = max((item.peak_step_tokens for item in sessions), default=0)

    sessions_with_tokens = sum(1 for item in sessions if item.total_tokens > 0)
    automation_sessions = sum(1 for item in sessions if item.is_automation)
    interactive_sessions = len(sessions) - automation_sessions

    top_by_tokens = sorted(
        sessions,
        key=lambda item: item.total_tokens,
        reverse=True,
    )[:5]

    return {
        "repo_filter": repo_filter,
        "codex_home": str(codex_home),
        "generated_at": _iso(datetime.now(UTC)),
        "summary": {
            "session_count": len(sessions),
            "interactive_sessions": interactive_sessions,
            "automation_sessions": automation_sessions,
            "sessions_with_tokens": sessions_with_tokens,
            "active_runtime_seconds": round(active_runtime_seconds, 3),
            "wall_clock_span_seconds": round(wall_clock_seconds, 3),
            "active_runtime_hours": round(active_runtime_seconds / 3600.0, 3),
            "wall_clock_span_hours": round(wall_clock_seconds / 3600.0, 3),
            "peak_single_step_tokens": peak_step_tokens,
            **totals,
            "date_range": {
                "start": _iso(min(non_null_starts)) if non_null_starts else "",
                "end": _iso(max(non_null_ends)) if non_null_ends else "",
            },
        },
        "top_sessions_by_total_tokens": [
            _serialize_session_metrics(item, codex_home=codex_home, repo_filter=repo_filter)
            for item in top_by_tokens
        ],
        "sessions": [
            _serialize_session_metrics(item, codex_home=codex_home, repo_filter=repo_filter)
            for item in sessions
        ],
    }


def _human_int(value: int) -> str:
    return f"{value:,}"


def _human_m(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _card_template_context(summary: dict[str, Any], title: str) -> dict[str, str]:
    stats = summary["summary"]
    data_range = stats["date_range"]
    start_date = data_range.get("start", "")[:10]
    end_date = data_range.get("end", "")[:10]
    date_span = (
        f"{start_date} to {end_date}"
        if start_date and end_date
        else "Date range unavailable"
    )

    return {
        "title": escape(title),
        "subtitle": escape(
            f"Using local Codex sessions filtered by {summary['repo_filter']} ({date_span})"
        ),
        "active_runtime": f"{stats['active_runtime_hours']:.1f}h",
        "active_runtime_detail": f"{stats['wall_clock_span_hours']:.1f}h wall-clock session span",
        "token_usage": _human_m(stats["total_tokens"]),
        "token_usage_detail": (
            f"{_human_m(stats['input_tokens'])} input + "
            f"{_human_m(stats['output_tokens'])} output"
        ),
        "cached_input_reused": _human_m(stats["cached_input_tokens"]),
        "cached_input_detail": "High context reuse across the run",
        "tool_calls": _human_int(stats["tool_calls"]),
        "tool_calls_detail": (
            f"{_human_int(stats['shell_calls'])} shell calls + "
            f"{_human_int(stats['patch_calls'])} patches"
        ),
        "patch_volume": _human_m(stats["apply_patch_lines_added"]),
        "patch_volume_detail": "Approximate lines added",
        "peak_single_step": _human_int(stats["peak_single_step_tokens"]),
        "peak_single_step_detail": "Tokens in one turn",
        "auto_context_compactions": _human_int(stats["context_compactions"]),
        "auto_context_compactions_detail": "Automatic context management events",
    }


def _default_svg_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "mcp-geo-long-horizon-summary"
        / "templates"
        / "summary_card.svg.tmpl"
    )


def render_summary_card_svg(
    summary: dict[str, Any],
    title: str = SUMMARY_TITLE_DEFAULT,
    template_path: Path | None = None,
) -> str:
    resolved_template = (template_path or _default_svg_template_path()).expanduser()
    template_text = resolved_template.read_text(encoding="utf-8")
    template = Template(template_text)
    return template.safe_substitute(_card_template_context(summary, title))


def render_markdown(
    summary: dict[str, Any],
    summary_image_path: str | None = None,
    summary_image_title: str = SUMMARY_TITLE_DEFAULT,
) -> str:
    stats = summary["summary"]
    data_range = stats["date_range"]

    lines = [
        *(
            [f"![{summary_image_title}]({summary_image_path})", ""]
            if summary_image_path
            else []
        ),
        "# MCP Geo Codex Session Summary",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Codex home: `{summary['codex_home']}`",
        f"Repo filter: `{summary['repo_filter']}`",
        "",
        "## Long Horizon-style Metrics",
        "",
        f"- Active runtime: `{stats['active_runtime_hours']:.1f}h`",
        f"- Wall-clock span: `{stats['wall_clock_span_hours']:.1f}h`",
        f"- Token usage: `{_human_m(stats['total_tokens'])}` "
        f"(`{_human_m(stats['input_tokens'])}` input + "
        f"`{_human_m(stats['output_tokens'])}` output)",
        f"- Cached input reused: `{_human_m(stats['cached_input_tokens'])}`",
        f"- Tool calls: `{_human_int(stats['tool_calls'])}` "
        f"(`{_human_int(stats['shell_calls'])}` shell + "
        f"`{_human_int(stats['patch_calls'])}` patches)",
        f"- Patch volume: `{_human_m(stats['apply_patch_lines_added'])}` lines "
        "(from `apply_patch` calls)",
        f"- Peak single step: `{_human_int(stats['peak_single_step_tokens'])}` tokens",
        f"- Auto context compactions: `{_human_int(stats['context_compactions'])}`",
        "",
        "## Session Coverage",
        "",
        f"- Sessions included: `{stats['session_count']}`",
        f"- Interactive sessions: `{stats['interactive_sessions']}`",
        f"- Automation sessions: `{stats['automation_sessions']}`",
        f"- Sessions with token telemetry: `{stats['sessions_with_tokens']}`",
        f"- Date range: `{data_range['start']}` to `{data_range['end']}`",
        "",
        "## Top Sessions by Total Tokens",
        "",
    ]

    top_sessions = summary.get("top_sessions_by_total_tokens") or []
    if not top_sessions:
        lines.append("- No sessions matched the filter.")
    else:
        for item in top_sessions:
            prompt = item.get("first_prompt") or "(no captured prompt)"
            lines.append(
                f"- `{item['session_id']}`: `{_human_int(item['total_tokens'])}` tokens, "
                f"`{item['start_iso']}` - `{item['end_iso']}`"
            )
            lines.append(f"  Prompt: {prompt[:180]}")

    lines.extend(
        [
            "",
            "## Method Notes",
            "",
            "- Data source: local Codex `sessions` + `archived_sessions` JSONL records.",
            "- Sessions are included when `session_meta.payload.cwd` contains the repo filter.",
            "- Patch volume is estimated from added `+` lines in `apply_patch` payloads.",
            "- Active runtime is summed per-session (`last_event_ts - first_event_ts`).",
        ]
    )

    return "\n".join(lines) + "\n"


def _default_codex_home() -> Path:
    env_value = os.environ.get("CODEX_HOME")
    if env_value:
        return Path(env_value).expanduser()
    return Path.home() / ".codex"


def _default_output_path(repo_filter: str) -> Path:
    date_part = datetime.now(UTC).date().isoformat()
    filename = f"{repo_filter.replace('/', '_')}_codex_long_horizon_summary_{date_part}.md"
    return Path("docs") / "reports" / filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Long Horizon-style Codex session metrics for a repo filter."
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=_default_codex_home(),
        help="Path to Codex home (default: $CODEX_HOME or ~/.codex).",
    )
    parser.add_argument(
        "--repo-filter",
        default="mcp-geo",
        help="Substring match against session_meta cwd (default: mcp-geo).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown output path (default: docs/reports/<repo>_...md).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    parser.add_argument(
        "--summary-svg-output",
        type=Path,
        default=None,
        help="Optional SVG output path for the summary card.",
    )
    parser.add_argument(
        "--summary-title",
        default=SUMMARY_TITLE_DEFAULT,
        help=f"Summary image title (default: {SUMMARY_TITLE_DEFAULT!r}).",
    )
    parser.add_argument(
        "--svg-template",
        type=Path,
        default=_default_svg_template_path(),
        help="Path to deterministic SVG template for the summary card.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print JSON summary to stdout.",
    )
    args = parser.parse_args()

    codex_home = args.codex_home.expanduser()
    summary = build_summary(codex_home=codex_home, repo_filter=args.repo_filter)

    output_path = args.output or _default_output_path(args.repo_filter)
    output_path = output_path.expanduser()

    summary_image_path: str | None = None
    svg_output_path = args.summary_svg_output.expanduser() if args.summary_svg_output else None
    if svg_output_path is not None:
        svg_output_path.parent.mkdir(parents=True, exist_ok=True)
        svg_content = render_summary_card_svg(
            summary=summary,
            title=args.summary_title,
            template_path=args.svg_template,
        )
        svg_output_path.write_text(svg_content, encoding="utf-8")
        rel_svg = os.path.relpath(svg_output_path, start=output_path.parent)
        summary_image_path = Path(rel_svg).as_posix()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_markdown(
            summary,
            summary_image_path=summary_image_path,
            summary_image_title=args.summary_title,
        ),
        encoding="utf-8",
    )

    if args.json_output is not None:
        json_output = args.json_output.expanduser()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.print_json:
        print(json.dumps(summary, indent=2))

    print(f"Wrote markdown summary: {output_path}")
    if svg_output_path is not None:
        print(f"Wrote summary card SVG: {svg_output_path}")
    if args.json_output is not None:
        print(f"Wrote JSON summary: {json_output}")


if __name__ == "__main__":
    main()
