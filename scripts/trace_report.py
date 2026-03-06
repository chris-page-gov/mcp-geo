#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.trace_utils import (
    classify_startup_discovery,
    classify_tool_search_usage,
    extract_fallback_responses,
    find_trace_files,
    format_bytes,
    parse_mcp_trace,
    parse_ui_events,
    resolve_session_dir,
    summarize_methods,
    summarize_upstream_log,
)

DEFAULT_SESSION_ROOT = Path("logs") / "sessions"


def _load_session_meta(files: dict[str, Path]) -> dict[str, Any]:
    session_path = files.get("session")
    if not session_path or not session_path.exists():
        return {}
    try:
        return json.loads(session_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _build_summary(
    session_dir: Path,
    files: dict[str, Path],
    mcp_summaries: list[dict[str, Any]],
    ui_summary: dict[str, Any] | None,
    upstream_lines: list[str],
) -> dict[str, Any]:
    session_meta = _load_session_meta(files)
    requests = [request for summary in mcp_summaries for request in summary["requests"]]
    responses = [response for summary in mcp_summaries for response in summary["responses"]]
    method_counts = summarize_methods(requests)
    tool_counts: Counter[str] = Counter(
        request["tool"]
        for request in requests
        if request.get("method") == "tools/call" and isinstance(request.get("tool"), str)
    )
    error_counts: Counter[str] = Counter(
        str(response.get("code") or "UNKNOWN")
        for response in responses
        if response.get("is_error")
    )
    timestamps = [ts for summary in mcp_summaries for ts in summary["timestamps"]]
    duration = (max(timestamps) - min(timestamps)) if timestamps else None
    initialize = next((request for request in requests if request.get("method") == "initialize"), None)
    first_useful = next(
        (
            request
            for request in requests
            if request.get("method") == "tools/call"
            and request.get("tool") not in {"os_apps.log_event", "os_apps_log_event"}
        ),
        None,
    )
    latency_ms = None
    if initialize and first_useful:
        init_ts = initialize.get("ts")
        first_ts = first_useful.get("ts")
        if isinstance(init_ts, (int, float)) and isinstance(first_ts, (int, float)):
            latency_ms = max(0.0, (float(first_ts) - float(init_ts)) * 1000.0)
    fallback_responses = extract_fallback_responses(responses)

    summary = {
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
        "session": {
            "sessionId": session_meta.get("sessionId", session_dir.name),
            "mode": session_meta.get("mode", "unknown"),
            "source": session_meta.get("source", "unknown"),
            "surface": session_meta.get("surface", "unknown"),
            "hostProfile": session_meta.get("hostProfile"),
            "clientVersion": session_meta.get("clientVersion"),
            "model": session_meta.get("model"),
            "scenarioPack": session_meta.get("scenarioPack"),
            "scenarioId": session_meta.get("scenarioId"),
            "version": session_meta.get("version"),
            "git": session_meta.get("git", {}),
        },
        "artifacts": {
            key: {"path": str(path), "sizeBytes": path.stat().st_size if path.exists() else 0}
            for key, path in files.items()
        },
        "mcp": {
            "requestCount": len(requests),
            "responseCount": len(responses),
            "errorCount": sum(1 for response in responses if response.get("is_error")),
            "parseErrorCount": sum(summary["parse_errors"] for summary in mcp_summaries),
            "durationSeconds": duration,
            "methodCounts": dict(method_counts),
            "toolCounts": dict(tool_counts),
            "errorCounts": dict(error_counts),
        },
        "hostSignals": {
            "initializeCount": method_counts.get("initialize", 0),
            "startupDiscoveryPattern": classify_startup_discovery(requests),
            "toolSearchUsage": classify_tool_search_usage(requests),
            "resourcesReadCount": method_counts.get("resources/read", 0),
            "uiEventCount": len(ui_summary["events"]) if ui_summary else 0,
            "uiEventTypes": dict(
                Counter(
                    event.get("eventType")
                    for event in (ui_summary["events"] if ui_summary else [])
                    if isinstance(event.get("eventType"), str)
                )
            ),
            "fallbackCount": len(fallback_responses),
            "fallbackTools": [
                response.get("result", {}).get("data", {}).get("tool")
                for response in fallback_responses
                if isinstance(response.get("result", {}).get("data"), dict)
            ],
            "latencyToFirstUsefulToolCallMs": latency_ms,
        },
        "upstreamLogHighlights": upstream_lines,
    }
    return summary


def _build_report(
    session_dir: Path,
    files: dict[str, Path],
    summary: dict[str, Any],
) -> str:
    session_meta = summary["session"]
    mcp = summary["mcp"]
    signals = summary["hostSignals"]

    lines: list[str] = []
    lines.append("# MCP Geo Trace Report")
    lines.append(f"Generated: {summary['generatedAt']}")
    lines.append(f"Session dir: {session_dir}")
    lines.append(f"Session id: {session_meta.get('sessionId', session_dir.name)}")
    lines.append(f"Mode: {session_meta.get('mode', 'unknown')}")
    lines.append(f"Source: {session_meta.get('source', 'unknown')}")
    lines.append(f"Surface: {session_meta.get('surface', 'unknown')}")
    if session_meta.get("hostProfile"):
        lines.append(f"Host profile: {session_meta['hostProfile']}")
    if session_meta.get("clientVersion"):
        lines.append(f"Client version: {session_meta['clientVersion']}")
    if session_meta.get("model"):
        lines.append(f"Model: {session_meta['model']}")
    if session_meta.get("scenarioPack"):
        lines.append(f"Scenario pack: {session_meta['scenarioPack']}")
    if session_meta.get("scenarioId"):
        lines.append(f"Scenario id: {session_meta['scenarioId']}")
    version = session_meta.get("version")
    if version:
        lines.append(f"Server version: {version}")
    git = session_meta.get("git", {})
    if isinstance(git, dict) and git.get("commit"):
        lines.append(f"Git: {git.get('branch', 'unknown')} @ {git['commit']}")
    lines.append("")

    lines.append("## Artifacts")
    for key, details in summary["artifacts"].items():
        lines.append(f"- {key}: {details['path']} ({format_bytes(int(details['sizeBytes']))})")
    lines.append("")

    lines.append("## MCP Summary")
    lines.append(f"- Requests: {mcp['requestCount']}")
    lines.append(f"- Responses: {mcp['responseCount']}")
    lines.append(f"- Errors: {mcp['errorCount']}")
    lines.append(f"- Parse errors: {mcp['parseErrorCount']}")
    duration = mcp.get("durationSeconds")
    if isinstance(duration, (int, float)):
        lines.append(f"- Duration: {duration:.1f}s")
    lines.append("")

    lines.append("## Host Signals")
    lines.append(f"- Initialize calls: {signals['initializeCount']}")
    lines.append(f"- Startup discovery: {signals['startupDiscoveryPattern']}")
    lines.append(f"- Tool search usage: {signals['toolSearchUsage']}")
    lines.append(f"- resources/read calls: {signals['resourcesReadCount']}")
    lines.append(f"- UI events: {signals['uiEventCount']}")
    lines.append(f"- Fallback responses: {signals['fallbackCount']}")
    latency_ms = signals.get("latencyToFirstUsefulToolCallMs")
    if isinstance(latency_ms, (int, float)):
        lines.append(f"- Latency to first useful tool call: {latency_ms:.1f} ms")
    lines.append("")

    tool_counts = Counter(mcp.get("toolCounts", {}))
    if tool_counts:
        lines.append("### Tool Calls")
        for tool, count in tool_counts.most_common(20):
            lines.append(f"- {tool}: {count}")
        lines.append("")

    method_counts = Counter(mcp.get("methodCounts", {}))
    if method_counts:
        lines.append("### Method Counts")
        for method, count in method_counts.most_common(10):
            lines.append(f"- {method}: {count}")
        lines.append("")

    error_counts = Counter(mcp.get("errorCounts", {}))
    if error_counts:
        lines.append("### Error Codes")
        for code, count in error_counts.most_common(10):
            lines.append(f"- {code}: {count}")
        lines.append("")

    ui_event_types = Counter(signals.get("uiEventTypes", {}))
    if ui_event_types:
        lines.append("### UI Event Types")
        for event_type, count in ui_event_types.most_common(10):
            lines.append(f"- {event_type}: {count}")
        lines.append("")

    upstream_lines = summary.get("upstreamLogHighlights") or []
    if upstream_lines:
        lines.append("## Upstream Log Highlights")
        lines.append("```text")
        lines.extend(upstream_lines)
        lines.append("```")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _bundle_zip(session_dir: Path, report_path: Path, summary_path: Path, files: dict[str, Path]) -> Path:
    bundle_path = session_dir / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(report_path, report_path.name)
        zf.write(summary_path, summary_path.name)
        for path in files.values():
            if path.exists():
                zf.write(path, path.relative_to(session_dir))
    return bundle_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize MCP Geo trace artifacts.")
    parser.add_argument(
        "session",
        nargs="?",
        default="latest",
        help="Session directory or 'latest'.",
    )
    parser.add_argument("--no-zip", action="store_true", help="Skip zip bundle creation.")
    args = parser.parse_args()

    session_dir = resolve_session_dir(args.session, session_root=DEFAULT_SESSION_ROOT)
    if not session_dir.exists():
        raise SystemExit(f"Session directory not found: {session_dir}")

    files = find_trace_files(session_dir)

    mcp_summaries = []
    if "stdio" in files:
        mcp_summaries.append(parse_mcp_trace(files["stdio"], "stdio"))
    if "http" in files:
        mcp_summaries.append(parse_mcp_trace(files["http"], "http"))

    ui_summary = parse_ui_events(files["ui"]) if "ui" in files else None
    upstream_lines = summarize_upstream_log(files["upstream"]) if "upstream" in files else []

    summary = _build_summary(session_dir, files, mcp_summaries, ui_summary, upstream_lines)
    summary_path = session_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report_text = _build_report(session_dir, files, summary)
    report_path = session_dir / "report.md"
    report_path.write_text(report_text, encoding="utf-8")

    if not args.no_zip:
        _bundle_zip(session_dir, report_path, summary_path, files)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
