from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from server.security import mask_in_value


EVENT_SCHEMA_VERSION = "1.0.0"
SCHEMA_DIR = Path(__file__).with_name("schemas")
CANONICAL_EVENT_TYPES = (
    "conversation.started",
    "conversation.snapshot_requested",
    "conversation.closed",
    "message.user_visible",
    "message.assistant_visible",
    "message.assistant_conclusion",
    "mcp.session.initialized",
    "mcp.tools.list",
    "mcp.tool.call",
    "mcp.tool.result",
    "mcp.resource.read",
    "mcp.elicitation.requested",
    "mcp.elicitation.responded",
    "ui.choice.made",
    "ui.event.logged",
    "source.http.requested",
    "source.http.responded",
    "decision.assumption_logged",
    "decision.uncertainty_logged",
    "decision.conclusion_recorded",
    "audit_pack.created",
    "audit_pack.sealed",
    "audit_pack.redacted",
    "audit_pack.legal_hold_applied",
)
_SELECTION_EVENT_TYPES = {
    "choose",
    "choice_made",
    "choose_result",
    "pick_result",
    "select",
    "select_result",
    "selection_made",
}
_MCP_REQUEST_DIRECTIONS = {"client->server", "client->upstream"}
_MCP_RESPONSE_DIRECTIONS = {"server->client", "upstream->client"}
_ELICITATION_METHODS = {
    "elicitation/create",
    "elicitation/request",
    "elicitation/requested",
}
_TRANSCRIPT_JSON_CANDIDATES = (
    "transcript-visible.json",
    "transcript-visible.jsonl",
)
_DECISION_LOG_CANDIDATES = (
    "decision-log.json",
    "decision-log.jsonl",
)
_SOURCE_HTTP_CANDIDATES = (
    "source-http-trace.jsonl",
    "source-access.jsonl",
)


def load_event_schema() -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / "event.schema.json").read_text(encoding="utf-8"))


def build_event_ledger(session_dir: Path) -> list[dict[str, Any]]:
    session_dir = Path(session_dir)
    session_meta = _load_json_file(session_dir / "session.json")
    conversation_id = _conversation_id(session_dir, session_meta)
    pending: list[tuple[float, int, dict[str, Any]]] = []
    emission_order = 0

    for event in _normalize_session_metadata(session_dir, conversation_id, session_meta):
        pending.append((event.pop("_sort"), emission_order, event))
        emission_order += 1

    for trace_name, channel in (
        ("mcp-stdio-trace.jsonl", "mcp_stdio"),
        ("mcp-http-trace.jsonl", "mcp_http"),
    ):
        trace_path = session_dir / trace_name
        if not trace_path.exists():
            continue
        for event in _normalize_mcp_trace(trace_path, channel, conversation_id):
            pending.append((event.pop("_sort"), emission_order, event))
            emission_order += 1

    ui_path = session_dir / "ui-events.jsonl"
    if ui_path.exists():
        for event in _normalize_ui_events(ui_path, conversation_id):
            pending.append((event.pop("_sort"), emission_order, event))
            emission_order += 1

    for transcript_name in _TRANSCRIPT_JSON_CANDIDATES:
        transcript_path = session_dir / transcript_name
        if not transcript_path.exists():
            continue
        for event in _normalize_visible_transcript(transcript_path, conversation_id):
            pending.append((event.pop("_sort"), emission_order, event))
            emission_order += 1
        break

    for decision_name in _DECISION_LOG_CANDIDATES:
        decision_path = session_dir / decision_name
        if not decision_path.exists():
            continue
        for event in _normalize_decision_log(decision_path, conversation_id):
            pending.append((event.pop("_sort"), emission_order, event))
            emission_order += 1
        break

    for source_name in _SOURCE_HTTP_CANDIDATES:
        source_path = session_dir / source_name
        if not source_path.exists():
            continue
        for event in _normalize_source_http(source_path, conversation_id):
            pending.append((event.pop("_sort"), emission_order, event))
            emission_order += 1
        break

    pending.sort(key=lambda item: (item[0], item[1]))

    events: list[dict[str, Any]] = []
    for sequence, (_sort, _order, event) in enumerate(pending, start=1):
        event["sequence"] = sequence
        event["eventId"] = _event_id(conversation_id, sequence, event)
        events.append(event)
    return events


def write_event_ledger(session_dir: Path, *, output_path: Path | None = None) -> Path:
    session_dir = Path(session_dir)
    target = output_path or (session_dir / "event-ledger.jsonl")
    events = build_event_ledger(session_dir)
    contents = "".join(
        json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n" for event in events
    )
    target.write_text(contents, encoding="utf-8")
    return target


def _normalize_session_metadata(
    session_dir: Path,
    conversation_id: str,
    session_meta: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    evidence = [_evidence_ref(session_dir / "session.json", line=1)]
    started_at = _timestamp_info(session_meta.get("startedAt"))
    if started_at is not None:
        events.append(
            _build_event(
                event_type="conversation.started",
                conversation_id=conversation_id,
                occurred_at=started_at[0],
                actor_kind="system",
                channel="session_metadata",
                evidence=evidence,
                data={
                    "mode": session_meta.get("mode"),
                    "source": session_meta.get("source"),
                    "surface": session_meta.get("surface"),
                    "hostProfile": session_meta.get("hostProfile"),
                    "clientVersion": session_meta.get("clientVersion"),
                    "model": session_meta.get("model"),
                    "scenarioPack": session_meta.get("scenarioPack"),
                    "scenarioId": session_meta.get("scenarioId"),
                    "version": session_meta.get("version"),
                    "git": _sanitize(session_meta.get("git") or {}),
                    "command": _sanitize(session_meta.get("command")),
                },
                correlation={"sessionId": conversation_id},
                sort_value=started_at[1],
                message="Trace session started.",
            )
        )
    ended_at = _timestamp_info(session_meta.get("endedAt"))
    if ended_at is not None:
        events.append(
            _build_event(
                event_type="conversation.closed",
                conversation_id=conversation_id,
                occurred_at=ended_at[0],
                actor_kind="system",
                channel="session_metadata",
                evidence=evidence,
                data={
                    "exitCode": session_meta.get("exitCode"),
                },
                correlation={"sessionId": conversation_id},
                sort_value=ended_at[1],
                message="Trace session closed.",
            )
        )
    return events


def _normalize_mcp_trace(
    path: Path,
    channel: str,
    conversation_id: str,
) -> list[dict[str, Any]]:
    rows = list(_iter_jsonl(path))
    request_index: dict[tuple[str, Any], dict[str, Any]] = {}
    for line, record in enumerate(rows, start=1):
        if record.get("direction") not in _MCP_REQUEST_DIRECTIONS:
            continue
        payload = _json_rpc_payload(record)
        if not isinstance(payload, dict):
            continue
        key = (channel, payload.get("id"))
        request_index[key] = {
            "line": line,
            "payload": payload,
            "record": record,
        }

    events: list[dict[str, Any]] = []
    for line, record in enumerate(rows, start=1):
        ts_info = _timestamp_info(record.get("ts"))
        if ts_info is None:
            continue
        payload = _json_rpc_payload(record)
        if record.get("direction") in _MCP_REQUEST_DIRECTIONS:
            if not isinstance(payload, dict):
                continue
            method = _json_rpc_method(record, payload)
            if not isinstance(method, str):
                continue
            params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
            evidence = [
                _evidence_ref(
                    path,
                    line=line,
                    record_index=line - 1,
                    direction=record.get("direction"),
                )
            ]
            if method == "tools/list":
                events.append(
                    _build_event(
                        event_type="mcp.tools.list",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="client",
                        channel=channel,
                        evidence=evidence,
                        data={"params": _sanitize(params)},
                        correlation={"requestId": payload.get("id")},
                        sort_value=ts_info[1],
                        message="Client requested tool listing.",
                    )
                )
            elif method == "tools/call":
                tool_name = params.get("name") or params.get("tool")
                arguments = params.get("arguments")
                if arguments is None:
                    arguments = params.get("args")
                if arguments is None:
                    arguments = {
                        key: value
                        for key, value in params.items()
                        if key not in {"name", "tool", "arguments", "args"}
                    }
                events.append(
                    _build_event(
                        event_type="mcp.tool.call",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="client",
                        channel=channel,
                        evidence=evidence,
                        data={
                            "toolName": tool_name,
                            "arguments": _sanitize(arguments),
                        },
                        correlation={"requestId": payload.get("id"), "toolName": tool_name},
                        sort_value=ts_info[1],
                        message="Client called an MCP tool.",
                    )
                )
            elif method == "resources/read":
                uri = params.get("uri") or params.get("name")
                events.append(
                    _build_event(
                        event_type="mcp.resource.read",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="client",
                        channel=channel,
                        evidence=evidence,
                        data={"params": _sanitize(params)},
                        correlation={"requestId": payload.get("id"), "resourceUri": uri},
                        sort_value=ts_info[1],
                        message="Client requested an MCP resource.",
                    )
                )
            elif method in _ELICITATION_METHODS:
                events.append(
                    _build_event(
                        event_type="mcp.elicitation.requested",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="client",
                        channel=channel,
                        evidence=evidence,
                        data={"params": _sanitize(params)},
                        correlation={"requestId": payload.get("id")},
                        sort_value=ts_info[1],
                        message="Client requested elicitation.",
                    )
                )
        elif record.get("direction") in _MCP_RESPONSE_DIRECTIONS and isinstance(payload, dict):
            request = request_index.get((channel, payload.get("id")))
            if request is None:
                continue
            request_payload = request["payload"]
            method = _json_rpc_method(request["record"], request_payload)
            if not isinstance(method, str):
                continue
            evidence = [
                _evidence_ref(
                    path,
                    line=line,
                    record_index=line - 1,
                    direction=record.get("direction"),
                )
            ]
            if method == "initialize":
                events.append(
                    _build_event(
                        event_type="mcp.session.initialized",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="server",
                        channel=channel,
                        evidence=evidence,
                        data={
                            "capabilities": _sanitize(
                                request_payload.get("params", {}).get("capabilities")
                                if isinstance(request_payload.get("params"), dict)
                                else {}
                            ),
                            "result": _sanitize(payload.get("result") or {}),
                            "error": _sanitize(payload.get("error") or {}),
                        },
                        correlation={"requestId": payload.get("id")},
                        sort_value=ts_info[1],
                        message="MCP session initialized.",
                        status="error" if isinstance(payload.get("error"), dict) else "observed",
                    )
                )
            elif method == "tools/call":
                params = (
                    request_payload.get("params")
                    if isinstance(request_payload.get("params"), dict)
                    else {}
                )
                tool_name = params.get("name") or params.get("tool")
                status = "observed"
                if isinstance(payload.get("error"), dict):
                    status = "error"
                else:
                    result = payload.get("result")
                    if isinstance(result, dict):
                        result_data = result.get("data")
                        if result.get("isError") or (
                            isinstance(result_data, dict) and result_data.get("isError")
                        ):
                            status = "error"
                events.append(
                    _build_event(
                        event_type="mcp.tool.result",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="server",
                        channel=channel,
                        evidence=evidence,
                        data={
                            "toolName": tool_name,
                            "result": _sanitize(payload.get("result") or {}),
                            "error": _sanitize(payload.get("error") or {}),
                        },
                        correlation={"requestId": payload.get("id"), "toolName": tool_name},
                        sort_value=ts_info[1],
                        message="MCP tool returned a result.",
                        status=status,
                    )
                )
            elif method in _ELICITATION_METHODS:
                events.append(
                    _build_event(
                        event_type="mcp.elicitation.responded",
                        conversation_id=conversation_id,
                        occurred_at=ts_info[0],
                        actor_kind="server",
                        channel=channel,
                        evidence=evidence,
                        data={
                            "result": _sanitize(payload.get("result") or {}),
                            "error": _sanitize(payload.get("error") or {}),
                        },
                        correlation={"requestId": payload.get("id")},
                        sort_value=ts_info[1],
                        message="Elicitation response recorded.",
                        status="error" if isinstance(payload.get("error"), dict) else "observed",
                    )
                )
    return events


def _normalize_ui_events(path: Path, conversation_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line, record in enumerate(_iter_jsonl(path), start=1):
        ts_info = _timestamp_info(record.get("timestamp"))
        if ts_info is None:
            continue
        raw_event_type = str(record.get("eventType") or "").strip()
        normalized_type = "ui.event.logged"
        if raw_event_type.lower() in _SELECTION_EVENT_TYPES:
            normalized_type = "ui.choice.made"
        message = "UI event logged."
        if normalized_type != "ui.event.logged":
            message = "UI choice recorded."
        events.append(
            _build_event(
                event_type=normalized_type,
                conversation_id=conversation_id,
                occurred_at=ts_info[0],
                actor_kind="ui",
                channel="ui_event_log",
                evidence=[_evidence_ref(path, line=line, record_index=line - 1)],
                data={
                    "source": record.get("source"),
                    "payload": _sanitize(record.get("payload")),
                    "context": _sanitize(record.get("context")),
                    "originalEventType": raw_event_type,
                },
                correlation={"uiEventId": record.get("eventId")},
                sort_value=ts_info[1],
                message=message,
            )
        )
    return events


def _normalize_visible_transcript(path: Path, conversation_id: str) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows = list(_iter_jsonl(path))
    else:
        payload = _load_json_value(path)
        rows = payload if isinstance(payload, list) else []
    events: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        ts_info = _timestamp_info(row.get("timestamp") or row.get("createdAt"))
        if ts_info is None:
            continue
        role = str(row.get("role") or "").strip().lower()
        event_type = "message.assistant_visible"
        actor_kind = "assistant"
        if role == "user":
            event_type = "message.user_visible"
            actor_kind = "user"
        elif bool(row.get("isConclusion")) or (
            str(row.get("messageType") or "").strip().lower() == "conclusion"
        ):
            event_type = "message.assistant_conclusion"
        events.append(
            _build_event(
                event_type=event_type,
                conversation_id=conversation_id,
                occurred_at=ts_info[0],
                actor_kind=actor_kind,
                channel="transcript_visible",
                evidence=[_evidence_ref(path, line=index, record_index=index - 1)],
                data={"content": _sanitize(row.get("content")), "role": role},
                correlation={},
                sort_value=ts_info[1],
                message="Visible transcript message recorded.",
            )
        )
    return events


def _normalize_source_http(path: Path, conversation_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line, row in enumerate(_iter_jsonl(path), start=1):
        ts_info = _timestamp_info(row.get("ts") or row.get("timestamp"))
        if ts_info is None:
            continue
        direction = str(row.get("direction") or "").strip().lower()
        if "request" in direction or direction.endswith("->source"):
            event_type = "source.http.requested"
            actor_kind = "source"
            message = "Source HTTP request recorded."
        elif "response" in direction or direction.startswith("source->"):
            event_type = "source.http.responded"
            actor_kind = "source"
            message = "Source HTTP response recorded."
        else:
            continue
        events.append(
            _build_event(
                event_type=event_type,
                conversation_id=conversation_id,
                occurred_at=ts_info[0],
                actor_kind=actor_kind,
                channel="source_http",
                evidence=[_evidence_ref(path, line=line, record_index=line - 1)],
                data=_sanitize(row),
                correlation={"source": row.get("source"), "status": row.get("status")},
                sort_value=ts_info[1],
                message=message,
            )
        )
    return events


def _normalize_decision_log(path: Path, conversation_id: str) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows = list(_iter_jsonl(path))
    else:
        payload = _load_json_value(path)
        rows = payload if isinstance(payload, list) else []
    events: list[dict[str, Any]] = []
    kind_to_event = {
        "assumption": "decision.assumption_logged",
        "uncertainty": "decision.uncertainty_logged",
        "conclusion": "decision.conclusion_recorded",
    }
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        ts_info = _timestamp_info(
            row.get("timestamp") or row.get("occurredAt") or row.get("createdAt")
        )
        if ts_info is None:
            continue
        kind = str(row.get("kind") or row.get("type") or row.get("eventType") or "").strip().lower()
        event_type = kind_to_event.get(kind)
        if event_type is None:
            continue
        content = row.get("content")
        if content is None:
            content = row.get("message") or row.get("text")
        events.append(
            _build_event(
                event_type=event_type,
                conversation_id=conversation_id,
                occurred_at=ts_info[0],
                actor_kind="assistant",
                channel="transcript_visible",
                evidence=[_evidence_ref(path, line=index, record_index=index - 1)],
                data={"content": _sanitize(content), "kind": kind},
                correlation={"decisionId": row.get("decisionId")},
                sort_value=ts_info[1],
                message="Decision log entry recorded.",
            )
        )
    return events


def _build_event(
    *,
    event_type: str,
    conversation_id: str,
    occurred_at: str,
    actor_kind: str,
    channel: str,
    evidence: list[dict[str, Any]],
    data: dict[str, Any],
    correlation: dict[str, Any],
    sort_value: float,
    message: str | None = None,
    status: str = "observed",
) -> dict[str, Any]:
    return {
        "schemaVersion": EVENT_SCHEMA_VERSION,
        "eventType": event_type,
        "conversationId": conversation_id,
        "decisionEpisodeId": None,
        "occurredAt": occurred_at,
        "actor": {"kind": actor_kind, "id": None},
        "channel": channel,
        "status": status,
        "message": message,
        "data": data,
        "correlation": correlation,
        "evidence": evidence,
        "_sort": sort_value,
    }


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = _load_json_value(path)
    return payload if isinstance(payload, dict) else {}


def _load_json_value(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _json_rpc_payload(record: dict[str, Any]) -> dict[str, Any] | None:
    payload = record.get("json")
    return payload if isinstance(payload, dict) else None


def _json_rpc_method(record: dict[str, Any], payload: dict[str, Any]) -> str | None:
    method = payload.get("method")
    if isinstance(method, str):
        return method
    method_name = record.get("method_name")
    if isinstance(method_name, str):
        return method_name
    return None


def _timestamp_info(value: Any) -> tuple[str, float] | None:
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(float(value), tz=UTC)
        return dt.isoformat().replace("+00:00", "Z"), float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        return dt.isoformat().replace("+00:00", "Z"), dt.timestamp()
    return None


def _conversation_id(session_dir: Path, session_meta: dict[str, Any]) -> str:
    session_id = session_meta.get("sessionId")
    if isinstance(session_id, str) and session_id.strip():
        return session_id.strip()
    return session_dir.name


def _sanitize(value: Any) -> Any:
    return mask_in_value(value, [])


def _event_id(conversation_id: str, sequence: int, event: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        f"{conversation_id}:{sequence}:{event['eventType']}:{event['occurredAt']}".encode("utf-8")
    ).hexdigest()
    return f"evt_{digest[:16]}"


def _evidence_ref(
    path: Path,
    *,
    line: int | None = None,
    record_index: int | None = None,
    direction: str | None = None,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "kind": "file_record" if record_index is not None else "file",
        "path": str(path),
    }
    if line is not None:
        ref["line"] = line
    if record_index is not None:
        ref["recordIndex"] = record_index
    if isinstance(direction, str) and direction:
        ref["direction"] = direction
    return ref


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize a trace session into DSAP events.")
    parser.add_argument("session_dir", help="Session directory containing trace artifacts.")
    parser.add_argument(
        "--output",
        help="Optional event-ledger output path. Defaults to <session-dir>/event-ledger.jsonl.",
    )
    args = parser.parse_args()

    output = write_event_ledger(
        Path(args.session_dir),
        output_path=Path(args.output) if args.output else None,
    )
    print(output)
