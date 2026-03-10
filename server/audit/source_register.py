from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


_HELD_STATUSES = {"held", "partial", "not_held"}


def build_source_register(events: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    conversation_id = str(events[0].get("conversationId")) if events else ""

    for event in events:
        event_type = event.get("eventType")
        if event_type not in {"source.http.requested", "source.http.responded"}:
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        correlation = event.get("correlation") if isinstance(event.get("correlation"), dict) else {}
        source_access_id = _source_access_id(event, data, correlation)
        entry = grouped.setdefault(
            source_access_id,
            {
                "sourceAccessId": source_access_id,
                "source": data.get("source") or correlation.get("source"),
                "method": data.get("method"),
                "url": data.get("url"),
                "requestedAt": None,
                "respondedAt": None,
                "statusCode": None,
                "requestEventId": None,
                "responseEventId": None,
                "requestHeldStatus": None,
                "responseHeldStatus": None,
                "heldStatus": None,
                "evidence": [],
            },
        )
        if data.get("source") and not entry["source"]:
            entry["source"] = data["source"]
        if data.get("method") and not entry["method"]:
            entry["method"] = data["method"]
        if data.get("url") and not entry["url"]:
            entry["url"] = data["url"]
        if event_type == "source.http.requested":
            entry["requestedAt"] = event.get("occurredAt")
            entry["requestEventId"] = event.get("eventId")
            entry["requestHeldStatus"] = _normalize_held_status(data.get("heldStatus"))
        else:
            entry["respondedAt"] = event.get("occurredAt")
            entry["responseEventId"] = event.get("eventId")
            entry["responseHeldStatus"] = _normalize_held_status(data.get("heldStatus"))
            status_code = data.get("status") or data.get("statusCode")
            if status_code is not None:
                entry["statusCode"] = status_code
        evidence = event.get("evidence") if isinstance(event.get("evidence"), list) else []
        entry["evidence"].extend(evidence)

    entries = []
    for entry in grouped.values():
        entry["heldStatus"] = _combine_held_status(
            entry["requestHeldStatus"],
            entry["responseHeldStatus"],
            entry["requestedAt"] is not None,
            entry["respondedAt"] is not None,
        )
        entries.append(entry)

    entries.sort(key=lambda entry: (str(entry.get("requestedAt") or entry.get("respondedAt") or ""), entry["sourceAccessId"]))
    counts = {"held": 0, "partial": 0, "not_held": 0}
    for entry in entries:
        counts[entry["heldStatus"]] += 1

    gaps = []
    if not entries:
        gaps.append("No explicit source access evidence retained.")
    if counts["partial"]:
        gaps.append("One or more source accesses are only partially retained.")
    if counts["not_held"]:
        gaps.append("One or more source accesses are referenced but not held.")

    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "conversationId": conversation_id,
        "entries": entries,
        "counts": counts,
        "gaps": gaps,
    }


def _source_access_id(
    event: dict[str, Any],
    data: dict[str, Any],
    correlation: dict[str, Any],
) -> str:
    for key in ("sourceAccessId", "requestId", "traceId"):
        value = data.get(key) or correlation.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(event.get("eventId"))


def _normalize_held_status(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _HELD_STATUSES:
        return normalized
    return None


def _combine_held_status(
    request_status: str | None,
    response_status: str | None,
    has_request: bool,
    has_response: bool,
) -> str:
    explicit = [status for status in (request_status, response_status) if status]
    if "not_held" in explicit:
        return "not_held"
    if "partial" in explicit:
        return "partial"
    if explicit and all(status == "held" for status in explicit) and has_request and has_response:
        return "held"
    if has_request and has_response:
        return "held"
    if has_request or has_response:
        return "partial"
    return "not_held"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
