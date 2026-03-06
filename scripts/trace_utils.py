from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SESSION_ROOT = Path("logs") / "sessions"
DOCKER_LOCAL_WRAPPER_NAMES = {"claude-mcp-local", "codex-mcp-local", "mcp-docker-local"}
IGNORE_USEFUL_TOOL_NAMES = {"os_apps.log_event", "os_apps_log_event"}


def load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
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


def resolve_session_dir(value: str, *, session_root: Path = DEFAULT_SESSION_ROOT) -> Path:
    if value == "latest":
        marker = session_root / ".latest"
        if not marker.exists():
            raise FileNotFoundError("No latest session marker found.")
        path = Path(marker.read_text(encoding="utf-8").strip())
        if not path.exists():
            raise FileNotFoundError(f"Latest session directory missing: {path}")
        return path
    return Path(value)


def find_trace_files(session_dir: Path) -> dict[str, Path]:
    candidates = {
        "stdio": session_dir / "mcp-stdio-trace.jsonl",
        "http": session_dir / "mcp-http-trace.jsonl",
        "ui": session_dir / "ui-events.jsonl",
        "upstream": session_dir / "upstream.log",
        "session": session_dir / "session.json",
        "summary": session_dir / "summary.json",
        "benchmarkEvidence": session_dir / "benchmark-evidence.json",
        "benchmarkScore": session_dir / "benchmark-score.json",
    }
    return {key: path for key, path in candidates.items() if path.exists()}


def extract_method(record: dict[str, Any]) -> str | None:
    if "method_name" in record:
        return record.get("method_name")
    if "method" in record:
        return record.get("method")
    payload = record.get("json")
    if isinstance(payload, dict):
        return payload.get("method")
    return None


def extract_params(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("json")
    if isinstance(payload, dict):
        params = payload.get("params")
        if isinstance(params, dict):
            return params
    return {}


def extract_tool_name(params: dict[str, Any]) -> str | None:
    name = params.get("name") or params.get("tool")
    if isinstance(name, str):
        return name
    return None


def parse_mcp_trace(path: Path, transport: str) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    parse_errors = 0
    timestamps: list[float] = []

    for record in load_jsonl(path):
        if "_parse_error" in record:
            parse_errors += 1
            continue
        ts = record.get("ts")
        if isinstance(ts, (int, float)):
            timestamps.append(float(ts))
        direction = record.get("direction")
        if direction in {"client->server", "client->upstream"}:
            method = extract_method(record)
            if not method:
                continue
            payload = record.get("json") if isinstance(record.get("json"), dict) else {}
            req_id = record.get("id") or payload.get("id")
            params = extract_params(record)
            tool = extract_tool_name(params) if method == "tools/call" else None
            requests.append(
                {
                    "id": req_id,
                    "method": method,
                    "tool": tool,
                    "params": params,
                    "payload": payload,
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
            result = payload.get("result")
            if isinstance(payload.get("error"), dict):
                is_error = True
                error_code = payload["error"].get("code")
                error_message = payload["error"].get("message")
            else:
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
                    "payload": payload,
                    "result": result if isinstance(result, dict) else {},
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


def parse_ui_events(path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    parse_errors = 0
    for record in load_jsonl(path):
        if "_parse_error" in record:
            parse_errors += 1
            continue
        events.append(record)
    return {"events": events, "parse_errors": parse_errors}


def summarize_upstream_log(path: Path, max_lines: int = 120) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []
    tail = lines[-max_lines:]
    highlights = [line for line in tail if "Upstream error" in line or "ERROR" in line]
    return highlights if highlights else tail[-20:]


def format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def format_time(ts: float | None) -> str:
    if ts is None:
        return "n/a"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def first_useful_tool_request(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for request in requests:
        if request.get("method") != "tools/call":
            continue
        tool = request.get("tool")
        if tool in IGNORE_USEFUL_TOOL_NAMES:
            continue
        return request
    return None


def classify_startup_discovery(requests: list[dict[str, Any]]) -> str:
    useful = first_useful_tool_request(requests)
    pre_useful = []
    for request in requests:
        if useful and request is useful:
            break
        pre_useful.append(request)
    discovery = [request for request in pre_useful if request.get("method") in {"tools/list", "tools/search", "resources/list"}]
    if not discovery:
        return "direct_call"
    if any(request.get("method") == "tools/search" for request in discovery):
        first = discovery[0].get("method")
        return "search_first" if first == "tools/search" else "search_mixed"
    scoped = False
    for request in discovery:
        if request.get("method") != "tools/list":
            continue
        params = request.get("params") or {}
        if any(
            params.get(key) is not None
            for key in ("query", "q", "toolset", "includeToolsets", "excludeToolsets", "mode", "category")
        ):
            scoped = True
            break
    if scoped:
        return "scoped_list"
    if any(request.get("method") == "resources/list" for request in discovery):
        return "resource_catalog"
    return "full_catalog"


def classify_tool_search_usage(requests: list[dict[str, Any]]) -> str:
    if any(request.get("method") == "tools/search" for request in requests):
        return "used"
    scoped_search = False
    discovery_seen = False
    for request in requests:
        method = request.get("method")
        if method == "tools/list":
            discovery_seen = True
            params = request.get("params") or {}
            if any(params.get(key) is not None for key in ("query", "q", "mode", "category", "limit")):
                scoped_search = True
    if scoped_search:
        return "supported"
    if discovery_seen:
        return "unused"
    return "not evidenced"


def find_response_by_id(
    responses: list[dict[str, Any]],
    request: dict[str, Any],
) -> dict[str, Any] | None:
    req_id = request.get("id")
    transport = request.get("transport")
    for response in responses:
        if response.get("transport") != transport:
            continue
        if response.get("id") == req_id:
            return response
    return None


def extract_fallback_responses(responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for response in responses:
        result = response.get("result") or {}
        data = result.get("data") if isinstance(result, dict) else {}
        if isinstance(data, dict) and isinstance(data.get("fallback"), dict):
            rows.append(response)
    return rows


def extract_resource_reads(requests: list[dict[str, Any]]) -> list[str]:
    uris: list[str] = []
    for request in requests:
        if request.get("method") != "resources/read":
            continue
        params = request.get("params") or {}
        uri = params.get("uri") or params.get("name")
        if isinstance(uri, str):
            uris.append(uri)
    return uris


def summarize_methods(requests: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for request in requests:
        method = request.get("method")
        if isinstance(method, str):
            counts[method] += 1
    return counts
