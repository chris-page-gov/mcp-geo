from __future__ import annotations

import json
import threading
from collections import defaultdict
from typing import Any

_TOOL_LATENCY_BUCKETS = [5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000]
_TOOL_LOCK = threading.Lock()
_TOOL_CALLS_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_ERRORS_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_LATENCY_SUM_MS: dict[tuple[str, str], float] = defaultdict(float)
_TOOL_LATENCY_COUNT: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_LATENCY_HIST: dict[tuple[str, str], dict[int, int]] = {}
_TOOL_LATENCY_OVERFLOW: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_INPUT_BYTES_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_OUTPUT_BYTES_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_CACHE_HITS_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_TOOL_FALLBACK_TOTAL: dict[tuple[str, str], int] = defaultdict(int)

_PLAYGROUND_LOCK = threading.Lock()
_PLAYGROUND_TOOL_CALL_RECORDS_TOTAL = 0
_PLAYGROUND_ORCHESTRATION_REQUESTS_TOTAL = 0
_PLAYGROUND_EVENTS_TOTAL: dict[str, int] = defaultdict(int)


def _label_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _json_size_bytes(value: Any) -> int:
    try:
        encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    except Exception:
        encoded = str(value)
    return len(encoded.encode("utf-8"))


def _tool_key(tool_name: str, transport: str) -> tuple[str, str]:
    tool = tool_name.strip() if isinstance(tool_name, str) and tool_name.strip() else "unknown"
    kind = transport.strip() if isinstance(transport, str) and transport.strip() else "unknown"
    return tool, kind


def _result_has_cache_hit(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    if result.get("cacheHit") is True or result.get("fromCache") is True:
        return True
    meta = result.get("meta")
    if isinstance(meta, dict):
        if meta.get("cacheHit") is True:
            return True
        source = str(meta.get("source") or "").strip().lower()
        if source == "cache":
            return True
    return False


def _result_has_fallback(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    if result.get("fallback") is not None:
        return True
    meta = result.get("meta")
    return isinstance(meta, dict) and meta.get("fallback") is True


def record_tool_call(
    *,
    tool_name: str,
    transport: str,
    payload: Any,
    result: Any,
    status_code: int,
    latency_ms: float,
) -> None:
    key = _tool_key(tool_name, transport)
    input_size = _json_size_bytes(payload)
    output_size = _json_size_bytes(result)
    is_error = status_code >= 400 or (isinstance(result, dict) and result.get("isError") is True)
    cache_hit = _result_has_cache_hit(result)
    fallback = _result_has_fallback(result)

    with _TOOL_LOCK:
        _TOOL_CALLS_TOTAL[key] += 1
        if is_error:
            _TOOL_ERRORS_TOTAL[key] += 1
        _TOOL_LATENCY_SUM_MS[key] += max(latency_ms, 0.0)
        _TOOL_LATENCY_COUNT[key] += 1
        hist = _TOOL_LATENCY_HIST.setdefault(
            key,
            {bucket: 0 for bucket in _TOOL_LATENCY_BUCKETS},
        )
        for bucket in _TOOL_LATENCY_BUCKETS:
            if latency_ms <= bucket:
                hist[bucket] += 1
                break
        else:
            _TOOL_LATENCY_OVERFLOW[key] += 1
        _TOOL_INPUT_BYTES_TOTAL[key] += input_size
        _TOOL_OUTPUT_BYTES_TOTAL[key] += output_size
        if cache_hit:
            _TOOL_CACHE_HITS_TOTAL[key] += 1
        if fallback:
            _TOOL_FALLBACK_TOTAL[key] += 1


def record_playground_tool_call(_tool_name: str) -> None:
    global _PLAYGROUND_TOOL_CALL_RECORDS_TOTAL
    with _PLAYGROUND_LOCK:
        _PLAYGROUND_TOOL_CALL_RECORDS_TOTAL += 1


def record_playground_event(event_type: str) -> None:
    key = event_type.strip() if isinstance(event_type, str) and event_type.strip() else "unknown"
    with _PLAYGROUND_LOCK:
        _PLAYGROUND_EVENTS_TOTAL[key] += 1


def record_playground_orchestration_request() -> None:
    global _PLAYGROUND_ORCHESTRATION_REQUESTS_TOTAL
    with _PLAYGROUND_LOCK:
        _PLAYGROUND_ORCHESTRATION_REQUESTS_TOTAL += 1


def build_prometheus_lines() -> list[str]:
    lines: list[str] = [
        "# HELP mcp_tool_calls_total Total tool calls by tool and transport",
        "# TYPE mcp_tool_calls_total counter",
        "# HELP mcp_tool_errors_total Total failing tool calls by tool and transport",
        "# TYPE mcp_tool_errors_total counter",
        "# HELP mcp_tool_latency_ms Tool call latency histogram in milliseconds",
        "# TYPE mcp_tool_latency_ms histogram",
        "# HELP mcp_tool_payload_bytes_total Total tool payload bytes by direction",
        "# TYPE mcp_tool_payload_bytes_total counter",
        "# HELP mcp_tool_cache_hits_total Total tool results flagged as cache hits",
        "# TYPE mcp_tool_cache_hits_total counter",
        "# HELP mcp_tool_fallback_total Total tool results that included fallback payloads",
        "# TYPE mcp_tool_fallback_total counter",
        "# HELP playground_tool_call_records_total Total /playground/tool_call records",
        "# TYPE playground_tool_call_records_total counter",
        "# HELP playground_orchestration_requests_total Total /playground/orchestration reads",
        "# TYPE playground_orchestration_requests_total counter",
        "# HELP playground_events_total Total playground events by type",
        "# TYPE playground_events_total counter",
    ]

    with _TOOL_LOCK:
        keys = sorted(_TOOL_CALLS_TOTAL.keys())
        for tool, transport in keys:
            labels = (
                f'{{tool="{_label_escape(tool)}",transport="{_label_escape(transport)}"}}'
            )
            key = (tool, transport)
            calls = _TOOL_CALLS_TOTAL.get(key, 0)
            errors = _TOOL_ERRORS_TOTAL.get(key, 0)
            lines.append(f"mcp_tool_calls_total{labels} {calls}")
            lines.append(f"mcp_tool_errors_total{labels} {errors}")

            cumulative = 0
            hist = _TOOL_LATENCY_HIST.get(key, {})
            for bucket in _TOOL_LATENCY_BUCKETS:
                cumulative += hist.get(bucket, 0)
                lines.append(
                    "mcp_tool_latency_ms_bucket"
                    f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\","
                    f"le=\"{bucket}\"}} {cumulative}"
                )
            overflow = _TOOL_LATENCY_OVERFLOW.get(key, 0)
            count = cumulative + overflow
            lines.append(
                "mcp_tool_latency_ms_bucket"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\","
                f'le="+Inf"}} {count}'
            )
            lines.append(
                "mcp_tool_latency_ms_count"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\"}} {count}"
            )
            lines.append(
                "mcp_tool_latency_ms_sum"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\"}} "
                f"{_TOOL_LATENCY_SUM_MS.get(key, 0.0):.6f}"
            )

            input_total = _TOOL_INPUT_BYTES_TOTAL.get(key, 0)
            output_total = _TOOL_OUTPUT_BYTES_TOTAL.get(key, 0)
            lines.append(
                "mcp_tool_payload_bytes_total"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\","
                f'direction="input"}} {input_total}'
            )
            lines.append(
                "mcp_tool_payload_bytes_total"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\","
                f'direction="output"}} {output_total}'
            )
            lines.append(
                "mcp_tool_cache_hits_total"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\"}} "
                f"{_TOOL_CACHE_HITS_TOTAL.get(key, 0)}"
            )
            lines.append(
                "mcp_tool_fallback_total"
                f"{{tool=\"{_label_escape(tool)}\",transport=\"{_label_escape(transport)}\"}} "
                f"{_TOOL_FALLBACK_TOTAL.get(key, 0)}"
            )

    with _PLAYGROUND_LOCK:
        lines.append(f"playground_tool_call_records_total {_PLAYGROUND_TOOL_CALL_RECORDS_TOTAL}")
        lines.append(
            "playground_orchestration_requests_total "
            f"{_PLAYGROUND_ORCHESTRATION_REQUESTS_TOTAL}"
        )
        for event_type in sorted(_PLAYGROUND_EVENTS_TOTAL.keys()):
            total = _PLAYGROUND_EVENTS_TOTAL[event_type]
            lines.append(
                "playground_events_total"
                f"{{event_type=\"{_label_escape(event_type)}\"}} {total}"
            )

    return lines
