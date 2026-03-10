from __future__ import annotations

from copy import deepcopy
from typing import Any


VALID_SCOPE_TYPES = {"conversation", "episode", "snapshot"}


def normalize_scope_type(value: str | None) -> str:
    candidate = (value or "conversation").strip().lower()
    if candidate not in VALID_SCOPE_TYPES:
        raise ValueError(f"Unsupported scope type: {value}")
    return candidate


def build_decision_episode(
    events: list[dict[str, Any]],
    *,
    scope_type: str = "conversation",
    episode_id: str | None = None,
    title: str | None = None,
    start_sequence: int | None = None,
    end_sequence: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not events:
        raise ValueError("Cannot build a decision episode without events.")

    scope = normalize_scope_type(scope_type)
    ordered = sorted(events, key=lambda event: int(event.get("sequence", 0)))
    if scope == "episode":
        filtered = [
            event
            for event in ordered
            if (start_sequence is None or int(event.get("sequence", 0)) >= start_sequence)
            and (end_sequence is None or int(event.get("sequence", 0)) <= end_sequence)
        ]
        if not filtered:
            raise ValueError("Episode range did not match any events.")
    elif scope == "snapshot":
        filtered = [
            event
            for event in ordered
            if (start_sequence is None or int(event.get("sequence", 0)) >= start_sequence)
            and (end_sequence is None or int(event.get("sequence", 0)) <= end_sequence)
        ]
        if not filtered:
            filtered = [ordered[-1]]
        elif start_sequence is None and end_sequence is None:
            filtered = [filtered[-1]]
    else:
        filtered = ordered

    conversation_id = str(filtered[0].get("conversationId") or ordered[0]["conversationId"])
    resolved_episode_id = episode_id or f"{conversation_id}-{scope}-1"
    resolved_title = title or _default_title(scope)
    copied = []
    for event in filtered:
        cloned = deepcopy(event)
        cloned["decisionEpisodeId"] = resolved_episode_id
        copied.append(cloned)

    episode = {
        "decisionEpisodeId": resolved_episode_id,
        "scopeType": scope,
        "title": resolved_title,
        "conversationId": conversation_id,
        "startSequence": copied[0]["sequence"],
        "endSequence": copied[-1]["sequence"],
        "startedAt": copied[0]["occurredAt"],
        "endedAt": copied[-1]["occurredAt"],
        "eventCount": len(copied),
    }
    return episode, copied


def _default_title(scope_type: str) -> str:
    if scope_type == "snapshot":
        return "Decision support snapshot"
    if scope_type == "episode":
        return "Decision episode"
    return "Conversation scope"
