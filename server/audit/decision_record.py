from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_decision_record(
    events: list[dict[str, Any]],
    episode: dict[str, Any],
) -> dict[str, Any]:
    assumptions = []
    uncertainties = []
    conclusions = []

    for event in events:
        event_type = event.get("eventType")
        if event_type == "decision.assumption_logged":
            assumptions.append(_decision_entry(event))
        elif event_type == "decision.uncertainty_logged":
            uncertainties.append(_decision_entry(event))
        elif event_type == "decision.conclusion_recorded":
            conclusions.append(_decision_entry(event))
        elif event_type == "message.assistant_conclusion":
            conclusions.append(
                {
                    "eventId": event.get("eventId"),
                    "occurredAt": event.get("occurredAt"),
                    "content": _extract_content(event),
                    "source": "assistant_visible_conclusion",
                }
            )

    gaps = []
    if not assumptions:
        gaps.append("No explicit assumption evidence retained.")
    if not uncertainties:
        gaps.append("No explicit uncertainty evidence retained.")
    if not conclusions:
        gaps.append("No explicit conclusion evidence retained.")

    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "conversationId": episode["conversationId"],
        "decisionEpisodeId": episode["decisionEpisodeId"],
        "scopeType": episode["scopeType"],
        "assumptions": assumptions,
        "uncertainties": uncertainties,
        "conclusions": conclusions,
        "counts": {
            "assumptions": len(assumptions),
            "uncertainties": len(uncertainties),
            "conclusions": len(conclusions),
        },
        "gaps": gaps,
    }


def _decision_entry(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": event.get("eventId"),
        "occurredAt": event.get("occurredAt"),
        "content": _extract_content(event),
        "source": event.get("eventType"),
    }


def _extract_content(event: dict[str, Any]) -> Any:
    data = event.get("data")
    if isinstance(data, dict):
        for key in ("content", "message", "text", "value"):
            if key in data:
                return data[key]
    return event.get("message")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
