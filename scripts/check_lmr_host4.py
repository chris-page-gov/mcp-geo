#!/usr/bin/env python3
"""Automate LMR-HOST-4 evidence checks for Claude Desktop sessions.

This script focuses on the known host-runtime gap:
- Widget tool call succeeds (`os_apps.render_boundary_explorer`)
- Resource is read (`ui://mcp-geo/boundary-explorer`)
- But no runtime bridge events (`os_apps.log_event`) follow

Optional prechecks:
- `scripts/mcp_ui_mode_probe.py` payload-shape probe
- Playwright deterministic host-bridge smoke (`trial-5`)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_TRACE_PATH = Path("logs/claude-trace.jsonl")
DEFAULT_UI_EVENTS_PATH = Path("logs/ui-events.jsonl")
DEFAULT_PROBE_JSON = Path("logs/ui-probe-lmr-host4.json")
DEFAULT_REPORT_JSON = Path("logs/lmr-host4-report.json")
DEFAULT_WINDOW_SECONDS = 180.0
DEFAULT_PLAYWRIGHT_GREP = (
    "trial-5 deterministic host-simulation fixtures are stable across engines"
)
DEFAULT_PLAYWRIGHT_WORKERS = 1

BOUNDARY_TOOL_NAMES = {
    "os_apps.render_boundary_explorer",
    "os_apps_render_boundary_explorer",
}
LOG_EVENT_TOOL_NAMES = {"os_apps.log_event", "os_apps_log_event"}
BOUNDARY_RESOURCE_URIS = {"ui://mcp-geo/boundary-explorer"}
BOUNDARY_RESOURCE_NAMES = {"ui_boundary_explorer"}
BOUNDARY_UI_SOURCES = {"boundary-explorer", "boundary_explorer"}
BOUNDARY_UI_RUNTIME_EVENT_TYPES = {
    "host_ready",
    "map_init_skipped",
    "map_init_failed",
    "window_error",
    "unhandled_rejection",
}


@dataclass(frozen=True)
class TraceMessage:
    ts: float
    direction: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    ts: float
    request_id: Any
    name: str


@dataclass(frozen=True)
class ToolResponse:
    ts: float
    request_id: Any
    status: int | None
    ok: bool
    is_error: bool


@dataclass(frozen=True)
class Host4Report:
    verdict: str
    reason: str
    checked_at_utc: str
    trace_path: str
    ui_events_path: str
    window_seconds: float
    boundary_tool_calls: int
    boundary_tool_successes: int
    boundary_resource_reads: int
    log_event_calls: int
    ui_events_in_window: int
    ui_event_types_in_window: list[str]
    boundary_ui_runtime_events: int
    last_boundary_success_ts: float | None
    last_resource_read_ts: float | None
    last_log_event_call_ts: float | None
    probe_ran: bool
    probe_ok: bool | None
    probe_summary: str
    playwright_ran: bool
    playwright_ok: bool | None
    playwright_summary: str


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _normalize_epoch_seconds(value: Any) -> float | None:
    ts = _to_float(value)
    if ts is None:
        return None
    # Browser timestamps may arrive in milliseconds.
    if ts > 1_000_000_000_000:
        return ts / 1000.0
    return ts


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _parse_payload(record: dict[str, Any]) -> dict[str, Any] | None:
    payload = record.get("json")
    if isinstance(payload, dict):
        return payload
    raw = record.get("raw")
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if isinstance(decoded, dict):
            return decoded
    return None


def _load_trace_messages(path: Path) -> list[TraceMessage]:
    out: list[TraceMessage] = []
    for row in _read_jsonl(path):
        direction = row.get("direction")
        if not isinstance(direction, str):
            continue
        payload = _parse_payload(row)
        if payload is None:
            continue
        ts = _normalize_epoch_seconds(row.get("ts"))
        if ts is None:
            continue
        out.append(TraceMessage(ts=ts, direction=direction, payload=payload))
    return sorted(out, key=lambda item: item.ts)


def _extract_tool_name(payload: dict[str, Any]) -> str | None:
    params = payload.get("params")
    if not isinstance(params, dict):
        return None
    name = params.get("name") or params.get("tool")
    if isinstance(name, str):
        return name
    return None


def _extract_response_status(result: Any) -> int | None:
    if not isinstance(result, dict):
        return None
    status = result.get("status")
    if isinstance(status, int):
        return status
    parsed = _to_float(status)
    if parsed is None:
        return None
    return int(parsed)


def _response_ok(payload: dict[str, Any]) -> tuple[int | None, bool, bool]:
    error = payload.get("error")
    if isinstance(error, dict):
        return None, False, True
    result = payload.get("result")
    status = _extract_response_status(result)
    if isinstance(result, dict):
        ok_flag = result.get("ok")
        if isinstance(ok_flag, bool):
            return status, ok_flag and (status in (None, 200)), False
        is_error = bool(result.get("isError"))
        if is_error:
            return status, False, True
    return status, status in (None, 200), False


def _is_boundary_resource_read(payload: dict[str, Any]) -> bool:
    params = payload.get("params")
    if not isinstance(params, dict):
        return False
    uri = params.get("uri")
    if isinstance(uri, str) and uri in BOUNDARY_RESOURCE_URIS:
        return True
    name = params.get("name")
    if isinstance(name, str) and name in BOUNDARY_RESOURCE_NAMES:
        return True
    return False


def _find_responses_by_id(messages: list[TraceMessage]) -> dict[Any, list[ToolResponse]]:
    out: dict[Any, list[ToolResponse]] = {}
    for row in messages:
        if row.direction != "server->client":
            continue
        req_id = row.payload.get("id")
        if req_id is None:
            continue
        status, ok, is_error = _response_ok(row.payload)
        out.setdefault(req_id, []).append(
            ToolResponse(
                ts=row.ts,
                request_id=req_id,
                status=status,
                ok=ok,
                is_error=is_error,
            )
        )
    for req_id in out:
        out[req_id].sort(key=lambda item: item.ts)
    return out


def _find_matching_response(
    call: ToolCall,
    responses_by_id: dict[Any, list[ToolResponse]],
) -> ToolResponse | None:
    candidates = responses_by_id.get(call.request_id, [])
    for item in candidates:
        if item.ts >= call.ts:
            return item
    return None


def _load_ui_events(path: Path) -> list[dict[str, Any]]:
    rows = _read_jsonl(path)
    out: list[dict[str, Any]] = []
    for row in rows:
        ts = _normalize_epoch_seconds(row.get("timestamp"))
        event_type = row.get("eventType")
        if ts is None or not isinstance(event_type, str):
            continue
        source = row.get("source")
        session_id = row.get("sessionId")
        out.append(
            {
                "timestamp": ts,
                "eventType": event_type,
                "source": source if isinstance(source, str) else None,
                "sessionId": session_id if isinstance(session_id, str) else None,
            }
        )
    return sorted(out, key=lambda item: float(item["timestamp"]))


def _run_probe(
    *,
    timeout_seconds: float,
    save_path: Path,
    command: list[str] | None,
) -> tuple[bool, str]:
    probe_cmd = [sys.executable, "scripts/mcp_ui_mode_probe.py", "--timeout", f"{timeout_seconds:.1f}"]
    probe_cmd.extend(["--save", str(save_path)])
    if command:
        probe_cmd.append("--")
        probe_cmd.extend(command)
    proc = subprocess.run(
        probe_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        return False, f"probe failed (code={proc.returncode}): {stderr}"
    if not save_path.exists():
        return False, "probe did not write save file"
    data = json.loads(save_path.read_text(encoding="utf-8"))
    rows = data.get("results")
    if not isinstance(rows, list):
        return False, "probe output missing results"
    resource_link_ok = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        mode = row.get("mode")
        response = row.get("response")
        if mode != "resource_link" or not isinstance(response, dict):
            continue
        result = response.get("result")
        if not isinstance(result, dict):
            continue
        content = result.get("content")
        if not isinstance(content, list):
            continue
        content_types = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("type"), str):
                content_types.append(block["type"])
        if "resource_link" in content_types:
            resource_link_ok = True
            break
    if resource_link_ok:
        return True, "probe passed (`resource_link` content present)"
    return False, "probe missing `resource_link` content in resource_link mode"


def _run_playwright_smoke(
    *,
    projects: list[str] | None,
    grep: str,
    workers: int,
    test_path: str | None,
) -> tuple[bool, str]:
    if workers < 1:
        return False, "playwright workers must be >= 1"
    cmd = [
        "npx",
        "playwright",
        "test",
    ]
    if test_path:
        cmd.append(test_path)
    cmd.extend(["--config", "playwright.trials.config.js", f"--workers={workers}"])
    if grep:
        cmd.extend(["-g", grep])
    if projects:
        for project in projects:
            cmd.extend(["--project", project])
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd="playground",
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr or stdout or "no output"
        if len(detail) > 400:
            detail = detail[:400] + "..."
        return False, f"playwright smoke failed (code={proc.returncode}): {detail}"
    project_summary = ",".join(projects) if projects else "all projects"
    return True, f"playwright trial-5 smoke passed ({project_summary})"


def _load_ui_events_with_fallback(path: Path) -> tuple[list[dict[str, Any]], Path]:
    events = _load_ui_events(path)
    if events:
        return events, path
    # VS Code commonly writes either trace-mode or non-trace UI logs.
    if path.name == "ui-events.vscode-trace.jsonl":
        alt = path.with_name("ui-events.vscode.jsonl")
        alt_events = _load_ui_events(alt)
        if alt_events:
            return alt_events, alt
    return events, path


def _boundary_ui_runtime_events(ui_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in ui_events:
        source = row.get("source")
        event_type = row.get("eventType")
        if not isinstance(source, str) or not isinstance(event_type, str):
            continue
        if source in BOUNDARY_UI_SOURCES and event_type in BOUNDARY_UI_RUNTIME_EVENT_TYPES:
            out.append(row)
    return out


def analyze_lmr_host4(
    *,
    trace_path: Path,
    ui_events_path: Path,
    window_seconds: float,
) -> Host4Report:
    messages = _load_trace_messages(trace_path)
    responses_by_id = _find_responses_by_id(messages)

    boundary_calls: list[ToolCall] = []
    resource_reads: list[float] = []
    log_event_calls: list[float] = []

    for row in messages:
        if row.direction != "client->server":
            continue
        method = row.payload.get("method")
        if method == "tools/call":
            tool_name = _extract_tool_name(row.payload)
            if not tool_name:
                continue
            if tool_name in BOUNDARY_TOOL_NAMES:
                boundary_calls.append(
                    ToolCall(
                        ts=row.ts,
                        request_id=row.payload.get("id"),
                        name=tool_name,
                    )
                )
            elif tool_name in LOG_EVENT_TOOL_NAMES:
                log_event_calls.append(row.ts)
        elif method == "resources/read":
            if _is_boundary_resource_read(row.payload):
                resource_reads.append(row.ts)

    successful_calls: list[ToolCall] = []
    for call in boundary_calls:
        response = _find_matching_response(call, responses_by_id)
        if response and response.ok and not response.is_error:
            successful_calls.append(call)

    ui_events, ui_events_used_path = _load_ui_events_with_fallback(ui_events_path)
    boundary_runtime_events = _boundary_ui_runtime_events(ui_events)
    ui_event_types_in_window: list[str] = []
    ui_events_in_window = 0

    if not boundary_calls:
        if boundary_runtime_events:
            boundary_event_types = sorted(
                {
                    str(item.get("eventType"))
                    for item in boundary_runtime_events
                    if isinstance(item.get("eventType"), str)
                }
            )
            return Host4Report(
                verdict="PASS_UI_ONLY",
                reason=(
                    "No boundary-explorer tool calls found in trace, but boundary-explorer UI "
                    "runtime events were observed in UI logs."
                ),
                checked_at_utc=_now_iso(),
                trace_path=str(trace_path),
                ui_events_path=str(ui_events_used_path),
                window_seconds=window_seconds,
                boundary_tool_calls=0,
                boundary_tool_successes=0,
                boundary_resource_reads=len(resource_reads),
                log_event_calls=len(log_event_calls),
                ui_events_in_window=len(boundary_runtime_events),
                ui_event_types_in_window=boundary_event_types,
                boundary_ui_runtime_events=len(boundary_runtime_events),
                last_boundary_success_ts=None,
                last_resource_read_ts=max(resource_reads) if resource_reads else None,
                last_log_event_call_ts=max(log_event_calls) if log_event_calls else None,
                probe_ran=False,
                probe_ok=None,
                probe_summary="not run",
                playwright_ran=False,
                playwright_ok=None,
                playwright_summary="not run",
            )
        return Host4Report(
            verdict="INCONCLUSIVE",
            reason="No boundary-explorer tool calls found in trace.",
            checked_at_utc=_now_iso(),
            trace_path=str(trace_path),
            ui_events_path=str(ui_events_used_path),
            window_seconds=window_seconds,
            boundary_tool_calls=0,
            boundary_tool_successes=0,
            boundary_resource_reads=len(resource_reads),
            log_event_calls=len(log_event_calls),
            ui_events_in_window=0,
            ui_event_types_in_window=[],
            boundary_ui_runtime_events=0,
            last_boundary_success_ts=None,
            last_resource_read_ts=max(resource_reads) if resource_reads else None,
            last_log_event_call_ts=max(log_event_calls) if log_event_calls else None,
            probe_ran=False,
            probe_ok=None,
            probe_summary="not run",
            playwright_ran=False,
            playwright_ok=None,
            playwright_summary="not run",
        )

    if not successful_calls:
        return Host4Report(
            verdict="FAIL_SERVER",
            reason="Boundary-explorer tool calls found, but none returned success.",
            checked_at_utc=_now_iso(),
            trace_path=str(trace_path),
            ui_events_path=str(ui_events_used_path),
            window_seconds=window_seconds,
            boundary_tool_calls=len(boundary_calls),
            boundary_tool_successes=0,
            boundary_resource_reads=len(resource_reads),
            log_event_calls=len(log_event_calls),
            ui_events_in_window=0,
            ui_event_types_in_window=[],
            boundary_ui_runtime_events=0,
            last_boundary_success_ts=None,
            last_resource_read_ts=max(resource_reads) if resource_reads else None,
            last_log_event_call_ts=max(log_event_calls) if log_event_calls else None,
            probe_ran=False,
            probe_ok=None,
            probe_summary="not run",
            playwright_ran=False,
            playwright_ok=None,
            playwright_summary="not run",
        )

    target = max(successful_calls, key=lambda row: row.ts)
    window_start = target.ts
    window_end = target.ts + window_seconds

    reads_in_window = [ts for ts in resource_reads if window_start <= ts <= window_end]
    resource_gate = min(reads_in_window) if reads_in_window else window_start
    log_events_in_window = [ts for ts in log_event_calls if resource_gate <= ts <= window_end]

    for row in ui_events:
        ts = float(row["timestamp"])
        if resource_gate <= ts <= window_end:
            ui_events_in_window += 1
            ui_event_types_in_window.append(str(row["eventType"]))

    has_resource_read = bool(reads_in_window)
    has_runtime_events = bool(log_events_in_window) or ui_events_in_window > 0

    if has_resource_read and has_runtime_events:
        verdict = "PASS"
        reason = (
            "Widget tool call, boundary resource read, and runtime bridge events were all observed."
        )
    elif has_resource_read and not has_runtime_events:
        verdict = "FAIL_HOST_RUNTIME"
        reason = (
            "Resource was read after successful widget tool call, but no runtime bridge events were "
            "observed."
        )
    else:
        verdict = "FAIL_RESOURCE_READ"
        reason = (
            "Successful widget tool call observed, but no boundary resource read followed in window."
        )

    return Host4Report(
        verdict=verdict,
        reason=reason,
        checked_at_utc=_now_iso(),
        trace_path=str(trace_path),
        ui_events_path=str(ui_events_used_path),
        window_seconds=window_seconds,
        boundary_tool_calls=len(boundary_calls),
        boundary_tool_successes=len(successful_calls),
        boundary_resource_reads=len(resource_reads),
        log_event_calls=len(log_event_calls),
        ui_events_in_window=ui_events_in_window,
        ui_event_types_in_window=sorted(set(ui_event_types_in_window)),
        boundary_ui_runtime_events=0,
        last_boundary_success_ts=target.ts,
        last_resource_read_ts=max(reads_in_window) if reads_in_window else None,
        last_log_event_call_ts=max(log_events_in_window) if log_events_in_window else None,
        probe_ran=False,
        probe_ok=None,
        probe_summary="not run",
        playwright_ran=False,
        playwright_ok=None,
        playwright_summary="not run",
    )


def _with_precheck_results(
    report: Host4Report,
    *,
    probe_ran: bool,
    probe_ok: bool | None,
    probe_summary: str,
    playwright_ran: bool,
    playwright_ok: bool | None,
    playwright_summary: str,
) -> Host4Report:
    payload = asdict(report)
    payload["probe_ran"] = probe_ran
    payload["probe_ok"] = probe_ok
    payload["probe_summary"] = probe_summary
    payload["playwright_ran"] = playwright_ran
    payload["playwright_ok"] = playwright_ok
    payload["playwright_summary"] = playwright_summary
    return Host4Report(**payload)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automate LMR-HOST-4 consistency checks.")
    parser.add_argument(
        "--trace",
        default=str(DEFAULT_TRACE_PATH),
        help="Path to Claude stdio trace JSONL.",
    )
    parser.add_argument(
        "--ui-events",
        default=str(DEFAULT_UI_EVENTS_PATH),
        help="Path to UI events JSONL.",
    )
    parser.add_argument(
        "--window-seconds",
        type=float,
        default=DEFAULT_WINDOW_SECONDS,
        help="Analysis window after latest successful boundary tool call.",
    )
    parser.add_argument(
        "--save",
        default=str(DEFAULT_REPORT_JSON),
        help="Path to save analysis JSON report.",
    )
    parser.add_argument(
        "--run-probe",
        action="store_true",
        help="Run mcp_ui_mode_probe.py before trace analysis.",
    )
    parser.add_argument(
        "--probe-save",
        default=str(DEFAULT_PROBE_JSON),
        help="Where to save probe JSON output when --run-probe is used.",
    )
    parser.add_argument(
        "--probe-timeout",
        type=float,
        default=10.0,
        help="Per-request timeout for mcp_ui_mode_probe.py.",
    )
    parser.add_argument(
        "--probe-command",
        nargs="+",
        help="Optional command passed to mcp_ui_mode_probe.py after '--'.",
    )
    parser.add_argument(
        "--run-playwright-smoke",
        action="store_true",
        help="Run trial-5 deterministic host-simulation smoke before analysis.",
    )
    parser.add_argument(
        "--playwright-project",
        action="append",
        default=[],
        help=(
            "Playwright project name to run for smoke precheck (repeatable). "
            "Defaults to all projects."
        ),
    )
    parser.add_argument(
        "--playwright-grep",
        default=DEFAULT_PLAYWRIGHT_GREP,
        help="Playwright test title grep passed to `-g`.",
    )
    parser.add_argument(
        "--playwright-workers",
        type=int,
        default=DEFAULT_PLAYWRIGHT_WORKERS,
        help="Playwright worker count for smoke precheck.",
    )
    parser.add_argument(
        "--playwright-test",
        help=(
            "Optional specific test file/path for smoke precheck "
            "(relative to playground)."
        ),
    )
    parser.add_argument(
        "--strict-prechecks",
        action="store_true",
        help="Fail immediately if requested prechecks fail.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    trace_path = Path(args.trace)
    ui_events_path = Path(args.ui_events)
    save_path = Path(args.save)

    probe_ran = False
    probe_ok: bool | None = None
    probe_summary = "not run"
    playwright_ran = False
    playwright_ok: bool | None = None
    playwright_summary = "not run"

    if args.run_probe:
        probe_ran = True
        probe_ok, probe_summary = _run_probe(
            timeout_seconds=float(args.probe_timeout),
            save_path=Path(args.probe_save),
            command=args.probe_command,
        )
        if args.strict_prechecks and not probe_ok:
            print(f"LMR-HOST-4 precheck failed: {probe_summary}", file=sys.stderr)
            return 3

    if args.run_playwright_smoke:
        playwright_ran = True
        playwright_ok, playwright_summary = _run_playwright_smoke(
            projects=list(args.playwright_project),
            grep=str(args.playwright_grep),
            workers=int(args.playwright_workers),
            test_path=str(args.playwright_test) if args.playwright_test else None,
        )
        if args.strict_prechecks and not playwright_ok:
            print(f"LMR-HOST-4 precheck failed: {playwright_summary}", file=sys.stderr)
            return 4

    report = analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_events_path,
        window_seconds=float(args.window_seconds),
    )
    report = _with_precheck_results(
        report,
        probe_ran=probe_ran,
        probe_ok=probe_ok,
        probe_summary=probe_summary,
        playwright_ran=playwright_ran,
        playwright_ok=playwright_ok,
        playwright_summary=playwright_summary,
    )

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(
        json.dumps(asdict(report), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"LMR-HOST-4 verdict: {report.verdict}")
    print(report.reason)
    print(f"Boundary tool calls: {report.boundary_tool_calls}")
    print(f"Boundary successes: {report.boundary_tool_successes}")
    print(f"Boundary resource reads: {report.boundary_resource_reads}")
    print(f"Log-event tool calls: {report.log_event_calls}")
    print(f"UI events in window: {report.ui_events_in_window}")
    if report.ui_event_types_in_window:
        print("UI event types in window:", ", ".join(report.ui_event_types_in_window))
    if report.boundary_ui_runtime_events:
        print(f"Boundary UI runtime events: {report.boundary_ui_runtime_events}")
    if report.probe_ran:
        print(f"Probe: {'ok' if report.probe_ok else 'failed'} - {report.probe_summary}")
    if report.playwright_ran:
        print(
            f"Playwright smoke: {'ok' if report.playwright_ok else 'failed'} - "
            f"{report.playwright_summary}"
        )
    print(f"Saved report: {save_path}")

    if report.verdict in {"PASS", "PASS_UI_ONLY"}:
        return 0
    if report.verdict == "INCONCLUSIVE":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
