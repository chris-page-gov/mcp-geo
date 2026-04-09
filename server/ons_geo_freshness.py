from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADDRESSBASE_EPOCH_SCHEDULE_PATH = ROOT / "resources" / "addressbase_epoch_schedule.json"
_EPOCH_RE = re.compile(r"\bepoch[\s_-]*(?P<epoch>\d+)\b", re.IGNORECASE)

_UPRN_DATASET_IDS = {"ONSUD", "NSUL"}


def load_addressbase_epoch_schedule(
    path: Path = DEFAULT_ADDRESSBASE_EPOCH_SCHEDULE_PATH,
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("epochs", [])
    if not isinstance(entries, list):
        return []
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        epoch_raw = entry.get("epoch")
        publication_raw = str(entry.get("publication_date") or "").strip()
        if not isinstance(epoch_raw, int) or not publication_raw:
            continue
        scheduled = bool(entry.get("scheduled", False))
        normalized.append(
            {
                "epoch": epoch_raw,
                "publication_date": publication_raw,
                "scheduled": scheduled,
            }
        )
    return sorted(normalized, key=lambda item: item["epoch"])


def parse_epoch_from_text(*values: str | None) -> int | None:
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        match = _EPOCH_RE.search(text)
        if match:
            return int(match.group("epoch"))
    return None


def latest_published_epoch(
    schedule: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> dict[str, Any] | None:
    current = today or date.today()
    latest: dict[str, Any] | None = None
    for entry in schedule:
        publication = date.fromisoformat(entry["publication_date"])
        if publication <= current:
            latest = entry
        else:
            break
    return latest


def next_scheduled_epoch(
    schedule: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> dict[str, Any] | None:
    current = today or date.today()
    for entry in schedule:
        publication = date.fromisoformat(entry["publication_date"])
        if publication > current:
            return entry
    return None


def summarize_uprn_dataset_freshness(
    *,
    dataset_id: str,
    resolved_release: str | None,
    resolved_source_url: str | None = None,
    today: date | None = None,
    schedule: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if dataset_id.upper() not in _UPRN_DATASET_IDS:
        return None

    epoch_schedule = schedule if schedule is not None else load_addressbase_epoch_schedule()
    latest = latest_published_epoch(epoch_schedule, today=today)
    upcoming = next_scheduled_epoch(epoch_schedule, today=today)
    resolved_epoch = parse_epoch_from_text(resolved_release, resolved_source_url)

    payload: dict[str, Any] = {
        "applicable": True,
        "datasetId": dataset_id.upper(),
        "resolvedEpoch": resolved_epoch,
        "resolvedRelease": resolved_release,
        "resolvedSourceUrl": resolved_source_url,
        "latestPublishedEpoch": latest["epoch"] if latest else None,
        "latestPublicationDate": latest["publication_date"] if latest else None,
        "nextScheduledEpoch": upcoming["epoch"] if upcoming else None,
        "nextScheduledPublicationDate": upcoming["publication_date"] if upcoming else None,
        "scheduleSource": "addressbase_epoch_schedule",
        "lagEpochs": None,
        "status": "unknown",
        "message": None,
    }

    if latest is None:
        payload["status"] = "schedule_unavailable"
        payload["message"] = "No published AddressBase epoch is available in the local schedule."
        return payload

    if resolved_epoch is None:
        payload["status"] = "epoch_unknown"
        payload["message"] = "Could not parse an epoch number from the resolved dataset metadata."
        return payload

    if resolved_epoch == latest["epoch"]:
        payload["lagEpochs"] = 0
        payload["status"] = "current"
        payload["message"] = (
            f"Resolved epoch {resolved_epoch} matches the latest published AddressBase epoch."
        )
        return payload

    if resolved_epoch < latest["epoch"]:
        payload["lagEpochs"] = latest["epoch"] - resolved_epoch
        payload["status"] = "lagging"
        payload["message"] = (
            f"Resolved epoch {resolved_epoch} lags the latest published AddressBase epoch "
            f"{latest['epoch']}."
        )
        return payload

    payload["lagEpochs"] = 0
    payload["status"] = "ahead_of_schedule"
    payload["message"] = (
        f"Resolved epoch {resolved_epoch} is ahead of the latest published AddressBase epoch "
        f"{latest['epoch']}."
    )
    return payload
