#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SESSION_ROOT = Path("logs") / "sessions"


def _load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": line}
                continue
            if isinstance(payload, dict):
                yield payload


def _resolve_session_dir(value: str) -> Path:
    if value == "latest":
        marker = DEFAULT_SESSION_ROOT / ".latest"
        if not marker.exists():
            raise FileNotFoundError("No latest session marker found.")
        path = Path(marker.read_text(encoding="utf-8").strip())
        if not path.exists():
            raise FileNotFoundError(f"Latest session directory missing: {path}")
        return path
    return Path(value)


def _find_trace_files(session_dir: Path) -> dict[str, Path]:
    candidates = {
        "stdio": session_dir / "mcp-stdio-trace.jsonl",
        "http": session_dir / "mcp-http-trace.jsonl",
        "ui": session_dir / "ui-events.jsonl",
        "upstream": session_dir / "upstream.log",
        "session": session_dir / "session.json",
    }
    return {key: path for key, path in candidates.items() if path.exists()}


def _extract_method(record: dict[str, Any]) -> str | None:
    if "method_name" in record:
        return record.get("method_name")
    if "method" in record:
        return record.get("method")
    payload = record.get("json")
    if isinstance(payload, dict):
        return payload.get("method")
    return None


def _extract_params(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("json")
    if isinstance(payload, dict):
        params = payload.get("params")
        if isinstance(params, dict):
            return params
    return {}


def _extract_tool_name(params: dict[str, Any]) -> str | None:
    name = params.get("name") or params.get("tool")
    if isinstance(name, str):
        return name
    return None


def _parse_mcp_trace(path: Path, transport: str) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    parse_errors = 0
    timestamps: list[float] = []

    for record in _load_jsonl(path):
        if "_parse_error" in record:
            parse_errors += 1
            continue
        ts = record.get("ts")
        if isinstance(ts, (int, float)):
            timestamps.append(float(ts))
        direction = record.get("direction")
        if direction in {"client->server", "client->upstream"}:
            method = _extract_method(record)
            if not method:
                continue
            payload = record.get("json") if isinstance(record.get("json"), dict) else {}
            req_id = record.get("id") or payload.get("id")
            params = _extract_params(record)
            tool = _extract_tool_name(params) if method == "tools/call" else None
            requests.append(
                {
                    "id": req_id,
                    "method": method,
                    "tool": tool,
                    "ts": ts,
                    "transport": transport,
                }
            )
        elif direction in {"server->client", "upstream->client"}:
            payload = record.get("json")
            if not isinstance(payload, dict):
                continue
            resp_id = payload.get("id")
            if resp_id is None:
                continue
            error_code = None
            error_message = None
            is_error = False
            if isinstance(payload.get("error"), dict):
                is_error = True
                error_code = payload["error"].get("code")
                error_message = payload["error"].get("message")
            else:
                result = payload.get("result")
                if isinstance(result, dict):
                    data = result.get("data") if isinstance(result.get("data"), dict) else {}
                    if result.get("isError") or (isinstance(data, dict) and data.get("isError")):
                        is_error = True
                        error_code = data.get("code") or result.get("code")
                        error_message = data.get("message") or result.get("message")
            responses.append(
                {
                    "id": resp_id,
                    "is_error": is_error,
                    "code": error_code,
                    "message": error_message,
                    "ts": ts,
                    "transport": transport,
                }
            )

    return {
        "requests": requests,
        "responses": responses,
        "parse_errors": parse_errors,
        "timestamps": timestamps,
    }


def _parse_ui_events(path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    parse_errors = 0
    for record in _load_jsonl(path):
        if "_parse_error" in record:
            parse_errors += 1
            continue
        events.append(record)
    return {"events": events, "parse_errors": parse_errors}


def _summarize_upstream_log(path: Path, max_lines: int = 120) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []
    tail = lines[-max_lines:]
    highlights = [line for line in tail if "Upstream error" in line or "ERROR" in line]
    return highlights if highlights else tail[-20:]


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def _format_time(ts: float | None) -> str:
    if ts is None:
        return "n/a"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _build_report(
    session_dir: Path,
    files: dict[str, Path],
    mcp_summaries: list[dict[str, Any]],
    ui_summary: dict[str, Any] | None,
    upstream_lines: list[str],
) -> str:
    now = datetime.now(tz=timezone.utc).isoformat()
    session_meta = {}
    session_path = files.get("session")
    if session_path and session_path.exists():
        try:
            session_meta = json.loads(session_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            session_meta = {}

    lines: list[str] = []
    lines.append("# MCP Geo Trace Report")
    lines.append(f"Generated: {now}")
    lines.append(f"Session dir: {session_dir}")
    if session_meta:
        lines.append(f"Session id: {session_meta.get('sessionId', session_dir.name)}")
        lines.append(f"Mode: {session_meta.get('mode', 'unknown')}")
        version = session_meta.get("version")
        if version:
            lines.append(f"Version: {version}")
        git = session_meta.get("git", {})
        if isinstance(git, dict) and git.get("commit"):
            lines.append(f"Git: {git.get('branch', 'unknown')} @ {git['commit']}")
    lines.append("")

    lines.append("## Artifacts")
    for key, path in files.items():
        size = path.stat().st_size if path.exists() else 0
        lines.append(f"- {key}: {path} ({_format_bytes(size)})")
    lines.append("")

    lines.append("## MCP Summary")
    total_requests = sum(len(s["requests"]) for s in mcp_summaries)
    total_responses = sum(len(s["responses"]) for s in mcp_summaries)
    total_errors = sum(1 for s in mcp_summaries for r in s["responses"] if r["is_error"])
    parse_errors = sum(s["parse_errors"] for s in mcp_summaries)
    timestamps = [ts for s in mcp_summaries for ts in s["timestamps"]]
    duration = None
    if timestamps:
        duration = max(timestamps) - min(timestamps)
    lines.append(f"- Requests: {total_requests}")
    lines.append(f"- Responses: {total_responses}")
    lines.append(f"- Errors: {total_errors}")
    lines.append(f"- Parse errors: {parse_errors}")
    if duration is not None:
        start = _format_time(min(timestamps))
        end = _format_time(max(timestamps))
        lines.append(f"- Duration: {duration:.1f}s ({start} to {end})")
    lines.append("")

    tool_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    request_by_id: dict[Any, dict[str, Any]] = {}
    response_ids: set[Any] = set()
    error_counts: Counter[str] = Counter()
    error_samples: dict[str, str] = {}

    for summary in mcp_summaries:
        for request in summary["requests"]:
            method_counts[request["method"]] += 1
            if request.get("tool"):
                tool_counts[request["tool"]] += 1
            req_id = request.get("id")
            if req_id is not None:
                request_by_id[(request["transport"], req_id)] = request
        for response in summary["responses"]:
            resp_id = response.get("id")
            if resp_id is not None:
                response_ids.add((response["transport"], resp_id))
            if response["is_error"]:
                code = response.get("code") or "UNKNOWN"
                error_counts[code] += 1
                if code not in error_samples and response.get("message"):
                    error_samples[code] = str(response["message"])[:200]

    if tool_counts:
        lines.append("### Tool Calls")
        for tool, count in tool_counts.most_common(20):
            lines.append(f"- {tool}: {count}")
        lines.append("")

    if method_counts:
        lines.append("### Method Counts")
        for method, count in method_counts.most_common(10):
            lines.append(f"- {method}: {count}")
        lines.append("")

    if error_counts:
        lines.append("### Error Codes")
        for code, count in error_counts.most_common(10):
            sample = error_samples.get(code, "")
            if sample:
                lines.append(f"- {code}: {count} (sample: {sample})")
            else:
                lines.append(f"- {code}: {count}")
        lines.append("")

    missing = []
    for key, request in request_by_id.items():
        if key not in response_ids:
            missing.append(request)
    if missing:
        lines.append("### Missing Responses")
        for req in missing[:20]:
            tool = f" ({req['tool']})" if req.get("tool") else ""
            lines.append(f"- {req['transport']} id={req['id']} {req['method']}{tool}")
        if len(missing) > 20:
            lines.append(f"- ... and {len(missing) - 20} more")
        lines.append("")

    if ui_summary:
        events = ui_summary["events"]
        lines.append("## UI Events")
        lines.append(f"- Events: {len(events)}")
        if ui_summary["parse_errors"]:
            lines.append(f"- Parse errors: {ui_summary['parse_errors']}")
        counts = Counter()
        for event in events:
            event_type = event.get("eventType")
            if isinstance(event_type, str):
                counts[event_type] += 1
        for event_type, count in counts.most_common(10):
            lines.append(f"- {event_type}: {count}")
        lines.append("")

    if upstream_lines:
        lines.append("## Upstream Log Highlights")
        lines.append("```text")
        lines.extend(upstream_lines)
        lines.append("```")
        lines.append("")

    if not mcp_summaries:
        lines.append("## Notes")
        lines.append(
            "No MCP trace logs found. Ensure the session captured a stdio or HTTP trace log."
        )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _bundle_zip(session_dir: Path, report_path: Path, files: dict[str, Path]) -> Path:
    bundle_path = session_dir / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(report_path, report_path.name)
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

    session_dir = _resolve_session_dir(args.session)
    if not session_dir.exists():
        raise SystemExit(f"Session directory not found: {session_dir}")

    files = _find_trace_files(session_dir)

    mcp_summaries = []
    if "stdio" in files:
        mcp_summaries.append(_parse_mcp_trace(files["stdio"], "stdio"))
    if "http" in files:
        mcp_summaries.append(_parse_mcp_trace(files["http"], "http"))

    ui_summary = _parse_ui_events(files["ui"]) if "ui" in files else None
    upstream_lines = _summarize_upstream_log(files["upstream"]) if "upstream" in files else []

    report_text = _build_report(session_dir, files, mcp_summaries, ui_summary, upstream_lines)
    report_path = session_dir / "report.md"
    report_path.write_text(report_text, encoding="utf-8")

    if not args.no_zip:
        _bundle_zip(session_dir, report_path, files)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
