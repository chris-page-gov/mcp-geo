from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_RETENTION_CLASS = "default_operational"
VALID_RETENTION_CLASSES = {
    "default_operational",
    "foi_support",
    "investigation",
    "engineering_reconstruction",
}


def normalize_retention_class(value: str | None) -> str:
    candidate = (value or DEFAULT_RETENTION_CLASS).strip().lower()
    if candidate not in VALID_RETENTION_CLASSES:
        raise ValueError(f"Unsupported retention class: {value}")
    return candidate


def retention_state_path(pack_dir: Path) -> Path:
    return pack_dir / "retention-state.json"


def load_retention_state(pack_dir: Path) -> dict[str, Any]:
    path = retention_state_path(pack_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    audit_card_path = pack_dir / "audit-card.json"
    if audit_card_path.exists():
        audit_card = json.loads(audit_card_path.read_text(encoding="utf-8"))
        return {
            "packId": audit_card.get("packId") or pack_dir.name,
            "retentionClass": audit_card.get("retentionClass", DEFAULT_RETENTION_CLASS),
            "legalHold": bool(audit_card.get("legalHold")),
            "updatedAt": audit_card.get("createdAt"),
            "history": [],
        }
    return {
        "packId": pack_dir.name,
        "retentionClass": DEFAULT_RETENTION_CLASS,
        "legalHold": False,
        "updatedAt": _utc_now(),
        "history": [],
    }


def write_retention_state(
    pack_dir: Path,
    *,
    retention_class: str | None = None,
    legal_hold: bool | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    state = load_retention_state(pack_dir)
    if retention_class is not None:
        state["retentionClass"] = normalize_retention_class(retention_class)

    if legal_hold is not None and bool(legal_hold) != bool(state.get("legalHold")):
        state.setdefault("history", []).append(
            {
                "eventType": "audit_pack.legal_hold_applied" if legal_hold else "legal_hold.released",
                "occurredAt": _utc_now(),
                "legalHold": bool(legal_hold),
                "reason": reason,
            }
        )
        state["legalHold"] = bool(legal_hold)
    state["updatedAt"] = _utc_now()
    target = retention_state_path(pack_dir)
    target.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
